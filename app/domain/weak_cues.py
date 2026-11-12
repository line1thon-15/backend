"""더 연습이 필요한 단서(아이 Y8 — F-29 ①)·약점 단서(보호자 G3 — F-30 ①) 공통 규칙 (T-46).

근거: 사용자 결정(2026-11-12) 원문 "2번 이상 + 최근 놓침 (추천)" — 설명 원문 "종료 세션에서 2번 이상
놓친 단서 중, 가장 최근 판정이 '놓침'인 것만. 많이 놓친 순, 최대 3개. 나중에 찾으면 목록에서 빠져
성장이 보여요." T-25·T-90이 이 함수를 재사용한다.

입력은 종료(`status = ended`) 세션의 판정만 — 멈춘·진행 중 세션은 리포지토리가 넘기지 않는다.
규칙에 없는 세부(결정적으로 정함):
- 기간 제한 없음(종료 세션 누적 — 규칙에 기간이 없음). 그래서 시계를 쓰지 않는다.
- 같은 시각 판정에 found·missed가 함께 있으면 found를 최근으로 본다(목록에서 빠짐).
- 놓친 횟수 동점 → 마지막으로 놓친 시각이 최근인 순 → cue_id 오름차순.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

NEEDS_PRACTICE_MIN_MISSED = 2
NEEDS_PRACTICE_MAX = 3
_OUTCOMES = frozenset({"found", "missed"})


@dataclass(frozen=True)
class CueOutcome:
    cue_id: str
    outcome: str  # found | missed
    judged_at: datetime  # 판정 시각(= 세션 종료 시각, tz 포함)


def select_weak_cues(outcomes: Sequence[CueOutcome]) -> tuple[str, ...]:
    by_cue: dict[str, list[CueOutcome]] = {}
    for item in outcomes:
        if item.outcome not in _OUTCOMES:
            raise ValueError(f"unknown cue outcome: {item.outcome}")
        if item.judged_at.tzinfo is None:
            raise ValueError("judged_at needs a timezone-aware datetime")
        by_cue.setdefault(item.cue_id, []).append(item)

    picked: list[tuple[int, datetime, str]] = []
    for cue_id, items in by_cue.items():
        misses = [i.judged_at for i in items if i.outcome == "missed"]
        if len(misses) < NEEDS_PRACTICE_MIN_MISSED:
            continue
        # 가장 최근 판정 — 같은 시각이면 found가 뒤(최근)로 오게 정렬
        latest = max(items, key=lambda i: (i.judged_at, i.outcome == "found"))
        if latest.outcome != "missed":
            continue
        picked.append((len(misses), max(misses), cue_id))

    picked.sort(key=lambda p: (-p[0], -p[1].timestamp(), p[2]))
    return tuple(cue_id for _, _, cue_id in picked[:NEEDS_PRACTICE_MAX])
