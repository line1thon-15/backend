"""보호자 리포트 집계 규칙 (T-25 — F-30 ①). 표준 라이브러리만 쓰는 순수 함수.

약점 단서는 공통 함수 `app.domain.weak_cues.select_weak_cues`(DECISIONS #122)를 쓴다.

입력은 `status = ended` 세션만(멈춘·진행 중 연습 제외 — Tasks T-25, PRD F-11 ⑧). 거르는 것은 리포지토리 몫이다.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EndedSession:
    area: str
    ended_at: datetime  # UTC aware


@dataclass(frozen=True)
class AreaProgress:
    area: str
    practice_count: int
    last_practiced_at: datetime | None


def area_progress(areas: Sequence[str], sessions: Iterable[EndedSession]) -> list[AreaProgress]:
    """영역마다 종료 세션 수와 마지막 종료 시각. 결과 순서 = `areas` 순서, 기록 없는 영역은 0·None."""
    counts: Counter[str] = Counter()
    latest: dict[str, datetime] = {}
    for session in sessions:
        if session.area not in areas:
            raise ValueError(f"unknown area: {session.area!r}")
        if session.ended_at.tzinfo is None:
            raise ValueError("ended_at must be timezone-aware")
        counts[session.area] += 1
        if session.area not in latest or session.ended_at > latest[session.area]:
            latest[session.area] = session.ended_at
    return [
        AreaProgress(area=area, practice_count=counts[area], last_practiced_at=latest.get(area))
        for area in areas
    ]
