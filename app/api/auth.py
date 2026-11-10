from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.security import SESSION_TTL_SECONDS
from app.services.auth import AuthResult, AuthService

router = APIRouter()

EmailValue = Annotated[EmailStr, Field(max_length=254)]
PasswordValue = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class GuardianCredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailValue
    password: PasswordValue


class GuardianCreatedResponse(BaseModel):
    guardian_id: UUID


class GuardianLoginResponse(BaseModel):
    guardian_id: UUID
    has_children: bool


def _set_session_cookie(
    response: Response,
    request: Request,
    result: AuthResult,
) -> None:
    settings = request.app.state.settings
    response.set_cookie(
        key="sid",
        value=result.session_token,
        max_age=SESSION_TTL_SECONDS,
        path="/api",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post(
    "/guardians",
    status_code=status.HTTP_201_CREATED,
    response_model=GuardianCreatedResponse,
)
def register_guardian(
    payload: GuardianCredentialsRequest,
    request: Request,
    response: Response,
) -> GuardianCreatedResponse:
    service: AuthService = request.app.state.auth_service
    result = service.register_guardian(payload.email, payload.password)
    _set_session_cookie(response, request, result)
    return GuardianCreatedResponse(guardian_id=result.guardian_id)


@router.post(
    "/auth/guardian/login",
    response_model=GuardianLoginResponse,
)
def login_guardian(
    payload: GuardianCredentialsRequest,
    request: Request,
    response: Response,
) -> GuardianLoginResponse:
    service: AuthService = request.app.state.auth_service
    result = service.login_guardian(payload.email, payload.password)
    _set_session_cookie(response, request, result)
    return GuardianLoginResponse(
        guardian_id=result.guardian_id,
        has_children=result.has_children,
    )