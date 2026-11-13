"""연습 세션 API A15·A16·A17 (T-15)·A18과 A15 다시 도전 (T-16) — Architecture "API 규격",
"응답 DTO" PracticeSessionView·TurnView·CueCard·PracticeResultView.

아이 API는 경로·본문으로 아이 ID를 받지 않는다 — 주체는 세션 쿠키에서만 꺼낸다.
공개 응답에는 선택지 `kind`·`is_terminal`·단서 ID가 없다. 결과 `cards[]`에도 단서 ID가 없다(#75 ②).
"""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import require_child_id
from app.services.practice import PracticeService, ResultOutput, SessionOutput

router = APIRouter()

Area = Literal["scam", "identity_lending", "friend_pressure"]


class StartAreaSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["area"]
    area: Area


class StartRetrySessionRequest(BaseModel):
    # 다시 도전 (T-16, F-13 ③) — 영역은 retry_of 세션 값을 쓴다
    model_config = ConfigDict(extra="forbid")

    mode: Literal["retry"]
    retry_of: UUID


# mission(F-10)은 담당 작업에서 추가 — 지금은 422
StartSessionRequest = Annotated[
    StartAreaSessionRequest | StartRetrySessionRequest,
    Field(discriminator="mode"),
]


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 길이 상한은 두지 않는다 — 현재 턴에 없는 id는 404·409 판정 뒤 서비스가 422 INVALID_CHOICE로 (리뷰 권고 #4)
    choice_id: str = Field(min_length=1)
    # 답하는 턴 번호 — A15·A16 응답의 turn.turn_index를 그대로 보낸다 (T-91, DECISIONS #128).
    # 현재 턴이 아니면 서비스가 409 TURN_ALREADY_ANSWERED. 누락·음수·문자열·실수·bool은 422 VALIDATION_ERROR.
    turn_index: int = Field(ge=0, strict=True)


class ChoiceView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str


class TurnView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_index: int
    speaker_name: str
    platform: str
    ai_line: str
    choices: list[ChoiceView]
    hint: str | None  # 1차 항상 null (#104 ④)
    substituted: bool


class PracticeSessionView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    mode: Literal["area", "mission", "retry"]
    area: Area
    is_retry: bool
    status: Literal["in_progress", "ended", "stopped"]
    turn: TurnView | None


class CueCardView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cue_id: str
    label: str
    sentence: str


class ResultCardView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["red", "yellow", "green"]
    sentence: str


class PracticeResultView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    found: list[CueCardView]
    missed: list[CueCardView]
    normal_outcome: Literal["trusted_correctly", "over_warned"] | None
    cards: list[ResultCardView]
    can_retry: bool


def _result_view(output: ResultOutput) -> PracticeResultView:
    return PracticeResultView(
        session_id=output.session_id,
        found=[CueCardView(cue_id=c.cue_id, label=c.label, sentence=c.sentence) for c in output.found],
        missed=[CueCardView(cue_id=c.cue_id, label=c.label, sentence=c.sentence) for c in output.missed],
        normal_outcome=output.normal_outcome,
        cards=[ResultCardView(level=card.level, sentence=card.sentence) for card in output.cards],
        can_retry=output.can_retry,
    )


def _view(output: SessionOutput) -> PracticeSessionView:
    turn = output.turn
    return PracticeSessionView(
        session_id=output.session_id,
        mode=output.mode,
        area=output.area,
        is_retry=output.is_retry,
        status=output.status,
        turn=(
            TurnView(
                turn_index=turn.turn_index,
                speaker_name=turn.speaker_name,
                platform=turn.platform,
                ai_line=turn.ai_line,
                choices=[ChoiceView(id=choice_id, text=text) for choice_id, text in turn.choices],
                hint=None,
                substituted=turn.substituted,
            )
            if turn is not None
            else None
        ),
    )


def _service(request: Request) -> PracticeService:
    return request.app.state.practice_service


@router.post("/practice/sessions", status_code=201, response_model=PracticeSessionView)
def start_practice_session(
    payload: StartSessionRequest,
    request: Request,
    child_id: UUID = Depends(require_child_id),
) -> PracticeSessionView:
    service = _service(request)
    if isinstance(payload, StartRetrySessionRequest):
        return _view(service.start_retry_session(child_id=child_id, retry_of=payload.retry_of))
    return _view(service.start_area_session(child_id=child_id, area=payload.area))


@router.get("/practice/sessions/{session_id}", response_model=PracticeSessionView)
def get_practice_session(
    session_id: UUID,
    request: Request,
    child_id: UUID = Depends(require_child_id),
) -> PracticeSessionView:
    return _view(_service(request).get_session(child_id=child_id, session_id=session_id))


@router.post("/practice/sessions/{session_id}/turns", response_model=PracticeSessionView)
def answer_practice_turn(
    session_id: UUID,
    payload: AnswerRequest,
    request: Request,
    child_id: UUID = Depends(require_child_id),
) -> PracticeSessionView:
    return _view(
        _service(request).answer(
            child_id=child_id,
            session_id=session_id,
            choice_id=payload.choice_id,
            turn_index=payload.turn_index,
        )
    )


@router.get("/practice/sessions/{session_id}/result", response_model=PracticeResultView)
def get_practice_result(
    session_id: UUID,
    request: Request,
    child_id: UUID = Depends(require_child_id),
) -> PracticeResultView:
    return _result_view(_service(request).get_result(child_id=child_id, session_id=session_id))
