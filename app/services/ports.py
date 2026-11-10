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


@dataclass(frozen=True)
class ChildLoginCredentials:
    child_id: UUID
    pin_hash: str
    first_login: bool


@dataclass(frozen=True)
class ChildRegistrationRecord:
    child_id: UUID
    nickname: str
    grade: str
    link_code: str


@dataclass(frozen=True)
class ChildSummary:
    child_id: UUID
    nickname: str
    grade: str


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

    def find_guardian_id_for_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> UUID | None: ...

    def find_child_by_link_code(
        self,
        link_code: str,
    ) -> ChildLoginCredentials | None: ...

    def create_child_session(
        self,
        child_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...

    def has_children(self, guardian_id: UUID) -> bool: ...


class ChildrenRepository(Protocol):
    def create_child(
        self,
        guardian_id: UUID,
        nickname: str,
        grade: str,
        pin_hash: str,
        consent_version: str,
        link_code: str,
    ) -> ChildRegistrationRecord | None: ...

    def list_children_for_guardian(
        self,
        guardian_id: UUID,
    ) -> list[ChildSummary]: ...