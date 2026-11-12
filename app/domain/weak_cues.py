"""더 연습이 필요한 단서(아이 Y8 — F-29 ①)·약점 단서(보호자 G3 — F-30 ①) 공통 규칙 (T-46).

근거: DECISIONS #122, Architecture "성장 계산 규칙" 더 연습이 필요한 단서 행(2026-11-12). 사용자 결정 원문
"2번 이상 + 최근 놓침 (추천)" — 설명 원문 "종료 세션에서 2번 이상 놓친 단서 중, 가장 최근 판정이 '놓침'인
것만. 많이 놓친 순, 최대 3개. 나중에 찾으면 목록에서 빠져 성장이 보여요." A19(T-90)·A11(T-25)이 함께 쓴다.

입력은 종료(`status = ended`) 세션의 `cue_results`만 — 멈춘·진행 중 세션은 리포지토리가 넘기지 않는다.
기간 제한 없음(시계를 쓰지 않는다). architect 판단(#122, 사용자 확인 대상):
- 놓친 수 동점 → 가장 최근 missed 세션의 ended_at이 늦은 순 → cue_id 오름차순.
- 같은 단서에서 ended_at이 같은 세션이 둘 이상이면 session_id가 큰 쪽을 최근으로 본다.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

WEAK_CUE_MIN_MISSES = 2
WEAK_CUE_MAX = 3
_OUTCOMES = frozenset({"found", "missed"})


@dataclass(frozen=True)
class CueOutcome:
    cue_id: str
    outcome: str  # found | missed
    ended_at: datetime  # 판정한 세션의 종료 시각(tz 포함)
    session_id: UUID


def _recency(item: CueOutcome) -> tuple[datetime, int]:
    return (item.ended_at, item.session_id.int)


def select_weak_cues(outcomes: Sequence[CueOutcome]) -> tuple[str, ...]:
    by_cue: dict[str, list[CueOutcome]] = {}
    for item in outcomes:
        if item.outcome not in _OUTCOMES:
            raise ValueError(f"unknown cue outcome: {item.outcome}")
        if item.ended_at.tzinfo is None:
            raise ValueError("ended_at needs a timezone-aware datetime")
        by_cue.setdefault(item.cue_id, []).append(item)

    picked: list[tuple[int, datetime, str]] = []
    for cue_id, items in by_cue.items():
        misses = [i for i in items if i.outcome == "missed"]
        if len(misses) < WEAK_CUE_MIN_MISSES:
            continue
        if max(items, key=_recency).outcome != "missed":
            continue
        picked.append((len(misses), max(m.ended_at for m in misses), cue_id))

    picked.sort(key=lambda p: (-p[0], -p[1].timestamp(), p[2]))
    return tuple(cue_id for _, _, cue_id in picked[:WEAK_CUE_MAX])
