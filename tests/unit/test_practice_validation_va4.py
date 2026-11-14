"""VA4 — fallback 변형이 직전과 같을 때 (T-95, 2026-11-14 사용자 결정 "백엔드가 다른 변형 요청 (추천)").

- fallback(AI가 변형 생성 실패 → 원본)이 직전 세션과 같으면: 서비스가 1회 재요청한다.
  재요청 뒤(또는 남은 조합이 없을 때)에는 같아도 허용(`allow_fallback_repeat=True`).
- model 응답의 VA4는 그대로 — 허용 플래그가 있어도 거부.
"""

import pytest

from app.ai_client.ports import AiRole, AIUnavailableError, ClueVariant, Variant, VariantRequest, VariantResponse
from app.services import practice_validation as check

CLUES = ("clue_a", "clue_b")
PREVIOUS = ("dm", "다정한 말투")


def response(source: str, platform: str, tone: str, context: str = "ctx") -> VariantResponse:
    return VariantResponse(
        source=source,
        variant=Variant(
            base_scenario_id="s1",
            platform=platform,
            tone=tone,
            context=context,
            title="제목",
            child_setup="설정",
            opening_line="첫 대사",
            ai_role=AiRole(name="상대", persona="사람", tone=tone),
            clues=[
                ClueVariant(id=clue_id, reveal_when="언제", reveal_line="대사") for clue_id in CLUES
            ],
        ),
    )


def request(platform: str = "game_chat", tone: str = "급한 말투") -> VariantRequest:
    return VariantRequest(scenario_id="s1", platform=platform, tone=tone, context="ctx")


def test_fallback_same_as_previous_fails_va4_before_retry():
    with pytest.raises(AIUnavailableError, match="VA4"):
        check.check_variant(response("fallback", *PREVIOUS), request=request(), scenario_clue_ids=CLUES, previous=PREVIOUS)


def test_fallback_same_as_previous_is_allowed_after_retry():
    check.check_variant(
        response("fallback", *PREVIOUS),
        request=request(),
        scenario_clue_ids=CLUES,
        previous=PREVIOUS,
        allow_fallback_repeat=True,
    )


def test_model_same_as_previous_still_fails_va4_even_when_allowed():
    with pytest.raises(AIUnavailableError, match="VA4"):
        check.check_variant(
            response("model", *PREVIOUS),
            request=request(*PREVIOUS),
            scenario_clue_ids=CLUES,
            previous=PREVIOUS,
            allow_fallback_repeat=True,
        )


def test_allow_flag_does_not_skip_other_rules():
    bad = response("fallback", *PREVIOUS).model_copy(
        update={"variant": response("fallback", *PREVIOUS).variant.model_copy(update={"base_scenario_id": "other"})}
    )
    with pytest.raises(AIUnavailableError, match="VA1"):
        check.check_variant(bad, request=request(), scenario_clue_ids=CLUES, previous=PREVIOUS, allow_fallback_repeat=True)


@pytest.mark.parametrize(
    ("source", "pair", "previous", "expected"),
    [
        ("fallback", PREVIOUS, PREVIOUS, True),
        ("fallback", ("dm", "다른 말투"), PREVIOUS, False),
        ("fallback", PREVIOUS, None, False),
        ("model", PREVIOUS, PREVIOUS, False),
    ],
)
def test_is_fallback_repeat(source, pair, previous, expected):
    assert check.is_fallback_repeat(response(source, *pair), previous=previous) is expected
