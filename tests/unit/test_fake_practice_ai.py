"""FakePracticeAI·FakeSummaryAI = AI 계약 v1 (Architecture "1차 내부 API v1", DECISIONS #96·#97·#115, Tasks T-86 ①(마)).

Fake 응답이 같은 응답 모델 검증을 통과하고 선택지 규칙 C(정확히 3개, kind 3종 각 1개, id 중복 없음)를 지키는지 본다.
safe_reply·blocked는 생성자로, not_shown은 보낸 revealed_clue_ids로 테스트가 주입한다(T-15·T-16 테스트용).
"""

import pytest

from app.ai_client.fake import FakePracticeAI, FakeSummaryAI
from app.ai_client.ports import (
    Choice,
    FeedbackRequest,
    FeedbackResponse,
    JudgeRequest,
    JudgeResponse,
    Message,
    PracticeAI,
    StartRequest,
    StartResponse,
    SummaryAI,
    SummaryRequest,
    SummaryResponse,
    TurnRequest,
    TurnResponse,
    VariantRequest,
    VariantResponse,
)

SCENARIO_ID = "scam_fake_01"


def assert_choice_rule_c(choices: list[Choice]) -> None:
    assert len(choices) == 3
    assert sorted(c.kind for c in choices) == ["correct", "doubtful", "other"]
    assert len({c.id for c in choices}) == 3
    assert all(c.text.strip() for c in choices)


def make_variant(fake: FakePracticeAI):
    request = VariantRequest(scenario_id=SCENARIO_ID, platform="open_chat", tone="편한 말투", context="포장 알바")
    return fake.variant(request).variant


def child(text: str, kind: str, clue_id: str | None) -> Message:
    return Message(role="child", text=text, choice_kind=kind, clue_id=clue_id)


def ai(text: str) -> Message:
    return Message(role="ai", text=text)


# ---- 포트 적합 --------------------------------------------------------------


def test_fake_practice_ai_satisfies_port():
    assert isinstance(FakePracticeAI(), PracticeAI)


def test_fake_summary_ai_satisfies_port():
    assert isinstance(FakeSummaryAI(), SummaryAI)


def test_fake_has_no_opening():
    assert not hasattr(FakePracticeAI(), "opening")


# ---- variant ----------------------------------------------------------------


def test_variant_echoes_requested_values_and_validates():
    fake = FakePracticeAI()
    request = VariantRequest(scenario_id=SCENARIO_ID, platform="open_chat", tone="편한 말투", context="포장 알바")

    response = fake.variant(request)

    assert VariantResponse.model_validate(response.model_dump()) == response
    assert response.source == "model"
    assert response.variant.base_scenario_id == SCENARIO_ID
    assert (response.variant.platform, response.variant.tone, response.variant.context) == (
        "open_chat",
        "편한 말투",
        "포장 알바",
    )
    assert [c.id for c in response.variant.clues] == list(fake.clue_ids)


def test_variant_is_deterministic():
    request = VariantRequest(scenario_id=SCENARIO_ID, platform="dm", tone="존댓말", context="게임")

    assert FakePracticeAI().variant(request) == FakePracticeAI().variant(request)


def test_fake_rejects_empty_clue_ids():
    with pytest.raises(ValueError):
        FakePracticeAI(clue_ids=())


# ---- start ------------------------------------------------------------------


def test_start_returns_ok_with_choice_rule_c():
    fake = FakePracticeAI()
    variant = make_variant(fake)

    response = fake.start(StartRequest(scenario_id=SCENARIO_ID, variant=variant))

    assert StartResponse.model_validate(response.model_dump()) == response
    assert response.status == "ok"
    assert_choice_rule_c(response.choices)
    assert response.reply == variant.opening_line
    assert response.title == variant.title
    assert response.child_setup == variant.child_setup
    assert response.ai_role_name == variant.ai_role.name
    assert response.revealed_clue_ids == [fake.clue_ids[0]]
    assert response.target_clue_id == fake.clue_ids[0]


def test_start_without_variant_still_validates():
    fake = FakePracticeAI()

    response = fake.start(StartRequest(scenario_id=SCENARIO_ID))

    assert StartResponse.model_validate(response.model_dump()) == response
    assert_choice_rule_c(response.choices)
    assert response.reply.strip() and response.title.strip()


# ---- turn -------------------------------------------------------------------


def make_turn_request(revealed: list[str]) -> TurnRequest:
    return TurnRequest(
        scenario_id=SCENARIO_ID,
        messages=[ai("첫 대사"), child("예시 답", "other", revealed[-1] if revealed else None)],
        revealed_clue_ids=revealed,
    )


def test_turn_ok_reveals_next_clue_with_choice_rule_c():
    fake = FakePracticeAI(clue_ids=("clue_a", "clue_b", "clue_c"))

    response = fake.turn(make_turn_request(["clue_a"]))

    assert TurnResponse.model_validate(response.model_dump()) == response
    assert response.status == "ok"
    assert_choice_rule_c(response.choices)
    assert response.revealed_clue_ids == ["clue_a", "clue_b"]
    assert response.target_clue_id == "clue_b"
    assert response.all_clues_revealed is False


def test_turn_ok_when_all_revealed_keeps_list_and_null_target():
    fake = FakePracticeAI(clue_ids=("clue_a", "clue_b"))

    response = fake.turn(make_turn_request(["clue_a", "clue_b"]))

    assert response.status == "ok"
    assert response.revealed_clue_ids == ["clue_a", "clue_b"]
    assert response.target_clue_id is None
    assert response.all_clues_revealed is True
    assert_choice_rule_c(response.choices)


def test_turn_safe_reply_is_injectable():
    fake = FakePracticeAI(turn_status="safe_reply")

    response = fake.turn(make_turn_request(["clue_a"]))

    assert TurnResponse.model_validate(response.model_dump()) == response
    assert response.status == "safe_reply"
    assert response.choices == []
    assert response.choices_source == "none"
    assert response.target_clue_id is None
    assert response.revealed_clue_ids == ["clue_a"]


def test_turn_blocked_is_injectable_and_keeps_choice_rule_c():
    fake = FakePracticeAI(turn_status="blocked")

    response = fake.turn(make_turn_request(["clue_a"]))

    assert TurnResponse.model_validate(response.model_dump()) == response
    assert response.status == "blocked"
    assert response.source == "fixed"
    assert_choice_rule_c(response.choices)


def test_fake_rejects_unknown_turn_status():
    with pytest.raises(ValueError):
        FakePracticeAI(turn_status="ended")


def test_turn_uses_variant_clues_when_given():
    fake = FakePracticeAI(clue_ids=("clue_a", "clue_b"))
    variant = make_variant(fake)
    request = TurnRequest(
        scenario_id=SCENARIO_ID,
        messages=[child("예시 답", "doubtful", "clue_a")],
        revealed_clue_ids=["clue_a"],
        variant=variant,
    )

    assert fake.turn(request).revealed_clue_ids == ["clue_a", "clue_b"]


# ---- judge ------------------------------------------------------------------


def test_judge_marks_found_missed_and_not_shown_in_scenario_order():
    fake = FakePracticeAI(clue_ids=("clue_a", "clue_b", "clue_c"))
    request = JudgeRequest(
        scenario_id=SCENARIO_ID,
        messages=[
            ai("대사 1"),
            child("따를게요", "other", "clue_a"),
            ai("대사 2"),
            child("이상해요, 어른께 물어볼게요", "correct", "clue_b"),
        ],
        revealed_clue_ids=["clue_a", "clue_b"],
    )

    response = fake.judge(request)

    assert JudgeResponse.model_validate(response.model_dump()) == response
    assert [(r.clue_id, r.result) for r in response.results] == [
        ("clue_a", "missed"),
        ("clue_b", "found"),
        ("clue_c", "not_shown"),
    ]
    assert response.source == "choices"


def test_judge_doubtful_is_not_found():
    # AI doubtful("의심되는 답")은 PRD '의심' 태그가 아니다 (#97) — correct만 찾음.
    fake = FakePracticeAI(clue_ids=("clue_a",))
    request = JudgeRequest(
        scenario_id=SCENARIO_ID,
        messages=[child("음… 일단 해 볼까요", "doubtful", "clue_a")],
        revealed_clue_ids=["clue_a"],
    )

    assert [r.result for r in fake.judge(request).results] == ["missed"]


def test_judge_correct_on_unrevealed_clue_is_not_shown():
    fake = FakePracticeAI(clue_ids=("clue_a", "clue_b"))
    request = JudgeRequest(
        scenario_id=SCENARIO_ID,
        messages=[child("이상해요", "correct", "clue_b")],
        revealed_clue_ids=["clue_a"],
    )

    assert [r.result for r in fake.judge(request).results] == ["missed", "not_shown"]


# ---- feedback ---------------------------------------------------------------


def test_feedback_cards_only_found_and_missed_in_request_order():
    fake = FakePracticeAI()
    request = FeedbackRequest(
        scenario_id=SCENARIO_ID,
        results=[
            {"clue_id": "clue_a", "result": "missed"},
            {"clue_id": "clue_b", "result": "not_shown"},
            {"clue_id": "clue_c", "result": "found"},
        ],
    )

    response = fake.feedback(request)

    assert FeedbackResponse.model_validate(response.model_dump()) == response
    assert [(c.clue_id, c.result) for c in response.cards] == [("clue_a", "missed"), ("clue_c", "found")]
    assert all(c.text.strip() for c in response.cards)
    assert response.closing_line.strip()


def test_feedback_with_all_not_shown_has_no_cards():
    response = FakePracticeAI().feedback(
        FeedbackRequest(scenario_id=SCENARIO_ID, results=[{"clue_id": "clue_a", "result": "not_shown"}])
    )

    assert response.cards == []
    assert response.closing_line.strip()


# ---- summary ----------------------------------------------------------------


def test_summary_returns_validated_non_blank_sentence():
    request = SummaryRequest(area="사기", practice_count=3, found_clues=["돈 요구"], missed_clues=[], growth_level=None)

    response = FakeSummaryAI().summary(request)

    assert SummaryResponse.model_validate(response.model_dump()) == response
    assert isinstance(response.summary, str) and response.summary.strip()


def test_summary_mentions_only_input_numbers():
    # S2: 숫자는 입력 값에 있는 것만 (#53).
    response = FakeSummaryAI().summary(SummaryRequest(area="사기", practice_count=0))

    assert "0" in response.summary
    assert not any(ch.isdigit() and ch != "0" for ch in response.summary)


# ---- T-15: 시나리오별 단서 (dev 서버·E2E에서 VA2 검증 통과용) ----------------------------


def test_variant_uses_scenario_clue_ids_when_mapped():
    fake = FakePracticeAI(scenario_clue_ids={"scam_a": ("x1", "x2"), "scam_b": ("y1",)})

    a = fake.variant(VariantRequest(scenario_id="scam_a", platform="p", tone="t", context="c")).variant
    b = fake.variant(VariantRequest(scenario_id="scam_b", platform="p", tone="t", context="c")).variant

    assert [clue.id for clue in a.clues] == ["x1", "x2"]
    assert [clue.id for clue in b.clues] == ["y1"]
    assert [clue.at_opening for clue in a.clues] == [True, False]


def test_variant_falls_back_to_default_clues_for_unmapped_scenario():
    fake = FakePracticeAI(clue_ids=("d1", "d2"), scenario_clue_ids={"scam_a": ("x1",)})

    variant = fake.variant(VariantRequest(scenario_id="other", platform="p", tone="t", context="c")).variant

    assert [clue.id for clue in variant.clues] == ["d1", "d2"]


def test_fake_rejects_empty_scenario_clue_ids():
    with pytest.raises(ValueError):
        FakePracticeAI(scenario_clue_ids={"scam_a": ()})
