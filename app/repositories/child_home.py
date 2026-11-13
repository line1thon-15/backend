"""아이 홈(A13) 믿는 사람 연락처 조회 Repository (T-90) — SQL·ORM 코드는 여기에만 (Architecture "계층 규칙").

읽기 전용. 원천은 첫 설정(A12)이 저장한 `child_settings.trusted_contact_name`·`trusted_contact_phone`.
이름·번호 중 하나라도 비어 있으면 None — 반쪽 값을 만들지 않는다(A13 `trusted_contact:{name, phone}|null`).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ChildSettings
from app.services.child_views import TrustedContact, TrustedContactRepository


class SqlAlchemyTrustedContactRepository(TrustedContactRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def trusted_contact(self, child_id: UUID) -> TrustedContact | None:
        statement = select(ChildSettings.trusted_contact_name, ChildSettings.trusted_contact_phone).where(
            ChildSettings.child_id == child_id
        )
        with self._session_factory() as db:
            row = db.execute(statement).one_or_none()
        if row is None:
            return None
        name, phone = row
        if not name or not phone:
            return None
        return TrustedContact(name=name, phone=phone)
