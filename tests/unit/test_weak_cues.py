"""더 연습이 필요한 단서(아이 Y8)·약점 단서(보호자 G3) 공통 domain 규칙 (T-46 — F-29 ①).

근거: DECISIONS #122·Architecture "성장 계산 규칙" 더 연습이 필요한 단서 행(2026-11-12). 사용자 결정 원문 "2번 이상 + 최근 놓침 (추천)" — 선택지 설명 원문
"종료 세션에서 2번 이상 놓친 단서 중, 가장 최근 판정이 '놓침'인 것만. 많이 놓친 순, 최대 3개.
나중에 찾으면 목록에서 빠져 성장이 보여요."

architect 판단(#122, 사용자 확인 대상): 놓친 수 동점 → 가장 최근 missed 세션 ended_at 늦은 순 → cue_id 오름차순,
같은 단서에서 ended_at이 같은 세션이 둘 이상이면 session_id가 큰 쪽을 최근으로 본다. 기간 제한 없음.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.domain.weak_cues import (
    WEAK_CUE_MAX,
    WEAK_CUE_MIN_MISSES,
    CueOutcome,
    select_weak_cues,
)

T0 = datetime(2026, 11, 1, 3, 0, 0, tzinfo=timezone.utc)


def at(days: int) -> datetime:
    return T0 + timedelta(days=days)


_seq = iter(range(1, 10_000))


def sid(n: int) -> UUID:
    return UUID(int=n)


def o(cue_id: str, outcome: str, day: int, session: int | None = None) -> CueOutcome:
    session_id = sid(session if session is not None else next(_seq))
    return CueOutcome(cue_id=cue_id, outcome=outcome, ended_at=at(day), session_id=session_id)


def test_constants():
    assert WEAK_CUE_MIN_MISSES == 2
    assert WEAK_CUE_MAX == 3


def test_missed_twice_and_latest_missed_is_listed():
    assert select_weak_cues([o("c1", "missed", 0), o("c1", "missed", 1)]) == ("c1",)


def test_missed_once_is_not_listed():
    assert select_weak_cues([o("c1", "missed", 0), o("c1", "found", -1)]) == ()


def test_found_after_two_misses_drops_the_cue():
    # 나중에 찾으면 목록에서 빠진다
    assert select_weak_cues([o("c1", "missed", 0), o("c1", "missed", 1), o("c1", "found", 2)]) == ()


def test_found_in_between_but_latest_missed_is_listed():
    outcomes = [o("c1", "missed", 0), o("c1", "found", 1), o("c1", "missed", 2)]

    assert select_weak_cues(outcomes) == ("c1",)


def test_input_order_does_not_matter():
    outcomes = [o("c1", "found", 2), o("c1", "missed", 0), o("c1", "missed", 1)]

    assert select_weak_cues(outcomes) == ()
    assert select_weak_cues(list(reversed(outcomes))) == ()


def test_order_by_missed_count_then_latest_missed_then_cue_id_and_max_3():
    outcomes = [
        # c_low: 2회, 마지막 놓침 day 9
        o("c_low", "missed", 1), o("c_low", "missed", 9),
        # c_many: 4회
        o("c_many", "missed", 1), o("c_many", "missed", 2), o("c_many", "missed", 3), o("c_many", "missed", 4),
        # c_b·c_a: 3회, 마지막 놓침 같은 day 5 → cue_id 순
        o("c_b", "missed", 1), o("c_b", "missed", 2), o("c_b", "missed", 5),
        o("c_a", "missed", 1), o("c_a", "missed", 3), o("c_a", "missed", 5),
        # c_recent: 3회, 마지막 놓침 day 8 → c_a·c_b보다 앞
        o("c_recent", "missed", 1), o("c_recent", "missed", 2), o("c_recent", "missed", 8),
    ]

    assert select_weak_cues(outcomes) == ("c_many", "c_recent", "c_a")


def test_same_ended_at_larger_session_id_is_latest_found():
    outcomes = [o("c1", "missed", 0, 1), o("c1", "missed", 1, 2), o("c1", "found", 1, 3)]

    assert select_weak_cues(outcomes) == ()


def test_same_ended_at_larger_session_id_is_latest_missed():
    outcomes = [o("c1", "missed", 0, 1), o("c1", "found", 1, 2), o("c1", "missed", 1, 3)]

    assert select_weak_cues(outcomes) == ("c1",)


def test_empty_input():
    assert select_weak_cues([]) == ()


def test_invalid_outcome_raises():
    with pytest.raises(ValueError):
        select_weak_cues([o("c1", "not_shown", 0)])


def test_naive_time_raises():
    with pytest.raises(ValueError):
        select_weak_cues(
            [CueOutcome(cue_id="c1", outcome="missed", ended_at=datetime(2026, 11, 1), session_id=sid(1))]
        )
