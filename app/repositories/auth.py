from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, MetaData, Table, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import AuthSession, Child, ChildSettings, Guardian
from app.services.ports import (
    ChildIdentity,
    ChildLoginCredentials,
    CurrentIdentity,
    GuardianCredentials,
    GuardianIdentity,
)


class SqlAlchemyAuthRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        engine: Engine,
    ) -> None:
        self._session_factory = session_factory
        self._engine = engine

    def find_guardian_by_email(self, email: str) -> GuardianCredentials | None:
        with self._session_factory() as session:
            guardian = session.scalar(
                select(Guardian).where(Guardian.email == email)
            )
            if guardian is None:
                return None
            return GuardianCredentials(
                guardian_id=guardian.id,
                password_hash=guardian.password_hash,
            )

    def create_guardian_with_session(
        self,
        email: str,
        password_hash: str,
        token_hash: str,
        expires_at: datetime,
    ) -> UUID | None:
        try:
            with self._session_factory.begin() as session:
                guardian = Guardian(email=email, password_hash=password_hash)
                session.add(guardian)
                session.flush()

                session.add(
                    AuthSession(
                        token_hash=token_hash,
                        subject_type="guardian",
                        subject_id=guardian.id,
                        expires_at=expires_at,
                    )
                )
                guardian_id = guardian.id
        except IntegrityError:
            if self.find_guardian_by_email(email) is not None:
                return None
            raise

        return guardian_id

    def create_guardian_session(
        self,
        guardian_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._session_factory.begin() as session:
            session.add(
                AuthSession(
                    token_hash=token_hash,
                    subject_type="guardian",
                    subject_id=guardian_id,
                    expires_at=expires_at,
                )
            )

    def find_guardian_id_for_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> UUID | None:
        query = (
            select(Guardian.id)
            .join(AuthSession, AuthSession.subject_id == Guardian.id)
            .where(
                AuthSession.token_hash == token_hash,
                AuthSession.subject_type == "guardian",
                AuthSession.expires_at > now,
                AuthSession.revoked_at.is_(None),
            )
        )
        with self._session_factory() as session:
            return session.scalar(query)

    def find_child_id_for_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> UUID | None:
        query = (
            select(Child.id)
            .join(AuthSession, AuthSession.subject_id == Child.id)
            .where(
                AuthSession.token_hash == token_hash,
                AuthSession.subject_type == "child",
                AuthSession.expires_at > now,
                AuthSession.revoked_at.is_(None),
            )
        )
        with self._session_factory() as session:
            return session.scalar(query)

    def find_current_user_for_active_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> CurrentIdentity | None:
        query = select(AuthSession).where(
            AuthSession.token_hash == token_hash,
            AuthSession.expires_at > now,
            AuthSession.revoked_at.is_(None),
        )
        with self._session_factory() as session:
            auth_session = session.scalar(query)
            if auth_session is None:
                return None

            if auth_session.subject_type == "guardian":
                guardian = session.get(Guardian, auth_session.subject_id)
                if guardian is None:
                    return None
                return GuardianIdentity(
                    guardian_id=guardian.id,
                    email=guardian.email,
                )

            if auth_session.subject_type != "child":
                return None

            child = session.get(Child, auth_session.subject_id)
            if child is None:
                return None
            settings = session.get(ChildSettings, child.id)

            return ChildIdentity(
                nickname=child.nickname,
                grade=child.grade,
                onboarding_completed=child.onboarding_completed_at is not None,
                font_scale=settings.font_scale if settings is not None else "normal",
                high_contrast=settings.high_contrast if settings is not None else False,
                tts_enabled=settings.tts_enabled if settings is not None else False,
            )

    def find_child_by_link_code(
        self,
        link_code: str,
    ) -> ChildLoginCredentials | None:
        with self._session_factory() as session:
            child = session.scalar(
                select(Child).where(Child.link_code == link_code)
            )
            if child is None:
                return None
            return ChildLoginCredentials(
                child_id=child.id,
                pin_hash=child.pin_hash,
                first_login=child.onboarding_completed_at is None,
            )

    def create_child_session(
        self,
        child_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._session_factory.begin() as session:
            session.add(
                AuthSession(
                    token_hash=token_hash,
                    subject_type="child",
                    subject_id=child_id,
                    expires_at=expires_at,
                )
            )

    def has_children(self, guardian_id: UUID) -> bool:
        if not inspect(self._engine).has_table("children"):
            return False

        children = Table("children", MetaData(), autoload_with=self._engine)
        query = (
            select(children.c.guardian_id)
            .where(children.c.guardian_id == guardian_id)
            .limit(1)
        )

        with self._session_factory() as session:
            return session.scalar(query) is not None