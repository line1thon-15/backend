"""믿는 사람 연락 기록 A14 `POST /me/trusted-contact-events` (T-40 — F-23 ③).

Architecture "API 규격" A14: 요청 `{channel:"call"|"sms"}` → 200 `{ok: true}`, guardian_notices에 `trusted_contact` 기록.
인가: 아이 세션만 — 미로그인·무효 세션 401 `UNAUTHENTICATED`, 보호자 세션 403 `FORBIDDEN_ROLE`(Architecture "역할 분리").
대상 아이는 세션에서만 정한다. 요청은 채널 하나만 받는다(추가 필드 금지 — 연락처·원문이 들어올 자리가 없다).
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import require_child_role
from app.services.trusted_contact import TrustedContactEventService

router = APIRouter()


class TrustedContactEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Literal["call", "sms"]


class OkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: Literal[True]


@router.post("/me/trusted-contact-events", response_model=OkResponse)
def record_trusted_contact_event(
    body: TrustedContactEventRequest,
    request: Request,
    child_id: UUID = Depends(require_child_role),
) -> OkResponse:
    service: TrustedContactEventService = request.app.state.trusted_contact_event_service
    service.record(child_id, body.channel)
    return OkResponse(ok=True)
