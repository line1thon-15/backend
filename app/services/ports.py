from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


class DatabaseProbe(Protocol):
    def ping(self) -> bool: ...


@dataclass(frozen=True)
class GuardianCredentials:
    guardian_id: UUID
    password_hash: str


class AuthRepository(Protocol):
    def find_guardian_by_email(self, email: str) -> GuardianCredentials | None: ...

    def create_guardian_with_session(
        self,
        email: str,
        password_hash: str,
        token_hash: str,
        expires_at: datetime,
    ) -> UUID | None: ...

    def create_guardian_session(
        self,
        guardian_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...

    def has_children(self, guardian_id: UUID) -> bool: ...