"""보호자 리포트 domain 집계 (T-25 — F-30 ①).

근거: Architecture "응답 DTO" GuardianReport(`areas:[{area, practice_count, last_practiced_at|null}]`,
`weak_cues`는 공통 함수 `app/domain/weak_cues.py` — tests/unit/test_weak_cues.py), Tasks T-25 "영역별 진행·약점 단서 집계는 `status = ended` 세션만",
"영역 값은 scam·identity_lending·friend_pressure"(DECISIONS #108).

"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.guardian_report import AreaProgress, EndedSession, area_progress

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
