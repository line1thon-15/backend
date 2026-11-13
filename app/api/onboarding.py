from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.api.dependencies import require_child_role
from app.core.errors import AppError
from app.services.onboarding import OnboardingService

router = APIRouter()

FontScale = Annotated[
    str,
    StringConstraints(pattern=r"^(normal|large|xlarge)$"),
]
AppType = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]
ContactName = Annotated[
    str | None,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=20),
]
ContactPhone = Annotated[
    str | None,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[0-9+\-]+$",
    ),
]
Identifier = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]


class DisplaySettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    font_scale: FontScale
    high_contrast: bool
    tts_enabled: bool


class TrustedContactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ContactName
    phone: ContactPhone = None


class DiagnosisAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: Identifier
    option_id: Identifier


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display: DisplaySettingsRequest
    trusted_contact: TrustedContactRequest
    diagnosis_answers: list[DiagnosisAnswerRequest] = Field(
        min_length=3,
        max_length=3,
    )
    favorite_apps: list[AppType] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_questions(self):
        question_ids = [answer.question_id for answer in self.diagnosis_answers]
        if len(set(question_ids)) != len(question_ids):
            raise ValueError("diagnosis answers must use distinct questions")
        return self


class OnboardingResponse(BaseModel):
    start_difficulty: int


@router.put("/me/onboarding", response_model=OnboardingResponse)
def save_onboarding(
    payload: OnboardingRequest,
    request: Request,
    child_id: UUID = Depends(require_child_role),
) -> OnboardingResponse:
    allowed_app_type_ids = {
        app_type.id
        for app_type in request.app.state.content.platform_app_types.app_types
    }
    if not set(payload.favorite_apps).issubset(allowed_app_type_ids):
        raise AppError(
            code="VALIDATION_ERROR",
            status_code=422,
            message="request validation failed",
            details={"fields": ["favorite_apps"]},
        )

    service: OnboardingService = request.app.state.onboarding_service
    start_difficulty = service.save_onboarding(
        child_id=child_id,
        font_scale=payload.display.font_scale,
        high_contrast=payload.display.high_contrast,
        tts_enabled=payload.display.tts_enabled,
        trusted_contact_name=payload.trusted_contact.name,
        trusted_contact_phone=payload.trusted_contact.phone,
        diagnosis_answers=[
            (answer.question_id, answer.option_id)
            for answer in payload.diagnosis_answers
        ],
        favorite_apps=payload.favorite_apps,
    )
    return OnboardingResponse(start_difficulty=start_difficulty)
