"""힌트 단계 산정 domain 순수 함수 (T-36 — F-18 ②).

근거: Architecture "연습 출제 규칙" 힌트 감소 행 — 목표 단서별 연속 `found` 횟수 c에 대해
`hint_level = max(0, HINT_MAX − c)`, c가 늘면 힌트 단계가 줄거나 같음(단조). `HINT_MAX` 값은 PRD OQ 14(보류,
구현 중 결정) — 잠정값 2.
입력은 종료 세션의 `cue_results`(found·missed만 — not_shown은 저장되지 않음, DECISIONS #109)이고, 멈춘 세션은
리포지토리가 넘기지 않는다. "최근"의 정렬은 약점 단서 공통 규칙과 같다(ended_at, 같으면 session_id 큰 쪽).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.domain.hint_level import HINT_MAX, consecutive_found, hint_levels
from app.domain.weak_cues import CueOutcome

T0 = datetime(2026, 11, 1, 3, 0, 0, tzinfo=timezone.utc)
_seq = iter(range(1, 10_000))


def o(cue_id: str, outcome: str, day: int, session: int | None = None) -> CueOutcome:
    return CueOutcome(
        cue_id=cue_id,
        outcome=outcome,
        ended_at=T0 + timedelta(days=day),
        session_id=UUID(int=session if session is not None else next(_seq)),
    )


def test_hint_max_is_provisional_two():
    # PRD OQ 14 잠정값 — 바뀌면 이 테스트와 보고를 함께 고친다
    assert HINT_MAX == 2


# ---- 정상 ------------------------------------------------------------------------


def test_one_recent_found_lowers_hint_by_one():
    assert hint_levels([o("c1", "found", 0)], ["c1"]) == {"c1": HINT_MAX - 1}


def test_levels_are_per_target_cue():
    outcomes = [o("c1", "found", 0), o("c1", "found", 1), o("c2", "missed", 1)]
    assert hint_levels(outcomes, ["c1", "c2", "c3"]) == {"c1": 0, "c2": HINT_MAX, "c3": HINT_MAX}


# ---- 경계 ------------------------------------------------------------------------


def test_no_record_is_full_hint():
    assert consecutive_found([], "c1") == 0
    assert hint_levels([], ["c1"]) == {"c1": HINT_MAX}


def test_more_finds_than_hint_max_clamps_to_zero():
    outcomes = [o("c1", "found", day) for day in range(HINT_MAX + 3)]
    assert consecutive_found(outcomes, "c1") == HINT_MAX + 3
    assert hint_levels(outcomes, ["c1"]) == {"c1": 0}


def test_streak_counts_from_latest_until_first_miss():
    outcomes = [o("c1", "found", 0), o("c1", "missed", 1), o("c1", "found", 2)]
    assert consecutive_found(outcomes, "c1") == 1
    # 입력 순서와 무관 — 최근 순으로 센다
    assert consecutive_found(list(reversed(outcomes)), "c1") == 1


def test_latest_miss_resets_to_full_hint():
    outcomes = [o("c1", "found", 0), o("c1", "found", 1), o("c1", "missed", 2)]
    assert hint_levels(outcomes, ["c1"]) == {"c1": HINT_MAX}


def test_same_ended_at_uses_larger_session_id_as_latest():
    outcomes = [o("c1", "found", 0, session=5), o("c1", "missed", 0, session=9)]
    assert consecutive_found(outcomes, "c1") == 0
    outcomes = [o("c1", "found", 0, session=9), o("c1", "missed", 0, session=5)]
    assert consecutive_found(outcomes, "c1") == 1


def test_other_cues_do_not_break_the_streak():
    # 다른 단서의 놓침, 이 단서가 드러나지 않은 세션(행 없음)은 연속에 끼지 않는다
    outcomes = [o("c1", "found", 0), o("c2", "missed", 1), o("c1", "found", 2)]
    assert consecutive_found(outcomes, "c1") == 2


@pytest.mark.parametrize("history_length", range(0, 6))
def test_another_found_never_raises_hint_level(history_length):
    # F-18 ② 단조: 같은 단서를 한 번 더 찾으면 힌트는 이전보다 적거나 같다
    outcomes = [o("c1", "found" if day % 2 else "missed", day) for day in range(history_length)]
    before = hint_levels(outcomes, ["c1"])["c1"]
    after = hint_levels(outcomes + [o("c1", "found", history_length)], ["c1"])["c1"]
    assert after <= before
    assert 0 <= after <= HINT_MAX


# ---- 예외 ------------------------------------------------------------------------


def test_unknown_outcome_is_rejected():
    with pytest.raises(ValueError, match="unknown cue outcome"):
        hint_levels([o("c1", "not_shown", 0)], ["c1"])


def test_naive_ended_at_is_rejected():
    naive = CueOutcome(cue_id="c1", outcome="found", ended_at=datetime(2026, 11, 1), session_id=UUID(int=1))
    with pytest.raises(ValueError, match="timezone"):
        consecutive_found([naive], "c1")
