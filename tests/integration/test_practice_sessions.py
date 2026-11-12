"""연습 세션 API A15·A16·A17 (T-15 — F-09 ①, F-11, F-12, F-14 ①②, N-10).

근거: Architecture "API 규격" A15~A17, "응답 DTO" PracticeSessionView·TurnView, "1차 내부 API v1"(VA·ST·TU·J' 검증,
safe_reply·blocked 처리, 상태 재구성, TurnView 대응), DECISIONS #80·#82·#97~#99·#102·#112·#118.

AI는 포트(`app.ai_client.ports.PracticeAI`)를 만족하는 기록용 Fake로만 호출한다(실제 HTTP 없음).
DB는 테스트마다 OS 임시 디렉터리(pytest tmp_path)의 SQLite 파일 — pytest가 정리한다.
"""

import json
import logging
import random
from collections.abc import Callable, Iterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.ai_client.fake import FakePracticeAI
from app.ai_client.ports import AIUnavailableError, Choice, ClueResult
from app.content.loader import load_content
from app.core.config import Settings
from app.db.base import Base
from app.db.models import CueResult, PracticeSession, PracticeTurn
from app.main import create_app

CONTENT = load_content()
SCAM_SCENARIO_IDS = {sid for sid, entry in CONTENT.scenarios.items() if entry.area == "scam"}
SCENARIO_CLUES = {
    sid: tuple(clue.id for clue in entry.scenario.clues) for sid, entry in CONTENT.scenarios.items()
}
SAFETY_MESSAGE = CONTENT.safety_stop.message
MARKER = "UNIQUE-MARKER-7f3a9c"


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

    def answer(self, session_id: str, choice_id: str):
        return self.client.post(f"/api/v1/practice/sessions/{session_id}/turns", json={"choice_id": choice_id})

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

    def cue_rows(self, session_id: str) -> list[CueResult]:
        with self.session_factory() as db:
            return list(db.scalars(select(CueResult).where(CueResult.session_id == UUID(session_id))))

    def count(self, model) -> int:
        with self.session_factory() as db:
            return db.scalar(select(func.count()).select_from(model))


def choice_id_of(view: dict, kind: str, env: Env) -> str:
    """공개 응답에는 kind가 없으므로 DB 턴 행에서 kind로 선택지 id를 찾는다."""
    rows = env.turn_rows(view["session_id"])
    current = rows[view["turn"]["turn_index"]]
    return next(choice["id"] for choice in current.choices if choice["kind"] == kind)


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'practice.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield Env(client, ai)
    app.state.engine.dispose()


# ==== A15 출제 ===================================================================


def test_start_creates_session_and_first_turn(env):
    env.login_child(grade="H1")

    response = env.start()

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"session_id", "mode", "area", "is_retry", "status", "turn"}
    assert body["mode"] == "area"
    assert body["area"] == "scam"
    assert body["is_retry"] is False
    assert body["status"] == "in_progress"
    turn = body["turn"]
    assert set(turn) == {"turn_index", "speaker_name", "platform", "ai_line", "choices", "hint", "substituted"}
    assert turn["turn_index"] == 0
    assert turn["hint"] is None
    assert turn["substituted"] is False
    assert [set(choice) for choice in turn["choices"]] == [{"id", "text"}] * 3
    assert env.ai.names() == ["variant", "start"]


def test_start_stores_variant_and_start_values(env):
    child_id = env.login_child(grade="H1")

    body = env.started()

    row = env.session_row(body["session_id"])
    variant_request = env.ai.requests("variant")[0]
    start_request = env.ai.requests("start")[0]
    assert row.child_id == child_id
    assert row.scenario_id in SCAM_SCENARIO_IDS
    assert row.area == "scam"
    assert row.mode == "area"
    assert row.status == "in_progress"
    assert row.is_normal is False
    assert row.origin == "live"
    assert row.subtype == "high_paying_job"
    assert row.target_cue_ids == list(SCENARIO_CLUES[row.scenario_id])
    assert row.variant == start_request.variant.model_dump(mode="json")
    assert row.variant["platform"] == variant_request.platform
    assert row.scenario_title == "[fake] 연습 상황"
    assert row.child_setup == "[fake] 모르는 사람이 메시지를 보냈어요."
    assert row.ai_role_name == "[fake] 상대"
    assert row.retry_of is None
    assert row.ended_at is None
    # start 요청에 받은 variant를 그대로 보낸다 (#98, T-86 리뷰 권고 #1)
    assert start_request.variant is not None
    assert start_request.variant.base_scenario_id == row.scenario_id
    assert start_request.scenario_id == row.scenario_id

    turns = env.turn_rows(body["session_id"])
    assert len(turns) == 1
    first = turns[0]
    assert first.turn_index == 0
    assert first.ai_line == "[fake] 안녕! 좋은 제안이 있어."
    assert first.choices == [
        {"id": "c1", "text": "[fake] 이상해요, 어른께 물어볼게요", "kind": "correct"},
        {"id": "c2", "text": "[fake] 좀 이상하지만… 해 볼까요?", "kind": "doubtful"},
        {"id": "c3", "text": "[fake] 좋아요, 그렇게 할게요", "kind": "other"},
    ]
    clues = SCENARIO_CLUES[row.scenario_id]
    assert first.target_clue_id == clues[0]
    assert first.revealed_clue_ids == [clues[0]]
    assert first.ai_status == "ok"
    assert first.chosen_choice_id is None
    assert first.substituted is False


def test_start_variant_request_uses_scenario_axes(env):
    env.login_child(grade="H1")

    env.started()

    request = env.ai.requests("variant")[0]
    axes = CONTENT.scenarios[request.scenario_id].variation_axes
    assert request.platform in axes.platform
    assert request.tone in axes.tone
    assert request.context in axes.context


def test_turn_view_uses_session_values(env):
    env.login_child(grade="H1")

    body = env.started()

    row = env.session_row(body["session_id"])
    assert body["turn"]["speaker_name"] == row.ai_role_name
    assert body["turn"]["platform"] == row.variant["platform"]
    assert body["turn"]["ai_line"] == env.turn_rows(body["session_id"])[0].ai_line


def test_start_prefers_favorite_app_platform(env):
    env.login_child(grade="H1", favorite_apps=["job_site"])

    env.started()

    # job_board(app_type job_site)는 scam_jobboard_link_01 축에만 있다 — 그 시나리오가 뽑히면 job_board
    request = env.ai.requests("variant")[0]
    if "job_board" in CONTENT.scenarios[request.scenario_id].variation_axes.platform:
        assert request.platform == "job_board"
    else:
        assert CONTENT.app_type_of(request.platform) != "job_site"


@pytest.mark.parametrize("grade", ["E6", "M3"])
def test_non_high_school_child_gets_no_scenario_for_scam(env, grade):
    # 현재 사본의 사기 시나리오 2개는 모두 고수익 알바(min_grade H1)
    env.login_child(grade=grade)

    response = env.start("scam")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NO_SCENARIO_AVAILABLE"
    assert env.ai.calls == []
    assert env.count(PracticeSession) == 0
    assert env.count(PracticeTurn) == 0


@pytest.mark.parametrize("grade", ["H1", "H3"])
def test_high_school_child_gets_high_paying_job_scenario(env, grade):
    env.login_child(grade=grade)

    response = env.start("scam")

    assert response.status_code == 201
    assert env.session_row(response.json()["session_id"]).subtype == "high_paying_job"


@pytest.mark.parametrize("area", ["identity_lending", "friend_pressure"])
def test_area_without_scenarios_is_no_scenario_available(env, area):
    env.login_child(grade="H1")

    response = env.start(area)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NO_SCENARIO_AVAILABLE"
    assert env.ai.calls == []
    assert env.count(PracticeSession) == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "area", "area": "name_lending"},
        {"mode": "area", "area": "friend_request"},
        {"mode": "area", "area": ""},
        {"mode": "area"},
        {"mode": "area", "area": "scam", "emotion": 3},
        {},
    ],
)
def test_invalid_start_request_is_422(env, payload):
    env.login_child(grade="H1")

    response = env.client.post("/api/v1/practice/sessions", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert env.ai.calls == []


def test_start_requires_child_session(env):
    response = env.start()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("failing", ["variant", "start"])
def test_ai_failure_on_start_is_503_and_saves_nothing(env, failing):
    env.login_child(grade="H1")
    env.ai.fail.add(failing)

    response = env.start()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.count(PracticeSession) == 0
    assert env.count(PracticeTurn) == 0


# ---- VA1~VA4 / ST1~ST5 -----------------------------------------------------------


def _variant_with(**changes):
    def override(_request, response):
        return response.model_copy(update={"variant": response.variant.model_copy(update=changes)})

    return override


def _clue_variants(response, ids):
    template = response.variant.clues[0]
    return [template.model_copy(update={"id": clue_id}) for clue_id in ids]


VARIANT_VIOLATIONS = {
    "VA1_base_scenario_id": _variant_with(base_scenario_id="other_scenario"),
    "VA2_clue_order": lambda req, res: res.model_copy(
        update={"variant": res.variant.model_copy(update={"clues": list(reversed(res.variant.clues))})}
    ),
    "VA2_clue_missing": lambda req, res: res.model_copy(
        update={"variant": res.variant.model_copy(update={"clues": res.variant.clues[:-1]})}
    ),
    "VA2_clue_unknown": lambda req, res: res.model_copy(
        update={"variant": res.variant.model_copy(update={"clues": _clue_variants(res, ["nope"] + [c.id for c in res.variant.clues[1:]])})}
    ),
    "VA3_model_platform": _variant_with(platform="somewhere_else"),
    "VA3_model_tone": _variant_with(tone="다른 말투"),
    "VA3_model_context": _variant_with(context="다른 맥락"),
}


@pytest.mark.parametrize("case", sorted(VARIANT_VIOLATIONS))
def test_variant_validation_violation_is_503(env, case):
    env.login_child(grade="H1")
    env.ai.overrides["variant"] = VARIANT_VIOLATIONS[case]

    response = env.start()

    assert response.status_code == 503, case
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert "start" not in env.ai.names()
    assert env.count(PracticeSession) == 0


def _choices(*items):
    return [Choice(id=i, text=t, kind=k) for i, t, k in items]


GOOD_CHOICES = (("c1", "a", "correct"), ("c2", "b", "doubtful"), ("c3", "c", "other"))
RULE_C_VIOLATIONS = {
    "two_choices": _choices(("c1", "a", "correct"), ("c2", "b", "doubtful")),
    "four_choices": _choices(*GOOD_CHOICES, ("c4", "d", "other")),
    "no_correct": _choices(("c1", "a", "other"), ("c2", "b", "doubtful"), ("c3", "c", "other")),
    "all_correct": _choices(("c1", "a", "correct"), ("c2", "b", "correct"), ("c3", "c", "correct")),
    "duplicate_id": _choices(("c1", "a", "correct"), ("c1", "b", "doubtful"), ("c3", "c", "other")),
    "blank_text": _choices(("c1", "  ", "correct"), ("c2", "b", "doubtful"), ("c3", "c", "other")),
    "empty": [],
}


def _start_with(**changes):
    return lambda _request, response: response.model_copy(update=changes)


START_VIOLATIONS = {
    **{f"ST2_{name}": _start_with(choices=choices) for name, choices in RULE_C_VIOLATIONS.items()},
    "ST3_revealed_unknown": _start_with(revealed_clue_ids=["not_a_scenario_clue"]),
    "ST4_target_not_revealed": lambda req, res: res.model_copy(
        update={"target_clue_id": [c for c in SCENARIO_CLUES[req.scenario_id] if c not in res.revealed_clue_ids][0]}
    ),
    "ST5_blank_reply": _start_with(reply="   "),
    "ST5_blank_title": _start_with(title=""),
    "ST5_blank_child_setup": _start_with(child_setup=" "),
    "ST5_blank_ai_role_name": _start_with(ai_role_name="\n"),
}


@pytest.mark.parametrize("case", sorted(START_VIOLATIONS))
def test_start_validation_violation_is_503(env, case):
    env.login_child(grade="H1")
    env.ai.overrides["start"] = START_VIOLATIONS[case]

    response = env.start()

    assert response.status_code == 503, case
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.count(PracticeSession) == 0
    assert env.count(PracticeTurn) == 0


def test_start_target_clue_null_is_allowed(env):
    env.login_child(grade="H1")
    env.ai.overrides["start"] = _start_with(target_clue_id=None)

    response = env.start()

    assert response.status_code == 201
    assert env.turn_rows(response.json()["session_id"])[0].target_clue_id is None


# ---- F-12 직전 세션과 차이 / VA4 -----------------------------------------------------


def test_new_session_differs_from_previous_session_of_same_scenario(env):
    env.login_child(grade="H1")
    seen: dict[str, tuple[str, str]] = {}
    for _ in range(6):
        body = env.started()
        row = env.session_row(body["session_id"])
        pair = (row.variant["platform"], row.variant["tone"])
        if row.scenario_id in seen:
            assert pair != seen[row.scenario_id]
        seen[row.scenario_id] = pair


def test_fallback_variant_same_as_previous_is_503(env):
    env.login_child(grade="H1")
    first = env.session_row(env.started()["session_id"])
    previous = first.variant

    def fallback_like_previous(request, response):
        if request.scenario_id != first.scenario_id:
            return response
        return response.model_copy(
            update={
                "source": "fallback",
                "variant": response.variant.model_copy(
                    update={"platform": previous["platform"], "tone": previous["tone"]}
                ),
            }
        )

    env.ai.overrides["variant"] = fallback_like_previous
    statuses = set()
    for _ in range(8):
        response = env.start()
        statuses.add(response.status_code)
        sid = env.ai.requests("variant")[-1].scenario_id
        if sid == first.scenario_id:
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert 503 in statuses


def test_fallback_variant_without_previous_session_is_accepted(env):
    env.login_child(grade="H1")

    def original_values(_request, response):
        return response.model_copy(
            update={"source": "fallback", "variant": response.variant.model_copy(update={"platform": "orig", "tone": "원래 말투"})}
        )

    env.ai.overrides["variant"] = original_values

    response = env.start()

    assert response.status_code == 201
    assert env.session_row(response.json()["session_id"]).variant["platform"] == "orig"


# ==== A16 조회 ===================================================================


def test_get_in_progress_session_returns_current_turn(env):
    env.login_child(grade="H1")
    body = env.started()

    response = env.get(body["session_id"])

    assert response.status_code == 200
    assert response.json() == body


def test_get_other_childs_session_is_404(env):
    env.login_child(grade="H1")
    body = env.started()
    env.login_child(grade="H1")

    response = env.get(body["session_id"])

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_get_unknown_session_is_404(env):
    env.login_child(grade="H1")

    response = env.get(str(uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_get_malformed_session_id_is_422(env):
    env.login_child(grade="H1")

    response = env.get("not-a-uuid")

    assert response.status_code == 422


# ==== A17 턴 — 종료 판정 ============================================================


def test_correct_first_answer_ends_session(env):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.calls.clear()

    response = env.answer(body["session_id"], choice_id_of(body, "correct", env))

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "ended"
    assert result["turn"] is None
    assert env.ai.names() == ["judge"]
    row = env.session_row(body["session_id"])
    assert row.status == "ended"
    assert row.ended_at is not None
    turns = env.turn_rows(body["session_id"])
    assert len(turns) == 1
    assert turns[0].chosen_choice_id == choice_id_of(body, "correct", env)


@pytest.mark.parametrize("kind", ["doubtful", "other"])
def test_non_correct_answers_continue_until_third(env, kind):
    env.login_child(grade="H1")
    view = env.started()
    for answer_number in (1, 2, 3):
        env.ai.calls.clear()
        response = env.answer(view["session_id"], choice_id_of(view, kind, env))
        assert response.status_code == 200
        view = response.json()
        assert view["status"] == "in_progress"
        assert view["turn"]["turn_index"] == answer_number
        assert env.ai.names() == ["turn"]
    assert len(env.turn_rows(view["session_id"])) == 4


@pytest.mark.parametrize("kind", ["doubtful", "other", "correct"])
def test_fourth_answer_ends_regardless_of_kind(env, kind):
    env.login_child(grade="H1")
    view = env.started()
    for _ in range(3):
        view = env.answer(view["session_id"], choice_id_of(view, "other", env)).json()
    env.ai.calls.clear()

    response = env.answer(view["session_id"], choice_id_of(view, kind, env))

    assert response.status_code == 200
    assert response.json()["status"] == "ended"
    assert response.json()["turn"] is None
    assert env.ai.names() == ["judge"]
    assert len(env.turn_rows(view["session_id"])) == 4


def test_answer_after_end_is_409_session_ended(env):
    env.login_child(grade="H1")
    body = env.started()
    env.answer(body["session_id"], choice_id_of(body, "correct", env))
    env.ai.calls.clear()

    response = env.answer(body["session_id"], "c1")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ENDED"
    assert env.ai.calls == []


def test_get_ended_session_has_no_turn(env):
    env.login_child(grade="H1")
    body = env.started()
    env.answer(body["session_id"], choice_id_of(body, "correct", env))

    response = env.get(body["session_id"])

    assert response.status_code == 200
    assert response.json() == {
        "session_id": body["session_id"],
        "mode": "area",
        "area": "scam",
        "is_retry": False,
        "status": "ended",
        "turn": None,
    }


def test_end_saves_found_and_missed_only(env):
    child_id = env.login_child(grade="H1")
    body = env.started()

    env.answer(body["session_id"], choice_id_of(body, "correct", env))

    row = env.session_row(body["session_id"])
    clues = SCENARIO_CLUES[row.scenario_id]
    cue_rows = env.cue_rows(body["session_id"])
    # 첫 답 correct로 끝난 4단서 세션 → 드러난 단서 1개만 found, not_shown은 0행
    assert [(r.cue_id, r.outcome) for r in cue_rows] == [(clues[0], "found")]
    assert all(r.child_id == child_id for r in cue_rows)


def test_end_after_misses_saves_missed(env):
    env.login_child(grade="H1")
    view = env.started()
    session_id = view["session_id"]
    view = env.answer(session_id, choice_id_of(view, "other", env)).json()

    env.answer(session_id, choice_id_of(view, "correct", env))

    clues = SCENARIO_CLUES[env.session_row(session_id).scenario_id]
    outcomes = {r.cue_id: r.outcome for r in env.cue_rows(session_id)}
    assert outcomes == {clues[0]: "missed", clues[1]: "found"}


# ---- 처리 순서 404 → 409 → 422 -------------------------------------------------------


def test_answer_on_other_childs_session_is_404(env):
    env.login_child(grade="H1")
    body = env.started()
    env.login_child(grade="H1")
    env.ai.calls.clear()

    response = env.answer(body["session_id"], "zz")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
    assert env.ai.calls == []


def test_answer_on_ended_session_with_invalid_choice_is_409(env):
    env.login_child(grade="H1")
    body = env.started()
    env.answer(body["session_id"], choice_id_of(body, "correct", env))

    response = env.answer(body["session_id"], "zz")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ENDED"


@pytest.mark.parametrize("choice_id", ["zz", "c9", "C1"])
def test_choice_not_in_current_turn_is_422(env, choice_id):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.calls.clear()

    response = env.answer(body["session_id"], choice_id)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CHOICE"
    assert env.ai.calls == []
    assert env.turn_rows(body["session_id"])[0].chosen_choice_id is None


@pytest.mark.parametrize("payload", [{}, {"choice_id": ""}, {"choice_id": "c1", "emotion": 2}])
def test_malformed_turn_request_is_422_validation(env, payload):
    env.login_child(grade="H1")
    body = env.started()

    response = env.client.post(f"/api/v1/practice/sessions/{body['session_id']}/turns", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---- 한 트랜잭션 (#82·#85) -------------------------------------------------------------


def test_turn_failure_saves_nothing_and_same_choice_can_retry(env):
    env.login_child(grade="H1")
    body = env.started()
    choice = choice_id_of(body, "other", env)
    env.ai.fail.add("turn")

    failed = env.answer(body["session_id"], choice)

    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "AI_UNAVAILABLE"
    turns = env.turn_rows(body["session_id"])
    assert len(turns) == 1
    assert turns[0].chosen_choice_id is None

    env.ai.fail.clear()
    retried = env.answer(body["session_id"], choice)

    assert retried.status_code == 200
    assert retried.json()["status"] == "in_progress"
    assert len(env.turn_rows(body["session_id"])) == 2


def test_judge_failure_saves_nothing_and_same_choice_can_retry(env):
    env.login_child(grade="H1")
    body = env.started()
    choice = choice_id_of(body, "correct", env)
    env.ai.fail.add("judge")

    failed = env.answer(body["session_id"], choice)

    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.session_row(body["session_id"]).status == "in_progress"
    assert env.turn_rows(body["session_id"])[0].chosen_choice_id is None
    assert env.count(CueResult) == 0

    env.ai.fail.clear()
    retried = env.answer(body["session_id"], choice)

    assert retried.status_code == 200
    assert retried.json()["status"] == "ended"
    assert env.count(CueResult) == 1


# ---- TU1~TU4 ----------------------------------------------------------------------


def _turn_with(**changes):
    return lambda _request, response: response.model_copy(update=changes)


TURN_VIOLATIONS = {
    **{f"TU1_{name}": _turn_with(choices=choices) for name, choices in RULE_C_VIOLATIONS.items()},
    "TU2_drops_sent_clue": _turn_with(revealed_clue_ids=[]),
    "TU2_unknown_clue": lambda req, res: res.model_copy(
        update={"revealed_clue_ids": list(res.revealed_clue_ids) + ["not_a_scenario_clue"]}
    ),
    "TU3_target_not_revealed": lambda req, res: res.model_copy(
        update={"target_clue_id": [c for c in SCENARIO_CLUES[req.scenario_id] if c not in res.revealed_clue_ids][0]}
    ),
    "TU4_blank_reply": _turn_with(reply=" "),
}


@pytest.mark.parametrize("status", ["ok", "blocked"])
@pytest.mark.parametrize("case", sorted(TURN_VIOLATIONS))
def test_turn_validation_violation_is_503_and_saves_nothing(env, case, status):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.turn_status = status
    env.ai.overrides["turn"] = TURN_VIOLATIONS[case]

    response = env.answer(body["session_id"], choice_id_of(body, "other", env))

    assert response.status_code == 503, case
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert len(env.turn_rows(body["session_id"])) == 1
    assert env.turn_rows(body["session_id"])[0].chosen_choice_id is None


def test_turn_ignores_all_clues_revealed_and_masked(env):
    # F-11 ⑥: AI 참고값은 종료 입력이 아니다 — all_clues_revealed true여도 계속
    env.login_child(grade="H1")
    body = env.started()
    env.ai.overrides["turn"] = _turn_with(all_clues_revealed=True, masked=True)

    response = env.answer(body["session_id"], choice_id_of(body, "other", env))

    assert response.json()["status"] == "in_progress"


# ---- J1'~J4' ------------------------------------------------------------------------


def _judge_results(request, mapping):
    return [ClueResult(clue_id=clue_id, result=mapping(clue_id)) for clue_id in SCENARIO_CLUES[request.scenario_id]]


JUDGE_VIOLATIONS = {
    "J1_missing_clue": lambda req, res: res.model_copy(update={"results": res.results[:-1]}),
    "J1_reordered": lambda req, res: res.model_copy(update={"results": list(reversed(res.results))}),
    "J1_duplicate": lambda req, res: res.model_copy(update={"results": res.results + res.results[:1]}),
    "J2_not_shown_for_revealed": lambda req, res: res.model_copy(
        update={"results": _judge_results(req, lambda c: "not_shown")}
    ),
    "J2_found_for_unrevealed": lambda req, res: res.model_copy(
        update={"results": _judge_results(req, lambda c: "found" if c in req.revealed_clue_ids else "missed")}
    ),
    "J3_found_flipped_to_missed": lambda req, res: res.model_copy(
        update={
            "results": _judge_results(req, lambda c: "missed" if c in req.revealed_clue_ids else "not_shown")
        }
    ),
    "J4_source_model": lambda req, res: res.model_copy(update={"source": "model"}),
    "J4_source_fallback": lambda req, res: res.model_copy(update={"source": "fallback"}),
}


@pytest.mark.parametrize("case", sorted(JUDGE_VIOLATIONS))
def test_judge_validation_violation_is_503_and_saves_nothing(env, case):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.overrides["judge"] = JUDGE_VIOLATIONS[case]

    response = env.answer(body["session_id"], choice_id_of(body, "correct", env))

    assert response.status_code == 503, case
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.session_row(body["session_id"]).status == "in_progress"
    assert env.count(CueResult) == 0


def test_judge_source_fixed_is_accepted(env):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.overrides["judge"] = lambda req, res: res.model_copy(update={"source": "fixed"})

    response = env.answer(body["session_id"], choice_id_of(body, "correct", env))

    assert response.json()["status"] == "ended"


# ---- 상태 재구성 (#98) ----------------------------------------------------------------


def test_messages_and_variant_are_rebuilt_from_turn_rows(env):
    env.login_child(grade="H1")
    view0 = env.started()
    session_id = view0["session_id"]
    c0 = choice_id_of(view0, "other", env)
    view1 = env.answer(session_id, c0).json()
    c1 = choice_id_of(view1, "doubtful", env)
    view2 = env.answer(session_id, c1).json()
    c2 = choice_id_of(view2, "correct", env)
    env.answer(session_id, c2)

    rows = env.turn_rows(session_id)
    stored_variant = env.session_row(session_id).variant

    def expected_messages(upto: int) -> list[dict]:
        messages = []
        for row in rows[: upto + 1]:
            messages.append({"role": "ai", "text": row.ai_line, "choice_kind": None, "clue_id": None})
            chosen = next(c for c in row.choices if c["id"] == row.chosen_choice_id)
            messages.append(
                {"role": "child", "text": chosen["text"], "choice_kind": chosen["kind"], "clue_id": row.target_clue_id}
            )
        return messages

    turn_requests = env.ai.requests("turn")
    assert [m.model_dump() for m in turn_requests[0].messages] == expected_messages(0)
    assert [m.model_dump() for m in turn_requests[1].messages] == expected_messages(1)
    assert turn_requests[0].revealed_clue_ids == rows[0].revealed_clue_ids
    assert turn_requests[1].revealed_clue_ids == rows[1].revealed_clue_ids
    judge_request = env.ai.requests("judge")[0]
    assert [m.model_dump() for m in judge_request.messages] == expected_messages(2)
    assert judge_request.revealed_clue_ids == rows[2].revealed_clue_ids
    # start·turn·judge 요청마다 저장된 variant 전체를 보낸다 (#98, T-86 리뷰 권고 #1)
    for request in [*env.ai.requests("start"), *turn_requests, judge_request]:
        assert request.variant is not None
        assert request.variant.model_dump(mode="json") == stored_variant
        assert request.scenario_id == env.session_row(session_id).scenario_id


def test_new_turn_rows_store_ai_values(env):
    env.login_child(grade="H1")
    body = env.started()

    env.answer(body["session_id"], choice_id_of(body, "other", env))

    rows = env.turn_rows(body["session_id"])
    clues = SCENARIO_CLUES[env.session_row(body["session_id"]).scenario_id]
    assert rows[1].turn_index == 1
    assert rows[1].ai_line == "[fake] 다음 대사 2"
    assert rows[1].revealed_clue_ids == [clues[0], clues[1]]
    assert rows[1].target_clue_id == clues[1]
    assert rows[1].ai_status == "ok"
    assert rows[1].substituted is False
    assert [c["kind"] for c in rows[1].choices] == ["correct", "doubtful", "other"]


@pytest.mark.parametrize(("source", "substituted"), [("model", False), ("fallback", True), ("fixed", True)])
def test_substituted_follows_turn_source(env, source, substituted):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.overrides["turn"] = _turn_with(source=source)

    response = env.answer(body["session_id"], choice_id_of(body, "other", env))

    assert response.json()["turn"]["substituted"] is substituted


# ---- blocked / safe_reply (#99·#113·#118) -------------------------------------------


def test_blocked_turn_continues_as_substituted_and_counts_answer(env):
    env.login_child(grade="H1")
    view = env.started()
    session_id = view["session_id"]
    env.ai.turn_status = "blocked"
    for answer_number in (1, 2, 3):
        response = env.answer(session_id, choice_id_of(view, "other", env))
        view = response.json()
        assert view["status"] == "in_progress"
        assert view["turn"]["substituted"] is True
        assert view["turn"]["turn_index"] == answer_number
    assert env.turn_rows(session_id)[1].ai_status == "blocked"

    response = env.answer(session_id, choice_id_of(view, "other", env))

    assert response.json()["status"] == "ended"


def _safe_reply_with_marker(_request, response):
    return response.model_copy(update={"reply": f"위험 {MARKER}"})


def test_safe_reply_stops_session_with_fixed_message(env, caplog):
    env.login_child(grade="H1")
    body = env.started()
    session_id = body["session_id"]
    choice = choice_id_of(body, "other", env)
    env.ai.turn_status = "safe_reply"
    env.ai.overrides["turn"] = _safe_reply_with_marker
    env.ai.calls.clear()

    with caplog.at_level(logging.DEBUG):
        response = env.answer(session_id, choice)

    assert response.status_code == 200
    view = response.json()
    assert view["status"] == "stopped"
    row = env.session_row(session_id)
    assert view["turn"] == {
        "turn_index": 1,
        "speaker_name": row.ai_role_name,
        "platform": row.variant["platform"],
        "ai_line": SAFETY_MESSAGE,
        "choices": [],
        "hint": None,
        "substituted": False,
    }
    assert env.ai.names() == ["turn"]
    assert row.status == "stopped"
    assert row.ended_at is not None
    rows = env.turn_rows(session_id)
    assert rows[0].chosen_choice_id == choice
    assert rows[1].ai_line == SAFETY_MESSAGE
    assert rows[1].choices == []
    assert rows[1].target_clue_id is None
    assert rows[1].revealed_clue_ids == rows[0].revealed_clue_ids
    assert rows[1].ai_status == "safe_reply"
    assert env.count(CueResult) == 0
    # AI reply는 응답·DB·로그 어디에도 남지 않는다 (#118 ①)
    assert MARKER not in response.text
    assert all(MARKER not in json.dumps([r.ai_line, r.choices], ensure_ascii=False) for r in rows)
    assert MARKER not in caplog.text


def test_safe_reply_with_odd_body_still_stops(env):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.turn_status = "safe_reply"
    env.ai.overrides["turn"] = _turn_with(
        reply="", choices=_choices(*GOOD_CHOICES), revealed_clue_ids=["garbage"], target_clue_id="garbage"
    )

    response = env.answer(body["session_id"], choice_id_of(body, "other", env))

    assert response.status_code == 200
    assert response.json()["status"] == "stopped"
    assert response.json()["turn"]["choices"] == []


def test_safe_reply_on_fourth_answer_is_not_reached(env):
    # 4번째 답은 turn을 부르지 않고 종료한다 — safe_reply 경로 없음
    env.login_child(grade="H1")
    view = env.started()
    for _ in range(3):
        view = env.answer(view["session_id"], choice_id_of(view, "other", env)).json()
    env.ai.turn_status = "safe_reply"

    response = env.answer(view["session_id"], choice_id_of(view, "other", env))

    assert response.json()["status"] == "ended"


def test_stopped_session_get_returns_same_view_and_answer_is_409(env):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.turn_status = "safe_reply"
    stopped = env.answer(body["session_id"], choice_id_of(body, "other", env)).json()
    env.ai.calls.clear()

    got = env.get(body["session_id"])
    answered = env.answer(body["session_id"], "c1")

    assert got.status_code == 200
    assert got.json() == stopped
    assert answered.status_code == 409
    assert answered.json()["error"]["code"] == "SESSION_STOPPED"
    assert env.ai.calls == []


# ---- 공개 응답 금지 키 ----------------------------------------------------------------


FORBIDDEN_PUBLIC_KEYS = {
    "kind",
    "is_terminal",
    "judgment",
    "cue_ids",
    "target_cue_ids",
    "target_clue_id",
    "revealed_clue_ids",
    "is_normal",
    "variant",
    "ai_status",
}


def _keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(v) for v in value)) if value else set()
    return set()


def test_public_responses_have_no_internal_keys(env):
    env.login_child(grade="H1")
    started = env.start()
    body = started.json()
    continued = env.answer(body["session_id"], choice_id_of(body, "other", env))
    fetched = env.get(body["session_id"])
    ended = env.answer(body["session_id"], choice_id_of(continued.json(), "correct", env))

    for response in (started, continued, fetched, ended):
        assert _keys(response.json()) & FORBIDDEN_PUBLIC_KEYS == set()


# ---- 긴 choice_id도 처리 순서 404 → 409 → 422 INVALID_CHOICE (리뷰 권고 #4) ---------------

LONG_CHOICE_ID = "x" * 9


def test_long_choice_id_is_invalid_choice(env):
    env.login_child(grade="H1")
    body = env.started()
    env.ai.calls.clear()

    response = env.answer(body["session_id"], LONG_CHOICE_ID)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CHOICE"
    assert env.ai.calls == []


def test_long_choice_id_on_other_childs_session_is_404(env):
    env.login_child(grade="H1")
    body = env.started()
    env.login_child(grade="H1")

    response = env.answer(body["session_id"], LONG_CHOICE_ID)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_long_choice_id_on_ended_session_is_409(env):
    env.login_child(grade="H1")
    body = env.started()
    env.answer(body["session_id"], choice_id_of(body, "correct", env))

    response = env.answer(body["session_id"], LONG_CHOICE_ID)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ENDED"


# ---- 같은 세션 A17 동시 요청 (리뷰 치명 #1 → 재작업 T-91, DECISIONS #128) --------------------
# 바깥 요청이 AI 응답을 기다리는 사이 같은 세션의 다른 요청이 먼저 저장을 끝낸 상황을 재현한다:
# AI 응답 덮어쓰기 콜백 안에서 같은 서비스로 안쪽 요청을 한 번 끝까지 처리한다.
# 충돌한 바깥 요청은 세션을 다시 읽어 상태별 409를 낸다 — in_progress → TURN_ALREADY_ANSWERED,
# ended → SESSION_ENDED, stopped → SESSION_STOPPED (Architecture A17 행·오류 코드 표).
# 바깥 요청은 충돌 뒤 AI를 더 부르지 않고 아무것도 저장하지 않는다.


def _race(
    env,
    name: str,
    child_id: UUID,
    session_id: str,
    inner_choice: str,
    inner_turn_status: str | None = None,
):
    """바깥 요청의 AI `name` 응답 직후 안쪽 요청을 끝까지 처리한다.

    inner_turn_status를 주면 안쪽 요청이 받는 Fake `turn` 상태만 바꾼다(바깥 응답은 이미 만들어짐).
    안쪽 요청이 끝난 직후의 DB 스냅숏을 돌려준 dict의 "snapshot"에 담는다 — 바깥 요청이 저장을 시도하기 전 시점.
    """
    service = env.client.app.state.practice_service
    state: dict[str, Any] = {"done": False, "snapshot": None}

    def override(_request, response):
        if not state["done"]:
            state["done"] = True
            saved = env.ai.turn_status
            if inner_turn_status is not None:
                env.ai.turn_status = inner_turn_status
            try:
                service.answer(child_id=child_id, session_id=UUID(session_id), choice_id=inner_choice)
            finally:
                env.ai.turn_status = saved
            state["snapshot"] = _snapshot(env, session_id)
        return response

    env.ai.overrides[name] = override
    return state


def _snapshot(env, session_id: str) -> tuple:
    """세션·턴·판정 행의 비교용 스냅숏 — 충돌한 요청이 저장한 것이 없는지 본다."""
    row = env.session_row(session_id)
    turns = tuple(
        (turn.turn_index, turn.ai_line, turn.chosen_choice_id, turn.ai_status) for turn in env.turn_rows(session_id)
    )
    cues = tuple(sorted((cue.cue_id, cue.outcome) for cue in env.cue_rows(session_id)))
    return (row.status, row.ended_at, turns, cues)


def _assert_loser_saved_nothing(env, session_id: str, race: dict) -> None:
    assert race["snapshot"] is not None
    assert _snapshot(env, session_id) == race["snapshot"]


# (a) 진행 중인 세션과 충돌 → 409 TURN_ALREADY_ANSWERED


def test_concurrent_continue_answers_are_turn_already_answered(env):
    # 계속 답 두 개가 겹침(더블탭) → 뒤쪽은 409 TURN_ALREADY_ANSWERED, 세션은 in_progress, 턴은 하나만 추가
    child_id = env.login_child(grade="H1")
    body = env.started()
    doubtful = choice_id_of(body, "doubtful", env)
    other = choice_id_of(body, "other", env)
    race = _race(env, "turn", child_id, body["session_id"], doubtful)
    env.ai.calls.clear()

    response = env.answer(body["session_id"], other)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TURN_ALREADY_ANSWERED"
    turns = env.turn_rows(body["session_id"])
    assert len(turns) == 2
    assert turns[0].chosen_choice_id == doubtful
    assert turns[1].chosen_choice_id is None
    assert env.session_row(body["session_id"]).status == "in_progress"
    assert env.cue_rows(body["session_id"]) == []
    # 바깥 1회 + 안쪽 1회 — 충돌 뒤 추가 AI 호출 0회, 바깥 요청 저장 0건
    assert env.ai.names() == ["turn", "turn"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


def test_same_choice_double_tap_is_turn_already_answered(env):
    # 같은 선택지를 두 번 눌러 같은 choice_id가 동시에 들어옴 → 409 TURN_ALREADY_ANSWERED
    child_id = env.login_child(grade="H1")
    body = env.started()
    doubtful = choice_id_of(body, "doubtful", env)
    race = _race(env, "turn", child_id, body["session_id"], doubtful)
    env.ai.calls.clear()

    response = env.answer(body["session_id"], doubtful)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TURN_ALREADY_ANSWERED"
    assert env.session_row(body["session_id"]).status == "in_progress"
    assert len(env.turn_rows(body["session_id"])) == 2
    assert env.ai.names() == ["turn", "turn"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


def test_ending_answer_racing_a_continue_answer_is_turn_already_answered(env):
    # 계속 답이 먼저 저장된 뒤 종료 답(judge 응답 직후)이 저장하려 함 → 세션은 진행 중 → TURN_ALREADY_ANSWERED
    child_id = env.login_child(grade="H1")
    body = env.started()
    correct = choice_id_of(body, "correct", env)
    doubtful = choice_id_of(body, "doubtful", env)
    race = _race(env, "judge", child_id, body["session_id"], doubtful)
    env.ai.calls.clear()

    response = env.answer(body["session_id"], correct)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TURN_ALREADY_ANSWERED"
    assert env.session_row(body["session_id"]).status == "in_progress"
    assert env.cue_rows(body["session_id"]) == []
    assert env.turn_rows(body["session_id"])[0].chosen_choice_id == doubtful
    assert env.ai.names() == ["judge", "turn"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


# (b) 끝난 세션과 충돌 → 409 SESSION_ENDED


def test_concurrent_ending_answers_save_cue_results_once(env):
    # 종료 답 두 개가 겹침 → 뒤에 저장하려는 쪽은 409 SESSION_ENDED, cue_results 중복 없음
    child_id = env.login_child(grade="H1")
    body = env.started()
    correct = choice_id_of(body, "correct", env)
    race = _race(env, "judge", child_id, body["session_id"], correct)
    env.ai.calls.clear()

    response = env.answer(body["session_id"], correct)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ENDED"
    assert len(env.cue_rows(body["session_id"])) == 1
    assert env.session_row(body["session_id"]).status == "ended"
    assert env.ai.names() == ["judge", "judge"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


def test_continue_answer_racing_an_ending_answer_is_session_ended(env):
    # 종료 답이 먼저 저장된 뒤 계속 답이 저장하려 함 → 409 SESSION_ENDED, 턴 추가·선택 덮어쓰기 없음
    child_id = env.login_child(grade="H1")
    body = env.started()
    correct = choice_id_of(body, "correct", env)
    other = choice_id_of(body, "other", env)
    race = _race(env, "turn", child_id, body["session_id"], correct)
    env.ai.calls.clear()

    response = env.answer(body["session_id"], other)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_ENDED"
    turns = env.turn_rows(body["session_id"])
    assert len(turns) == 1
    assert turns[0].chosen_choice_id == correct
    assert env.session_row(body["session_id"]).status == "ended"
    assert env.ai.names() == ["turn", "judge"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


# (c) 멈춘 세션과 충돌 → 409 SESSION_STOPPED


def test_stop_racing_a_stop_is_session_stopped(env):
    # 두 요청 모두 safe_reply를 받음 → 먼저 멈춤이 저장됨 → 뒤쪽 멈춤 저장은 409 SESSION_STOPPED
    child_id = env.login_child(grade="H1")
    body = env.started()
    doubtful = choice_id_of(body, "doubtful", env)
    race = _race(env, "turn", child_id, body["session_id"], doubtful)
    env.ai.turn_status = "safe_reply"
    env.ai.calls.clear()

    response = env.answer(body["session_id"], choice_id_of(body, "other", env))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_STOPPED"
    assert env.session_row(body["session_id"]).status == "stopped"
    assert len(env.turn_rows(body["session_id"])) == 2
    assert env.ai.names() == ["turn", "turn"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


def test_continue_answer_racing_a_stop_is_session_stopped(env):
    # 안쪽 요청만 safe_reply → 멈춤이 먼저 저장된 뒤 바깥 계속 답이 저장하려 함 → 409 SESSION_STOPPED
    child_id = env.login_child(grade="H1")
    body = env.started()
    doubtful = choice_id_of(body, "doubtful", env)
    other = choice_id_of(body, "other", env)
    race = _race(env, "turn", child_id, body["session_id"], doubtful, inner_turn_status="safe_reply")
    env.ai.calls.clear()

    response = env.answer(body["session_id"], other)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_STOPPED"
    turns = env.turn_rows(body["session_id"])
    assert len(turns) == 2
    assert turns[1].ai_status == "safe_reply"
    assert env.session_row(body["session_id"]).status == "stopped"
    assert env.ai.names() == ["turn", "turn"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


def test_ending_answer_racing_a_stop_is_session_stopped(env):
    # 안쪽 계속 답이 safe_reply로 멈춘 뒤 바깥 종료 답(judge 응답 직후)이 저장하려 함 → 409 SESSION_STOPPED
    child_id = env.login_child(grade="H1")
    body = env.started()
    correct = choice_id_of(body, "correct", env)
    doubtful = choice_id_of(body, "doubtful", env)
    race = _race(env, "judge", child_id, body["session_id"], doubtful, inner_turn_status="safe_reply")
    env.ai.calls.clear()

    response = env.answer(body["session_id"], correct)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_STOPPED"
    assert env.session_row(body["session_id"]).status == "stopped"
    assert env.cue_rows(body["session_id"]) == []
    assert env.ai.names() == ["judge", "turn"]
    _assert_loser_saved_nothing(env, body["session_id"], race)


def test_cue_results_reject_duplicate_session_cue(env):
    # DB 유일 제약 uq_cue_results_session_cue
    from datetime import datetime, timezone

    from sqlalchemy.exc import IntegrityError

    child_id = env.login_child(grade="H1")
    body = env.started()
    env.answer(body["session_id"], choice_id_of(body, "correct", env))
    existing = env.cue_rows(body["session_id"])[0]

    with pytest.raises(IntegrityError):
        with env.session_factory.begin() as db:
            db.add(
                CueResult(
                    session_id=UUID(body["session_id"]),
                    child_id=child_id,
                    cue_id=existing.cue_id,
                    outcome="missed",
                    recorded_at=datetime.now(timezone.utc),
                )
            )
