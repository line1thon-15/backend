"""연습 세션 통합 테스트 공용 헬퍼 (T-99 ② — PR #33 후속 권고 3 "다른 테스트 모듈의 헬퍼 import 의존성 정리").

원래 `test_practice_sessions.py`(RecordingPracticeAI·Env·콘텐츠 상수)와 `test_practice_weak_priority.py`(WeakEnv)에
있던 정의를 옮겼다. 두 모듈은 여기서 다시 가져다 쓴다(동작 변경 없음).

AI는 포트(`app.ai_client.ports.PracticeAI`)를 만족하는 기록용 Fake로만 호출한다(실제 HTTP 없음).
"""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.ai_client.fake import FakePracticeAI
from app.ai_client.ports import AIUnavailableError
from app.content.loader import load_content
from app.db.models import CueResult, PracticeSession, PracticeTurn

CONTENT = load_content()
SCAM_SCENARIO_IDS = {sid for sid, entry in CONTENT.scenarios.items() if entry.area == "scam"}
SCENARIO_CLUES = {
    sid: tuple(clue.id for clue in entry.scenario.clues) for sid, entry in CONTENT.scenarios.items()
}
# WeakEnv.past_session의 기준 시각 (원래 test_practice_weak_priority.T0)
WEAK_T0 = datetime(2026, 11, 1, 3, 0, 0, tzinfo=timezone.utc)


class RecordingPracticeAI(FakePracticeAI):
    """FakePracticeAI에 호출 기록·실패 주입·응답 덮어쓰기를 더한 테스트용 구현."""

    def __init__(self) -> None:
        super().__init__(scenario_clue_ids=SCENARIO_CLUES)
        self.calls: list[tuple[str, Any]] = []
        self.fail: set[str] = set()
        self.overrides: dict[str, Callable[[Any, Any], Any]] = {}

    def names(self) -> list[str]:
        return [name for name, _ in self.calls]

    def requests(self, name: str) -> list[Any]:
        return [request for call, request in self.calls if call == name]

    def _run(self, name: str, request: Any, default: Callable[[Any], Any]) -> Any:
        self.calls.append((name, request))
        if name in self.fail:
            raise AIUnavailableError(f"{name} failed")
        response = default(request)
        if name in self.overrides:
            response = self.overrides[name](request, response)
        return response

    def variant(self, request):
        return self._run("variant", request, super().variant)

    def start(self, request):
        return self._run("start", request, super().start)

    def turn(self, request):
        return self._run("turn", request, super().turn)

    def judge(self, request):
        return self._run("judge", request, super().judge)

    def feedback(self, request):
        return self._run("feedback", request, super().feedback)


class Env:
    def __init__(self, client: TestClient, ai: RecordingPracticeAI) -> None:
        self.client = client
        self.ai = ai
        self.session_factory = client.app.state.session_factory
        self._guardian_count = 0

    # ---- 계정 ----------------------------------------------------------------

    def login_child(self, grade: str = "H1", favorite_apps: list[str] | None = None) -> UUID:
        self._guardian_count += 1
        self.client.cookies.clear()
        guardian = self.client.post(
            "/api/v1/guardians",
            json={"email": f"parent{self._guardian_count}@example.com", "password": "correct-horse-42"},
        )
        assert guardian.status_code == 201
        child = self.client.post(
            "/api/v1/children",
            json={"consent_agreed": True, "consent_version": "v1", "nickname": "하늘이", "grade": grade, "pin": "1234"},
        )
        assert child.status_code == 201
        self.client.cookies.clear()
        login = self.client.post(
            "/api/v1/auth/child/login", json={"link_code": child.json()["link_code"], "pin": "1234"}
        )
        assert login.status_code == 200
        if favorite_apps is not None:
            saved = self.client.put(
                "/api/v1/me/onboarding",
                json={
                    "display": {"font_scale": "normal", "high_contrast": False, "tts_enabled": False},
                    "trusted_contact": {"name": "엄마", "phone": "010-1234-5678"},
                    "diagnosis_answers": [
                        {"question_id": "q1", "option_id": "q1_a"},
                        {"question_id": "q2", "option_id": "q2_a"},
                        {"question_id": "q3", "option_id": "q3_a"},
                    ],
                    "favorite_apps": favorite_apps,
                },
            )
            assert saved.status_code == 200
        return UUID(child.json()["child_id"])

    # ---- API -----------------------------------------------------------------

    def start(self, area: str = "scam"):
        return self.client.post("/api/v1/practice/sessions", json={"mode": "area", "area": area})

    def started(self) -> dict:
        response = self.start()
        assert response.status_code == 201, response.text
        return response.json()

    def answer(self, session_id: str, choice_id: str, turn_index: int | None = None):
        """A17 `{choice_id, turn_index}` (T-91). turn_index를 안 주면 DB의 현재(마지막) 턴 번호를 담는다 —
        프론트가 A15·A16 응답의 `turn.turn_index`를 그대로 보내는 것과 같다."""
        if turn_index is None:
            turn_index = self.current_turn_index(session_id)
        return self.client.post(
            f"/api/v1/practice/sessions/{session_id}/turns",
            json={"choice_id": choice_id, "turn_index": turn_index},
        )

    def get(self, session_id: str):
        return self.client.get(f"/api/v1/practice/sessions/{session_id}")

    # ---- DB ------------------------------------------------------------------

    def session_row(self, session_id: str) -> PracticeSession:
        with self.session_factory() as db:
            return db.get(PracticeSession, UUID(session_id))

    def turn_rows(self, session_id: str) -> list[PracticeTurn]:
        with self.session_factory() as db:
            return list(
                db.scalars(
                    select(PracticeTurn)
                    .where(PracticeTurn.session_id == UUID(session_id))
                    .order_by(PracticeTurn.turn_index)
                )
            )

    def current_turn_index(self, session_id: str) -> int:
        """현재(마지막) 턴 번호 — 없는 세션·남의 세션이면 0(요청 형식만 맞춘다)."""
        try:
            key = UUID(session_id)
        except ValueError:
            return 0
        with self.session_factory() as db:
            value = db.scalar(select(func.max(PracticeTurn.turn_index)).where(PracticeTurn.session_id == key))
        return 0 if value is None else value

    def cue_rows(self, session_id: str) -> list[CueResult]:
        with self.session_factory() as db:
            return list(db.scalars(select(CueResult).where(CueResult.session_id == UUID(session_id))))

    def count(self, model) -> int:
        with self.session_factory() as db:
            return db.scalar(select(func.count()).select_from(model))


class WeakEnv(Env):
    def __init__(self, client: TestClient, ai: RecordingPracticeAI) -> None:
        super().__init__(client, ai)
        self._day = 0

    def past_session(
        self,
        child_id: UUID,
        cues: dict[str, str],
        *,
        status: str = "ended",
        ended_at: datetime | None = None,
    ) -> None:
        """과거 세션 1개 + 단서 판정 행. 시나리오 ID는 콘텐츠에 없는 값(F-12 직전 변형 조회에 끼지 않게).
        `ended_at`을 주지 않으면 WEAK_T0부터 하루씩 늘린다."""
        self._day += 1
        ended_at = ended_at or WEAK_T0 + timedelta(days=self._day)
        with self.session_factory.begin() as db:
            # 순번은 그 아이 live 최댓값 + 1 — 고유 인덱스(child_id, origin, draw_index)와 겹치지 않게 (T-99 ①, ADR-0023)
            live_max = db.scalar(
                select(func.max(PracticeSession.draw_index)).where(
                    PracticeSession.child_id == child_id, PracticeSession.origin == "live"
                )
            )
            row = PracticeSession(
                child_id=child_id,
                mode="area",
                area="scam",
                subtype=None,
                scenario_id=f"past_{self._day}",
                is_normal=False,
                target_cue_ids=sorted(cues),
                variant={"platform": "sms", "tone": "friendly"},
                scenario_title="제목",
                child_setup="설정",
                ai_role_name="상대",
                retry_of=None,
                draw_index=(live_max or 0) + 1,
                hint_level=None,
                status=status,
                normal_outcome=None,
                origin="live",
                started_at=ended_at,
                ended_at=None if status == "in_progress" else ended_at,
            )
            db.add(row)
            db.flush()
            for cue_id, outcome in cues.items():
                db.add(
                    CueResult(
                        session_id=row.id, child_id=child_id, cue_id=cue_id, outcome=outcome, recorded_at=ended_at
                    )
                )

    def drawn_scenario(self) -> str:
        view = self.started()
        return self.session_row(view["session_id"]).scenario_id
