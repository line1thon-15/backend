"""시연 예시 데이터 적재 저장소 (T-67 — DECISIONS #30·#132, Architecture app/demo 행).

- 예시 행은 `origin = demo_seed`로 같은 테이블에 넣는다.
- 재실행 안전: 그 아이의 `demo_seed` 행(세션·턴·단서 판정·알림)을 지우고 새 계획으로 다시 넣는다 — 한 트랜잭션.
  `live` 행은 건드리지 않는다.
"""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Child, CueResult, Guardian, GuardianNotice, PracticeSession, PracticeTurn
from app.demo.plan import DemoPlan

DEMO_ORIGIN = "demo_seed"


@dataclass(frozen=True)
class FixedAccountSpec:
    guardian_email: str
    child_nickname: str
    child_grade: str
    child_link_code: str
    consent_version: str


class LinkCodeTakenError(Exception):
    """고정 시연 계정의 연결 코드를 다른 보호자의 아이가 쓰고 있음."""


class SqlAlchemyDemoSeedRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def ensure_fixed_account(
        self,
        spec: FixedAccountSpec,
        password_hash: Callable[[], str],
        pin_hash: Callable[[], str],
    ) -> UUID:
        """보호자(이메일)·아이(연결 코드)가 있으면 그대로 쓰고, 없으면 만든다. 비밀번호·PIN은 새로 만들 때만 해시."""
        with self._session_factory.begin() as db:
            guardian = db.scalar(select(Guardian).where(Guardian.email == spec.guardian_email))
            child = db.scalar(select(Child).where(Child.link_code == spec.child_link_code))
            if child is not None and (guardian is None or child.guardian_id != guardian.id):
                raise LinkCodeTakenError(spec.child_link_code)
            if guardian is None:
                guardian = Guardian(email=spec.guardian_email, password_hash=password_hash())
                db.add(guardian)
                db.flush()
            if child is None:
                child = Child(
                    guardian_id=guardian.id,
                    nickname=spec.child_nickname,
                    grade=spec.child_grade,
                    link_code=spec.child_link_code,
                    pin_hash=pin_hash(),
                    consent_version=spec.consent_version,
                )
                db.add(child)
                db.flush()
            return child.id

    def replace_demo_records(self, child_id: UUID, plan: DemoPlan) -> bool:
        """아이가 없으면 False(아무것도 쓰지 않음)."""
        with self._session_factory.begin() as db:
            if db.get(Child, child_id) is None:
                return False
            old_ids = select(PracticeSession.id).where(
                PracticeSession.child_id == child_id, PracticeSession.origin == DEMO_ORIGIN
            )
            db.execute(delete(CueResult).where(CueResult.session_id.in_(old_ids)))
            db.execute(delete(PracticeTurn).where(PracticeTurn.session_id.in_(old_ids)))
            db.execute(
                delete(PracticeSession).where(
                    PracticeSession.child_id == child_id, PracticeSession.origin == DEMO_ORIGIN
                )
            )
            db.execute(
                delete(GuardianNotice).where(
                    GuardianNotice.child_id == child_id, GuardianNotice.origin == DEMO_ORIGIN
                )
            )

            for item in plan.sessions:
                session = PracticeSession(
                    child_id=child_id,
                    mode=item.mode,
                    area=item.area,
                    subtype=None,
                    scenario_id=item.scenario_id,
                    is_normal=item.is_normal,
                    target_cue_ids=list(item.target_cue_ids),
                    variant=item.variant,
                    scenario_title=item.scenario_title,
                    child_setup=item.child_setup,
                    ai_role_name=item.ai_role_name,
                    retry_of=None,
                    draw_index=item.draw_index,
                    hint_level=None,
                    status="ended",
                    normal_outcome=None,
                    origin=DEMO_ORIGIN,
                    started_at=item.started_at,
                    ended_at=item.ended_at,
                )
                db.add(session)
                db.flush()
                db.add(
                    PracticeTurn(
                        session_id=session.id,
                        turn_index=0,
                        ai_line=item.ai_line,
                        choices=[dict(choice) for choice in item.turn_choices],
                        chosen_choice_id=item.chosen_choice_id,
                        substituted=False,
                        target_clue_id=item.target_clue_id,
                        revealed_clue_ids=list(item.revealed_clue_ids),
                        ai_status="ok",
                    )
                )
                for cue_id, outcome in item.cue_outcomes:
                    db.add(
                        CueResult(
                            session_id=session.id,
                            child_id=child_id,
                            cue_id=cue_id,
                            outcome=outcome,
                            recorded_at=item.ended_at,
                        )
                    )
            for notice in plan.notices:
                db.add(
                    GuardianNotice(
                        child_id=child_id,
                        kind="safety",
                        level=notice.level,
                        area=notice.area,
                        channel=None,
                        origin=DEMO_ORIGIN,
                        occurred_at=notice.occurred_at,
                    )
                )
        return True
