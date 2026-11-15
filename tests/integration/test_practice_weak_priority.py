"""A15 약점 우선 출제 (T-36 — F-18 ①) 통합 테스트.

F-18 ① Given 같은 단서를 반복해서 놓친 기록 When 다음 출제 Then 그 단서가 포함된 상황이 우선 출제된다.
약점 단서 = 공통 규칙 `select_weak_cues`(DECISIONS #122 — 종료 세션 missed 2번 이상 + 최근 판정 missed)를
출제에도 쓴다(OQ 14 잠정 — 임계값 2, 기간 제한 없음). 멈춘·진행 중 세션은 집계하지 않는다(T-36 완료 조건,
DECISIONS #113). not_shown은 저장되지 않으므로 영향이 없다(#109, ADR-0018).

과거 기록은 DB에 직접 넣는다(AI Fake의 판정을 조작하지 않기 위해). 출제 난수는 고정 시드(1234)다.

T-30(사본 ai dev 8d900d1)부터 사기 영역은 4개 시나리오이고 어느 시나리오에도 그 시나리오에만 있는 단서가 없다.
그래서 "약점 단서를 포함한 시나리오 집합(`scenarios_with`)"이 사기 영역 전체보다 작은 단서로 검증한다 — 약점 우선이면
그 집합 안에서, 아니면 기준 출제(baseline)와 같다. baseline이 그 집합 밖인 단서(`cue_absent_from`)를 쓰면 둘이 구분된다.
"""

import random
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.main import create_app
from tests.integration.helpers.practice_env import SCENARIO_CLUES, RecordingPracticeAI, WeakEnv

SCAM = sorted(sid for sid in SCENARIO_CLUES if sid.startswith("scam_"))
SCAM_CUES = sorted({c for sid in SCAM for c in SCENARIO_CLUES[sid]})


def scenarios_with(cue: str) -> set[str]:
    """그 단서를 목표 단서로 가진 사기 시나리오."""
    return {sid for sid in SCAM if cue in SCENARIO_CLUES[sid]}


def cue_absent_from(scenario_id: str) -> str:
    """그 시나리오에는 없고 다른 사기 시나리오에는 있는 단서 하나(정렬 순 첫 번째)."""
    return next(c for c in SCAM_CUES if c not in SCENARIO_CLUES[scenario_id])


@pytest.fixture
def env(tmp_path) -> Iterator[WeakEnv]:
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'weak.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield WeakEnv(client, ai)
    app.state.engine.dispose()


@pytest.fixture
def baseline(env) -> str:
    """기록 없는 아이가 같은 시드로 받는 시나리오(약점 우선이 없을 때의 출제)."""
    env.login_child()
    return env.drawn_scenario()


def test_every_scam_cue_selects_a_proper_subset_of_scam_scenarios():
    # 이 파일의 전제 — 어떤 단서든 그 단서를 가진 사기 시나리오가 전체보다 적다(약점 우선이 후보를 좁힌다).
    # 콘텐츠가 바뀌면 테스트를 다시 설계해야 한다
    assert len(SCAM) >= 2
    for cue in SCAM_CUES:
        assert scenarios_with(cue), cue
        assert scenarios_with(cue) != set(SCAM), cue


# ---- 정상 ------------------------------------------------------------------------


@pytest.mark.parametrize("cue", SCAM_CUES)
def test_repeatedly_missed_cue_scenario_is_drawn(env, cue):
    child_id = env.login_child()
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})

    assert env.drawn_scenario() in scenarios_with(cue)


def test_weak_priority_overrides_baseline_draw(env, baseline):
    cue = cue_absent_from(baseline)
    child_id = env.login_child()
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})

    drawn = env.drawn_scenario()
    assert drawn != baseline
    assert drawn in scenarios_with(cue)


# ---- 경계 ------------------------------------------------------------------------


def test_single_miss_is_not_weak(env, baseline):
    child_id = env.login_child()
    env.past_session(child_id, {cue_absent_from(baseline): "missed"})

    assert env.drawn_scenario() == baseline


def test_found_after_misses_is_no_longer_weak(env, baseline):
    cue = cue_absent_from(baseline)
    child_id = env.login_child()
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "found"})

    assert env.drawn_scenario() == baseline


# ---- 예외(집계 제외) ---------------------------------------------------------------


@pytest.mark.parametrize("status", ["stopped", "in_progress"])
def test_misses_in_not_ended_sessions_are_ignored(env, baseline, status):
    cue = cue_absent_from(baseline)
    child_id = env.login_child()
    env.past_session(child_id, {cue: "missed"}, status=status)
    env.past_session(child_id, {cue: "missed"}, status=status)

    assert env.drawn_scenario() == baseline


def test_other_childs_misses_are_ignored(env, baseline):
    cue = cue_absent_from(baseline)
    someone = env.login_child()
    env.past_session(someone, {cue: "missed"})
    env.past_session(someone, {cue: "missed"})
    env.login_child()

    assert env.drawn_scenario() == baseline
