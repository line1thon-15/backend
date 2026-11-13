"""배지·연속 기록 산정 — 저장소 + 서비스 통합 (T-45 — F-28 ②③).

근거: Architecture "성장 계산 규칙"(공통·배지·연속 기록·저장 여부 행), 엔티티 practice_sessions·cue_results,
DECISIONS #28·#89·#90·#109·#113·#116·#119, Tasks T-45 완료 조건.

기존 테이블(practice_sessions·cue_results)만 읽는다 — 새 테이블·마이그레이션 없음(매 요청 계산, 저장 없음).
시계는 주입한다. DB는 테스트마다 pytest tmp_path SQLite 파일(Base.metadata.create_all).
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.base import Base
from app.db.models import Child, CueResult, Guardian, PracticeSession
from app.db.session import make_engine, make_session_factory
from app.repositories.badges import SqlAlchemyBadgeRepository
from app.services.badges import Badge, BadgeService, BadgeStreak

UTC = timezone.utc
# 한국 시간 2026-11-12 12:00 = UTC 03:00
NOON_KST_1112 = datetime(2026, 11, 12, 3, 0, tzinfo=UTC)


@dataclass
class Db:
    session_factory: object
    engine: object

    def child(self) -> UUID:
        with self.session_factory() as db:
            guardian = Guardian(email=f"{uuid4().hex}@example.com", password_hash="x")
            db.add(guardian)
            db.flush()
            child = Child(
                guardian_id=guardian.id,
                nickname="아이",
                grade="H1",
                link_code=uuid4().hex[:6],
                pin_hash="x",
                consent_version="v1",
            )
            db.add(child)
            db.commit()
            return child.id

    def session(
        self,
        child_id: UUID,
        *,
        ended_at: datetime | None,
        area: str = "scam",
        found: int = 1,
        missed: int = 0,
        status: str = "ended",
        is_normal: bool = False,
        mode: str = "area",
        origin: str = "live",
    ) -> UUID:
        with self.session_factory() as db:
            row = PracticeSession(
                child_id=child_id,
                mode=mode,
                area=area,
                scenario_id="scam_test",
                is_normal=is_normal,
                target_cue_ids=[],
                variant={"platform": "p", "tone": "t"},
                scenario_title="제목",
                child_setup="설정",
                ai_role_name="역할",
                status=status,
                origin=origin,
                started_at=(ended_at or NOON_KST_1112) - timedelta(minutes=5),
                ended_at=ended_at,
            )
            db.add(row)
            db.flush()
            for index in range(found):
                db.add(self._cue(row, f"found_{index}", "found", ended_at))
            for index in range(missed):
                db.add(self._cue(row, f"missed_{index}", "missed", ended_at))
            db.commit()
            return row.id

    @staticmethod
    def _cue(row: PracticeSession, cue_id: str, outcome: str, at: datetime | None) -> CueResult:
        return CueResult(
            session_id=row.id,
            child_id=row.child_id,
            cue_id=cue_id,
            outcome=outcome,
            recorded_at=at or NOON_KST_1112,
        )

    def service(self, now: datetime) -> BadgeService:
        return BadgeService(SqlAlchemyBadgeRepository(self.session_factory), clock=lambda: now)


@pytest.fixture
def env(tmp_path) -> Iterator[Db]:
    engine = make_engine(f"sqlite:///{(tmp_path / 'badges.db').as_posix()}")
    Base.metadata.create_all(engine)
    yield Db(session_factory=make_session_factory(engine), engine=engine)
    engine.dispose()


def kst_noon(days_ago: int) -> datetime:
    return NOON_KST_1112 - timedelta(days=days_ago)


def compute(env: Db, child_id: UUID, now: datetime = NOON_KST_1112) -> BadgeStreak:
    return env.service(now).badges_and_streak(child_id)


# ---------- 배지 ----------


def test_three_badge_sessions_in_area_give_badge_view(env):
    child = env.child()
    for day in range(3):
        env.session(child, ended_at=kst_noon(day), area="scam")

    result = compute(env, child)

    assert result.badges == (Badge(badge_id="independent:scam", area="scam", label="혼자 할 수 있어요"),)


def test_two_badge_sessions_give_no_badge(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(1))

    assert compute(env, child).badges == ()


def test_other_area_sessions_are_not_mixed(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0), area="scam")
    env.session(child, ended_at=kst_noon(0), area="scam")
    env.session(child, ended_at=kst_noon(0), area="identity_lending")

    assert compute(env, child).badges == ()


def test_normal_situation_sessions_are_not_counted_for_badge(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0), is_normal=True, found=0, missed=0)

    assert compute(env, child).badges == ()


def test_retry_sessions_are_counted_for_badge(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0), mode="retry")
    env.session(child, ended_at=kst_noon(0), mode="retry")

    assert [badge.area for badge in compute(env, child).badges] == ["scam"]


def test_first_answer_doubt_sessions_found1_missed0_three_give_badge(env):
    child = env.child()
    for _ in range(3):
        env.session(child, ended_at=kst_noon(0), area="friend_pressure", found=1, missed=0)

    assert [badge.badge_id for badge in compute(env, child).badges] == ["independent:friend_pressure"]


def test_found0_missed0_sessions_are_not_counted(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0), found=0, missed=0)

    assert compute(env, child).badges == ()


def test_sessions_with_missed_are_not_counted(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0), found=2, missed=1)

    assert compute(env, child).badges == ()


def test_stopped_and_in_progress_sessions_are_not_counted_for_badge(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(0), status="stopped", found=0, missed=0)
    env.session(child, ended_at=None, status="in_progress", found=0, missed=0)

    assert compute(env, child).badges == ()


def test_demo_seed_sessions_are_counted(env):
    child = env.child()
    for _ in range(3):
        env.session(child, ended_at=kst_noon(0), origin="demo_seed")

    assert len(compute(env, child).badges) == 1


def test_badge_has_no_period_limit(env):
    child = env.child()
    for day in (30, 60, 90):
        env.session(child, ended_at=kst_noon(day))

    assert len(compute(env, child).badges) == 1


def test_other_child_sessions_are_not_counted(env):
    me = env.child()
    other = env.child()
    for _ in range(3):
        env.session(other, ended_at=kst_noon(0))
    env.session(other, ended_at=kst_noon(1))

    result = compute(env, me)

    assert result == BadgeStreak(badges=(), streak_days=0)


# ---------- 연속 기록 ----------


def test_three_consecutive_days_including_today_is_three(env):
    child = env.child()
    for day in (0, 1, 2):
        env.session(child, ended_at=kst_noon(day))

    assert compute(env, child).streak_days == 3


def test_today_missing_yesterday_streak_two_is_kept(env):
    child = env.child()
    for day in (1, 2):
        env.session(child, ended_at=kst_noon(day))

    assert compute(env, child).streak_days == 2


def test_neither_today_nor_yesterday_is_zero(env):
    child = env.child()
    for day in (2, 3):
        env.session(child, ended_at=kst_noon(day))

    assert compute(env, child).streak_days == 0


def test_many_sessions_in_one_day_count_as_one_day(env):
    child = env.child()
    for minutes in (0, 10, 20, 30):
        env.session(child, ended_at=kst_noon(0) + timedelta(minutes=minutes))

    assert compute(env, child).streak_days == 1


def test_stopped_only_day_is_not_counted_for_streak(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0), status="stopped", found=0, missed=0)
    env.session(child, ended_at=kst_noon(1))
    env.session(child, ended_at=kst_noon(2))

    # 오늘은 멈춘 연습만 → 오늘 미완료, 어제까지 연속 2일 유지
    assert compute(env, child).streak_days == 2


def test_stopped_only_day_breaks_streak_in_the_middle(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0))
    env.session(child, ended_at=kst_noon(1), status="stopped", found=0, missed=0)
    env.session(child, ended_at=kst_noon(2))

    assert compute(env, child).streak_days == 1


def test_normal_and_retry_and_missed_sessions_count_for_streak(env):
    child = env.child()
    env.session(child, ended_at=kst_noon(0), is_normal=True, found=0, missed=0)
    env.session(child, ended_at=kst_noon(1), mode="retry", found=0, missed=2)
    env.session(child, ended_at=kst_noon(2), found=0, missed=0)

    assert compute(env, child).streak_days == 3


def test_no_sessions_gives_zero_and_no_badges(env):
    child = env.child()

    assert compute(env, child) == BadgeStreak(badges=(), streak_days=0)


# ---------- 한국 시간 날짜 경계 (DECISIONS #89 — UTC 저장, 계산 때만 한국 시간) ----------

# 한국 자정 직전: UTC 2026-11-11 14:59:59 = 한국 11-11 23:59:59
JUST_BEFORE_KST_MIDNIGHT = datetime(2026, 11, 11, 14, 59, 59, tzinfo=UTC)
# 한국 자정 직후: UTC 2026-11-11 15:00:01 = 한국 11-12 00:00:01 (UTC 날짜는 아직 11-11)
JUST_AFTER_KST_MIDNIGHT = datetime(2026, 11, 11, 15, 0, 1, tzinfo=UTC)


def test_sessions_on_both_sides_of_kst_midnight_are_two_days(env):
    child = env.child()
    env.session(child, ended_at=JUST_BEFORE_KST_MIDNIGHT)
    env.session(child, ended_at=JUST_AFTER_KST_MIDNIGHT)

    # 한국 시간으로는 11-11·11-12 이틀(UTC 날짜로 세면 같은 날 1일)
    now = datetime(2026, 11, 11, 15, 30, tzinfo=UTC)  # 한국 11-12 00:30
    assert compute(env, child, now).streak_days == 2


def test_session_just_after_kst_midnight_is_today_for_clock_just_after_midnight(env):
    child = env.child()
    env.session(child, ended_at=JUST_AFTER_KST_MIDNIGHT)

    now = datetime(2026, 11, 11, 15, 30, tzinfo=UTC)  # 한국 11-12 00:30 (UTC 날짜 11-11)
    assert compute(env, child, now).streak_days == 1


def test_clock_just_before_kst_midnight_uses_kst_today(env):
    child = env.child()
    # 한국 11-10 23:00 (UTC 11-10 14:00) — 한국 기준 '어제'
    env.session(child, ended_at=datetime(2026, 11, 10, 14, 0, tzinfo=UTC))

    just_before = datetime(2026, 11, 11, 14, 59, 59, tzinfo=UTC)  # 한국 11-11 23:59:59
    assert compute(env, child, just_before).streak_days == 1

    just_after = datetime(2026, 11, 11, 15, 0, 0, tzinfo=UTC)  # 한국 11-12 00:00:00 → 그 세션은 그제
    assert compute(env, child, just_after).streak_days == 0


# ---------- 저장 없음 (매 요청 계산 — DECISIONS #28·#90) ----------


def test_computation_does_not_write_rows(env):
    child = env.child()
    for day in range(3):
        env.session(child, ended_at=kst_noon(day))

    def counts() -> tuple[int, int]:
        with env.session_factory() as db:
            return (
                db.scalar(select(func.count()).select_from(PracticeSession)),
                db.scalar(select(func.count()).select_from(CueResult)),
            )

    before = counts()
    first = compute(env, child)
    second = compute(env, child)

    assert counts() == before
    assert first == second
    # 새 세션이 쌓이면 다음 요청에 바로 반영된다(저장된 값 없음)
    env.session(child, ended_at=kst_noon(3))
    assert compute(env, child).streak_days == 4
