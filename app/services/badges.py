"""배지·연속 기록 산정 서비스 (T-45 — F-28 ②③).

근거: Architecture "성장 계산 규칙"(공통·배지·연속 기록·저장 여부 행), BadgeView DTO, DECISIONS #28·#89·#90.
저장하지 않고 요청마다 기존 테이블(practice_sessions·cue_results)에서 계산한다. 오늘 = 주입 시계의 한국 시간 날짜.
공개 엔드포인트(A13 `/me/home`·A19 `/me/growth`) 연결은 이 작업 범위 밖이다 — 두 응답 모두 이 결과를 쓴다.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from app.domain.badges import (
    BADGE_LABEL,
    BadgeSessionFacts,
    badge_areas,
    streak_days,
)
from app.domain.service_time import service_date


@dataclass(frozen=True)
class EndedSessionRecord:
    """종료(`status = ended`) 세션 1개 — 드러난 단서 판정 개수(N1: found·missed만 저장)."""

    area: str
    is_normal: bool
    ended_at: datetime
    found_count: int
    missed_count: int


class BadgeRepository(Protocol):
    def ended_sessions(self, child_id: UUID) -> list[EndedSessionRecord]: ...


@dataclass(frozen=True)
class Badge:
    badge_id: str
    area: str
    label: str


@dataclass(frozen=True)
class BadgeStreak:
    badges: tuple[Badge, ...]
    streak_days: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BadgeService:
    def __init__(
        self,
        repository: BadgeRepository,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def badges_and_streak(self, child_id: UUID) -> BadgeStreak:
        sessions = self._repository.ended_sessions(child_id)
        areas = badge_areas(
            BadgeSessionFacts(
                area=session.area,
                is_normal=session.is_normal,
                found_count=session.found_count,
                missed_count=session.missed_count,
            )
            for session in sessions
        )
        streak = streak_days(
            (service_date(session.ended_at) for session in sessions),
            service_date(self._clock()),
        )
        return BadgeStreak(
            badges=tuple(
                Badge(badge_id=f"independent:{area}", area=area, label=BADGE_LABEL)
                for area in areas
            ),
            streak_days=streak,
        )
