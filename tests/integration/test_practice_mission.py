"""A15 오늘의 미션 `{mode:"mission"}` (T-49 — F-10).

근거: Architecture "API 규격" A15(`{mode:"area", area}` | `{mode:"mission"}` | `{mode:"retry", retry_of}`),
"연습 출제 규칙" 절 "오늘의 미션 (F-10)" 행 — `mode:"mission"` = 영역 미지정 새 출제(위 규칙 그대로),
구성 규칙은 PRD OQ 13 중 미션 — 보류(임시 구조). practice_sessions `mode` enum(`area`,`mission`,`retry`),
`draw_index` = 아이별 새 출제 순번(retry 제외).

T-30(사본 ai dev 8d900d1 — 3개 영역 각 4개)부터 실제 콘텐츠에 세 영역이 모두 있다. 학년 제한으로 후보가 갈리는
경우는 실제 사본의 scenario_meta.json에서 지정 영역 시나리오를 모두 min_grade H1로 바꾼 OS 임시 디렉터리 콘텐츠로 검증한다.
"""

import json
import random
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.content.loader import DEFAULT_DATA_DIR
from app.core.config import Settings
from app.db.base import Base
from app.db.models import PracticeSession, PracticeTurn
from app.main import create_app
from tests.integration.helpers.practice_env import CONTENT, SCENARIO_CLUES, RecordingPracticeAI, WeakEnv

ALL_AREAS = ("scam", "identity_lending", "friend_pressure")


def _content_limited_to_high_school(root: Path, areas: tuple[str, ...]) -> Path:
    """실제 콘텐츠 사본 + `areas` 영역 시나리오를 모두 min_grade H1로 (scenario_meta.json만 바꿈)."""
    data_dir = root / "content"
    shutil.copytree(DEFAULT_DATA_DIR, data_dir)
    meta_path = data_dir / "scenario_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    for item in meta["scenarios"]:
        if CONTENT.scenarios[item["scenario_id"]].area in areas:
            item["min_grade"] = "H1"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return data_dir


class MissionEnv(WeakEnv):
    def mission(self):
        return self.client.post("/api/v1/practice/sessions", json={"mode": "mission"})

    def retry(self, retry_of: str):
        return self.client.post("/api/v1/practice/sessions", json={"mode": "retry", "retry_of": retry_of})


def _make_env(tmp_path: Path, *, content_dir: Path | None = None) -> Iterator[MissionEnv]:
    ai = RecordingPracticeAI()
    kwargs = {"content_dir": content_dir} if content_dir is not None else {}
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'mission.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
        **kwargs,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield MissionEnv(client, ai)
    app.state.engine.dispose()


@pytest.fixture
def env(tmp_path) -> Iterator[MissionEnv]:
    yield from _make_env(tmp_path)


@pytest.fixture
def scam_limited_env(tmp_path) -> Iterator[MissionEnv]:
    yield from _make_env(tmp_path, content_dir=_content_limited_to_high_school(tmp_path, ("scam",)))


@pytest.fixture
def all_limited_env(tmp_path) -> Iterator[MissionEnv]:
    yield from _make_env(tmp_path, content_dir=_content_limited_to_high_school(tmp_path, ALL_AREAS))


# ---- 정상 --------------------------------------------------------------------------


def test_mission_starts_session_with_mode_mission(env):
    child_id = env.login_child(grade="H1")

    response = env.mission()

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["mode"] == "mission"
    assert body["area"] in ALL_AREAS
    assert body["is_retry"] is False
    assert body["status"] == "in_progress"
    assert body["turn"]["turn_index"] == 0
    row = env.session_row(body["session_id"])
    assert row.child_id == child_id
    assert row.mode == "mission"
    assert row.area == body["area"]
    assert CONTENT.scenarios[row.scenario_id].area == row.area
    assert row.retry_of is None
    assert row.draw_index == 1
    assert env.ai.names() == ["variant", "start"]


def test_mission_draw_index_counts_with_area_draws(env):
    # 새 출제 순번은 area·mission을 함께 센다(retry 제외 — Architecture practice_sessions draw_index)
    env.login_child(grade="H1")

    first = env.started()
    second = env.mission().json()
    third = env.started()

    assert [env.session_row(v["session_id"]).draw_index for v in (first, second, third)] == [1, 2, 3]


def test_mission_draws_from_area_other_than_scam(scam_limited_env):
    # 사기 영역이 전부 고등학생 전용이면 중학생은 사기 영역 후보가 없다 — 영역 미지정이면 다른 영역에서 출제된다
    env = scam_limited_env
    env.login_child(grade="M2")
    assert env.start("scam").status_code == 409

    response = env.mission()

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["area"] in ("identity_lending", "friend_pressure")
    row = env.session_row(body["session_id"])
    assert row.area == body["area"]
    assert CONTENT.scenarios[row.scenario_id].area == row.area
    assert row.mode == "mission"
    assert row.target_cue_ids == list(SCENARIO_CLUES[row.scenario_id])


def test_mission_applies_weak_priority_across_areas(env):
    # 약점 우선(T-36, #122)도 영역 구분 없이 같은 규칙 — 친구 압박 영역에만 있는 단서를 반복해서 놓친 고등학생
    cue = "guilt_pressure"
    assert {entry.area for sid, entry in CONTENT.scenarios.items() if cue in SCENARIO_CLUES[sid]} == {
        "friend_pressure"
    }
    child_id = env.login_child(grade="H1")
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})

    body = env.mission().json()

    row = env.session_row(body["session_id"])
    assert cue in SCENARIO_CLUES[row.scenario_id]
    assert body["area"] == "friend_pressure"


# ---- 경계 --------------------------------------------------------------------------


def test_retry_of_mission_session_keeps_area_and_mode_retry(env):
    env.login_child(grade="H1")
    original = env.mission().json()
    session_id = original["session_id"]
    choice = next(c["id"] for c in env.turn_rows(session_id)[0].choices if c["kind"] == "correct")
    assert env.answer(session_id, choice).status_code == 200

    response = env.retry(session_id)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["mode"] == "retry"
    assert body["is_retry"] is True
    assert body["area"] == original["area"]
    row = env.session_row(body["session_id"])
    assert row.retry_of is not None and str(row.retry_of) == session_id
    assert row.scenario_id == env.session_row(session_id).scenario_id
    assert row.draw_index is None


def test_mission_varies_from_previous_session_of_same_scenario(env):
    # F-12: 같은 시나리오 직전 세션과 platform·tone 1개 이상 다름 — 새 출제 규칙 그대로
    env.login_child(grade="H1")
    seen: dict[str, tuple[str, str]] = {}
    for _ in range(4):
        body = env.mission().json()
        row = env.session_row(body["session_id"])
        pair = (row.variant["platform"], row.variant["tone"])
        if row.scenario_id in seen:
            assert pair != seen[row.scenario_id]
        seen[row.scenario_id] = pair


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "mission", "area": "scam"},
        {"mode": "mission", "retry_of": "00000000-0000-0000-0000-000000000000"},
        {"mode": "missions"},
    ],
)
def test_invalid_mission_request_is_422(env, payload):
    env.login_child(grade="H1")

    response = env.client.post("/api/v1/practice/sessions", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert env.ai.calls == []


# ---- 예외 --------------------------------------------------------------------------


@pytest.mark.parametrize("grade", ["E6", "M3"])
def test_mission_without_candidates_is_409_no_scenario(all_limited_env, grade):
    # 모든 영역 시나리오가 고등학생 전용인 콘텐츠 — 중학생 이하는 미션 후보가 없다
    env = all_limited_env
    env.login_child(grade=grade)

    response = env.mission()

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NO_SCENARIO_AVAILABLE"
    assert env.ai.calls == []
    assert env.count(PracticeSession) == 0


@pytest.mark.parametrize("failing", ["variant", "start"])
def test_mission_ai_failure_is_503_and_saves_nothing(env, failing):
    env.login_child(grade="H1")
    env.ai.fail.add(failing)

    response = env.mission()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.count(PracticeSession) == 0
    assert env.count(PracticeTurn) == 0


def test_mission_with_guardian_session_is_403(env):
    env.login_child(grade="H1")
    env.client.cookies.clear()
    assert (
        env.client.post(
            "/api/v1/guardians", json={"email": "mission-guardian@example.com", "password": "correct-horse-42"}
        ).status_code
        == 201
    )

    response = env.mission()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert env.ai.calls == []
    assert env.count(PracticeSession) == 0


def test_mission_without_session_is_401(env):
    env.client.cookies.clear()

    response = env.mission()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
