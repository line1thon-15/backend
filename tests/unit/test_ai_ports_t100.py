"""T-100 — AI 변형의 시작 선택지 `opening_choices` (DECISIONS #137~#139, ADR-0022 규칙 1~5).

규칙 1: `OpeningChoices{correct, doubtful, other}` 각 문자열 1~60자, `Variant.opening_choices: OpeningChoices | None = None`.
규칙 2: 형태·길이 위반 = variant 응답 스키마 위반(→ HttpPracticeAI가 AIUnavailableError).
규칙 3: 받은 값을 그대로 요청에 싣고, 없으면 `null`(키 생략 아님 — #138 2A).
규칙 5: FakePracticeAI는 opening_choices가 있는 변형과 없는 변형을 모두 돌려줄 수 있다.
"""

import pytest
from pydantic import ValidationError

from app.ai_client.fake import FakePracticeAI
from app.ai_client.ports import (
    AiRole,
    ClueVariant,
    OpeningChoices,
    StartRequest,
    TurnRequest,
    Message,
    Variant,
    VariantRequest,
    VariantResponse,
)

OPENING = {
    "correct": "스티커만 붙이는데 이렇게 많이 주는 건 이상해. 안 할래.",
    "doubtful": "좀 이상하긴 한데, 그래도 해 볼게.",
    "other": "하루에 15만 원이면 좋아. 바로 할게.",
}


def variant_data(**overrides) -> dict:
    data = {
        "base_scenario_id": "scam_dm_parttime_01",
        "platform": "instagram_dm",
        "tone": "친구처럼 편한 말투",
        "context": "방학",
        "title": "스티커 알바 제안",
        "child_setup": "모르는 사람이 DM을 보냈어요.",
        "opening_line": "스티커만 붙이면 한 달에 300만 원도 벌어.",
        "ai_role": {"name": "민지", "persona": "친근한 척하는 사람", "tone": "친구처럼 편한 말투"},
        "clues": [
            {"id": "too_good_pay", "at_opening": True, "reveal_when": "첫 대사에서", "reveal_line": "300만 원"},
        ],
    }
    data.update(overrides)
    return data


# ---- 규칙 1: 정상·경계 --------------------------------------------------------


def test_variant_keeps_opening_choices_from_response():
    parsed = VariantResponse.model_validate({"variant": variant_data(opening_choices=OPENING), "source": "model"})

    assert parsed.variant.opening_choices == OpeningChoices(**OPENING)
    assert parsed.variant.model_dump(mode="json")["opening_choices"] == OPENING


def test_variant_without_opening_choices_defaults_to_none():
    parsed = Variant.model_validate(variant_data())

    assert parsed.opening_choices is None


def test_variant_accepts_explicit_null_opening_choices():
    assert Variant.model_validate(variant_data(opening_choices=None)).opening_choices is None


@pytest.mark.parametrize("length", [1, 60])
@pytest.mark.parametrize("key", ["correct", "doubtful", "other"])
def test_opening_choice_text_length_boundaries_accepted(key, length):
    choices = {**OPENING, key: "가" * length}

    parsed = Variant.model_validate(variant_data(opening_choices=choices))

    assert getattr(parsed.opening_choices, key) == "가" * length


# ---- 규칙 2: 형태·길이 위반 ----------------------------------------------------


@pytest.mark.parametrize("key", ["correct", "doubtful", "other"])
def test_opening_choices_missing_key_rejected(key):
    choices = {k: v for k, v in OPENING.items() if k != key}

    with pytest.raises(ValidationError):
        Variant.model_validate(variant_data(opening_choices=choices))


@pytest.mark.parametrize("value", ["", "가" * 61, None, 3])
@pytest.mark.parametrize("key", ["correct", "doubtful", "other"])
def test_opening_choice_text_invalid_rejected(key, value):
    with pytest.raises(ValidationError):
        Variant.model_validate(variant_data(opening_choices={**OPENING, key: value}))


@pytest.mark.parametrize("value", ["정답", ["a", "b", "c"], {}])
def test_opening_choices_wrong_shape_rejected(value):
    with pytest.raises(ValidationError):
        Variant.model_validate(variant_data(opening_choices=value))


# ---- 규칙 3: 요청에 그대로·없으면 null ----------------------------------------


def test_start_and_turn_requests_carry_opening_choices_as_received():
    variant = Variant.model_validate(variant_data(opening_choices=OPENING))

    start = StartRequest(scenario_id="scam_dm_parttime_01", variant=variant).model_dump(mode="json")
    turn = TurnRequest(
        scenario_id="scam_dm_parttime_01",
        messages=[Message(role="ai", text="안녕"), Message(role="child", text="응")],
        variant=variant,
    ).model_dump(mode="json")

    assert start["variant"]["opening_choices"] == OPENING
    assert turn["variant"]["opening_choices"] == OPENING


def test_requests_send_null_when_opening_choices_absent():
    # #138 2A — 키를 생략하지 않고 null로 싣는다 (맞춤 직렬화 없음)
    variant = Variant.model_validate(variant_data())

    body = StartRequest(scenario_id="scam_dm_parttime_01", variant=variant).model_dump(mode="json")

    assert "opening_choices" in body["variant"]
    assert body["variant"]["opening_choices"] is None


# ---- 규칙 5: FakePracticeAI ---------------------------------------------------


def _variant_request() -> VariantRequest:
    return VariantRequest(scenario_id="scam_dm_parttime_01", platform="instagram_dm", tone="반말", context="방학")


def test_fake_variant_has_no_opening_choices_by_default():
    assert FakePracticeAI().variant(_variant_request()).variant.opening_choices is None


def test_fake_variant_returns_injected_opening_choices():
    fake = FakePracticeAI(opening_choices=OpeningChoices(**OPENING))

    assert fake.variant(_variant_request()).variant.opening_choices == OpeningChoices(**OPENING)


def test_opening_choices_is_inbound_model_ignoring_unknown_fields():
    # 받는 모델(_InboundModel) — 모르는 필드는 버린다 (ADR-0022 규칙 1)
    parsed = OpeningChoices.model_validate({**OPENING, "extra": "x"})

    assert parsed.model_dump() == OPENING


def test_variant_construct_helpers_still_build_without_opening_choices():
    # 기존 코드 경로(키워드 생성)가 opening_choices 없이도 동작한다 — 하위 호환
    variant = Variant(
        base_scenario_id="s",
        platform="p",
        tone="t",
        context="c",
        title="제목",
        child_setup="설명",
        opening_line="첫 대사",
        ai_role=AiRole(name="n", persona="p", tone="t"),
        clues=[ClueVariant(id="k", reveal_when="w", reveal_line="l")],
    )

    assert variant.opening_choices is None
