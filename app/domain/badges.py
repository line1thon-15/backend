"""배지·연속 기록 — 백엔드 domain 순수 함수 (T-45 — F-28 ②③).

근거: Architecture "성장 계산 규칙" 배지·연속 기록 행, DECISIONS #90·#109·#116·#119.
입력은 이미 종료(`status = ended`)된 세션의 범주값·개수·한국 시간 날짜뿐이다 — 멈춘(`stopped`)·진행 중 세션은
호출하는 쪽(저장소 조회)이 넣지 않는다.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

BADGE_REQUIRED_SESSIONS = 3  # 설정 상수 1곳 — 사용자 답 "3회 성공 + 하루 단위 (추천)"
BADGE_LABEL = "혼자 할 수 있어요"  # BadgeView.label 설정 상수 (DECISIONS #90)
AREA_ORDER: tuple[str, ...] = ("scam", "identity_lending", "friend_pressure")


@dataclass(frozen=True)
class BadgeSessionFacts:
    area: str
    is_normal: bool
    found_count: int
    missed_count: int


def is_badge_session(facts: BadgeSessionFacts) -> bool:
    """배지 성공 세션 = 위험 상황 + 놓친 단서 0개 + 찾은 단서 1개 이상 (N1 — #109)."""
    if facts.found_count < 0 or facts.missed_count < 0:
        raise ValueError(f"counts must be >= 0: {facts}")
    return not facts.is_normal and facts.missed_count == 0 and facts.found_count >= 1


def badge_areas(
    sessions: Iterable[BadgeSessionFacts],
    required: int = BADGE_REQUIRED_SESSIONS,
) -> tuple[str, ...]:
    """배지 성공 세션이 `required`개 이상 쌓인 영역 — 기간 제한 없음(누적), 영역 순서는 AREA_ORDER."""
    counts = dict.fromkeys(AREA_ORDER, 0)
    for facts in sessions:
        if facts.area not in counts:
            raise ValueError(f"unknown area: {facts.area!r}")
        if is_badge_session(facts):
            counts[facts.area] += 1
    return tuple(area for area in AREA_ORDER if counts[area] >= required)


def streak_days(ended_dates: Iterable[date], today: date) -> int:
    """연속 기록: 오늘 ∈ D면 오늘부터, 아니고 어제 ∈ D면 어제부터 하루씩 거슬러 D에 있는 일수. 둘 다 아니면 0."""
    days = set(ended_dates)
    yesterday = today - timedelta(days=1)
    if today in days:
        cursor = today
    elif yesterday in days:
        cursor = yesterday
    else:
        return 0
    count = 0
    while cursor in days:
        count += 1
        cursor -= timedelta(days=1)
    return count
