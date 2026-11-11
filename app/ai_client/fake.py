"""결정적 응답을 주는 PracticeAI·SummaryAI 구현 — 테스트·로컬·E2E 기본 (AI_CLIENT=fake).

AI 계약 v1(Architecture "1차 내부 API v1")과 같은 모델을 돌려준다. 선택지는 항상 규칙 C(정확히 3개,
kind 3종 각 1개, id 중복 없음)를 지킨다. 테스트 주입: turn 상태는 생성자 `turn_status`로(safe_reply·blocked),
judge의 not_shown은 보낸 `revealed_clue_ids`에서 뺀 단서로 만든다.
"""

from typing import get_args

from app.ai_client.ports import (
    AiRole,
    Choice,
    ClueResult,
    ClueVariant,
    FeedbackCard,
    FeedbackRequest,
    FeedbackResponse,
    JudgeRequest,
    JudgeResponse,
    StartRequest,
    StartResponse,
    SummaryRequest,
    SummaryResponse,
    TurnRequest,
    TurnResponse,
    Variant,
    VariantRequest,
    VariantResponse,
)

_TURN_STATUSES = get_args(TurnResponse.model_fields["status"].annotation)

DEFAULT_CLUE_IDS = ("fake_clue_1", "fake_clue_2", "fake_clue_3")

_CHOICES = (
    Choice(id="c1", text="[fake] 이상해요, 어른께 물어볼게요", kind="correct"),
    Choice(id="c2", text="[fake] 좀 이상하지만… 해 볼까요?", kind="doubtful"),
    Choice(id="c3", text="[fake] 좋아요, 그렇게 할게요", kind="other"),
)


class FakePracticeAI:
    def __init__(self, clue_ids: tuple[str, ...] = DEFAULT_CLUE_IDS, turn_status: str = "ok") -> None:
        if not clue_ids:
            raise ValueError("clue_ids must not be empty")
        if turn_status not in _TURN_STATUSES:
            raise ValueError(f"unknown turn_status: {turn_status}")
        self.clue_ids = tuple(clue_ids)
        self.turn_status = turn_status

    def _scenario_clue_ids(self, variant: Variant | None) -> list[str]:
        return [clue.id for clue in variant.clues] if variant else list(self.clue_ids)

    def variant(self, request: VariantRequest) -> VariantResponse:
        variant = Variant(
            base_scenario_id=request.scenario_id,
            platform=request.platform,
            tone=request.tone,
            context=request.context,
            title="[fake] 연습 상황",
            child_setup="[fake] 모르는 사람이 메시지를 보냈어요.",
            opening_line="[fake] 안녕! 좋은 제안이 있어.",
            ai_role=AiRole(name="[fake] 상대", persona="[fake] 친근한 척하는 사람", tone=request.tone),
            clues=[
                ClueVariant(
                    id=clue_id,
                    at_opening=index == 0,
                    reveal_when="[fake] 대화가 이어지면",
                    reveal_line=f"[fake] 단서 {clue_id}",
                )
                for index, clue_id in enumerate(self.clue_ids)
            ],
        )
        return VariantResponse(variant=variant, source="model")

    def start(self, request: StartRequest) -> StartResponse:
        variant = request.variant
        first = self._scenario_clue_ids(variant)[0]
        return StartResponse(
            status="ok",
            reply=variant.opening_line if variant else "[fake] 안녕! 좋은 제안이 있어.",
            ai_role_name=variant.ai_role.name if variant else "[fake] 상대",
            title=variant.title if variant else "[fake] 연습 상황",
            child_setup=variant.child_setup if variant else "[fake] 모르는 사람이 메시지를 보냈어요.",
            revealed_clue_ids=[first],
            target_clue_id=first,
            choices=list(_CHOICES),
            choices_source="template",
        )

    def turn(self, request: TurnRequest) -> TurnResponse:
        scenario = self._scenario_clue_ids(request.variant)
        sent = list(request.revealed_clue_ids)
        if self.turn_status == "safe_reply":
            return TurnResponse(
                status="safe_reply",
                reply="[fake] 이야기해 줘서 고마워. 믿을 수 있는 어른에게 꼭 알려 줘.",
                revealed_clue_ids=sent,
                all_clues_revealed=set(scenario) <= set(sent),
                target_clue_id=None,
                choices=[],
                choices_source="none",
                masked=False,
                source="fixed",
            )
        next_clue = next((clue_id for clue_id in scenario if clue_id not in sent), None)
        revealed = sent + [next_clue] if next_clue else sent
        blocked = self.turn_status == "blocked"
        return TurnResponse(
            status=self.turn_status,
            reply="[fake] 그 대답은 넘어갈게. 다른 이야기를 해 보자." if blocked else f"[fake] 다음 대사 {len(request.messages)}",
            revealed_clue_ids=revealed,
            all_clues_revealed=set(scenario) <= set(revealed),
            target_clue_id=next_clue,
            choices=list(_CHOICES),
            choices_source="template" if blocked else "model",
            masked=False,
            source="fixed" if blocked else "model",
        )

    def judge(self, request: JudgeRequest) -> JudgeResponse:
        revealed = set(request.revealed_clue_ids)
        chosen_correct = {
            message.clue_id
            for message in request.messages
            if message.role == "child" and message.choice_kind == "correct"
        }
        results = []
        for clue_id in self._scenario_clue_ids(request.variant):
            if clue_id not in revealed:
                result = "not_shown"
            elif clue_id in chosen_correct:
                result = "found"
            else:
                result = "missed"
            results.append(ClueResult(clue_id=clue_id, result=result))
        return JudgeResponse(results=results, source="choices")

    def feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        cards = [
            FeedbackCard(
                clue_id=item.clue_id,
                result=item.result,
                text=f"[fake] {item.clue_id} 단서를 {'잘 찾았어요' if item.result == 'found' else '다음엔 찾아봐요'}.",
            )
            for item in request.results
            if item.result != "not_shown"
        ]
        return FeedbackResponse(cards=cards, closing_line="[fake] 끝까지 연습해서 멋져요!", source="model")


class FakeSummaryAI:
    def summary(self, request: SummaryRequest) -> SummaryResponse:
        return SummaryResponse(summary=f"[fake] {request.area} 연습을 {request.practice_count}번 했어요.")
