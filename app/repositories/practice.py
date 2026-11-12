"""연습 세션 Repository (T-15) — SQL·ORM 코드는 여기에만 (Architecture "계층 규칙").

A17의 저장은 메서드 하나 = 한 트랜잭션이다(DECISIONS #82·#85). 서비스는 AI 호출과 응답 검증이 성공한 뒤에만 부른다.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Child, ChildSettings, CueResult, PracticeSession, PracticeTurn
from app.services.ports import (
    NewCueResult,
    NewPracticeSession,
    NewPracticeTurn,
    PracticeChildProfile,
    PracticeRepository,
    PracticeSessionRecord,
    PracticeTurnRecord,
)


def _turn_row(session_id: UUID, turn: NewPracticeTurn) -> PracticeTurn:
    return PracticeTurn(
        session_id=session_id,
        turn_index=turn.turn_index,
        ai_line=turn.ai_line,
        choices=[dict(choice) for choice in turn.choices],
        chosen_choice_id=None,
        substituted=turn.substituted,
        target_clue_id=turn.target_clue_id,
        revealed_clue_ids=list(turn.revealed_clue_ids),
        ai_status=turn.ai_status,
    )


class SqlAlchemyPracticeRepository(PracticeRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_child_profile(self, child_id: UUID) -> PracticeChildProfile | None:
        with self._session_factory() as db:
            child = db.get(Child, child_id)
            if child is None:
                return None
            settings = db.get(ChildSettings, child_id)
            favorite_apps = tuple(settings.favorite_apps) if settings is not None else ()
            return PracticeChildProfile(grade=child.grade, favorite_apps=favorite_apps)

    def latest_variant_axes(
        self,
        child_id: UUID,
        scenario_ids: list[str],
    ) -> dict[str, tuple[str, str]]:
        if not scenario_ids:
            return {}
        with self._session_factory() as db:
            rows = db.execute(
                select(PracticeSession.scenario_id, PracticeSession.variant)
                .where(
                    PracticeSession.child_id == child_id,
                    PracticeSession.scenario_id.in_(scenario_ids),
                )
                # 같은 시각이면 새 출제 순번이 큰 쪽이 직전 세션
                .order_by(PracticeSession.started_at.desc(), PracticeSession.draw_index.desc())
            ).all()
        latest: dict[str, tuple[str, str]] = {}
        for scenario_id, variant in rows:
            if scenario_id not in latest:
                latest[scenario_id] = (variant["platform"], variant["tone"])
        return latest

    def count_new_draws(self, child_id: UUID) -> int:
        with self._session_factory() as db:
            return db.scalar(
                select(func.count())
                .select_from(PracticeSession)
                .where(
                    PracticeSession.child_id == child_id,
                    PracticeSession.mode != "retry",
                )
            )

    def create_session(
        self,
        session: NewPracticeSession,
        first_turn: NewPracticeTurn,
    ) -> UUID:
        row = PracticeSession(
            child_id=session.child_id,
            mode=session.mode,
            area=session.area,
            subtype=session.subtype,
            scenario_id=session.scenario_id,
            is_normal=session.is_normal,
            target_cue_ids=list(session.target_cue_ids),
            variant=session.variant,
            scenario_title=session.scenario_title,
            child_setup=session.child_setup,
            ai_role_name=session.ai_role_name,
            retry_of=None,
            draw_index=session.draw_index,
            hint_level=None,
            status="in_progress",
            normal_outcome=None,
            origin="live",
            started_at=session.started_at,
            ended_at=None,
        )
        with self._session_factory.begin() as db:
            db.add(row)
            db.flush()
            db.add(_turn_row(row.id, first_turn))
            return row.id

    def get_session(
        self,
        session_id: UUID,
        child_id: UUID,
    ) -> PracticeSessionRecord | None:
        with self._session_factory() as db:
            row = db.get(PracticeSession, session_id)
            if row is None or row.child_id != child_id:
                return None
            turns = db.scalars(
                select(PracticeTurn)
                .where(PracticeTurn.session_id == session_id)
                .order_by(PracticeTurn.turn_index)
            ).all()
            return PracticeSessionRecord(
                session_id=row.id,
                child_id=row.child_id,
                mode=row.mode,
                area=row.area,
                scenario_id=row.scenario_id,
                is_normal=row.is_normal,
                target_cue_ids=tuple(row.target_cue_ids),
                variant=dict(row.variant),
                ai_role_name=row.ai_role_name,
                retry_of=row.retry_of,
                status=row.status,
                turns=tuple(
                    PracticeTurnRecord(
                        turn_index=turn.turn_index,
                        ai_line=turn.ai_line,
                        choices=tuple(dict(choice) for choice in turn.choices),
                        chosen_choice_id=turn.chosen_choice_id,
                        substituted=turn.substituted,
                        target_clue_id=turn.target_clue_id,
                        revealed_clue_ids=tuple(turn.revealed_clue_ids),
                        ai_status=turn.ai_status,
                    )
                    for turn in turns
                ),
            )

    @staticmethod
    def _record_choice(db: Session, session_id: UUID, turn_index: int, choice_id: str) -> None:
        turn = db.scalars(
            select(PracticeTurn).where(
                PracticeTurn.session_id == session_id,
                PracticeTurn.turn_index == turn_index,
            )
        ).one()
        turn.chosen_choice_id = choice_id

    def record_answer_and_continue(
        self,
        *,
        session_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        next_turn: NewPracticeTurn,
    ) -> None:
        with self._session_factory.begin() as db:
            self._record_choice(db, session_id, answered_turn_index, chosen_choice_id)
            db.add(_turn_row(session_id, next_turn))

    def record_answer_and_end(
        self,
        *,
        session_id: UUID,
        child_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        cue_results: list[NewCueResult],
        ended_at: datetime,
    ) -> None:
        with self._session_factory.begin() as db:
            self._record_choice(db, session_id, answered_turn_index, chosen_choice_id)
            for item in cue_results:
                db.add(
                    CueResult(
                        session_id=session_id,
                        child_id=child_id,
                        cue_id=item.cue_id,
                        outcome=item.outcome,
                        recorded_at=ended_at,
                    )
                )
            row = db.get(PracticeSession, session_id)
            row.status = "ended"
            row.ended_at = ended_at

    def record_answer_and_stop(
        self,
        *,
        session_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        stop_turn: NewPracticeTurn,
        stopped_at: datetime,
    ) -> None:
        with self._session_factory.begin() as db:
            self._record_choice(db, session_id, answered_turn_index, chosen_choice_id)
            db.add(_turn_row(session_id, stop_turn))
            row = db.get(PracticeSession, session_id)
            row.status = "stopped"
            row.ended_at = stopped_at
