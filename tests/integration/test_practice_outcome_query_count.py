"""연습 시작 시 종료 세션 기록 조회는 1회 (T-96 — PR #26 팀원 리뷰 P2).

리뷰 원문(사용자 전달): "`app/services/practice.py`에서 연습 시작 시 `_weak_cue_ids()`와 `_session_hint_level()`이
각각 `_ended_cue_outcomes()`를 호출해 동일한 종료 세션 기록을 두 번 조회합니다. … 종료 세션 기록을 한 번만 조회한 뒤
약점 단서 선정과 힌트 계산에 재사용하도록 개선하면 좋겠습니다."
동작 변화 없음 — 약점 우선 출제·힌트 단계 값은 tests/integration/test_practice_weak_priority.py·test_practice_hint_level.py가 지킨다.
"""

import pytest

from app.repositories.practice import SqlAlchemyPracticeRepository
from tests.integration.test_practice_result import env  # noqa: F401 — fixture 재사용


@pytest.fixture
def query_counter(monkeypatch) -> dict[str, int]:
    counter = {"ended_cue_outcomes": 0}
    original = SqlAlchemyPracticeRepository.ended_cue_outcomes

    def counting(self, *args, **kwargs):
        counter["ended_cue_outcomes"] += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(SqlAlchemyPracticeRepository, "ended_cue_outcomes", counting)
    return counter


def test_area_start_reads_ended_outcomes_once(env, query_counter):
    env.login_child(grade="H1")
    env.ended(("correct",))  # 기록이 있는 상태
    query_counter["ended_cue_outcomes"] = 0

    response = env.start()

    assert response.status_code == 201, response.text
    assert query_counter["ended_cue_outcomes"] == 1


def test_area_start_without_history_reads_once(env, query_counter):
    env.login_child(grade="H1")
    query_counter["ended_cue_outcomes"] = 0

    response = env.start()

    assert response.status_code == 201, response.text
    assert query_counter["ended_cue_outcomes"] == 1


def test_retry_reads_ended_outcomes_once(env, query_counter):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    query_counter["ended_cue_outcomes"] = 0

    response = env.retry(original_id)

    assert response.status_code == 201, response.text
    assert query_counter["ended_cue_outcomes"] == 1


def test_failed_start_does_not_change_query_count_rule(env, query_counter):
    # AI 실패(503)여도 조회는 1회를 넘지 않는다
    env.login_child(grade="H1")
    env.ai.fail.add("variant")
    query_counter["ended_cue_outcomes"] = 0

    response = env.start()

    assert response.status_code == 503
    assert query_counter["ended_cue_outcomes"] <= 1
