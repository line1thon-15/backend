"""연습 결과 A18·다시 도전 A15 retry (T-16 — F-13 ①③, F-12, F-26).

근거: Architecture "API 규격" A15·A18, "응답 DTO" CueCard·PracticeResultView, 내부 API `feedback` 행·
"`feedback` 응답 → PracticeResultView 매핑" 행(①~⑦), "다시 도전" 출제 규칙, DECISIONS #75·#101·#102·#109·#113.

`level` 키→값은 PRD OQ 63·24 미정이라 테스트가 값을 주입한다(LEVELS — 확정 값이 아님).
AI는 기록용 Fake로만 호출한다(실제 HTTP 없음). DB는 테스트마다 pytest tmp_path SQLite 파일.
"""

import random
from collections.abc import Iterator
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai_client.ports import FeedbackCard
from app.content.loader import ScenarioEntry
from app.core.config import Settings
from app.db.base import Base
from app.db.models import CueResult, PracticeSession
from app.main import create_app
from app.repositories.practice import SqlAlchemyPracticeRepository
from app.services.practice import PracticeService
from tests.integration.test_practice_sessions import (
    CONTENT,
    MARKER,
    SCENARIO_CLUES,
    Env,
    RecordingPracticeAI,
    choice_id_of,
)

# 테스트 주입 값 — 확정 값이 아니다 (PRD OQ 63·24)
LEVELS = {"K1": "green", "K2": "red", "K3": "yellow", "K4": "green", "K5": "yellow"}


class ResultEnv(Env):
    def result(self, session_id: str):
        return self.client.get(f"/api/v1/practice/sessions/{session_id}/result")

    def retry(self, retry_of: str):
        return self.client.post("/api/v1/practice/sessions", json={"mode": "retry", "retry_of": retry_of})

    def ended(self, kinds: tuple[str, ...] = ("correct",)) -> str:
        """kinds 순서대로 답해 끝낸 세션 id."""
        view = self.started()
        session_id = view["session_id"]
        for kind in kinds:
            view = self.answer(session_id, choice_id_of(view, kind, self)).json()
        assert view["status"] == "ended", view
        return session_id

    def use_levels(self, levels: dict) -> None:
        self._swap_service(card_level_by_key=levels)

    def use_content(self, content) -> None:
        self._swap_service(content=content)

    def _swap_service(self, **changes) -> None:
        current: PracticeService = self.client.app.state.practice_service
        self.client.app.state.practice_service = PracticeService(
            SqlAlchemyPracticeRepository(self.session_factory),
            self.ai,
            changes.get("content", current._content),
            rng_factory=lambda: random.Random(1234),
            card_level_by_key=changes.get("card_level_by_key", LEVELS),
        )


@pytest.fixture
def env(tmp_path) -> Iterator[ResultEnv]:
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'result.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
        card_level_by_key=LEVELS,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield ResultEnv(client, ai)
    app.state.engine.dispose()


def cue_card(cue_id: str) -> dict:
    clue = CONTENT.clues[cue_id]
    return {"cue_id": cue_id, "label": clue.name, "sentence": clue.description}


def narrowed_content(scenario_id: str):
    """그 시나리오의 platform·tone을 1개씩만 남긴 콘텐츠 — 다시 도전 가능한 변형이 없다."""
    entry = CONTENT.scenarios[scenario_id]
    axes = entry.scenario.variation_axes
    narrow_axes = axes.model_copy(update={"platform": axes.platform[:1], "tone": axes.tone[:1]})
    scenario = entry.scenario.model_copy(update={"variation_axes": narrow_axes})
    scenarios = dict(CONTENT.scenarios)
    scenarios[scenario_id] = ScenarioEntry(area=entry.area, scenario=scenario)
    return replace(CONTENT, scenarios=scenarios)


# ==== A18 정상 =====================================================================


def test_result_after_correct_first_answer(env):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))
    clues = SCENARIO_CLUES[env.session_row(session_id).scenario_id]
    cue_before = env.count(CueResult)
    env.ai.calls.clear()

    response = env.result(session_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"session_id", "found", "missed", "normal_outcome", "cards", "can_retry"}
    assert body["session_id"] == session_id
    assert body["found"] == [cue_card(clues[0])]
    assert body["missed"] == []
    assert body["normal_outcome"] is None
    assert body["can_retry"] is True
    feedback = env.ai.requests("feedback")
    assert env.ai.names() == ["feedback"]
    # 카드: AI 카드 순서대로 + 마지막 closing_line(K3)
    assert body["cards"] == [
        {"level": LEVELS["K1"], "sentence": f"[fake] {clues[0]} 단서를 잘 찾았어요."},
        {"level": LEVELS["K3"], "sentence": "[fake] 끝까지 연습해서 멋져요!"},
    ]
    assert len(feedback) == 1
    # 읽기 요청 — 아무것도 저장하지 않는다
    assert env.count(CueResult) == cue_before


def test_result_with_missed_and_found(env):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "correct"))
    clues = SCENARIO_CLUES[env.session_row(session_id).scenario_id]

    body = env.result(session_id).json()

    assert body["found"] == [cue_card(clues[1])]
    assert body["missed"] == [cue_card(clues[0])]
    assert [card["level"] for card in body["cards"]] == [LEVELS["K2"], LEVELS["K1"], LEVELS["K3"]]


def test_result_after_four_misses_lists_missed_in_scenario_order(env):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "doubtful", "other", "doubtful"))
    clues = SCENARIO_CLUES[env.session_row(session_id).scenario_id]

    body = env.result(session_id).json()

    assert body["found"] == []
    assert body["missed"] == [cue_card(clue_id) for clue_id in clues]
    assert [card["level"] for card in body["cards"]] == [LEVELS["K2"]] * len(clues) + [LEVELS["K3"]]


def test_result_with_no_revealed_clue_has_only_closing_card(env):
    # 경계: 드러난 단서 0개 → cue_results 0행, found·missed 빈 목록, 카드는 closing_line 1장
    env.login_child(grade="H1")
    env.ai.overrides["start"] = lambda req, res: res.model_copy(
        update={"revealed_clue_ids": [], "target_clue_id": None}
    )
    session_id = env.ended(("correct",))
    assert env.cue_rows(session_id) == []

    body = env.result(session_id).json()

    assert body["found"] == [] and body["missed"] == []
    assert body["cards"] == [{"level": LEVELS["K3"], "sentence": "[fake] 끝까지 연습해서 멋져요!"}]
    assert [item.result for item in env.ai.requests("feedback")[0].results] == ["not_shown"] * 4


def test_cue_card_sentence_is_content_and_ai_text_stays_in_cards(env):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "correct"))
    env.ai.overrides["feedback"] = lambda req, res: res.model_copy(
        update={
            "cards": [card.model_copy(update={"text": f"{MARKER} {card.clue_id}"}) for card in res.cards],
            "closing_line": f"{MARKER} closing",
        }
    )

    body = env.result(session_id).json()

    for card in body["found"] + body["missed"]:
        clue = CONTENT.clues[card["cue_id"]]
        assert card["label"] == clue.name
        assert card["sentence"] == clue.description
        assert MARKER not in card["label"] + card["sentence"]
    # AI 문장은 cards[]에만, CueCard 설명은 cards[]에 넣지 않는다
    assert all(card["sentence"].startswith(MARKER) for card in body["cards"])
    descriptions = {CONTENT.clues[c["cue_id"]].description for c in body["found"] + body["missed"]}
    assert not descriptions & {card["sentence"] for card in body["cards"]}


def test_cards_follow_ai_order_and_have_no_cue_id(env):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "correct"))
    env.ai.overrides["feedback"] = lambda req, res: res.model_copy(update={"cards": list(reversed(res.cards))})

    body = env.result(session_id).json()

    assert [card["level"] for card in body["cards"]] == [LEVELS["K1"], LEVELS["K2"], LEVELS["K3"]]
    assert all(set(card) == {"level", "sentence"} for card in body["cards"])


def test_feedback_request_uses_stored_results_messages_and_variant(env):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "correct"))
    row = env.session_row(session_id)
    clues = SCENARIO_CLUES[row.scenario_id]
    judge_request = env.ai.requests("judge")[0]
    env.ai.calls.clear()

    env.result(session_id)

    request = env.ai.requests("feedback")[0]
    assert request.scenario_id == row.scenario_id
    # 시나리오 단서 순서 — 저장된 found·missed + 나머지 not_shown
    assert [(item.clue_id, item.result) for item in request.results] == [
        (clues[0], "missed"),
        (clues[1], "found"),
        (clues[2], "not_shown"),
        (clues[3], "not_shown"),
    ]
    # 대화 이력 전체(마지막 아이 답 포함) — judge에 보낸 것과 같다
    assert [m.model_dump() for m in request.messages] == [m.model_dump() for m in judge_request.messages]
    # 저장된 variant 그대로 (T-86 리뷰 권고 #1)
    assert request.variant is not None
    assert request.variant.model_dump(mode="json") == row.variant


def test_result_can_be_requested_again(env):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))

    first = env.result(session_id)
    second = env.result(session_id)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert env.ai.names().count("feedback") == 2


# ==== A18 404·409 — AI 미호출 =========================================================


def test_result_of_other_childs_session_is_404(env):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))
    env.login_child(grade="H1")
    env.ai.calls.clear()

    response = env.result(session_id)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
    assert env.ai.calls == []


def test_result_of_unknown_session_is_404(env):
    env.login_child(grade="H1")

    response = env.result(str(uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
    assert env.ai.calls == []


def test_result_requires_child_session(env):
    response = env.result(str(uuid4()))

    assert response.status_code == 401


def test_result_of_in_progress_session_is_409_not_ended(env):
    env.login_child(grade="H1")
    session_id = env.started()["session_id"]
    env.ai.calls.clear()

    response = env.result(session_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_NOT_ENDED"
    assert env.ai.calls == []


def test_result_of_stopped_session_is_409_stopped(env):
    env.login_child(grade="H1")
    view = env.started()
    env.ai.turn_status = "safe_reply"
    env.answer(view["session_id"], choice_id_of(view, "other", env))
    env.ai.calls.clear()

    response = env.result(view["session_id"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_STOPPED"
    assert env.ai.calls == []


# ==== A18 503 — feedback 실패·검증 V1'~V3' 위반 (부분 응답 없음) ==========================


def test_feedback_failure_is_503_without_partial_body(env):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))
    env.ai.fail.add("feedback")

    response = env.result(session_id)

    assert response.status_code == 503
    assert response.json() == {"error": {"code": "AI_UNAVAILABLE", "message": "AI service is unavailable"}}


def _cards(res, cards):
    return res.model_copy(update={"cards": cards})


FEEDBACK_VIOLATIONS = {
    # V1' 카드 clue_id 집합 = 저장된 found∪missed, 단서마다 1장
    "V1_missing_card": lambda req, res: _cards(res, res.cards[:-1]),
    "V1_not_shown_card": lambda req, res: _cards(
        res, res.cards + [FeedbackCard(clue_id=req.results[-1].clue_id, result="missed", text="추가")]
    ),
    "V1_unknown_clue": lambda req, res: _cards(
        res, res.cards + [FeedbackCard(clue_id="no_such_clue", result="missed", text="추가")]
    ),
    "V1_duplicate_card": lambda req, res: _cards(res, res.cards + [res.cards[0]]),
    # V2' text·closing_line 공백만이 아님
    "V2_blank_text": lambda req, res: _cards(res, [res.cards[0].model_copy(update={"text": "  "})] + res.cards[1:]),
    "V2_empty_text": lambda req, res: _cards(res, [res.cards[0].model_copy(update={"text": ""})] + res.cards[1:]),
    "V2_blank_closing": lambda req, res: res.model_copy(update={"closing_line": " \n "}),
    # V3' 카드 result = 저장된 판정
    "V3_result_flipped": lambda req, res: _cards(
        res,
        [card.model_copy(update={"result": "missed" if card.result == "found" else "found"}) for card in res.cards],
    ),
}


@pytest.mark.parametrize("case", sorted(FEEDBACK_VIOLATIONS))
def test_feedback_validation_violation_is_503(env, case):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "correct"))
    env.ai.overrides["feedback"] = FEEDBACK_VIOLATIONS[case]

    response = env.result(session_id)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert set(response.json()) == {"error"}


@pytest.mark.parametrize("source", ["model", "fallback", "mixed", "fixed"])
def test_feedback_source_is_not_restricted(env, source):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))
    env.ai.overrides["feedback"] = lambda req, res: res.model_copy(update={"source": source})

    assert env.result(session_id).status_code == 200


# ==== A18 level 매핑 =================================================================


def test_level_follows_injected_mapping(env):
    env.login_child(grade="H1")
    session_id = env.ended(("other", "correct"))
    env.use_levels({"K1": "red", "K2": "green", "K3": "red", "K4": "red", "K5": "red"})

    body = env.result(session_id).json()

    assert [card["level"] for card in body["cards"]] == ["green", "red", "red"]


def test_unmapped_level_key_is_500_internal(env):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))
    env.use_levels({"K1": "green"})  # K3(closing_line) 값 없음 — 임의 색을 보이지 않는다

    env.ai.calls.clear()

    response = env.result(session_id)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL"
    # T-89 ③ — 매핑 확인은 feedback 호출 전 (T-16 리뷰 권고 #1, DECISIONS #120)
    assert env.ai.calls == []


def test_app_default_mapping_returns_decided_levels(tmp_path):
    # T-89 ② — 기본 앱(매핑 주입 없음)에서 A18 200, K2 노랑 → K1 초록 → K3 초록
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'd.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        local = ResultEnv(client, ai)
        local.login_child(grade="H1")
        session_id = local.ended(("other", "correct"))
        response = local.result(session_id)
    app.state.engine.dispose()

    assert response.status_code == 200
    assert [card["level"] for card in response.json()["cards"]] == ["yellow", "green", "green"]


# ==== A15 다시 도전 (F-13 ③, F-12) =====================================================


def test_retry_starts_same_scenario_with_different_variant(env):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    original = env.session_row(original_id)
    env.ai.calls.clear()

    response = env.retry(original_id)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["mode"] == "retry"
    assert body["is_retry"] is True
    assert body["area"] == original.area
    assert body["status"] == "in_progress"
    assert body["turn"]["turn_index"] == 0
    assert env.ai.names() == ["variant", "start"]
    row = env.session_row(body["session_id"])
    assert row.scenario_id == original.scenario_id
    assert row.target_cue_ids == original.target_cue_ids
    assert row.retry_of == UUID(original_id)
    assert row.mode == "retry"
    assert row.draw_index is None
    assert row.subtype == original.subtype
    assert row.is_normal is False
    assert (row.variant["platform"], row.variant["tone"]) != (original.variant["platform"], original.variant["tone"])
    variant_request = env.ai.requests("variant")[0]
    axes = CONTENT.scenarios[original.scenario_id].variation_axes
    assert variant_request.scenario_id == original.scenario_id
    assert variant_request.platform in axes.platform
    assert variant_request.tone in axes.tone
    assert variant_request.context in axes.context


def test_retry_session_can_be_played_and_retried_again(env):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    retry = env.retry(original_id).json()
    second_axes = env.session_row(retry["session_id"]).variant
    env.answer(retry["session_id"], choice_id_of(retry, "correct", env))

    result = env.result(retry["session_id"])
    again = env.retry(retry["session_id"])

    assert result.status_code == 200
    assert result.json()["can_retry"] is True
    assert again.status_code == 201
    third = env.session_row(again.json()["session_id"])
    assert third.retry_of == UUID(retry["session_id"])
    # F-12 비교 대상은 retry_of(직전) 세션
    assert (third.variant["platform"], third.variant["tone"]) != (second_axes["platform"], second_axes["tone"])


def test_retry_does_not_consume_draw_index(env):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    env.retry(original_id)

    next_area = env.started()

    assert env.session_row(next_area["session_id"]).draw_index == 2


def test_retry_of_other_childs_session_is_404(env):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    env.login_child(grade="H1")
    env.ai.calls.clear()
    before = env.count(PracticeSession)

    response = env.retry(original_id)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
    assert env.ai.calls == []
    assert env.count(PracticeSession) == before


def test_retry_of_unknown_session_is_404(env):
    env.login_child(grade="H1")

    response = env.retry(str(uuid4()))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
    assert env.ai.calls == []


def test_retry_of_in_progress_session_is_409_not_ended(env):
    env.login_child(grade="H1")
    session_id = env.started()["session_id"]
    env.ai.calls.clear()

    response = env.retry(session_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_NOT_ENDED"
    assert env.ai.calls == []


def test_retry_of_stopped_session_is_409_stopped(env):
    env.login_child(grade="H1")
    view = env.started()
    env.ai.turn_status = "safe_reply"
    env.answer(view["session_id"], choice_id_of(view, "other", env))
    env.ai.calls.clear()

    response = env.retry(view["session_id"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_STOPPED"
    assert env.ai.calls == []


def test_retry_without_other_variant_is_no_scenario_and_result_cannot_retry(env):
    env.login_child(grade="H1")
    session_id = env.ended(("correct",))
    scenario_id = env.session_row(session_id).scenario_id
    env.use_content(narrowed_content(scenario_id))
    # 남은 조합이 (원래 세션 값과) 같도록 원래 세션의 platform·tone을 그 1개 조합으로 맞춘다
    axes = env.client.app.state.practice_service._content.scenarios[scenario_id].variation_axes
    with env.session_factory.begin() as db:
        row = db.get(PracticeSession, UUID(session_id))
        row.variant = {**row.variant, "platform": axes.platform[0], "tone": axes.tone[0]}
    env.ai.calls.clear()

    result = env.result(session_id)
    retry = env.retry(session_id)

    assert result.json()["can_retry"] is False
    assert retry.status_code == 409
    assert retry.json()["error"]["code"] == "NO_SCENARIO_AVAILABLE"
    assert env.ai.names() == ["feedback"]


def test_retry_fallback_variant_same_as_retry_of_is_503(env):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    original = env.session_row(original_id).variant
    env.ai.overrides["variant"] = lambda req, res: res.model_copy(
        update={
            "source": "fallback",
            "variant": res.variant.model_copy(update={"platform": original["platform"], "tone": original["tone"]}),
        }
    )
    before = env.count(PracticeSession)

    response = env.retry(original_id)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.count(PracticeSession) == before


@pytest.mark.parametrize("failing", ["variant", "start"])
def test_retry_ai_failure_is_503_and_saves_nothing(env, failing):
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    env.ai.fail.add(failing)
    before = env.count(PracticeSession)

    response = env.retry(original_id)

    assert response.status_code == 503
    assert env.count(PracticeSession) == before


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "retry"},
        {"mode": "retry", "retry_of": "not-a-uuid"},
        {"mode": "retry", "retry_of": None},
        {"mode": "retry", "retry_of": "00000000-0000-0000-0000-000000000000", "area": "scam"},
        {"mode": "area", "retry_of": "00000000-0000-0000-0000-000000000000"},
        {"mode": "mission"},
    ],
)
def test_invalid_retry_request_is_422(env, payload):
    env.login_child(grade="H1")

    response = env.client.post("/api/v1/practice/sessions", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert env.ai.calls == []
