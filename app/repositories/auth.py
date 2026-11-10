from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, MetaData, Table, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import AuthSession, Guardian
from app.services.ports import GuardianCredentials


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