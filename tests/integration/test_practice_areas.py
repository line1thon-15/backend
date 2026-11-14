"""A15 영역 출제 활성화 — 명의 빌려주기·친구의 무리한 부탁 (T-30 — F-15, F-16, F-14 ②).

근거: Architecture "API 규격" A15(`{mode:"area", area}` | `{mode:"mission"}`), "콘텐츠 파일 규격"(AI 사본 =
ai 저장소 고정 커밋 통째 복사, 학년 제한은 백엔드 `scenario_meta.json`), DECISIONS #108(영역 값
`identity_lending`·`friend_pressure`). F-15: 1차 출제 영역은 사기·명의 빌려주기·친구의 무리한 부탁 — 따돌림 등은
출제하지 않는다.

실제 콘텐츠 사본(ai dev 8d900d1)으로 검증한다. AI는 기록용 Fake(실제 HTTP 없음), DB는 pytest tmp_path SQLite.
"""

import itertools
import random
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.db.models import PracticeSession
from app.main import create_app
from tests.integration.test_practice_sessions import Env, RecordingPracticeAI

IDENTITY_IDS = {
    "identity_dm_account_01",
    "identity_phone_senior_01",
    "identity_openchat_card_01",
    "identity_game_account_01",
}
FRIEND_IDS = {"friend_homework_01", "friend_money_01", "friend_game_skin_01", "friend_cover_lie_01"}
SCAM_UNRESTRICTED = {"scam_game_item_01": "game_item", "scam_allowance_event_01": "allowance"}
HIGH_PAYING_JOB_IDS = {"scam_dm_parttime_01", "scam_jobboard_link_01"}
AREA_SCENARIOS = {"identity_lending": IDENTITY_IDS, "friend_pressure": FRIEND_IDS}


def _make_env(tmp_path, rng_factory) -> Iterator[Env]:
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'areas.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=rng_factory,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield Env(client, ai)
    app.state.engine.dispose()


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    yield from _make_env(tmp_path, lambda: random.Random(1234))


@pytest.fixture
def seeded_env(tmp_path) -> Iterator[Env]:
    """새 출제마다 다른 시드(0, 1, 2, …) — 여러 번 출제해 후보 집합을 관찰한다(결정적)."""
    seeds = itertools.count()
    yield from _make_env(tmp_path, lambda: random.Random(next(seeds)))


# ---- 정상: 두 영역 영역 선택 출제 -------------------------------------------------------


@pytest.mark.parametrize("area", ["identity_lending", "friend_pressure"])
def test_area_mode_starts_session_for_new_area(env, area):
    env.login_child(grade="H1")

    response = env.start(area)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["mode"] == "area"
    assert body["area"] == area
    assert body["status"] == "in_progress"
    assert body["turn"]["turn_index"] == 0
    row = env.session_row(body["session_id"])
    assert row.area == area
    assert row.mode == "area"
    assert row.scenario_id in AREA_SCENARIOS[area]
    assert row.subtype is None  # 하위 유형(F-14)은 사기 영역에만 있다
    assert env.ai.names() == ["variant", "start"]
    assert env.ai.requests("variant")[0].scenario_id == row.scenario_id


# ---- 경계: 학년 제한 없음 — 가장 낮은 학년(E6)·중학생 -----------------------------------------


@pytest.mark.parametrize("area", ["identity_lending", "friend_pressure"])
@pytest.mark.parametrize("grade", ["E6", "M1"])
def test_new_areas_have_no_grade_limit(env, area, grade):
    env.login_child(grade=grade)

    response = env.start(area)

    assert response.status_code == 201, response.text
    assert env.session_row(response.json()["session_id"]).scenario_id in AREA_SCENARIOS[area]


@pytest.mark.parametrize("grade", ["E6", "M1", "M3"])
def test_non_high_school_child_gets_unrestricted_scam_scenario(seeded_env, grade):
    # 고수익 알바(min_grade H1) 2개만 학년 제한 — 게임 아이템·용돈 이벤트는 중학생 이하도 받는다
    seeded_env.login_child(grade=grade)

    drawn = []
    for _ in range(12):
        response = seeded_env.start("scam")
        assert response.status_code == 201, response.text
        drawn.append(seeded_env.session_row(response.json()["session_id"]))

    assert {row.scenario_id for row in drawn} == set(SCAM_UNRESTRICTED)
    for row in drawn:
        assert row.subtype == SCAM_UNRESTRICTED[row.scenario_id]


def test_high_school_child_scam_candidates_include_high_paying_job(seeded_env):
    seeded_env.login_child(grade="H1")

    drawn = set()
    for _ in range(20):
        response = seeded_env.start("scam")
        assert response.status_code == 201, response.text
        drawn.add(seeded_env.session_row(response.json()["session_id"]).scenario_id)

    assert drawn == set(SCAM_UNRESTRICTED) | HIGH_PAYING_JOB_IDS


# ---- 정상: 오늘의 미션 후보에 두 영역 포함 ------------------------------------------------


def _mission_rows(env: Env, times: int) -> list[PracticeSession]:
    rows = []
    for _ in range(times):
        response = env.client.post("/api/v1/practice/sessions", json={"mode": "mission"})
        assert response.status_code == 201, response.text
        body = response.json()
        row = env.session_row(body["session_id"])
        assert body["area"] == row.area
        rows.append(row)
    return rows


def test_mission_candidates_include_all_three_areas(seeded_env):
    seeded_env.login_child(grade="H1")

    rows = _mission_rows(seeded_env, 30)

    assert {row.area for row in rows} == {"scam", "identity_lending", "friend_pressure"}
    for row in rows:
        assert row.mode == "mission"
        if row.area != "scam":
            assert row.scenario_id in AREA_SCENARIOS[row.area]


def test_mission_for_middle_school_child_never_draws_high_paying_job(seeded_env):
    seeded_env.login_child(grade="M2")

    rows = _mission_rows(seeded_env, 30)

    assert {row.area for row in rows} == {"scam", "identity_lending", "friend_pressure"}
    assert not {row.scenario_id for row in rows} & HIGH_PAYING_JOB_IDS


# ---- 예외: 1차 밖 영역은 출제되지 않음 (F-15) ----------------------------------------------


@pytest.mark.parametrize("area", ["bullying", "ostracism", "SCAM", "identity-lending"])
def test_area_outside_first_phase_is_422(env, area):
    env.login_child(grade="H1")

    response = env.start(area)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert env.ai.calls == []
    assert env.count(PracticeSession) == 0
