"""한국 시간 날짜 계산 — 백엔드 domain 순수 함수 (DECISIONS #89·#94, Architecture 공통 값 타입 "시각" 행).

시각은 UTC로 저장하고, 날짜 단위 집계(연속 기록·지표 기간·요약 기간)만 계산할 때 한국 시간 날짜로 바꾼다.
"""

from datetime import date, datetime, timedelta, timezone

SERVICE_TZ = timezone(timedelta(hours=9))  # 설정 상수 1곳 — UTC+09:00 고정 오프셋


def service_date(moment: datetime) -> date:
    """시각 → 한국 시간 날짜. 시간대 없는 값은 UTC인지 알 수 없어 받지 않는다."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("timezone-aware datetime required")
    return moment.astimezone(SERVICE_TZ).date()
