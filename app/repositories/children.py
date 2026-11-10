from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Child
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

    def _link_code_exists(self, link_code: str) -> bool:
        query = (
            select(Child.id)
            .where(Child.link_code == link_code)
            .limit(1)
        )
        with self._session_factory() as session:
            return session.scalar(query) is not None