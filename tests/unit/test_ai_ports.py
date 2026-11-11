"""AI 포트·DTO = AI 계약 v1 (Architecture "1차 내부 API v1", DECISIONS #96·#97·#104·#112·#115, ADR-0017, Tasks T-86).

계약 샘플은 tests/contracts/ai/ — ai 저장소 feature/ai 331d2c6 contracts/*.json 사본(SOURCE.txt).
응답 검증 규칙(VA·ST·TU·J'·V'·S)은 범위 밖(T-15·T-16·T-76) — 여기서는 필드·타입만 본다.
"""

import json
from pathlib import Path
from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

from app.ai_client import ports
from app.ai_client.ports import (
    Area,
    ChoiceKind,
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
    Variant,
    VariantRequest,
    VariantResponse,
)

CONTRACT_DIR = Path(__file__).resolve().parents[1] / "contracts" / "ai"

SAMPLE_MODELS: dict[str, type[BaseModel]] = {
    "practice.variant.request.json": VariantRequest,
    "practice.variant.response.json": VariantResponse,
    "practice.start.request.json": StartRequest,
    "practice.start.response.json": StartResponse,
    "practice.turn.request.json": TurnRequest,
    "practice.turn.response.json": TurnResponse,
    "practice.judge.request.json": JudgeRequest,
    "practice.judge.response.json": JudgeResponse,
    "practice.feedback.request.json": FeedbackRequest,
    "practice.feedback.response.json": FeedbackResponse,
    "summary.request.json": SummaryRequest,
    "summary.response.json": SummaryResponse,
}


def load_sample(name: str) -> dict:
    return json.loads((CONTRACT_DIR / name).read_text(encoding="utf-8"))


def child_message(**overrides) -> dict:
    data = {"role": "child", "text": "예시 답", "choice_kind": "correct", "clue_id": "clue_a"}
    data.update(overrides)
    return data


# ---- (라) 계약 샘플 12개 ------------------------------------------------------


def test_contract_dir_has_exactly_the_12_pinned_samples():
    names = sorted(p.name for p in CONTRACT_DIR.glob("*.json"))

    assert names == sorted(SAMPLE_MODELS)


def test_contract_source_records_pinned_commit():
    source = (CONTRACT_DIR / "SOURCE.txt").read_text(encoding="utf-8")

    assert "line1thon-15/ai" in source
    assert "feature/ai" in source
    assert "331d2c6" in source


@pytest.mark.parametrize("name", sorted(SAMPLE_MODELS))
def test_contract_sample_parses_without_losing_fields(name):
    data = load_sample(name)

    parsed = SAMPLE_MODELS[name].model_validate(data)

    # 모델에 없는 필드는 응답 모델에서 버려지므로, 덤프가 원문과 같으면 필드 이름·값이 모두 대응한다.
    assert parsed.model_dump(mode="json", exclude_unset=True) == data


# ---- (나) 열거값 ------------------------------------------------------------


def test_choice_kind_values_match_ai_contract():
    assert set(get_args(ChoiceKind)) == {"correct", "doubtful", "other"}


def test_turn_status_values_match_ai_contract():
    sample = load_sample("practice.turn.response.json")
    for status in ("ok", "safe_reply", "blocked"):
        assert TurnResponse.model_validate({**sample, "status": status}).status == status

    with pytest.raises(ValidationError):
        TurnResponse.model_validate({**sample, "status": "ended"})


def test_judge_result_values_match_ai_contract():
    sample = load_sample("practice.judge.response.json")
    for result in ("found", "missed", "not_shown"):
        data = {**sample, "results": [{"clue_id": "clue_a", "result": result}]}
        assert JudgeResponse.model_validate(data).results[0].result == result

    with pytest.raises(ValidationError):
        JudgeResponse.model_validate({**sample, "results": [{"clue_id": "clue_a", "result": "suspicious"}]})


def test_feedback_card_result_excludes_not_shown():
    sample = load_sample("practice.feedback.response.json")
    card = {"clue_id": "clue_a", "result": "not_shown", "text": "예시"}

    with pytest.raises(ValidationError):
        FeedbackResponse.model_validate({**sample, "cards": [card]})


def test_choice_rejects_old_judgment_tag():
    sample = load_sample("practice.start.response.json")
    choices = [{"id": "c1", "text": "예시", "kind": "suspicious"}]

    with pytest.raises(ValidationError):
        StartResponse.model_validate({**sample, "choices": choices})


def test_summary_response_allows_null_summary():
    assert SummaryResponse.model_validate({"summary": None}).summary is None


def test_summary_response_requires_summary_key():
    with pytest.raises(ValidationError):
        SummaryResponse.model_validate({})


# ---- (다) Area -------------------------------------------------------------


def test_area_uses_ai_ids():
    assert set(get_args(Area)) == {"scam", "identity_lending", "friend_pressure"}


# ---- (바) 참고값 필드는 파싱만 ------------------------------------------------


def test_turn_response_parses_reference_only_fields():
    data = {
        **load_sample("practice.turn.response.json"),
        "all_clues_revealed": True,
        "masked": True,
        "choices_source": "template",
    }

    turn = TurnResponse.model_validate(data)

    assert turn.all_clues_revealed is True
    assert turn.masked is True
    assert turn.choices_source == "template"


# ---- 요청 모델 경계 (outbound — N-05: 규격 밖 필드 거부) --------------------------


@pytest.mark.parametrize(
    "model, name",
    [
        (VariantRequest, "practice.variant.request.json"),
        (StartRequest, "practice.start.request.json"),
        (TurnRequest, "practice.turn.request.json"),
        (JudgeRequest, "practice.judge.request.json"),
        (FeedbackRequest, "practice.feedback.request.json"),
        (SummaryRequest, "summary.request.json"),
    ],
)
def test_outbound_request_rejects_child_identifying_field(model, name):
    with pytest.raises(ValidationError):
        model.model_validate({**load_sample(name), "nickname": "예시별명"})


def test_message_rejects_child_identifying_field():
    with pytest.raises(ValidationError):
        Message.model_validate(child_message(child_id=1))


@pytest.mark.parametrize("length, ok", [(1, True), (500, True), (0, False), (501, False)])
def test_message_text_length_is_1_to_500(length, ok):
    data = child_message(text="가" * length)
    if ok:
        assert len(Message.model_validate(data).text) == length
    else:
        with pytest.raises(ValidationError):
            Message.model_validate(data)


def test_message_clue_id_max_64():
    assert Message.model_validate(child_message(clue_id="a" * 64)).clue_id == "a" * 64
    with pytest.raises(ValidationError):
        Message.model_validate(child_message(clue_id="a" * 65))


def test_ai_message_defaults_choice_fields_to_none():
    message = Message.model_validate({"role": "ai", "text": "예시 대사"})

    assert message.choice_kind is None
    assert message.clue_id is None


def test_turn_request_requires_last_message_from_child():
    with pytest.raises(ValidationError):
        TurnRequest.model_validate(
            {"scenario_id": "s1", "messages": [child_message(), {"role": "ai", "text": "예시 대사"}]}
        )


@pytest.mark.parametrize("count, ok", [(1, True), (40, True), (0, False), (41, False)])
def test_turn_request_messages_count_is_1_to_40(count, ok):
    data = {"scenario_id": "s1", "messages": [child_message() for _ in range(count)]}
    if ok:
        assert len(TurnRequest.model_validate(data).messages) == count
    else:
        with pytest.raises(ValidationError):
            TurnRequest.model_validate(data)


def test_variant_request_requires_platform_tone_context():
    # 백엔드는 세 값을 항상 채운다 (#102).
    with pytest.raises(ValidationError):
        VariantRequest.model_validate({"scenario_id": "s1"})


def test_summary_request_rejects_negative_practice_count():
    with pytest.raises(ValidationError):
        SummaryRequest.model_validate({**load_sample("summary.request.json"), "practice_count": -1})


def test_variant_round_trips_into_later_requests():
    # 받은 variant를 그대로 저장해 같은 세션의 이후 요청에 보낸다 (#98).
    variant = VariantResponse.model_validate(load_sample("practice.variant.response.json")).variant

    request = StartRequest(scenario_id="scam_dm_parttime_01", variant=variant)

    assert isinstance(request.variant, Variant)
    assert request.model_dump(mode="json")["variant"] == load_sample("practice.variant.response.json")["variant"]


def test_variant_clues_must_be_1_to_10():
    data = load_sample("practice.variant.response.json")["variant"]

    with pytest.raises(ValidationError):
        Variant.model_validate({**data, "clues": []})
    with pytest.raises(ValidationError):
        Variant.model_validate({**data, "clues": data["clues"] * 3})


# ---- (가) 포트 모양 ----------------------------------------------------------


def test_practice_ai_port_methods():
    methods = {"variant", "start", "turn", "judge", "feedback"}

    assert methods <= set(dir(PracticeAI))
    assert not hasattr(PracticeAI, "opening")


def test_summary_ai_port_methods():
    assert hasattr(SummaryAI, "summary")


# 옛 요청·턴·개시 모델 3종은 완료 조건 ⑤ grep(app/·tests/ 0건)으로 확인한다 — 이름을 여기 적지 않는다.
@pytest.mark.parametrize("old_name", ["ChoiceOption", "ReviewResult", "ChoiceJudgment", "TargetCue"])
def test_old_models_are_removed(old_name):
    assert not hasattr(ports, old_name)
