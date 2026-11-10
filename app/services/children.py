import secrets
from uuid import UUID

from app.core.errors import AppError
from app.core.security import hash_password
from app.services.ports import (
    ChildRegistrationRecord,
    ChildSummary,
    ChildrenRepository,
)

LINK_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
LINK_CODE_LENGTH = 6
MAX_LINK_CODE_ATTEMPTS = 5
VALID_GRADES = frozenset({"E6", "M1", "M2", "M3", "H1", "H2", "H3"})


class ChildrenService:
    def __init__(self, repository: ChildrenRepository) -> None:
        self._repository = repository

    def register_child(
        self,
        guardian_id: UUID,
        consent_agreed: bool,
        consent_version: str,
        nickname: str,
        grade: str,
        pin: str,
    ) -> ChildRegistrationRecord:
        if not consent_agreed:
            raise AppError(
                code="CONSENT_REQUIRED",
                status_code=422,
                message="required consent must be accepted",
            )

        normalized_nickname = nickname.strip()
        normalized_version = consent_version.strip()
        if not normalized_nickname:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["nickname"]},
            )
        if not normalized_version:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["consent_version"]},
            )
        if grade not in VALID_GRADES:
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["grade"]},
            )
        if len(pin) != 4 or not pin.isascii() or not pin.isdigit():
            raise AppError(
                code="VALIDATION_ERROR",
                status_code=422,
                message="request validation failed",
                details={"fields": ["pin"]},
            )

        pin_hash = hash_password(pin)
        for _ in range(MAX_LINK_CODE_ATTEMPTS):
            link_code = "".join(
                secrets.choice(LINK_CODE_ALPHABET)
                for _ in range(LINK_CODE_LENGTH)
            )
            child = self._repository.create_child(
                guardian_id=guardian_id,
                nickname=normalized_nickname,
                grade=grade,
                pin_hash=pin_hash,
                consent_version=normalized_version,
                link_code=link_code,
            )
            if child is not None:
                return child

        raise AppError(
            code="INTERNAL",
            status_code=500,
            message="could not issue child login code",
        )

    def list_children(self, guardian_id: UUID) -> list[ChildSummary]:
        return self._repository.list_children_for_guardian(guardian_id)