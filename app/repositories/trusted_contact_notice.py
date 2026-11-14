"""믿는 사람 연락 알림 쓰기 Repository (T-40) — SQL·ORM 코드는 여기에만 (Architecture "계층 규칙").

guardian_notices에 `kind = trusted_contact`, `level`·`area` NULL, `channel` 값, `origin = live`로 한 행을 넣는다
(테이블·CHECK 제약은 T-25 — 이 작업은 쓰기만 한다).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import GuardianNotice
from app.services.trusted_contact import ContactChannel, TrustedContactNoticeRepository


class SqlAlchemyTrustedContactNoticeRepository(TrustedContactNoticeRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add_trusted_contact_notice(self, child_id: UUID, channel: ContactChannel, occurred_at: datetime) -> None:
        with self._session_factory.begin() as db:
            db.add(
                GuardianNotice(
                    child_id=child_id,
                    kind="trusted_contact",
                    level=None,
                    area=None,
                    channel=channel,
                    origin="live",
                    occurred_at=occurred_at,
                )
            )
