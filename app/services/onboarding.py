from datetime import datetime, timezone
from uuid import UUID

from app.content.schemas import DiagnosisFile
from app.core.errors import AppError
from app.services.ports import OnboardingRepository


class OnboardingService:
    def __init__(
        self,
        repository: OnboardingRepository,
        diagnosis: DiagnosisFile,
    ) -> None:
        self._repository = repository
        self._diagnosis = diagnosis

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

        questions = {question.id: question for question in self._diagnosis.questions}
        if len(diagnosis_answers) != len(questions):
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["diagnosis_answers"]},
            )

        question_ids = [question_id for question_id, _ in diagnosis_answers]
        if len(set(question_ids)) != len(question_ids):
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["diagnosis_answers"]},
            )

        total_score = 0
        for question_id, option_id in diagnosis_answers:
            question = questions.get(question_id)
            if question is None:
                raise AppError(
                    code="VALIDATION_ERROR",
                    status_code=422,
                    message="request validation failed",
                    details={"fields": ["diagnosis_answers"]},
                )

            option = next(
                (item for item in question.options if item.id == option_id),
                None,
            )
            if option is None:
                raise AppError(
                    code="VALIDATION_ERROR",
                    status_code=422,
                    message="request validation failed",
                    details={"fields": ["diagnosis_answers"]},
                )
            total_score += option.score

        start_difficulty = next(
            (
                item.difficulty
                for item in self._diagnosis.difficulty_by_score
                if item.min_score <= total_score <= item.max_score
            ),
            None,
        )
        if start_difficulty is None:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["diagnosis_answers"]},
            )

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
