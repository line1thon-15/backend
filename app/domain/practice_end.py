"""연습 종료 판정 — 백엔드 domain 순수 함수 (F-11 ④⑤⑥, DECISIONS #80·#97, ADR-0015).

입력은 세션 `is_normal`, 고른 선택지 `kind`, 아이 답 수 `answer_count`(= 답한 턴 `turn_index + 1`)뿐이다.
AI 응답의 어떤 값도 입력이 아니다(F-11 ⑥).
"""

MAX_CHILD_ANSWERS = 4  # 설정 상수 1곳 — 사용자 답 "4번 (Recommended)"

_KINDS = frozenset({"correct", "doubtful", "other"})


class NormalSituationEndRuleUndefined(Exception):
    """정상 상황 종료 규칙은 PRD OQ 61 미결 — 임의 규칙으로 끝내지 않는다(500 INTERNAL)."""


def is_practice_over(*, is_normal: bool, kind: str, answer_count: int) -> bool:
    if kind not in _KINDS:
        raise ValueError(f"unknown choice kind: {kind!r}")
    if answer_count < 1:
        raise ValueError(f"answer_count must be >= 1: {answer_count}")
    if is_normal:
        raise NormalSituationEndRuleUndefined("normal situation end rule is undefined (PRD OQ 61)")
    # PRD '의심' = kind correct → 그 답에서 종료 / 상한에 닿으면 kind와 관계없이 종료
    return kind == "correct" or answer_count >= MAX_CHILD_ANSWERS
