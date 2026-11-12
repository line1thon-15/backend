"""AI 응답 검증 — 위반이면 `AIUnavailableError` → 503 `AI_UNAVAILABLE` (Architecture "1차 내부 API v1").

VA1~VA4(variant) · ST1~ST5(start) · TU1~TU4(turn ok·blocked) · J1'~J4'(judge) · 선택지 규칙 C(#97).
safe_reply는 `status`만 읽고 검증하지 않는다(#118).
열 길이(턴 선택지 id ≤ 8, 세션 제목·설정·역할 이름)는 DB 열 상한을 넘는 값을 저장 전에 막는 백엔드 추가 검증이다.
"""

from collections.abc import Sequence

from app.ai_client.ports import (
    AIUnavailableError,
    Choice,
    JudgeResponse,
    Message,
    StartResponse,
    TurnResponse,
    VariantRequest,
    VariantResponse,
)

_KINDS = ("correct", "doubtful", "other")
CHOICE_ID_MAX = 8
SCENARIO_TITLE_MAX = 80
CHILD_SETUP_MAX = 300
AI_ROLE_NAME_MAX = 40


def _fail(rule: str) -> None:
    raise AIUnavailableError(f"AI response violates {rule}")


def _blank(value: str) -> bool:
    return not value.strip()


def check_choice_rule_c(choices: Sequence[Choice], rule: str) -> None:
    if len(choices) != 3:
        _fail(rule)
    if sorted(choice.kind for choice in choices) != sorted(_KINDS):
        _fail(rule)
    ids = [choice.id for choice in choices]
    if len(set(ids)) != len(ids):
        _fail(rule)
    if any(_blank(choice.text) or _blank(choice.id) or len(choice.id) > CHOICE_ID_MAX for choice in choices):
        _fail(rule)


def check_variant(
    response: VariantResponse,
    *,
    request: VariantRequest,
    scenario_clue_ids: Sequence[str],
    previous: tuple[str, str] | None,
) -> None:
    variant = response.variant
    if variant.base_scenario_id != request.scenario_id:
        _fail("VA1")
    if [clue.id for clue in variant.clues] != list(scenario_clue_ids):
        _fail("VA2")
    if response.source == "model" and (
        variant.platform != request.platform
        or variant.tone != request.tone
        or variant.context != request.context
    ):
        _fail("VA3")
    if previous is not None and (variant.platform, variant.tone) == previous:
        _fail("VA4")


def check_start(response: StartResponse, *, scenario_clue_ids: Sequence[str]) -> None:
    if response.status != "ok":
        _fail("ST1")
    check_choice_rule_c(response.choices, "ST2")
    if not set(response.revealed_clue_ids) <= set(scenario_clue_ids):
        _fail("ST3")
    if response.target_clue_id is not None and response.target_clue_id not in response.revealed_clue_ids:
        _fail("ST4")
    if any(_blank(value) for value in (response.reply, response.title, response.child_setup, response.ai_role_name)):
        _fail("ST5")
    if (
        len(response.title) > SCENARIO_TITLE_MAX
        or len(response.child_setup) > CHILD_SETUP_MAX
        or len(response.ai_role_name) > AI_ROLE_NAME_MAX
    ):
        _fail("ST5 column length")


def check_turn(
    response: TurnResponse,
    *,
    sent_revealed: Sequence[str],
    scenario_clue_ids: Sequence[str],
) -> None:
    """status ok·blocked 응답만 검증한다(safe_reply는 호출하지 않는다)."""
    check_choice_rule_c(response.choices, "TU1")
    revealed = set(response.revealed_clue_ids)
    if not set(sent_revealed) <= revealed or not revealed <= set(scenario_clue_ids):
        _fail("TU2")
    if response.target_clue_id is not None and response.target_clue_id not in response.revealed_clue_ids:
        _fail("TU3")
    if _blank(response.reply):
        _fail("TU4")


def check_judge(
    response: JudgeResponse,
    *,
    scenario_clue_ids: Sequence[str],
    sent_revealed: Sequence[str],
    messages: Sequence[Message],
) -> None:
    if [item.clue_id for item in response.results] != list(scenario_clue_ids):
        _fail("J1'")
    revealed = set(sent_revealed)
    found = {
        message.clue_id
        for message in messages
        if message.role == "child" and message.choice_kind == "correct" and message.clue_id is not None
    } & revealed
    for item in response.results:
        if (item.result == "not_shown") != (item.clue_id not in revealed):
            _fail("J2'")
        if item.result != "not_shown" and (item.result == "found") != (item.clue_id in found):
            _fail("J3'")
    if response.source not in ("choices", "fixed"):
        _fail("J4'")
