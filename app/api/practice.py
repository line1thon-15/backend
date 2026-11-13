"""연습 세션 API A15·A16·A17 (T-15 — Architecture "API 규격", "응답 DTO" PracticeSessionView·TurnView).

아이 API는 경로·본문으로 아이 ID를 받지 않는다 — 주체는 세션 쿠키에서만 꺼낸다.
공개 응답에는 선택지 `kind`·`is_terminal`·단서 ID가 없다.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import require_child_id
from app.services.practice import PracticeService, SessionOutput

router = APIRouter()

Area = Literal["scam", "identity_lending", "friend_pressure"]


class StartAreaSessionRequest(BaseModel):
    # 1차 T-15는 영역 출제만 — mission(F-10)·retry(F-13 ③)는 담당 작업에서 추가
    model_config = ConfigDict(extra="forbid")

    mode: Literal["area"]
    area: Area


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # 길이 상한은 두지 않는다 — 현재 턴에 없는 id는 404·409 판정 뒤 서비스가 422 INVALID_CHOICE로 (리뷰 권고 #4)
    choice_id: str = Field(min_length=1)


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
    payload: StartAreaSessionRequest,
    request: Request,
    child_id: UUID = Depends(require_child_id),
) -> PracticeSessionView:
    return _view(_service(request).start_area_session(child_id=child_id, area=payload.area))


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
        _service(request).answer(child_id=child_id, session_id=session_id, choice_id=payload.choice_id)
    )
