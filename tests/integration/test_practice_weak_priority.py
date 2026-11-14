"""A15 약점 우선 출제 (T-36 — F-18 ①) 통합 테스트.

F-18 ① Given 같은 단서를 반복해서 놓친 기록 When 다음 출제 Then 그 단서가 포함된 상황이 우선 출제된다.
약점 단서 = 공통 규칙 `select_weak_cues`(DECISIONS #122 — 종료 세션 missed 2번 이상 + 최근 판정 missed)를
출제에도 쓴다(OQ 14 잠정 — 임계값 2, 기간 제한 없음). 멈춘·진행 중 세션은 집계하지 않는다(T-36 완료 조건,
DECISIONS #113). not_shown은 저장되지 않으므로 영향이 없다(#109, ADR-0018).

과거 기록은 DB에 직접 넣는다(AI Fake의 판정을 조작하지 않기 위해). 출제 난수는 고정 시드(1234)다.
"""

import random
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.db.models import CueResult, PracticeSession
from app.main import create_app
from tests.integration.test_practice_sessions import SCENARIO_CLUES, Env, RecordingPracticeAI

T0 = datetime(2026, 11, 1, 3, 0, 0, tzinfo=timezone.utc)
SCAM = sorted(sid for sid in SCENARIO_CLUES if sid.startswith("scam_"))


def unique_cue(scenario_id: str) -> str:
    """그 시나리오에만 있는 단서 하나 — 다른 scam 시나리오에는 없다."""
    others = {c for sid in SCAM if sid != scenario_id for c in SCENARIO_CLUES[sid]}
    return next(c for c in SCENARIO_CLUES[scenario_id] if c not in others)


class WeakEnv(Env):
    def __init__(self, client: TestClient, ai: RecordingPracticeAI) -> None:
        super().__init__(client, ai)
        self._day = 0

    def past_session(self, child_id: UUID, cues: dict[str, str], *, status: str = "ended") -> None:
        """과거 세션 1개 + 단서 판정 행. 시나리오 ID는 콘텐츠에 없는 값(F-12 직전 변형 조회에 끼지 않게)."""
        self._day += 1
        ended_at = T0 + timedelta(days=self._day)
        with self.session_factory.begin() as db:
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
                draw_index=self._day,
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


def test_scam_area_has_two_scenarios_with_unique_cues():
    # 이 파일의 전제 — 콘텐츠가 바뀌면 테스트를 다시 설계해야 한다
    assert len(SCAM) == 2
    assert all(unique_cue(sid) for sid in SCAM)


# ---- 정상 ------------------------------------------------------------------------


@pytest.mark.parametrize("target", SCAM)
def test_repeatedly_missed_cue_scenario_is_drawn(env, target):
    child_id = env.login_child()
    cue = unique_cue(target)
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})

    assert env.drawn_scenario() == target


def test_weak_priority_overrides_baseline_draw(env, baseline):
    other = next(sid for sid in SCAM if sid != baseline)
    child_id = env.login_child()
    env.past_session(child_id, {unique_cue(other): "missed"})
    env.past_session(child_id, {unique_cue(other): "missed"})

    assert env.drawn_scenario() == other


# ---- 경계 ------------------------------------------------------------------------


def test_single_miss_is_not_weak(env, baseline):
    other = next(sid for sid in SCAM if sid != baseline)
    child_id = env.login_child()
    env.past_session(child_id, {unique_cue(other): "missed"})

    assert env.drawn_scenario() == baseline


def test_found_after_misses_is_no_longer_weak(env, baseline):
    other = next(sid for sid in SCAM if sid != baseline)
    cue = unique_cue(other)
    child_id = env.login_child()
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "found"})

    assert env.drawn_scenario() == baseline


# ---- 예외(집계 제외) ---------------------------------------------------------------


@pytest.mark.parametrize("status", ["stopped", "in_progress"])
def test_misses_in_not_ended_sessions_are_ignored(env, baseline, status):
    other = next(sid for sid in SCAM if sid != baseline)
    child_id = env.login_child()
    env.past_session(child_id, {unique_cue(other): "missed"}, status=status)
    env.past_session(child_id, {unique_cue(other): "missed"}, status=status)

    assert env.drawn_scenario() == baseline


def test_other_childs_misses_are_ignored(env, baseline):
    other = next(sid for sid in SCAM if sid != baseline)
    someone = env.login_child()
    env.past_session(someone, {unique_cue(other): "missed"})
    env.past_session(someone, {unique_cue(other): "missed"})
    env.login_child()

    assert env.drawn_scenario() == baseline
