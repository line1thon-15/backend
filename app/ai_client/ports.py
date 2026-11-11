"""백엔드–AI 내부 API 포트와 DTO (Architecture "1차 내부 API v1", DECISIONS #96·#97·#104·#112·#115, ADR-0017).

필드는 AI 계약(ai 저장소 feature/ai 331d2c6 `contracts/`)과 같다. 응답 검증 규칙(VA·ST·TU·J'·V'·S)은
이 모델이 아니라 HttpPracticeAI·services 쪽 몫이다(T-15·T-16·T-76).
"""

from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator

Area = Literal["scam", "identity_lending", "friend_pressure"]
ScamSubtype = Literal["game_item", "allowance", "high_paying_job"]
GradeBand = Literal["elementary", "middle", "high"]

ChoiceKind = Literal["correct", "doubtful", "other"]
ClueResultValue = Literal["found", "missed", "not_shown"]
ChoicesSource = Literal["model", "template", "none"]

ScenarioId = Annotated[str, Field(min_length=1, max_length=64)]


class _OutboundModel(BaseModel):
    # AI 서비스로 나가는 값 — 규격에 없는 필드(아이 식별 정보 등)가 실리지 않게 거부한다 (N-05).
    model_config = ConfigDict(extra="forbid", frozen=True)


class _InboundModel(BaseModel):
    # AI 서비스에서 받는 값 — 하위 호환 선택 필드 추가에 깨지지 않게 모르는 필드는 버린다.
    model_config = ConfigDict(frozen=True)


# ---- 공통 -------------------------------------------------------------------


class Message(_OutboundModel):
    role: Literal["ai", "child"]
    text: str = Field(min_length=1, max_length=500)
    # 아이가 고른 답: 고른 선택지 kind, 그 턴의 target_clue_id (#98)
    choice_kind: ChoiceKind | None = None
    clue_id: str | None = Field(default=None, max_length=64)


class Choice(_InboundModel):
    id: str
    text: str
    kind: ChoiceKind


class AiRole(_InboundModel):
    name: str = Field(min_length=1, max_length=40)
    persona: str = Field(min_length=1, max_length=300)
    tone: str = Field(min_length=1, max_length=100)


class ClueVariant(_InboundModel):
    id: str = Field(min_length=1, max_length=64)
    at_opening: bool = False
    reveal_when: str = Field(min_length=1, max_length=100)
    reveal_line: str = Field(min_length=1, max_length=200)


class Variant(_InboundModel):
    # 양방향: variant 응답으로 받아 그대로 저장하고 같은 세션의 이후 요청에 그대로 보낸다 (#98).
    base_scenario_id: str = Field(min_length=1, max_length=64)
    platform: str = Field(min_length=1, max_length=40)
    tone: str = Field(min_length=1, max_length=100)
    context: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=80)
    child_setup: str = Field(min_length=1, max_length=300)
    opening_line: str = Field(min_length=1, max_length=200)
    ai_role: AiRole
    clues: list[ClueVariant] = Field(min_length=1, max_length=10)


class ClueResult(_InboundModel):
    clue_id: str = Field(min_length=1, max_length=64)
    result: ClueResultValue


# ---- POST /internal/v1/practice/variant -------------------------------------


class VariantRequest(_OutboundModel):
    scenario_id: ScenarioId
    # 백엔드는 세 값을 항상 채운다 — domain이 시나리오 variation_axes에서 선택 (#102)
    platform: str
    tone: str
    context: str


class VariantResponse(_InboundModel):
    variant: Variant
    source: Literal["model", "fallback"]


# ---- POST /internal/v1/practice/start ---------------------------------------


class StartRequest(_OutboundModel):
    scenario_id: ScenarioId
    variant: Variant | None = None


class StartResponse(_InboundModel):
    status: Literal["ok"]
    reply: str
    ai_role_name: str
    title: str
    child_setup: str
    revealed_clue_ids: list[str]
    target_clue_id: str | None
    choices: list[Choice]
    choices_source: ChoicesSource


# ---- POST /internal/v1/practice/turn ----------------------------------------


class TurnRequest(_OutboundModel):
    scenario_id: ScenarioId
    messages: list[Message] = Field(min_length=1, max_length=40)
    revealed_clue_ids: list[str] = Field(default_factory=list, max_length=20)
    variant: Variant | None = None

    @field_validator("messages")
    @classmethod
    def _last_is_child(cls, messages: list[Message]) -> list[Message]:
        if messages[-1].role != "child":
            raise ValueError("마지막 메시지는 아이의 답이어야 합니다")
        return messages


class TurnResponse(_InboundModel):
    status: Literal["ok", "safe_reply", "blocked"]
    reply: str
    revealed_clue_ids: list[str]
    # all_clues_revealed·masked·choices_source는 참고값 — 종료·검증 입력이 아니다 (F-11 ⑥, #96)
    all_clues_revealed: bool
    target_clue_id: str | None
    choices: list[Choice]
    choices_source: ChoicesSource
    masked: bool
    source: Literal["model", "fallback", "fixed"]


# ---- POST /internal/v1/practice/judge ---------------------------------------


class JudgeRequest(_OutboundModel):
    scenario_id: ScenarioId
    messages: list[Message] = Field(min_length=1, max_length=40)
    revealed_clue_ids: list[str] = Field(default_factory=list, max_length=20)
    variant: Variant | None = None


class JudgeResponse(_InboundModel):
    results: list[ClueResult]
    source: Literal["choices", "model", "fallback", "fixed"]


# ---- POST /internal/v1/practice/feedback ------------------------------------


class FeedbackRequest(_OutboundModel):
    scenario_id: ScenarioId
    results: list[ClueResult] = Field(min_length=1, max_length=20)
    messages: list[Message] = Field(default_factory=list, max_length=40)
    variant: Variant | None = None


class FeedbackCard(_InboundModel):
    clue_id: str
    result: Literal["found", "missed"]
    text: str


class FeedbackResponse(_InboundModel):
    cards: list[FeedbackCard]
    closing_line: str
    source: Literal["model", "fallback", "mixed", "fixed"]


# ---- POST /internal/v1/summary ----------------------------------------------


class SummaryRequest(_OutboundModel):
    area: str  # 영역 표시 이름(콘텐츠 areas[].name) — Area ID가 아니다
    practice_count: int = Field(ge=0)
    found_clues: list[str] = Field(default_factory=list)
    missed_clues: list[str] = Field(default_factory=list)
    growth_level: str | None = None  # 백엔드는 항상 null로 보낸다 (F-29 ③, G1)


class SummaryResponse(_InboundModel):
    summary: str | None


# ---- 포트 -------------------------------------------------------------------


@runtime_checkable
class PracticeAI(Protocol):
    def variant(self, request: VariantRequest) -> VariantResponse: ...

    def start(self, request: StartRequest) -> StartResponse: ...

    def turn(self, request: TurnRequest) -> TurnResponse: ...

    def judge(self, request: JudgeRequest) -> JudgeResponse: ...

    def feedback(self, request: FeedbackRequest) -> FeedbackResponse: ...


@runtime_checkable
class SummaryAI(Protocol):
    def summary(self, request: SummaryRequest) -> SummaryResponse: ...
