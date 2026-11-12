"""보호자 리포트 domain 집계 (T-25 — F-30 ①).

근거: Architecture "응답 DTO" GuardianReport(`areas:[{area, practice_count, last_practiced_at|null}]`,
`weak_cues:[{cue_id, label}]`), Tasks T-25 "영역별 진행·약점 단서 집계는 `status = ended` 세션만",
"영역 값은 scam·identity_lending·friend_pressure"(DECISIONS #108).

약점 단서 기준은 2026-11-12 사용자 답 "2번 이상 + 최근 놓침 (추천)" — 설명 원문 "종료 세션에서 2번 이상 놓친
단서 중, 가장 최근 판정이 '놓침'인 것만. 많이 놓친 순, 최대 3개." 동점 정렬(마지막 놓친 시각 최신 순 → cue_id 순)은
implementer가 정한 결정적 규칙이다.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.guardian_report import (
    WEAK_CUE_LIMIT,
    WEAK_CUE_MIN_MISSED,
    AreaProgress,
    CueOutcome,
    EndedSession,
    WeakCue,
    area_progress,
    weak_cues,
)

AREAS = ("scam", "identity_lending", "friend_pressure")
T0 = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)


def test_area_progress_counts_and_latest_per_area_in_given_order():
    sessions = [
        EndedSession(area="scam", ended_at=T0),
        EndedSession(area="scam", ended_at=T0 + timedelta(days=1)),
        EndedSession(area="friend_pressure", ended_at=T0 - timedelta(hours=1)),
    ]

    result = area_progress(AREAS, sessions)

    assert result == [
        AreaProgress(area="scam", practice_count=2, last_practiced_at=T0 + timedelta(days=1)),
        AreaProgress(area="identity_lending", practice_count=0, last_practiced_at=None),
        AreaProgress(area="friend_pressure", practice_count=1, last_practiced_at=T0 - timedelta(hours=1)),
    ]


def test_area_progress_without_sessions_is_zero_and_null_for_every_area():
    assert area_progress(AREAS, []) == [
        AreaProgress(area=area, practice_count=0, last_practiced_at=None) for area in AREAS
    ]


def test_area_progress_unknown_area_raises():
    with pytest.raises(ValueError):
        area_progress(AREAS, [EndedSession(area="name_lending", ended_at=T0)])


def test_area_progress_naive_ended_at_raises():
    with pytest.raises(ValueError):
        area_progress(AREAS, [EndedSession(area="scam", ended_at=datetime(2026, 11, 10))])


def at(hours: int) -> datetime:
    return T0 + timedelta(hours=hours)


def test_weak_cue_constants_are_user_decision():
    # 2026-11-12 사용자 답 "2번 이상 + 최근 놓침 (추천)" — 최대 3개
    assert WEAK_CUE_MIN_MISSED == 2
    assert WEAK_CUE_LIMIT == 3


def test_weak_cues_boundary_one_miss_is_not_weak_two_misses_is_weak():
    outcomes = [
        CueOutcome("keep_secret", "missed", at(1)),
        CueOutcome("urgency", "missed", at(1)),
        CueOutcome("urgency", "missed", at(2)),
    ]

    assert weak_cues(outcomes) == [WeakCue(cue_id="urgency", missed_count=2)]


def test_weak_cues_found_after_misses_drops_out():
    outcomes = [
        CueOutcome("urgency", "missed", at(1)),
        CueOutcome("urgency", "missed", at(2)),
        CueOutcome("urgency", "found", at(3)),
    ]

    assert weak_cues(outcomes) == []


def test_weak_cues_missed_again_after_found_comes_back():
    outcomes = [
        CueOutcome("urgency", "missed", at(1)),
        CueOutcome("urgency", "found", at(2)),
        CueOutcome("urgency", "missed", at(3)),
    ]

    assert weak_cues(outcomes) == [WeakCue(cue_id="urgency", missed_count=2)]


def test_weak_cues_input_order_does_not_matter():
    outcomes = [
        CueOutcome("urgency", "found", at(3)),
        CueOutcome("urgency", "missed", at(1)),
        CueOutcome("urgency", "missed", at(2)),
    ]

    assert weak_cues(outcomes) == []


def test_weak_cues_found_and_missed_at_same_latest_time_is_not_latest_missed():
    # 가장 최근 시각에 찾음·놓침이 같이 있으면 '최근 판정이 놓침'으로 보지 않는다(보수적 — 결정적 규칙)
    outcomes = [
        CueOutcome("urgency", "missed", at(1)),
        CueOutcome("urgency", "missed", at(2)),
        CueOutcome("urgency", "found", at(2)),
    ]

    assert weak_cues(outcomes) == []


def test_weak_cues_sorted_by_missed_desc_then_latest_miss_desc_then_cue_id_and_capped_at_three():
    outcomes = [
        # keep_secret 3회
        CueOutcome("keep_secret", "missed", at(1)),
        CueOutcome("keep_secret", "missed", at(2)),
        CueOutcome("keep_secret", "missed", at(3)),
        # urgency 2회, 마지막 놓침 at(9)
        CueOutcome("urgency", "missed", at(4)),
        CueOutcome("urgency", "missed", at(9)),
        # advance_payment 2회, 마지막 놓침 at(5)
        CueOutcome("advance_payment", "missed", at(4)),
        CueOutcome("advance_payment", "missed", at(5)),
        # personal_info 2회, 마지막 놓침 at(5) — advance_payment와 동점 → cue_id 순으로 뒤
        CueOutcome("personal_info", "missed", at(1)),
        CueOutcome("personal_info", "missed", at(5)),
    ]

    assert weak_cues(outcomes) == [
        WeakCue(cue_id="keep_secret", missed_count=3),
        WeakCue(cue_id="urgency", missed_count=2),
        WeakCue(cue_id="advance_payment", missed_count=2),
    ]


def test_weak_cues_empty_input_is_empty():
    assert weak_cues([]) == []


def test_weak_cues_unknown_outcome_raises():
    with pytest.raises(ValueError):
        weak_cues([CueOutcome("urgency", "not_shown", at(1))])


def test_weak_cues_naive_time_raises():
    with pytest.raises(ValueError):
        weak_cues([CueOutcome("urgency", "missed", datetime(2026, 11, 10))])
