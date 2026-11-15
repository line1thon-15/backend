"""연습 세션 Repository (T-15, 결과·다시 도전 T-16) — SQL·ORM 코드는 여기에만 (Architecture "계층 규칙").

A17의 저장은 메서드 하나 = 한 트랜잭션이다(DECISIONS #82·#85). 서비스는 AI 호출과 응답 검증이 성공한 뒤에만 부른다.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import (
    DRAW_INDEX_UNIQUE_NAME,
    Child,
    ChildSettings,
    CueResult,
    PracticeSession,
    PracticeTurn,
)
from app.services.ports import (
    EndedCueOutcome,
    EndedSessionStats,
    FirstAnswerKind,
    NewCueResult,
    NewPracticeSession,
    NewPracticeTurn,
    PracticeChildProfile,
    PracticeRepository,
    PracticeSessionRecord,
    PracticeStateConflict,
    PracticeTurnRecord,
)

logger = logging.getLogger(__name__)


def _is_draw_index_conflict(exc: IntegrityError) -> bool:
    """순번 고유 인덱스 위반인가. PostgreSQL은 제약 이름, SQLite는 열 목록으로 알린다."""
    message = str(exc.orig)
    return DRAW_INDEX_UNIQUE_NAME in message or (
        "practice_sessions.child_id, practice_sessions.origin, practice_sessions.draw_index" in message
    )


def _as_utc(moment: datetime) -> datetime:
    """조회 경계는 UTC로 맞춰 넘긴다. SQLite는 tz 없이 돌려주므로 읽은 값은 UTC로 붙인다(저장값이 UTC)."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


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

    def create_session(
        self,
        session: NewPracticeSession,
        first_turn: NewPracticeTurn,
    ) -> UUID:
        try:
            return self._insert_session(session, first_turn)
        except IntegrityError as exc:
            # 순번 고유 인덱스 위반만 1회 재시도 — 순번만 다시 계산, AI는 다시 부르지 않는다(입력 그대로).
            # 재시도도 위반이면 그대로 올린다(→ 500 INTERNAL). 다른 위반은 재시도하지 않는다 (ADR-0023 규칙 4)
            if not session.is_new_draw or not _is_draw_index_conflict(exc):
                raise
            logger.info("practice draw_index conflict, retrying once")
            return self._insert_session(session, first_turn)

    def _insert_session(self, session: NewPracticeSession, first_turn: NewPracticeTurn) -> UUID:
        with self._session_factory.begin() as db:
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
                retry_of=session.retry_of,
                # 순번은 이 트랜잭션 안에서 정한다 (ADR-0023 규칙 3) — 다시 도전은 NULL
                draw_index=self._next_draw_index(db, session.child_id) if session.is_new_draw else None,
                hint_level=session.hint_level,
                status="in_progress",
                normal_outcome=None,
                origin="live",
                started_at=session.started_at,
                ended_at=None,
            )
            db.add(row)
            db.flush()
            db.add(_turn_row(row.id, first_turn))
            return row.id

    def _next_draw_index(self, db: Session, child_id: UUID) -> int:
        """그 아이 `origin = 'live'` 비NULL `draw_index` 최댓값 + 1(없으면 1). 예시 행은 세지 않는다 (ADR-0023 규칙 2)."""
        current = db.scalar(
            select(func.max(PracticeSession.draw_index)).where(
                PracticeSession.child_id == child_id,
                PracticeSession.origin == "live",
                PracticeSession.draw_index.is_not(None),
            )
        )
        return 1 if current is None else current + 1

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
                normal_outcome=row.normal_outcome,
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

    def get_cue_results(self, session_id: UUID) -> dict[str, str]:
        """저장된 판정 {cue_id: found|missed} — not_shown은 저장되지 않는다 (#109)."""
        with self._session_factory() as db:
            rows = db.execute(
                select(CueResult.cue_id, CueResult.outcome).where(CueResult.session_id == session_id)
            ).all()
        return {cue_id: outcome for cue_id, outcome in rows}

    @staticmethod
    def _claim_turn(
        db: Session,
        session_id: UUID,
        turn_index: int,
        choice_id: str,
        session_values: dict,
    ) -> None:
        """조건부 갱신으로 같은 세션 동시 요청을 막는다 (T-15 리뷰 치명 #1).

        세션이 아직 in_progress일 때만 세션 행을 갱신하고(쓰기 잠금 — 동시 쓰기 직렬화),
        답할 턴의 chosen_choice_id가 비어 있을 때만 선택을 기록한다. 하나라도 0행이면 충돌.
        """
        claimed = db.execute(
            update(PracticeSession)
            .where(PracticeSession.id == session_id, PracticeSession.status == "in_progress")
            .values(**session_values)
            .execution_options(synchronize_session=False)
        )
        if claimed.rowcount != 1:
            raise PracticeStateConflict(str(session_id))
        chosen = db.execute(
            update(PracticeTurn)
            .where(
                PracticeTurn.session_id == session_id,
                PracticeTurn.turn_index == turn_index,
                PracticeTurn.chosen_choice_id.is_(None),
            )
            .values(chosen_choice_id=choice_id)
            .execution_options(synchronize_session=False)
        )
        if chosen.rowcount != 1:
            raise PracticeStateConflict(str(session_id))

    def _write(self, work) -> None:
        """한 트랜잭션. 유일 제약 위반(동시 요청이 먼저 저장함)도 충돌로 바꾼다."""
        try:
            with self._session_factory.begin() as db:
                work(db)
        except IntegrityError as exc:
            raise PracticeStateConflict("concurrent practice write") from exc

    def record_answer_and_continue(
        self,
        *,
        session_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        next_turn: NewPracticeTurn,
    ) -> None:
        def work(db: Session) -> None:
            self._claim_turn(
                db, session_id, answered_turn_index, chosen_choice_id, {"status": "in_progress"}
            )
            db.add(_turn_row(session_id, next_turn))

        self._write(work)

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
        def work(db: Session) -> None:
            self._claim_turn(
                db,
                session_id,
                answered_turn_index,
                chosen_choice_id,
                {"status": "ended", "ended_at": ended_at},
            )
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

        self._write(work)

    def record_answer_and_stop(
        self,
        *,
        session_id: UUID,
        answered_turn_index: int,
        chosen_choice_id: str,
        stop_turn: NewPracticeTurn,
        stopped_at: datetime,
    ) -> None:
        def work(db: Session) -> None:
            self._claim_turn(
                db,
                session_id,
                answered_turn_index,
                chosen_choice_id,
                {"status": "stopped", "ended_at": stopped_at},
            )
            db.add(_turn_row(session_id, stop_turn))

        self._write(work)

    # ---- 성장 지표 (T-46) ------------------------------------------------------
    # 기간은 [ended_from, ended_to) — 대상은 status = ended 세션만(in_progress·stopped 제외, #113).

    def ended_session_stats(
        self,
        child_id: UUID,
        ended_from: datetime,
        ended_to: datetime,
    ) -> list[EndedSessionStats]:
        found = func.coalesce(func.sum(case((CueResult.outcome == "found", 1), else_=0)), 0)
        missed = func.coalesce(func.sum(case((CueResult.outcome == "missed", 1), else_=0)), 0)
        with self._session_factory() as db:
            rows = db.execute(
                select(
                    PracticeSession.id,
                    PracticeSession.scenario_id,
                    PracticeSession.mode,
                    PracticeSession.is_normal,
                    PracticeSession.ended_at,
                    found,
                    missed,
                )
                .outerjoin(CueResult, CueResult.session_id == PracticeSession.id)
                .where(
                    PracticeSession.child_id == child_id,
                    PracticeSession.status == "ended",
                    PracticeSession.ended_at >= _as_utc(ended_from),
                    PracticeSession.ended_at < _as_utc(ended_to),
                )
                .group_by(PracticeSession.id)
            ).all()
        return [
            EndedSessionStats(
                session_id=session_id,
                scenario_id=scenario_id,
                mode=mode,
                is_normal=is_normal,
                ended_at=_as_utc(ended_at),
                found=int(found_count),
                missed=int(missed_count),
            )
            for session_id, scenario_id, mode, is_normal, ended_at, found_count, missed_count in rows
        ]

    def first_session_ids(
        self,
        child_id: UUID,
        scenario_ids: list[str],
    ) -> dict[str, UUID]:
        """시나리오마다 그 아이가 가장 먼저 받은 세션 — 상태·origin·기간 무관(멈춤·진행 중도 "받음")."""
        if not scenario_ids:
            return {}
        with self._session_factory() as db:
            rows = db.execute(
                select(PracticeSession.scenario_id, PracticeSession.id)
                .where(
                    PracticeSession.child_id == child_id,
                    PracticeSession.scenario_id.in_(sorted(set(scenario_ids))),
                )
                # 시작 시각이 같으면 최초 출제를 다시 도전보다 먼저 — draw_index NULL 정렬은 DB마다 달라 기대지 않는다 (T-93)
                .order_by(
                    PracticeSession.started_at,
                    case((PracticeSession.mode == "retry", 1), else_=0),
                    PracticeSession.draw_index,
                    PracticeSession.id,
                )
            ).all()
        first: dict[str, UUID] = {}
        for scenario_id, session_id in rows:
            first.setdefault(scenario_id, session_id)
        return first

    def first_answer_kinds(
        self,
        child_id: UUID,
        ended_from: datetime,
        ended_to: datetime,
    ) -> list[FirstAnswerKind]:
        """보호자 경로 practice_turns 예외 1개(ADR-0016, DECISIONS #87·#93).

        turn_index 0 행의 session_id·chosen_choice_id·choices만 SELECT한다(ai_line SELECT 금지 — R2).
        choices JSON은 여기서만 파싱해 고른 선택지의 kind만 꺼내고 버린다. 고른 선택지가 없거나
        목록에 없으면 그 세션은 반환하지 않는다(domain이 MissingFirstAnswerKind로 처리).
        """
        with self._session_factory() as db:
            rows = db.execute(
                select(PracticeTurn.session_id, PracticeTurn.chosen_choice_id, PracticeTurn.choices)
                .join(PracticeSession, PracticeSession.id == PracticeTurn.session_id)
                .where(
                    PracticeTurn.turn_index == 0,
                    PracticeSession.child_id == child_id,
                    PracticeSession.status == "ended",
                    PracticeSession.ended_at >= _as_utc(ended_from),
                    PracticeSession.ended_at < _as_utc(ended_to),
                )
            ).all()
        kinds: list[FirstAnswerKind] = []
        for session_id, chosen_choice_id, choices in rows:
            if chosen_choice_id is None:
                continue
            kind = next((c.get("kind") for c in choices if c.get("id") == chosen_choice_id), None)
            if isinstance(kind, str):
                kinds.append(FirstAnswerKind(session_id=session_id, kind=kind))
        return kinds

    def ended_cue_outcomes(self, child_id: UUID) -> list[EndedCueOutcome]:
        """종료 세션의 단서 판정 전부(기간 제한 없음) — 멈춘·진행 중 세션 제외, practice_turns 읽지 않음."""
        with self._session_factory() as db:
            rows = db.execute(
                select(CueResult.cue_id, CueResult.outcome, PracticeSession.ended_at, CueResult.session_id)
                .join(PracticeSession, PracticeSession.id == CueResult.session_id)
                .where(PracticeSession.child_id == child_id, PracticeSession.status == "ended")
            ).all()
        return [
            EndedCueOutcome(
                cue_id=cue_id, outcome=outcome, ended_at=_as_utc(ended_at), session_id=session_id
            )
            for cue_id, outcome, ended_at, session_id in rows
        ]
