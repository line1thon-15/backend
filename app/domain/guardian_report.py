"""보호자 리포트 집계 규칙 (T-25 — F-30 ①). 표준 라이브러리만 쓰는 순수 함수.

입력은 `status = ended` 세션만(멈춘·진행 중 연습 제외 — Tasks T-25, PRD F-11 ⑧). 거르는 것은 리포지토리 몫이다.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

# 약점 단서 (2026-11-12 사용자 답 "2번 이상 + 최근 놓침 (추천)" — 설명 원문 "종료 세션에서 2번 이상 놓친 단서 중,
# 가장 최근 판정이 '놓침'인 것만. 많이 놓친 순, 최대 3개."). 기간 제한 없음.
# 아이 Y8 "더 연습이 필요한 단서"(T-46)와 같은 규칙 — 함수 통합은 T-90.
WEAK_CUE_MIN_MISSED = 2
WEAK_CUE_LIMIT = 3

_OUTCOMES = frozenset({"found", "missed"})


@dataclass(frozen=True)
class EndedSession:
    area: str
    ended_at: datetime  # UTC aware


@dataclass(frozen=True)
class CueOutcome:
    cue_id: str
    outcome: str  # found | missed
    at: datetime  # 판정 시각(세션 종료 시각) — UTC aware


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
    outcomes: Iterable[CueOutcome],
    min_missed: int = WEAK_CUE_MIN_MISSED,
    limit: int = WEAK_CUE_LIMIT,
) -> list[WeakCue]:
    """놓친 횟수가 `min_missed` 이상이고 가장 최근 판정이 놓침인 단서, 최대 `limit`개.

    - 가장 최근 시각에 찾음·놓침이 함께 있으면 '최근 판정 = 놓침'으로 보지 않는다(보수적).
    - 정렬: 놓친 횟수 내림차순 → 마지막 놓친 시각 최신 순 → cue_id 오름차순 (입력 순서와 무관).
    """
    missed: Counter[str] = Counter()
    last_missed: dict[str, datetime] = {}
    last_found: dict[str, datetime] = {}
    for item in outcomes:
        if item.outcome not in _OUTCOMES:
            raise ValueError(f"unknown outcome: {item.outcome!r}")
        if item.at.tzinfo is None:
            raise ValueError("outcome time must be timezone-aware")
        latest = last_missed if item.outcome == "missed" else last_found
        if item.cue_id not in latest or item.at > latest[item.cue_id]:
            latest[item.cue_id] = item.at
        if item.outcome == "missed":
            missed[item.cue_id] += 1
    candidates = [
        cue_id
        for cue_id, count in missed.items()
        if count >= min_missed
        and (cue_id not in last_found or last_missed[cue_id] > last_found[cue_id])
    ]
    candidates.sort(key=lambda cue_id: cue_id)
    candidates.sort(key=lambda cue_id: (missed[cue_id], last_missed[cue_id]), reverse=True)
    return [WeakCue(cue_id=cue_id, missed_count=missed[cue_id]) for cue_id in candidates[:limit]]
