"""FakePracticeAI.opening 스모크 + 내부 API DTO 스키마 (Architecture "백엔드–AI 내부 API", Tasks T-01)."""

import pytest
from pydantic import ValidationError

from app.ai_client.fake import FakePracticeAI
from app.ai_client.ports import (
    OpeningResult,
    PracticeAI,
    ReviewResult,
    ScenarioSpec,
    TurnResult,
)

TARGET_CUES = [
    {"cue_id": "cue_urgent", "label": "급하게 재촉해요", "explanation": "예시 설명 1"},
    {"cue_id": "cue_money", "label": "돈을 먼저 달라고 해요", "explanation": "예시 설명 2"},
]


def make_spec(**overrides) -> ScenarioSpec:
    data = {
        "scenario_id": "scam_game_item_01",
        "area": "scam",
        "subtype": "game_item",
        "is_normal": False,
        "target_cues": TARGET_CUES,
        "situation_seed": "예시 상황 씨앗",
        "variant": {"tone": "friendly", "platform": "game_chat", "persona": "gamer"},
        "grade_band": "middle",
        "difficulty": None,
        "hint_level": 1,
    }
    data.update(overrides)
    return ScenarioSpec.model_validate(data)


def make_choice(choice_id: str) -> dict:
    return {"id": choice_id, "text": "예시 선택지", "judgment": "neutral", "cue_ids": []}


def test_opening_returns_turn_result_schema_and_passed_review():
    spec = make_spec()

    result = FakePracticeAI().opening(spec)

    assert isinstance(result, OpeningResult)
    assert isinstance(result.turn, TurnResult)
    assert isinstance(result.review, ReviewResult)
    revalidated = TurnResult.model_validate(result.turn.model_dump())
    assert revalidated == result.turn
    assert result.turn.ai_line.strip()
    assert result.turn.speaker_name.strip()
    assert 2 <= len(result.turn.choices) <= 4
    assert "is_terminal" not in result.turn.model_dump()
    assert result.turn.substituted is False
    assert result.review.passed is True
    assert result.review.reasons == []


def test_opening_choice_cue_ids_cover_only_target_cues():
    spec = make_spec()

    turn = FakePracticeAI().opening(spec).turn

    target_ids = {cue.cue_id for cue in spec.target_cues}
    used_ids = {cue_id for choice in turn.choices for cue_id in choice.cue_ids}
    assert used_ids == target_ids
    assert len({choice.id for choice in turn.choices}) == len(turn.choices)


def test_opening_hint_is_null_when_hint_level_is_zero():
    turn = FakePracticeAI().opening(make_spec(hint_level=0)).turn

    assert turn.hint is None


def test_opening_hint_is_text_when_hint_level_is_positive():
    turn = FakePracticeAI().opening(make_spec(hint_level=3)).turn

    assert isinstance(turn.hint, str) and turn.hint.strip()


def test_opening_normal_scenario_has_no_cue_ids():
    spec = make_spec(is_normal=True, target_cues=[], subtype=None, area="friend_request")

    turn = FakePracticeAI().opening(spec).turn

    assert 2 <= len(turn.choices) <= 4
    assert all(choice.cue_ids == [] for choice in turn.choices)


def test_opening_is_deterministic_for_same_spec():
    fake = FakePracticeAI()

    first = fake.opening(make_spec()).model_dump()
    second = fake.opening(make_spec()).model_dump()

    assert first == second


def test_fake_satisfies_practice_ai_port():
    assert isinstance(FakePracticeAI(), PracticeAI)


def test_scenario_spec_rejects_child_identifying_field():
    with pytest.raises(ValidationError):
        make_spec(nickname="예시별명")


def test_scenario_spec_rejects_unknown_area():
    with pytest.raises(ValidationError):
        make_spec(area="unknown_area")


@pytest.mark.parametrize("choice_count", [1, 5])
def test_turn_result_rejects_choice_count_outside_2_to_4(choice_count):
    with pytest.raises(ValidationError):
        TurnResult.model_validate(
            {
                "ai_line": "예시 대사",
                "speaker_name": "예시 상대",
                "choices": [make_choice(f"c{i}") for i in range(1, choice_count + 1)],
                "hint": None,
                "substituted": False,
            }
        )


def test_turn_result_has_no_is_terminal_field():
    # 종료 판정은 백엔드 규칙만 한다 (DECISIONS #81, ADR-0015) — AI 응답 DTO에 종료 플래그를 두지 않는다.
    assert "is_terminal" not in TurnResult.model_fields


@pytest.mark.parametrize("flag", [True, False])
def test_turn_result_ignores_is_terminal_from_ai(flag):
    # 전환 허용 (DECISIONS #81): AI가 아직 is_terminal을 보내도 오류 없이 파싱하고 값은 남기지 않는다.
    turn = TurnResult.model_validate(
        {
            "ai_line": "예시 대사",
            "speaker_name": "예시 상대",
            "choices": [make_choice("c1"), make_choice("c2")],
            "hint": None,
            "is_terminal": flag,
            "substituted": False,
        }
    )

    assert "is_terminal" not in turn.model_dump()
