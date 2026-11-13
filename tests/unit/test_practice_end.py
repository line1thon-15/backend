"""연습 종료 판정 domain 순수 함수 (T-15 — F-11 ④⑤⑥, DECISIONS #80·#97, Architecture "연습 종료" 행).

입력은 세션 `is_normal`, 고른 선택지 `kind`, 아이 답 수 `answer_count`뿐이다.
`kind = correct`(PRD '의심')면 그 답에서 종료, `answer_count >= MAX_CHILD_ANSWERS`면 종료, 그 외 계속.
정상 상황은 규칙이 없어(PRD OQ 61) 예외를 던진다.
"""

import inspect

import pytest

from app.domain import practice_end
from app.domain.practice_end import (
    MAX_CHILD_ANSWERS,
    NormalSituationEndRuleUndefined,
    is_practice_over,
)


def test_max_child_answers_is_four():
    assert MAX_CHILD_ANSWERS == 4


@pytest.mark.parametrize("answer_count", [1, 4])
def test_correct_answer_ends(answer_count):
    # 첫 답에서 의심 답(1) / 4번째 답이 의심 답인 겹침(4)
    assert is_practice_over(is_normal=False, kind="correct", answer_count=answer_count) is True


@pytest.mark.parametrize("kind", ["doubtful", "other"])
@pytest.mark.parametrize("answer_count", [1, 3])
def test_non_correct_answer_continues_before_limit(kind, answer_count):
    assert is_practice_over(is_normal=False, kind=kind, answer_count=answer_count) is False


@pytest.mark.parametrize("kind", ["doubtful", "other"])
def test_fourth_answer_ends_regardless_of_kind(kind):
    assert is_practice_over(is_normal=False, kind=kind, answer_count=4) is True


def test_normal_situation_raises():
    with pytest.raises(NormalSituationEndRuleUndefined):
        is_practice_over(is_normal=True, kind="other", answer_count=1)


@pytest.mark.parametrize("answer_count", [0, -1])
def test_answer_count_below_one_is_rejected(answer_count):
    with pytest.raises(ValueError):
        is_practice_over(is_normal=False, kind="other", answer_count=answer_count)


@pytest.mark.parametrize("kind", ["suspicious", "", "CORRECT"])
def test_unknown_kind_is_rejected(kind):
    with pytest.raises(ValueError):
        is_practice_over(is_normal=False, kind=kind, answer_count=1)


def test_end_function_takes_no_ai_response_values():
    # F-11 ⑥: 종료 함수 입력에 AI 응답 값(all_clues_revealed·is_terminal 등)이 없다 — 시그니처로 확인
    assert list(inspect.signature(is_practice_over).parameters) == [
        "is_normal",
        "kind",
        "answer_count",
    ]


def test_old_max_turns_constant_is_not_used():
    assert not hasattr(practice_end, "MAX_TURNS")
