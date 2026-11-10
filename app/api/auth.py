from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.security import SESSION_TTL_SECONDS
from app.services.auth import AuthResult, AuthService, ChildAuthResult

router = APIRouter()

EmailValue = Annotated[EmailStr, Field(max_length=254)]
PasswordValue = Annotated[str, StringConstraints(min_length=8, max_length=128)]
LinkCodeValue = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=6,
        max_length=6,
        pattern=r"^[A-Za-z0-9]{6}$",
    ),
]
PinValue = Annotated[
    str,
    StringConstraints(min_length=4, max_length=4, pattern=r"^[0-9]{4}$"),
]


class GuardianCredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailValue
    password: PasswordValue


class ChildLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_code: LinkCodeValue
    pin: PinValue


class GuardianCreatedResponse(BaseModel):
    guardian_id: UUID


class GuardianLoginResponse(BaseModel):
    guardian_id: UUID
    has_children: bool


class ChildLoginResponse(BaseModel):
    first_login: bool


def _set_session_cookie(
    response: Response,
    request: Request,
    session_token: str,
) -> None:
    settings = request.app.state.settings
    response.set_cookie(
        key="sid",
        value=session_token,
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
    _set_session_cookie(response, request, result.session_token)
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
    _set_session_cookie(response, request, result.session_token)
    return GuardianLoginResponse(
        guardian_id=result.guardian_id,
        has_children=result.has_children,
    )


@router.post(
    "/auth/child/login",
    response_model=ChildLoginResponse,
)
def login_child(
    payload: ChildLoginRequest,
    request: Request,
    response: Response,
) -> ChildLoginResponse:
    service: AuthService = request.app.state.auth_service
    result: ChildAuthResult = service.login_child(
        payload.link_code,
        payload.pin,
    )
    _set_session_cookie(response, request, result.session_token)
    return ChildLoginResponse(first_login=result.first_login)