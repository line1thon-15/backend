"""보호자 리포트 A11 `GET /children/{child_id}/report` (T-25 — F-30 ①②③④, N-05, F-48 ④ 1차).

근거: Architecture "API 규격" A11, "응답 DTO" GuardianReport·GuardianSummaryView·NoticeView·MetricView,
"보호자용 응답 금지 필드", 엔티티 practice_turns "보호자용 API는 이 테이블을 읽지 않는다",
"보안·개인정보" 인가 — 보호자(`get_owned_child`, 404 `CHILD_NOT_FOUND`)·역할 분리(403 `FORBIDDEN_ROLE`),
테스트 전략 "IDOR·보호자 응답 금지 키 0건", Tasks T-25 행(금지 키 목록·`status = ended`만·영역 값).

연습 기록은 DB에 직접 넣는다(AI 호출 없음). DB는 테스트마다 pytest tmp_path SQLite 파일.
`notices`·`metrics`·`summary`는 이 브랜치에 원천(guardian_notices 테이블·T-46·T-76)이 없어 빈 값·자리표시 값이다
(T-25 보고 Open Question — 확정 동작이 아님).
"""

import json
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import event

from app.api.report import GuardianReportResponse
from app.content.loader import load_content
from app.core.config import Settings
from app.db.base import Base
from app.db.models import CueResult, PracticeSession, PracticeTurn
from app.main import create_app

CONTENT = load_content()
MARKER = "GUARDIAN-REPORT-MARKER-5b1e"
T0 = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)

# Architecture "보호자용 응답 금지 필드" + Tasks T-25 행 + 원문·마스킹·이미지·감정 상태의 흔한 키 이름.
# `feedback`·`sentences`(심화 연습 피드백 DeepFeedbackView) 중 `sentences`는 GuardianSummaryView가 쓰므로
# 심화 연습 피드백은 `feedback`·`deep_feedback` 키로 검사한다.
FORBIDDEN_KEYS = frozenset(
    {
        # 메시지 원문·마스킹 텍스트·이미지 (F-30 ②)
        "message_text", "raw_text", "original_text", "masked_text", "extracted_text", "text",
        "image", "image_url", "images", "upload", "uploads",
        # 감정 상태 (F-30 ②, F-25)
        "emotion", "emotion_level", "emotion_score", "emotion_temperature", "temperature", "mood",
        # 연습 대화 문장·고른 선택지·태그 (F-30 ③, DECISIONS #87·#93)
        "ai_line", "choices", "chosen_choice_id", "judgment", "kind", "target_clue_id",
        "revealed_clue_ids", "messages", "history", "reply", "opening_line", "variant",
        # 심화 연습 (F-48 ④)
        "answer_text", "feedback", "deep_feedback",
    }
)


def all_keys(value) -> list[str]:
    if isinstance(value, dict):
        keys = list(value)
        for item in value.values():
            keys.extend(all_keys(item))
        return keys
    if isinstance(value, list):
        return [key for item in value for key in all_keys(item)]
    return []


class Env:
    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.session_factory = client.app.state.session_factory
        self._count = 0

    def new_guardian(self) -> dict:
        """보호자 가입 → 쿠키 반환 (클라이언트 쿠키는 비워 둔다)."""
        self._count += 1
        self.client.cookies.clear()
        response = self.client.post(
            "/api/v1/guardians",
            json={"email": f"guardian{self._count}@example.com", "password": "correct-horse-42"},
        )
        assert response.status_code == 201, response.text
        cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        return cookies

    def new_child(self, guardian_cookies: dict, nickname: str = "하늘이") -> dict:
        self.client.cookies.clear()
        self.client.cookies.update(guardian_cookies)
        response = self.client.post(
            "/api/v1/children",
            json={"consent_agreed": True, "consent_version": "v1", "nickname": nickname, "grade": "H1", "pin": "1234"},
        )
        assert response.status_code == 201, response.text
        self.client.cookies.clear()
        return response.json()

    def child_cookies(self, link_code: str) -> dict:
        self.client.cookies.clear()
        response = self.client.post("/api/v1/auth/child/login", json={"link_code": link_code, "pin": "1234"})
        assert response.status_code == 200, response.text
        cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        return cookies

    def report(self, child_id: str, cookies: dict | None):
        self.client.cookies.clear()
        if cookies:
            self.client.cookies.update(cookies)
        response = self.client.get(f"/api/v1/children/{child_id}/report")
        self.client.cookies.clear()
        return response

    def seed_session(
        self,
        child_id: str,
        *,
        area: str = "scam",
        status: str = "ended",
        ended_at: datetime | None = T0,
        outcomes: dict[str, str] | None = None,
    ) -> UUID:
        """연습 세션 1개 + 대사·선택지 문장에 표지가 든 턴 1개 + cue_results."""
        with self.session_factory.begin() as db:
            row = PracticeSession(
                child_id=UUID(child_id),
                mode="area",
                area=area,
                subtype=None,
                scenario_id="scam_dm_parttime_01",
                is_normal=False,
                target_cue_ids=list((outcomes or {}).keys()),
                variant={"opening_line": MARKER, "title": MARKER},
                scenario_title=f"{MARKER}-title",
                child_setup=f"{MARKER}-setup",
                ai_role_name="민수",
                status=status,
                origin="live",
                started_at=(ended_at or T0) - timedelta(minutes=5),
                ended_at=ended_at if status != "in_progress" else None,
            )
            db.add(row)
            db.flush()
            db.add(
                PracticeTurn(
                    session_id=row.id,
                    turn_index=0,
                    ai_line=f"{MARKER}-ai-line",
                    choices=[{"id": "c1", "text": f"{MARKER}-choice", "kind": "correct"}],
                    chosen_choice_id="c1",
                    substituted=False,
                    target_clue_id=None,
                    revealed_clue_ids=[],
                    ai_status="ok",
                )
            )
            for cue_id, outcome in (outcomes or {}).items():
                db.add(
                    CueResult(
                        session_id=row.id,
                        child_id=UUID(child_id),
                        cue_id=cue_id,
                        outcome=outcome,
                        recorded_at=ended_at or T0,
                    )
                )
            return row.id


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'report.db').as_posix()}", ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield Env(client)
    app.state.engine.dispose()


@pytest.fixture
def family(env):
    guardian = env.new_guardian()
    child = env.new_child(guardian)
    return guardian, child


def label(cue_id: str) -> str:
    return CONTENT.clues[cue_id].name


# ==== 정상 (F-30 ①) ================================================================


def test_report_shows_area_progress_and_weak_cues(env, family):
    guardian, child = family
    env.seed_session(
        child["child_id"],
        area="scam",
        ended_at=T0,
        outcomes={"urgency": "missed", "keep_secret": "missed", "advance_payment": "missed"},
    )
    env.seed_session(
        child["child_id"],
        area="scam",
        ended_at=T0 + timedelta(days=1),
        outcomes={"urgency": "missed", "advance_payment": "missed", "personal_info": "missed"},
    )
    # keep_secret: 놓침 2회였지만 가장 최근 판정이 찾음 → 약점에서 빠짐 / personal_info: 놓침 1회 → 빠짐
    env.seed_session(
        child["child_id"],
        area="friend_pressure",
        ended_at=T0 + timedelta(days=2),
        outcomes={"keep_secret": "found"},
    )
    env.seed_session(
        child["child_id"],
        area="friend_pressure",
        ended_at=T0 - timedelta(days=2),
        outcomes={"keep_secret": "missed"},
    )

    response = env.report(child["child_id"], guardian)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"child", "areas", "weak_cues", "notices", "metrics", "summary"}
    assert body["child"] == {"child_id": child["child_id"], "nickname": "하늘이"}
    assert body["areas"] == [
        {"area": "scam", "practice_count": 2, "last_practiced_at": "2026-11-11T15:00:00Z"},
        {"area": "identity_lending", "practice_count": 0, "last_practiced_at": None},
        {"area": "friend_pressure", "practice_count": 2, "last_practiced_at": "2026-11-12T15:00:00Z"},
    ]
    # 동점(놓침 2회·마지막 놓침 같은 시각) → cue_id 순
    assert body["weak_cues"] == [
        {"cue_id": "advance_payment", "label": label("advance_payment")},
        {"cue_id": "urgency", "label": label("urgency")},
    ]


def test_report_placeholders_for_sources_not_on_this_branch(env, family):
    guardian, child = family
    env.seed_session(child["child_id"], outcomes={"urgency": "missed"})

    body = env.report(child["child_id"], guardian).json()

    assert body["notices"] == []
    assert body["metrics"] == []
    # 2026-11-12 사용자 답 "아직 기록이 적어요 (추천)" — T-76 전 임시값
    assert body["summary"] == {"status": "insufficient", "unit": "area", "items": []}


def test_report_for_child_without_records_is_empty_progress(env, family):
    guardian, child = family

    response = env.report(child["child_id"], guardian)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["areas"] == [
        {"area": area, "practice_count": 0, "last_practiced_at": None}
        for area in ("scam", "identity_lending", "friend_pressure")
    ]
    assert body["weak_cues"] == []


def test_report_counts_only_ended_sessions(env, family):
    guardian, child = family
    env.seed_session(child["child_id"], status="ended", ended_at=T0, outcomes={"urgency": "found", "keep_secret": "missed"})
    env.seed_session(child["child_id"], status="stopped", ended_at=T0 + timedelta(days=1), outcomes={"keep_secret": "missed"})
    env.seed_session(child["child_id"], status="in_progress", ended_at=None, outcomes={"keep_secret": "missed"})

    body = env.report(child["child_id"], guardian).json()

    assert body["areas"][0] == {"area": "scam", "practice_count": 1, "last_practiced_at": "2026-11-10T15:00:00Z"}
    assert body["weak_cues"] == []


def test_report_does_not_mix_sibling_records(env, family):
    guardian, child = family
    sibling = env.new_child(guardian, nickname="바다")
    env.seed_session(sibling["child_id"], area="identity_lending", outcomes={"urgency": "missed"})
    env.seed_session(sibling["child_id"], area="identity_lending", ended_at=T0 + timedelta(days=1), outcomes={"urgency": "missed"})

    body = env.report(child["child_id"], guardian).json()

    assert all(area["practice_count"] == 0 for area in body["areas"])
    assert body["weak_cues"] == []


def test_report_skips_weak_cue_missing_from_content(env, family):
    guardian, child = family
    env.seed_session(child["child_id"], outcomes={"removed_clue_x": "missed", "urgency": "missed"})
    env.seed_session(child["child_id"], ended_at=T0 + timedelta(days=1), outcomes={"removed_clue_x": "missed", "urgency": "missed"})

    body = env.report(child["child_id"], guardian).json()

    assert body["weak_cues"] == [{"cue_id": "urgency", "label": label("urgency")}]


# ==== 비공개 (F-30 ②③, F-48 ④) ======================================================


def test_report_has_no_forbidden_keys_and_no_conversation_text(env, family):
    guardian, child = family
    env.seed_session(child["child_id"], outcomes={"urgency": "missed", "keep_secret": "found"})

    response = env.report(child["child_id"], guardian)

    assert response.status_code == 200, response.text
    body = response.json()
    assert FORBIDDEN_KEYS.isdisjoint(all_keys(body)), set(all_keys(body)) & FORBIDDEN_KEYS
    assert MARKER not in response.text


def test_report_request_does_not_read_practice_turns(env, family):
    guardian, child = family
    env.seed_session(child["child_id"], outcomes={"urgency": "missed"})
    statements: list[str] = []

    def capture(_conn, _cursor, statement, _params, _context, _executemany):
        statements.append(statement)

    event.listen(env.client.app.state.engine, "before_cursor_execute", capture)
    try:
        response = env.report(child["child_id"], guardian)
    finally:
        event.remove(env.client.app.state.engine, "before_cursor_execute", capture)

    assert response.status_code == 200, response.text
    assert any("practice_sessions" in statement for statement in statements)
    assert not any("practice_turns" in statement for statement in statements)


def test_report_response_model_forbids_extra_fields():
    valid = {
        "child": {"child_id": str(uuid4()), "nickname": "하늘이"},
        "areas": [],
        "weak_cues": [],
        "notices": [],
        "metrics": [],
        "summary": {"status": "unavailable", "unit": "area", "items": []},
    }
    GuardianReportResponse.model_validate(valid)

    with pytest.raises(ValidationError):
        GuardianReportResponse.model_validate({**valid, "answer_text": "x"})
    with pytest.raises(ValidationError):
        GuardianReportResponse.model_validate(
            {**valid, "weak_cues": [{"cue_id": "urgency", "label": "x", "missed_text": "y"}]}
        )


# ==== 인가 (F-30 ④, N-05) ==========================================================


def test_other_guardians_child_is_404_same_as_unknown(env, family):
    _owner, child = family
    env.seed_session(child["child_id"], outcomes={"urgency": "missed"})
    intruder = env.new_guardian()

    other = env.report(child["child_id"], intruder)
    unknown = env.report(str(uuid4()), intruder)

    assert other.status_code == 404
    assert other.json() == {"error": {"code": "CHILD_NOT_FOUND", "message": "child not found"}}
    assert unknown.status_code == 404
    assert unknown.json() == other.json()
    assert "하늘이" not in other.text


def test_child_session_calling_guardian_report_is_403(env, family):
    _guardian, child = family
    child_cookies = env.child_cookies(child["link_code"])

    own = env.report(child["child_id"], child_cookies)

    assert own.status_code == 403
    assert own.json()["error"]["code"] == "FORBIDDEN_ROLE"


def test_report_without_session_is_401(env, family):
    _guardian, child = family

    response = env.report(child["child_id"], None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_report_with_invalid_token_is_401(env, family):
    _guardian, child = family

    response = env.report(child["child_id"], {"sid": "not-a-real-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_report_malformed_child_id_is_422(env, family):
    guardian, _child = family

    response = env.report("not-a-uuid", guardian)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "not-a-uuid" not in json.dumps(response.json())
