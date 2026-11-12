"""성장 지표 서비스 + 리포지토리 (T-46 — F-29 ⑤⑥, F-31 데이터 측).

근거: Architecture "성장 계산 규칙" 절, 엔티티 practice_turns 행의 보호자 경로 예외(`first_answer_kinds`),
테스트 전략 2026-11-11 ①(R1·R2)·②·③, DECISIONS #87·#89·#93·#94·#109·#113·#116·#117, ADR-0016.

DB는 테스트마다 pytest tmp_path SQLite 파일. 행은 ORM으로 직접 넣는다(AI 호출 없음).
시계는 주입: 2026-11-12T03:00Z = 한국 시간 2026-11-12 12:00 → 이번 기간 [11-06, 11-12], 직전 [10-30, 11-05].
"""

import dataclasses
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event

from app.db.base import Base
from app.db.models import Child, CueResult, Guardian, PracticeSession, PracticeTurn
from app.db.session import make_engine, make_session_factory
from app.domain.metrics import MissingFirstAnswerKind
from app.repositories.practice import SqlAlchemyPracticeRepository
from app.services.growth import GrowthMetricsService
from app.services.ports import FirstAnswerKind

NOW = datetime(2026, 11, 12, 3, 0, 0, tzinfo=timezone.utc)
CUR_AT = datetime(2026, 11, 9, 3, 0, 0, tzinfo=timezone.utc)  # 한국 11-09 — 이번 기간
PREV_AT = datetime(2026, 11, 2, 3, 0, 0, tzinfo=timezone.utc)  # 한국 11-02 — 직전 기간
MARKER = "GROWTH-MARKER-91c2"


class Db:
    def __init__(self, url: str) -> None:
        self.engine = make_engine(url)
        Base.metadata.create_all(self.engine)
        self.session_factory = make_session_factory(self.engine)
        self.repository = SqlAlchemyPracticeRepository(self.session_factory)
        self._seq = 0

    def service(self) -> GrowthMetricsService:
        return GrowthMetricsService(self.repository, clock=lambda: NOW)

    def child(self) -> UUID:
        self._seq += 1
        with self.session_factory.begin() as db:
            guardian = Guardian(email=f"g{self._seq}@example.com", password_hash="x")
            db.add(guardian)
            db.flush()
            child = Child(
                guardian_id=guardian.id,
                nickname="하늘이",
                grade="H1",
                link_code=f"C{self._seq:05d}",
                pin_hash="x",
                consent_agreed_at=NOW,
                consent_version="v1",
            )
            db.add(child)
            db.flush()
            return child.id

    def session(
        self,
        child_id: UUID,
        *,
        ended_at: datetime | None,
        status: str = "ended",
        scenario_id: str | None = None,
        mode: str = "area",
        is_normal: bool = False,
        cues: dict[str, str] | None = None,
        first_kind: str | None = "correct",
        started_at: datetime | None = None,
    ) -> UUID:
        self._seq += 1
        cues = {"c1": "found"} if cues is None else cues
        with self.session_factory.begin() as db:
            row = PracticeSession(
                child_id=child_id,
                mode=mode,
                area="scam",
                subtype=None,
                scenario_id=scenario_id or f"scn_{self._seq}",
                is_normal=is_normal,
                target_cue_ids=sorted(cues),
                variant={"platform": "sms", "tone": "friendly"},
                scenario_title="제목",
                child_setup="설정",
                ai_role_name="상대",
                retry_of=None,
                draw_index=None if mode == "retry" else self._seq,
                hint_level=None,
                status=status,
                normal_outcome=None,
                origin="live",
                started_at=started_at or (ended_at or NOW),
                ended_at=ended_at,
            )
            db.add(row)
            db.flush()
            choices = [
                {"id": "a", "text": f"{MARKER} 거절", "kind": "correct"},
                {"id": "b", "text": f"{MARKER} 따름", "kind": "other"},
                {"id": "c", "text": f"{MARKER} 망설임", "kind": "doubtful"},
            ]
            chosen = {"correct": "a", "other": "b", "doubtful": "c", None: None}[first_kind]
            db.add(
                PracticeTurn(
                    session_id=row.id,
                    turn_index=0,
                    ai_line=f"{MARKER} 첫 대사",
                    choices=choices,
                    chosen_choice_id=chosen,
                    substituted=False,
                    target_clue_id="c1",
                    revealed_clue_ids=[],
                    ai_status="ok",
                )
            )
            for cue_id, outcome in cues.items():
                db.add(
                    CueResult(
                        session_id=row.id,
                        child_id=child_id,
                        cue_id=cue_id,
                        outcome=outcome,
                        recorded_at=ended_at or NOW,
                    )
                )
            return row.id


@pytest.fixture
def db(tmp_path):
    database = Db(f"sqlite:///{(tmp_path / 'growth.db').as_posix()}")
    yield database
    database.engine.dispose()


def by_id(results) -> dict:
    return {result.metric_id: result for result in results}


def seed_baseline(db: Db, child_id: UUID) -> None:
    """이번 기간 3개(찾음 2·놓침 1씩), 직전 기간 3개(찾음 1·놓침 1씩)."""
    for _ in range(3):
        db.session(child_id, ended_at=CUR_AT, cues={"c1": "found", "c2": "found", "c3": "missed"})
        db.session(child_id, ended_at=PREV_AT, cues={"c1": "found", "c2": "missed"}, first_kind="other")


# ==== 정상 =========================================================================


def test_metrics_from_db_rows(db):
    child_id = db.child()
    seed_baseline(db, child_id)

    results = db.service().metrics(child_id)

    assert [r.metric_id for r in results] == ["missed_ratio", "first_seen_accuracy", "ahead_of_ai_ratio"]
    values = by_id(results)
    assert values["missed_ratio"].status == "ok"
    assert values["missed_ratio"].current == pytest.approx(3 / 9)
    assert values["missed_ratio"].previous == pytest.approx(3 / 6)
    assert values["first_seen_accuracy"].current == pytest.approx(6 / 9)
    assert values["first_seen_accuracy"].previous == pytest.approx(3 / 6)
    assert values["ahead_of_ai_ratio"].current == 1.0
    assert values["ahead_of_ai_ratio"].previous == 0.0
    assert [(p.date.isoformat(), p.value) for p in values["ahead_of_ai_ratio"].trend] == [
        ("2026-11-05", 0.0),
        ("2026-11-12", 1.0),
    ]
    for result in results:
        assert result.level is None


# ==== 제외 대상 =====================================================================


def test_stopped_in_progress_and_other_child_sessions_change_nothing(db):
    child_id = db.child()
    seed_baseline(db, child_id)
    before = db.service().metrics(child_id)

    # 멈춘 연습(#113)·진행 중·다른 아이 세션 — 어느 지표에도 들어가지 않는다
    db.session(child_id, ended_at=CUR_AT, status="stopped", cues={"c1": "missed"}, first_kind="other")
    db.session(child_id, ended_at=None, status="in_progress", cues={"c1": "missed"}, first_kind="other")
    other = db.child()
    for _ in range(3):
        db.session(other, ended_at=CUR_AT, cues={"c1": "missed"}, first_kind="other")

    assert db.service().metrics(child_id) == before


def test_two_ended_plus_one_stopped_is_insufficient(db):
    child_id = db.child()
    for _ in range(3):
        db.session(child_id, ended_at=PREV_AT)
    for _ in range(2):
        db.session(child_id, ended_at=CUR_AT)
    db.session(child_id, ended_at=CUR_AT, status="stopped")

    for result in db.service().metrics(child_id):
        assert result.status == "insufficient"
        assert result.current is None
        assert result.trend == ()


def test_scenario_first_received_in_stopped_session_is_not_first_seen(db):
    child_id = db.child()
    seed_baseline(db, child_id)
    # 같은 시나리오를 먼저 받았다가 멈춤(기간 밖, 상태 무관하게 "받음") → 뒤의 종료 세션은 처음 보는 유형이 아님
    early = datetime(2026, 10, 1, 3, 0, 0, tzinfo=timezone.utc)
    db.session(child_id, ended_at=early, status="stopped", scenario_id="scn_repeat", started_at=early)
    db.session(child_id, ended_at=CUR_AT, scenario_id="scn_repeat", cues={"c1": "missed", "c2": "missed"})
    # 다시 도전 세션도 (나)에서 빠짐
    db.session(child_id, ended_at=CUR_AT, mode="retry", cues={"c1": "missed"})

    values = by_id(db.service().metrics(child_id))

    assert values["first_seen_accuracy"].current == pytest.approx(6 / 9)  # 기준선 그대로
    assert values["missed_ratio"].current == pytest.approx((3 + 2 + 1) / (9 + 2 + 1))


# ==== 한국 시간 경계 ==================================================================


@pytest.mark.parametrize(
    "ended_at, in_current",
    [
        (datetime(2026, 11, 5, 15, 0, 0, tzinfo=timezone.utc), True),  # 한국 11-06 00:00 — 이번 기간 첫날
        (datetime(2026, 11, 5, 14, 59, 59, tzinfo=timezone.utc), False),  # 한국 11-05 23:59:59 — 직전 기간
    ],
)
def test_korea_time_boundary_decides_period(db, ended_at, in_current):
    child_id = db.child()
    seed_baseline(db, child_id)
    db.session(child_id, ended_at=ended_at, cues={"c1": "missed"}, first_kind="other")

    values = by_id(db.service().metrics(child_id))["missed_ratio"]

    if in_current:
        assert values.current == pytest.approx(4 / 10)
        assert values.previous == pytest.approx(3 / 6)
    else:
        assert values.current == pytest.approx(3 / 9)
        assert values.previous == pytest.approx(4 / 7)


def test_sessions_before_previous_period_are_ignored(db):
    child_id = db.child()
    seed_baseline(db, child_id)
    before = db.service().metrics(child_id)
    # 한국 10-29 23:59:59 — 직전 기간 첫날(10-30) 하루 전
    db.session(child_id, ended_at=datetime(2026, 10, 29, 14, 59, 59, tzinfo=timezone.utc), first_kind=None)

    assert db.service().metrics(child_id) == before


# ==== 예외 =========================================================================


def test_ended_session_without_first_answer_raises(db):
    child_id = db.child()
    seed_baseline(db, child_id)
    db.session(child_id, ended_at=CUR_AT, first_kind=None)

    with pytest.raises(MissingFirstAnswerKind):
        db.service().metrics(child_id)


# ==== 보호자 경로 practice_turns 예외 강제 (ADR-0016 R1·R2) =========================


def test_r1_first_answer_kind_fields_are_exactly_session_id_and_kind():
    assert {field.name for field in dataclasses.fields(FirstAnswerKind)} == {"session_id", "kind"}


def _capture_sql(engine):
    statements: list[str] = []

    def before(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", before)
    return statements, lambda: event.remove(engine, "before_cursor_execute", before)


def test_r2_first_answer_kinds_sql_never_selects_ai_line(db):
    child_id = db.child()
    correct_id = db.session(child_id, ended_at=CUR_AT, first_kind="correct")
    other_id = db.session(child_id, ended_at=CUR_AT, first_kind="other")
    db.session(child_id, ended_at=CUR_AT, status="stopped", first_kind="correct")
    statements, stop = _capture_sql(db.engine)
    try:
        kinds = db.repository.first_answer_kinds(
            child_id,
            datetime(2026, 10, 29, 15, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 11, 12, 15, 0, 0, tzinfo=timezone.utc),
        )
    finally:
        stop()

    assert sorted(kinds, key=lambda k: k.kind) == sorted(
        [FirstAnswerKind(session_id=correct_id, kind="correct"), FirstAnswerKind(session_id=other_id, kind="other")],
        key=lambda k: k.kind,
    )
    assert statements
    assert all("ai_line" not in s for s in statements)
    assert any("turn_index" in s for s in statements)
    assert all(MARKER not in repr(k) for k in kinds)


def test_other_growth_queries_do_not_touch_practice_turns(db):
    child_id = db.child()
    seed_baseline(db, child_id)
    statements, stop = _capture_sql(db.engine)
    try:
        stats = db.repository.ended_session_stats(
            child_id,
            datetime(2026, 10, 29, 15, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 11, 12, 15, 0, 0, tzinfo=timezone.utc),
        )
        db.repository.first_session_ids(child_id, [s.scenario_id for s in stats])
    finally:
        stop()

    assert len(stats) == 6
    assert statements
    assert all("practice_turns" not in s for s in statements)


# ==== 더 연습이 필요한 단서 (2026-11-12 사용자 결정 "2번 이상 + 최근 놓침 (추천)") ============


def test_needs_practice_cue_ids_from_ended_sessions_only(db):
    child_id = db.child()
    day = lambda n: datetime(2026, 11, n, 3, 0, 0, tzinfo=timezone.utc)  # noqa: E731
    # c1: 종료 세션에서 2번 놓침, 마지막도 놓침 → 목록
    db.session(child_id, ended_at=day(1), cues={"c1": "missed", "c2": "missed"})
    db.session(child_id, ended_at=day(2), cues={"c1": "missed", "c2": "missed"})
    # c2: 그 뒤 찾음 → 빠짐 (기간 밖 오래된 판정도 누적으로 셈 — 아래 c6)
    db.session(child_id, ended_at=day(3), cues={"c2": "found"})
    # c3: 멈춘 세션 2번 놓침 → 제외 / c4: 진행 중 세션 → 제외
    db.session(child_id, ended_at=day(4), status="stopped", cues={"c3": "missed"})
    db.session(child_id, ended_at=day(5), status="stopped", cues={"c3": "missed"})
    db.session(child_id, ended_at=None, status="in_progress", cues={"c4": "missed"})
    db.session(child_id, ended_at=day(6), cues={"c4": "missed"})
    # c5: 다른 아이 → 제외
    other = db.child()
    db.session(other, ended_at=day(1), cues={"c5": "missed"})
    db.session(other, ended_at=day(2), cues={"c5": "missed"})
    db.session(child_id, ended_at=day(7), cues={"c5": "missed"})
    # c6: 오래전(10월 초) 두 번 놓침 — 기간 제한 없음
    db.session(child_id, ended_at=datetime(2026, 10, 1, 3, tzinfo=timezone.utc), cues={"c6": "missed"})
    db.session(child_id, ended_at=datetime(2026, 10, 2, 3, tzinfo=timezone.utc), cues={"c6": "missed"})

    assert db.service().needs_practice_cue_ids(child_id) == ("c1", "c6")


def test_needs_practice_cue_ids_empty_without_records(db):
    assert db.service().needs_practice_cue_ids(db.child()) == ()


def test_ended_cue_outcomes_query_does_not_touch_practice_turns(db):
    child_id = db.child()
    seed_baseline(db, child_id)
    statements, stop = _capture_sql(db.engine)
    try:
        outcomes = db.repository.ended_cue_outcomes(child_id)
    finally:
        stop()

    assert len(outcomes) == 15  # 이번 3세션×3 + 직전 3세션×2
    assert statements
    assert all("practice_turns" not in s for s in statements)
