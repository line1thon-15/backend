from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import AuthSession, Child
from app.services.ports import (
    ChildRegistrationRecord,
    ChildSummary,
    ChildrenRepository,
)


class SqlAlchemyChildrenRepository(ChildrenRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_child(
        self,
        guardian_id: UUID,
        nickname: str,
        grade: str,
        pin_hash: str,
        consent_version: str,
        link_code: str,
    ) -> ChildRegistrationRecord | None:
        try:
            with self._session_factory.begin() as session:
                child = Child(
                    guardian_id=guardian_id,
                    nickname=nickname,
                    grade=grade,
                    pin_hash=pin_hash,
                    consent_version=consent_version,
                    link_code=link_code,
                )
                session.add(child)
                session.flush()
                record = ChildRegistrationRecord(
                    child_id=child.id,
                    nickname=child.nickname,
                    grade=child.grade,
                    link_code=child.link_code,
                )
        except IntegrityError:
            if self._link_code_exists(link_code):
                return None
            raise

        return record

    def list_children_for_guardian(
        self,
        guardian_id: UUID,
    ) -> list[ChildSummary]:
        query = (
            select(Child)
            .where(Child.guardian_id == guardian_id)
            .order_by(Child.created_at, Child.id)
        )
        with self._session_factory() as session:
            children = session.scalars(query).all()
            return [
                ChildSummary(
                    child_id=child.id,
                    nickname=child.nickname,
                    grade=child.grade,
                )
                for child in children
            ]

    def reset_child_pin(
        self,
        guardian_id: UUID,
        child_id: UUID,
        pin_hash: str,
        revoked_at: datetime,
    ) -> bool:
        with self._session_factory.begin() as session:
            result = session.execute(
                update(Child)
                .where(
                    Child.id == child_id,
                    Child.guardian_id == guardian_id,
                )
                .values(pin_hash=pin_hash)
            )
            if result.rowcount == 0:
                return False

            session.execute(
                update(AuthSession)
                .where(
                    AuthSession.subject_type == "child",
                    AuthSession.subject_id == child_id,
                    AuthSession.revoked_at.is_(None),
                )
                .values(revoked_at=revoked_at)
            )
        return True

    def replace_child_link_code(
        self,
        guardian_id: UUID,
        child_id: UUID,
        link_code: str,
        revoked_at: datetime,
    ) -> bool | None:
        try:
            with self._session_factory.begin() as session:
                result = session.execute(
                    update(Child)
                    .where(
                        Child.id == child_id,
                        Child.guardian_id == guardian_id,
                    )
                    .values(link_code=link_code)
                )
                if result.rowcount == 0:
                    return False

                session.execute(
                    update(AuthSession)
                    .where(
                        AuthSession.subject_type == "child",
                        AuthSession.subject_id == child_id,
                        AuthSession.revoked_at.is_(None),
                    )
                    .values(revoked_at=revoked_at)
                )
        except IntegrityError:
            if self._link_code_exists(link_code):
                return None
            raise

        return True

    def _link_code_exists(self, link_code: str) -> bool:
        query = (
            select(Child.id)
            .where(Child.link_code == link_code)
            .limit(1)
        )
        with self._session_factory() as session:
            return session.scalar(query) is not None