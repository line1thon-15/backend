from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.errors import AppError
from app.core.security import (
    SESSION_TTL_SECONDS,
    create_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.services.ports import AuthRepository


@dataclass(frozen=True)
class AuthResult:
    guardian_id: UUID
    session_token: str
    has_children: bool


@dataclass(frozen=True)
class ChildAuthResult:
    session_token: str
    first_login: bool


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    def register_guardian(self, email: str, password: str) -> AuthResult:
        normalized_email = email.strip().casefold()
        password_hash = hash_password(password)
        token, token_hash = create_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=SESSION_TTL_SECONDS
        )

        guardian_id = self._repository.create_guardian_with_session(
            email=normalized_email,
            password_hash=password_hash,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        if guardian_id is None:
            raise AppError(
                code="EMAIL_TAKEN",
                status_code=409,
                message="guardian email already exists",
            )

        return AuthResult(
            guardian_id=guardian_id,
            session_token=token,
            has_children=False,
        )

    def login_guardian(self, email: str, password: str) -> AuthResult:
        normalized_email = email.strip().casefold()
        guardian = self._repository.find_guardian_by_email(normalized_email)

        if guardian is None or not verify_password(password, guardian.password_hash):
            raise AppError(
                code="INVALID_CREDENTIALS",
                status_code=401,
                message="email or password is incorrect",
            )

        token, token_hash = create_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=SESSION_TTL_SECONDS
        )

        self._repository.create_guardian_session(
            guardian_id=guardian.guardian_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return AuthResult(
            guardian_id=guardian.guardian_id,
            session_token=token,
            has_children=self._repository.has_children(guardian.guardian_id),
        )

    def login_child(self, link_code: str, pin: str) -> ChildAuthResult:
        normalized_link_code = link_code.strip().upper()
        child = self._repository.find_child_by_link_code(normalized_link_code)

        if child is None or not verify_password(pin, child.pin_hash):
            raise AppError(
                code="INVALID_CODE_OR_PIN",
                status_code=401,
                message="link code or PIN is incorrect",
            )

        token, token_hash = create_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=SESSION_TTL_SECONDS
        )
        self._repository.create_child_session(
            child_id=child.child_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return ChildAuthResult(
            session_token=token,
            first_login=child.first_login,
        )

    def guardian_id_for_session_token(self, session_token: str) -> UUID | None:
        return self._repository.find_guardian_id_for_active_session(
            hash_session_token(session_token),
            datetime.now(timezone.utc),
        )

    def child_id_for_session_token(self, session_token: str) -> UUID | None:
        return self._repository.find_child_id_for_active_session(
            hash_session_token(session_token),
            datetime.now(timezone.utc),
        )