from app.ai_client.ports import (
    ChoiceOption,
    OpeningResult,
    ReviewResult,
    ScenarioSpec,
    TurnResult,
)


class FakePracticeAI:
    """결정적 응답을 주는 PracticeAI 구현 — 테스트·로컬·E2E 기본 (AI_CLIENT=fake)."""

    def opening(self, spec: ScenarioSpec) -> OpeningResult:
        target_ids = [cue.cue_id for cue in spec.target_cues]
        if target_ids:
            choices = [
                ChoiceOption(id="c1", text="이상해요, 확인해 볼래요", judgment="suspicious", cue_ids=target_ids),
                ChoiceOption(id="c2", text="좋아요, 그렇게 할게요", judgment="trusting", cue_ids=[]),
                ChoiceOption(id="c3", text="잠깐 생각해 볼게요", judgment="neutral", cue_ids=[]),
            ]
        else:
            choices = [
                ChoiceOption(id="c1", text="괜찮아 보여요", judgment="trusting", cue_ids=[]),
                ChoiceOption(id="c2", text="뭔가 이상해요", judgment="suspicious", cue_ids=[]),
            ]
        hint = None if spec.hint_level == 0 else f"[fake] 힌트 단계 {spec.hint_level}"
        turn = TurnResult(
            ai_line=f"[fake] {spec.situation_seed}",
            speaker_name=f"[fake] {spec.variant.persona}",
            choices=choices,
            hint=hint,
            substituted=False,
        )
        return OpeningResult(turn=turn, review=ReviewResult(passed=True, reasons=[]))
