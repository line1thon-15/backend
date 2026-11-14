"""힌트 단계 산정 — 백엔드 domain 순수 함수 (T-36 — F-18 ②).

근거: Architecture "연습 출제 규칙" 힌트 감소 행 — 목표 단서별 연속 `found` 횟수 c에 대해
`hint_level = max(0, HINT_MAX − c)`. c가 늘면 힌트 단계가 줄거나 같다(단조).

- 입력은 종료(`status = ended`) 세션의 `cue_results`만 — 멈춘·진행 중 세션은 리포지토리가 넘기지 않는다.
  `not_shown`은 저장되지 않으므로(DECISIONS #109) 그 단서가 드러나지 않은 세션은 연속을 끊지도 늘리지도 않는다.
- c = 그 단서의 판정을 최근 순(ended_at, 같으면 session_id 큰 쪽 — 약점 단서 공통 규칙과 같음)으로 보며
  처음 `missed`가 나오기 전까지의 `found` 수.
- 1차 AI 계약에 힌트 문장이 없어(#104 ④) 이 값은 화면에 드러나지 않는다 — 힌트 문장은 T-74.
"""

from collections.abc import Sequence

from app.domain.weak_cues import CueOutcome

# PRD OQ 14(보류 — 구현 중 결정) 잠정값: 2 = 처음 힌트, 1 = 한 번 찾은 뒤 줄인 힌트, 0 = 두 번 연속 찾으면 힌트 없음
HINT_MAX = 2
_OUTCOMES = frozenset({"found", "missed"})


def _validate(outcomes: Sequence[CueOutcome]) -> None:
    for item in outcomes:
        if item.outcome not in _OUTCOMES:
            raise ValueError(f"unknown cue outcome: {item.outcome}")
        if item.ended_at.tzinfo is None:
            raise ValueError("ended_at needs a timezone-aware datetime")


def _consecutive_found(outcomes: Sequence[CueOutcome], cue_id: str) -> int:
    history = sorted(
        (item for item in outcomes if item.cue_id == cue_id),
        key=lambda item: (item.ended_at, item.session_id.int),
        reverse=True,
    )
    count = 0
    for item in history:
        if item.outcome != "found":
            break
        count += 1
    return count


def consecutive_found(outcomes: Sequence[CueOutcome], cue_id: str) -> int:
    _validate(outcomes)
    return _consecutive_found(outcomes, cue_id)


def hint_levels(outcomes: Sequence[CueOutcome], cue_ids: Sequence[str]) -> dict[str, int]:
    """목표 단서마다 힌트 단계 {cue_id: 0..HINT_MAX}."""
    _validate(outcomes)
    return {cue_id: max(0, HINT_MAX - _consecutive_found(outcomes, cue_id)) for cue_id in cue_ids}
