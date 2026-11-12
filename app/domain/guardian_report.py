"""보호자 리포트 집계 규칙 (T-25 — F-30 ①). 표준 라이브러리만 쓰는 순수 함수.

입력은 `status = ended` 세션만(멈춘·진행 중 연습 제외 — Tasks T-25, PRD F-11 ⑧). 거르는 것은 리포지토리 몫이다.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

# 약점 단서 = 종료 세션에서 놓친(missed) 횟수가 이 값 이상인 단서. 기간 제한 없음.
# 문서에 기준 수치가 없어 둔 가정값이다(PRD OQ 14 약점 임계값 미정 — T-25 보고 Open Question).
WEAK_CUE_MIN_MISSED = 1

_OUTCOMES = frozenset({"found", "missed"})


@dataclass(frozen=True)
class EndedSession:
    area: str
    ended_at: datetime  # UTC aware


@dataclass(frozen=True)
class AreaProgress:
    area: str
    practice_count: int
    last_practiced_at: datetime | None


@dataclass(frozen=True)
class WeakCue:
    cue_id: str
    missed_count: int


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


def weak_cues(
    outcomes: Iterable[tuple[str, str]],
    min_missed: int = WEAK_CUE_MIN_MISSED,
) -> list[WeakCue]:
    """(cue_id, outcome) 목록에서 놓친 횟수가 `min_missed` 이상인 단서. 놓친 횟수 내림차순, 같으면 cue_id 순."""
    missed: Counter[str] = Counter()
    for cue_id, outcome in outcomes:
        if outcome not in _OUTCOMES:
            raise ValueError(f"unknown outcome: {outcome!r}")
        if outcome == "missed":
            missed[cue_id] += 1
    ranked = sorted(
        (cue_id for cue_id, count in missed.items() if count >= min_missed),
        key=lambda cue_id: (-missed[cue_id], cue_id),
    )
    return [WeakCue(cue_id=cue_id, missed_count=missed[cue_id]) for cue_id in ranked]
