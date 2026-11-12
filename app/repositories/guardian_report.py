"""보호자 리포트 조회 (T-25). practice_turns는 읽지 않는다 — 필요한 열만 SELECT (F-30 ③)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Child, CueResult, PracticeSession
from app.domain.guardian_report import CueOutcome, EndedSession
from app.services.ports import GuardianReportRepository, ReportChild


def _as_utc(moment: datetime) -> datetime:
    # SQLite는 timezone 정보 없이 돌려준다 — 저장값은 UTC (Architecture 공통 값 타입 "시각")
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


class SqlAlchemyGuardianReportRepository(GuardianReportRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_owned_child(self, guardian_id: UUID, child_id: UUID) -> ReportChild | None:
        query = select(Child.id, Child.nickname).where(Child.id == child_id, Child.guardian_id == guardian_id)
        with self._session_factory() as session:
            row = session.execute(query).first()
        return None if row is None else ReportChild(child_id=row.id, nickname=row.nickname)

    def ended_sessions(self, child_id: UUID) -> list[EndedSession]:
        query = select(PracticeSession.area, PracticeSession.ended_at).where(
            PracticeSession.child_id == child_id,
            PracticeSession.status == "ended",
        )
        with self._session_factory() as session:
            rows = session.execute(query).all()
        return [EndedSession(area=row.area, ended_at=_as_utc(row.ended_at)) for row in rows]

    def ended_cue_outcomes(self, child_id: UUID) -> list[CueOutcome]:
        query = (
            select(CueResult.cue_id, CueResult.outcome, PracticeSession.ended_at)
            .join(PracticeSession, PracticeSession.id == CueResult.session_id)
            .where(
                CueResult.child_id == child_id,
                PracticeSession.child_id == child_id,
                PracticeSession.status == "ended",
            )
        )
        with self._session_factory() as session:
            rows = session.execute(query).all()
        return [CueOutcome(cue_id=row.cue_id, outcome=row.outcome, at=_as_utc(row.ended_at)) for row in rows]
