"""보호자 리포트 domain 집계 (T-25 — F-30 ①).

근거: Architecture "응답 DTO" GuardianReport(`areas:[{area, practice_count, last_practiced_at|null}]`,
`weak_cues:[{cue_id, label}]`), Tasks T-25 "영역별 진행·약점 단서 집계는 `status = ended` 세션만",
"영역 값은 scam·identity_lending·friend_pressure"(DECISIONS #108).

약점 단서 기준(놓친 횟수 1 이상, 기간 제한 없음)은 문서에 수치가 없어 설정 상수로 둔 가정값이다
(T-25 보고 Open Question — 확정 값이 아님).
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.guardian_report import (
    WEAK_CUE_MIN_MISSED,
    AreaProgress,
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


def test_weak_cue_threshold_is_one_missed():
    assert WEAK_CUE_MIN_MISSED == 1


def test_weak_cues_boundary_found_only_is_not_weak_and_one_miss_is_weak():
    outcomes = [("urgency", "found"), ("urgency", "found"), ("keep_secret", "missed")]

    assert weak_cues(outcomes) == [WeakCue(cue_id="keep_secret", missed_count=1)]


def test_weak_cues_cue_found_and_missed_counts_only_misses():
    outcomes = [("urgency", "found"), ("urgency", "missed"), ("urgency", "found")]

    assert weak_cues(outcomes) == [WeakCue(cue_id="urgency", missed_count=1)]


def test_weak_cues_sorted_by_missed_desc_then_cue_id():
    outcomes = [
        ("urgency", "missed"),
        ("advance_payment", "missed"),
        ("keep_secret", "missed"),
        ("keep_secret", "missed"),
    ]

    assert weak_cues(outcomes) == [
        WeakCue(cue_id="keep_secret", missed_count=2),
        WeakCue(cue_id="advance_payment", missed_count=1),
        WeakCue(cue_id="urgency", missed_count=1),
    ]


def test_weak_cues_with_higher_threshold_excludes_single_miss():
    outcomes = [("urgency", "missed"), ("keep_secret", "missed"), ("keep_secret", "missed")]

    assert weak_cues(outcomes, min_missed=2) == [WeakCue(cue_id="keep_secret", missed_count=2)]


def test_weak_cues_empty_input_is_empty():
    assert weak_cues([]) == []


def test_weak_cues_unknown_outcome_raises():
    with pytest.raises(ValueError):
        weak_cues([("urgency", "not_shown")])
