"""백엔드–AI 내부 API 포트와 DTO (Architecture "백엔드–AI 내부 API")."""

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

Area = Literal["scam", "name_lending", "friend_request"]
ScamSubtype = Literal["game_item", "allowance", "high_paying_job"]
GradeBand = Literal["elementary", "middle", "high"]
ChoiceJudgment = Literal["suspicious", "trusting", "neutral"]


class _OutboundModel(BaseModel):
    # AI 서비스로 나가는 값 — 규격에 없는 필드(아이 식별 정보 등)가 실리지 않게 거부한다 (N-05).
    model_config = ConfigDict(extra="forbid", frozen=True)


class TargetCue(_OutboundModel):
    cue_id: str
    label: str
    explanation: str


class Variant(_OutboundModel):
    tone: str
    platform: str
    persona: str


class ScenarioSpec(_OutboundModel):
    scenario_id: str
    area: Area
    subtype: ScamSubtype | None
    is_normal: bool
    target_cues: list[TargetCue]
    situation_seed: str
    variant: Variant
    grade_band: GradeBand
    difficulty: int | None
    hint_level: int = Field(ge=0)


class ChoiceOption(BaseModel):
    id: str
    text: str
    judgment: ChoiceJudgment
    cue_ids: list[str]


class TurnResult(BaseModel):
    ai_line: str
    speaker_name: str
    choices: list[ChoiceOption] = Field(min_length=2, max_length=4)
    hint: str | None
    is_terminal: bool
    substituted: bool


class ReviewResult(BaseModel):
    passed: bool
    reasons: list[str]


class OpeningResult(BaseModel):
    turn: TurnResult
    review: ReviewResult


@runtime_checkable
class PracticeAI(Protocol):
    def opening(self, spec: ScenarioSpec) -> OpeningResult: ...
