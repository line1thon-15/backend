from datetime import datetime, timezone
from uuid import UUID

from app.core.errors import AppError
from app.services.ports import OnboardingRepository

# The screenshot's three choices describe increasing comfort with risky situations.
# Higher risk scores start at an easier level and therefore receive more support.
OPTION_RISK_SCORE = {
    "agree": 2,
    "yes": 2,
    "그래요": 2,
    "sometimes": 1,
    "가끔": 1,
    "no": 0,
    "disagree": 0,
    "아니에요": 0,
}


class OnboardingService:
    def __init__(self, repository: OnboardingRepository) -> None:
        self._repository = repository

    def save_onboarding(
        self,
        *,
        child_id: UUID,
        font_scale: str,
        high_contrast: bool,
        tts_enabled: bool,
        trusted_contact_name: str | None,
        trusted_contact_phone: str | None,
        diagnosis_answers: list[tuple[str, str]],
        favorite_apps: list[str],
    ) -> int:
        if font_scale not in {"normal", "large", "xlarge"}:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["display.font_scale"]},
            )

        if len(diagnosis_answers) != 3:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["diagnosis_answers"]},
            )

        question_ids = [question_id for question_id, _ in diagnosis_answers]
        if len(set(question_ids)) != 3:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["diagnosis_answers"]},
            )

        risk_score = 0
        for _, option_id in diagnosis_answers:
            normalized_option = option_id.strip()
            score = OPTION_RISK_SCORE.get(
                normalized_option,
                OPTION_RISK_SCORE.get(normalized_option.casefold()),
            )
            if score is None:
                raise AppError(
                    code="VALIDATION_ERROR",
                    status_code=422,
                    message="request validation failed",
                    details={"fields": ["diagnosis_answers"]},
                )
            risk_score += score

        if risk_score >= 5:
            start_difficulty = 1
        elif risk_score >= 2:
            start_difficulty = 2
        else:
            start_difficulty = 3

        normalized_name = (
            trusted_contact_name.strip() if trusted_contact_name else None
        ) or None
        normalized_phone = (
            trusted_contact_phone.strip() if trusted_contact_phone else None
        ) or None

        saved = self._repository.save_onboarding(
            child_id=child_id,
            font_scale=font_scale,
            high_contrast=high_contrast,
            tts_enabled=tts_enabled,
            trusted_contact_name=normalized_name,
            trusted_contact_phone=normalized_phone,
            favorite_apps=favorite_apps,
            start_difficulty=start_difficulty,
            completed_at=datetime.now(timezone.utc),
        )
        if not saved:
            raise AppError(
                code="UNAUTHENTICATED",
                status_code=401,
                message="child authentication is required",
            )

        return start_difficulty
