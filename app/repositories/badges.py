"""배지·연속 기록 조회 Repository (T-45) — SQL·ORM 코드는 여기에만 (Architecture "계층 규칙").

읽기 전용. 종료(`status = ended`) 세션만 돌려준다 — `in_progress`·`stopped`(#113·#119)는 모든 규칙에서 제외.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import CueResult, PracticeSession
from app.services.badges import BadgeRepository, EndedSessionRecord


def _as_utc(moment: datetime) -> datetime:
    # SQLite는 시간대를 저장하지 않아 naive로 돌아온다 — 저장 규칙상 UTC(Architecture "시각" 행)
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


class SqlAlchemyBadgeRepository(BadgeRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def ended_sessions(self, child_id: UUID) -> list[EndedSessionRecord]:
        found = func.coalesce(func.sum(case((CueResult.outcome == "found", 1), else_=0)), 0)
        missed = func.coalesce(func.sum(case((CueResult.outcome == "missed", 1), else_=0)), 0)
        statement = (
            select(
                PracticeSession.area,
                PracticeSession.is_normal,
                PracticeSession.ended_at,
                found,
                missed,
            )
            .outerjoin(CueResult, CueResult.session_id == PracticeSession.id)
            .where(
                PracticeSession.child_id == child_id,
                PracticeSession.status == "ended",
                PracticeSession.ended_at.is_not(None),
            )
            .group_by(
                PracticeSession.id,
                PracticeSession.area,
                PracticeSession.is_normal,
                PracticeSession.ended_at,
            )
        )
        with self._session_factory() as db:
            rows = db.execute(statement).all()
        return [
            EndedSessionRecord(
                area=area,
                is_normal=is_normal,
                ended_at=_as_utc(ended_at),
                found_count=int(found_count),
                missed_count=int(missed_count),
            )
            for area, is_normal, ended_at, found_count, missed_count in rows
        ]
