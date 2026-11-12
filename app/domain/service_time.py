"""한국 시간 날짜 계산 — 설정 상수 1곳 (DECISIONS #89 → #94, Architecture "공통 값 타입" 시각 행).

시각은 UTC로 저장하고, 날짜 단위 집계(연속 기록·지표 기간·요약 기간)만 한국 시간 날짜로 바꾼다.
"""

from datetime import date, datetime, timedelta, timezone

SERVICE_TZ = timezone(timedelta(hours=9))


def service_date(moment: datetime) -> date:
    """UTC 시각 → 한국 시간 날짜. tz 없는 값은 받지 않는다(어느 시간대인지 모름)."""
    if moment.tzinfo is None:
        raise ValueError("service_date needs a timezone-aware datetime")
    return moment.astimezone(SERVICE_TZ).date()
