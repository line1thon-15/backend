"""배지·연속 기록 domain 순수 함수 (T-45 — F-28 ②③).

근거: Architecture "성장 계산 규칙" 배지·연속 기록 행, 공통 값 타입 "시각" 행, DECISIONS #89·#90·#109·#116·#119,
Tasks T-45 완료 조건. domain 입력은 날짜·범주값·개수뿐이다(DB·시계 없음).
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.badges import (
    BADGE_LABEL,
    BADGE_REQUIRED_SESSIONS,
    BadgeSessionFacts,
    badge_areas,
    is_badge_session,
    streak_days,
)
from app.domain.service_time import SERVICE_TZ, service_date

UTC = timezone.utc
TODAY = date(2026, 11, 12)


def risk(area: str = "scam", *, found: int = 1, missed: int = 0) -> BadgeSessionFacts:
    return BadgeSessionFacts(area=area, is_normal=False, found_count=found, missed_count=missed)


# ---------- 한국 시간 날짜 (DECISIONS #89) ----------


def test_service_tz_is_fixed_utc_plus_9():
    assert SERVICE_TZ.utcoffset(None) == timedelta(hours=9)


def test_service_date_just_before_kst_midnight_is_same_kst_day():
    # UTC 14:59:59 = 한국 23:59:59 → 한국 날짜 11-11
    assert service_date(datetime(2026, 11, 11, 14, 59, 59, tzinfo=UTC)) == date(2026, 11, 11)


def test_service_date_at_kst_midnight_is_next_kst_day():
    # UTC 15:00:00 = 한국 다음 날 00:00:00 → 한국 날짜 11-12 (UTC 날짜는 아직 11-11)
    assert service_date(datetime(2026, 11, 11, 15, 0, 0, tzinfo=UTC)) == date(2026, 11, 12)


def test_service_date_rejects_naive_datetime():
    with pytest.raises(ValueError):
        service_date(datetime(2026, 11, 11, 15, 0, 0))


# ---------- 배지 성공 세션 (N1 — 놓침 0 + 찾음 1 이상) ----------


def test_badge_session_requires_missed_zero_and_found_at_least_one():
    assert is_badge_session(risk(found=1, missed=0)) is True
    assert is_badge_session(risk(found=3, missed=0)) is True


def test_session_with_found_zero_and_missed_zero_is_not_badge_session():
    assert is_badge_session(risk(found=0, missed=0)) is False


def test_session_with_any_missed_is_not_badge_session():
    assert is_badge_session(risk(found=2, missed=1)) is False


def test_normal_situation_session_is_not_badge_session():
    normal = BadgeSessionFacts(area="scam", is_normal=True, found_count=1, missed_count=0)
    assert is_badge_session(normal) is False


@pytest.mark.parametrize("found,missed", [(-1, 0), (1, -1)])
def test_negative_counts_are_rejected(found, missed):
    with pytest.raises(ValueError):
        is_badge_session(risk(found=found, missed=missed))


# ---------- 배지 (3번 쌓이면 그 영역 배지) ----------


def test_required_sessions_constant_is_three():
    assert BADGE_REQUIRED_SESSIONS == 3
    assert BADGE_LABEL == "혼자 할 수 있어요"


def test_three_badge_sessions_in_area_earn_that_area_badge():
    assert badge_areas([risk("scam")] * 3) == ("scam",)


def test_three_first_answer_doubt_sessions_earn_badge():
    # 첫 답 의심으로 끝난 세션 = found 1·missed 0
    assert badge_areas([risk("identity_lending", found=1, missed=0)] * 3) == ("identity_lending",)


def test_two_badge_sessions_earn_no_badge():
    assert badge_areas([risk("scam")] * 2) == ()


def test_other_area_sessions_are_not_mixed():
    sessions = [risk("scam"), risk("scam"), risk("identity_lending")]
    assert badge_areas(sessions) == ()


def test_normal_sessions_do_not_fill_the_three():
    normal = BadgeSessionFacts(area="scam", is_normal=True, found_count=1, missed_count=0)
    assert badge_areas([risk("scam"), risk("scam"), normal]) == ()


def test_found_zero_missed_zero_sessions_do_not_fill_the_three():
    assert badge_areas([risk("scam"), risk("scam"), risk("scam", found=0, missed=0)]) == ()


def test_missed_sessions_do_not_fill_the_three():
    assert badge_areas([risk("scam"), risk("scam"), risk("scam", found=1, missed=1)]) == ()


def test_more_than_three_still_one_badge_and_areas_in_fixed_order():
    sessions = [risk("friend_pressure")] * 3 + [risk("scam")] * 5
    assert badge_areas(sessions) == ("scam", "friend_pressure")


def test_no_sessions_no_badges():
    assert badge_areas([]) == ()


def test_unknown_area_is_rejected():
    with pytest.raises(ValueError):
        badge_areas([risk("unknown_area")] * 3)


# ---------- 연속 기록 (한국 시간 날짜, 하루 단위) ----------


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def test_three_consecutive_days_including_today_is_three():
    assert streak_days([days_ago(0), days_ago(1), days_ago(2)], TODAY) == 3


def test_today_missing_but_yesterday_streak_of_two_is_kept():
    assert streak_days([days_ago(1), days_ago(2)], TODAY) == 2


def test_neither_today_nor_yesterday_is_zero_even_with_older_days():
    assert streak_days([days_ago(2), days_ago(3), days_ago(4)], TODAY) == 0


def test_many_sessions_in_one_day_count_as_one_day():
    assert streak_days([days_ago(0)] * 5, TODAY) == 1


def test_gap_breaks_streak():
    assert streak_days([days_ago(0), days_ago(1), days_ago(3), days_ago(4)], TODAY) == 2


def test_no_dates_is_zero():
    assert streak_days([], TODAY) == 0


def test_future_dates_are_ignored():
    # 오늘 이후 날짜는 연속 계산의 시작점이 되지 않는다(시계 기준 미래 기록)
    assert streak_days([days_ago(-1), days_ago(1)], TODAY) == 1
