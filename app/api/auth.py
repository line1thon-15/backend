from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.errors import AppError
from app.core.security import SESSION_TTL_SECONDS
from app.services.auth import AuthResult, AuthService, ChildAuthResult
from app.services.ports import ChildIdentity, GuardianIdentity

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


class DisplaySettingsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    font_scale: Literal["normal", "large", "xlarge"]
    high_contrast: bool
    tts_enabled: bool


class GuardianMeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["guardian"]
    guardian_id: UUID
    email: EmailValue


class ChildMeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["child"]
    nickname: str
    grade: str
    onboarding_completed: bool
    display: DisplaySettingsResponse


MeResponse = Annotated[
    GuardianMeResponse | ChildMeResponse,
    Field(discriminator="role"),
]


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


@router.get("/auth/me", response_model=MeResponse)
def get_current_user(request: Request) -> MeResponse:
    service: AuthService = request.app.state.auth_service
    identity = service.current_identity_for_session_token(
        request.cookies.get("sid")
    )
    if identity is None:
        raise AppError(
            code="UNAUTHENTICATED",
            status_code=401,
            message="authentication is required",
        )

    if isinstance(identity, GuardianIdentity):
        return GuardianMeResponse(
            role="guardian",
            guardian_id=identity.guardian_id,
            email=identity.email,
        )

    if isinstance(identity, ChildIdentity):
        return ChildMeResponse(
            role="child",
            nickname=identity.nickname,
            grade=identity.grade,
            onboarding_completed=identity.onboarding_completed,
            display=DisplaySettingsResponse(
                font_scale=identity.font_scale,
                high_contrast=identity.high_contrast,
                tts_enabled=identity.tts_enabled,
            ),
        )

    raise AppError(
        code="UNAUTHENTICATED",
        status_code=401,
        message="authentication is required",
    )
