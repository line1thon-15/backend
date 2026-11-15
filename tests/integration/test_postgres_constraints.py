"""PostgreSQL 통합 테스트 (T-99 ⑧ — 사용자 답 "CI에 PostgreSQL 추가", DECISIONS #142, Architecture 테스트 전략
"PostgreSQL 통합 테스트" 행, 근거 팀 리뷰 PR #37 P2-1).

대상(Tasks T-99 ⑧ (a)~(e)): (a) `alembic upgrade head` (b) 기존 중복 `draw_index` 자동 재번호(ADR-0023 규칙 5)
(c) 고유 인덱스 위반 → 롤백·순번 재계산 1회 재시도, 재충돌 500 `INTERNAL`(규칙 4) (d) 두 DB 연결의 동시 저장 충돌
(e) `guardian_notices` CHECK 위반 거부.

실행 조건:
- 마커 `postgres` + 환경 변수 `TEST_POSTGRES_URL`(형식 `postgresql+psycopg://…`). 값이 없으면 skip — 로컬 기본 SQLite
  실행에서는 건너뛴다. 단 `REQUIRE_TEST_POSTGRES`가 켜진 실행(CI job pytest-postgres)은 skip 대신 실패(T-101 ①).
  값이 있는데 연결·마이그레이션이 실패하면 skip이 아니라 오류.
- 호스트가 localhost·127.0.0.1이 아니면 실패(운영·외부 DB 오사용 방지). 앱의 DATABASE_URL을 대신 읽지 않는다.
- 스키마 삭제 전 DB 이름(`_ci`·`_test`로 끝남)·CI 환경(`CI=true`)도 확인 — 어긋나면 연결·삭제 없이 실패(T-101 ②).
  판정은 `helpers/postgres_guard.py`, 검증은 `test_postgres_guard.py`(PostgreSQL 없이 실행).
- 각 테스트는 `public` 스키마를 비운 뒤 `alembic upgrade head`(또는 지정 리비전)부터 시작한다 — CI 서비스 컨테이너
  전용 일회용 DB를 전제로 한다.
"""

import os
import random
import threading
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import Settings
from app.db import models  # noqa: F401  (메타데이터 등록)
from app.db.models import GuardianNotice, PracticeSession, PracticeTurn
from app.db.session import make_session_factory
from app.main import create_app
from app.repositories.practice import SqlAlchemyPracticeRepository
from app.services.ports import NewPracticeSession, NewPracticeTurn
from tests.integration.helpers.draw_index_cases import (
    CHILD_A,
    CHILD_B,
    RENUMBERED,
    T0,
    draw_indexes_by_id,
    expected_by_id,
    insert_duplicate_rows,
)
from tests.integration.helpers.practice_env import Env, RecordingPracticeAI
from tests.integration.helpers.postgres_guard import (
    checked_postgres_url,
    reset_public_schema,
    resolve_postgres_url,
)

pytestmark = pytest.mark.postgres

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_NAME = "uq_practice_sessions_child_origin_draw"
BEFORE_INDEX_REVISION = "20261112_05"


@pytest.fixture
def pg_url() -> str:
    # URL 없음: 로컬은 skip, CI 전용 변수 REQUIRE_TEST_POSTGRES가 켜져 있으면 실패 (T-101 ①, helpers/postgres_guard.py)
    return resolve_postgres_url(os.environ)


@pytest.fixture
def pg(pg_url, monkeypatch) -> Iterator[tuple[Config, Engine, str]]:
    """빈 public 스키마 + alembic 설정. 연결 실패는 그대로 오류로 올라간다(조용한 skip 금지).

    스키마 삭제 전 호스트·DB 이름·CI 환경을 확인한다(T-101 ②) — 하나라도 어긋나면 연결·삭제 없이 실패.
    """
    engine = reset_public_schema(pg_url, os.environ)
    # alembic env.py는 Settings().database_url을 읽는다 — 이 테스트 동안만 PostgreSQL을 가리킨다
    monkeypatch.setenv("DATABASE_URL", pg_url)
    config = Config(str(REPO_ROOT / "alembic.ini"))
    yield config, engine, pg_url
    engine.dispose()


@pytest.fixture
def pg_app(pg) -> Iterator[Env]:
    """head까지 마이그레이션한 PostgreSQL 위의 앱(가짜 AI). 500 응답을 단언하려고 서버 예외를 다시 던지지 않는다."""
    config, _engine, url = pg
    command.upgrade(config, "head")
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=url, ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        yield Env(client, ai)
    app.state.engine.dispose()


def _index(engine: Engine):
    return {index["name"]: index for index in inspect(engine).get_indexes("practice_sessions")}.get(INDEX_NAME)


def _live_draws(env: Env, child_id: UUID) -> list[int | None]:
    with env.session_factory() as db:
        return list(
            db.scalars(
                select(PracticeSession.draw_index)
                .where(PracticeSession.child_id == child_id, PracticeSession.origin == "live")
                .order_by(PracticeSession.started_at, PracticeSession.id)
            )
        )


# ---- 안전장치 ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "postgresql+psycopg://user:pw@db.example.com:5432/db",
        "postgresql+psycopg://user:pw@10.0.0.5:5432/db",
        "sqlite:///local.db",
    ],
)
def test_non_local_or_non_postgres_url_is_rejected(pg_url, raw):
    # 연결하지 않는다 — 다른 호스트·드라이버는 연결 전에 실패시킨다 (pg_url 요구 = TEST_POSTGRES_URL 없으면 skip)
    with pytest.raises(pytest.fail.Exception):
        checked_postgres_url(raw)


def test_local_postgres_url_is_accepted(pg_url):
    assert checked_postgres_url("postgresql+psycopg://u:p@127.0.0.1:5432/db").endswith("/db")


# ---- (a) upgrade head ------------------------------------------------------------------


def test_alembic_upgrade_head_on_postgres(pg):
    config, engine, _url = pg

    command.upgrade(config, "head")

    head = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT version_num FROM alembic_version")) == head
    index = _index(engine)
    assert index is not None
    assert index["column_names"] == ["child_id", "origin", "draw_index"]
    assert index["unique"]
    assert {"guardians", "children", "practice_sessions", "practice_turns", "cue_results", "guardian_notices"} <= set(
        inspect(engine).get_table_names()
    )


# ---- (b) 기존 중복 재번호 ------------------------------------------------------------------


def test_upgrade_renumbers_existing_duplicates_on_postgres(pg, capsys):
    config, engine, url = pg
    command.upgrade(config, BEFORE_INDEX_REVISION)
    # 외래 키를 검사하므로 실제 아이 2명을 API로 만든다(인덱스 이전 리비전에서도 가입·등록 테이블은 있다)
    app = create_app(Settings(_env_file=None, database_url=url, ai_client="fake"), practice_ai=RecordingPracticeAI())
    try:
        with TestClient(app) as client:
            env = Env(client, RecordingPracticeAI())
            children = {CHILD_A: env.login_child(), CHILD_B: env.login_child()}
    finally:
        app.state.engine.dispose()
    insert_duplicate_rows(engine, children)
    capsys.readouterr()

    command.upgrade(config, "head")

    assert draw_indexes_by_id(engine) == expected_by_id()
    assert _index(engine) is not None
    out = capsys.readouterr().out
    assert f"draw_index renumbered rows: {RENUMBERED}" in out
    assert all(str(child) not in out and child.hex not in out for child in children.values())


# ---- (c) 고유 인덱스 위반 → 롤백·1회 재시도 / 재충돌 500 -------------------------------------


def _force_conflicts(monkeypatch, conflicts: int) -> list[int]:
    original = SqlAlchemyPracticeRepository._next_draw_index
    calls: list[int] = []

    def patched(self, db, child_id):
        calls.append(1)
        if len(calls) <= conflicts:
            return 1  # 이미 있는 순번 — 고유 인덱스 위반
        return original(self, db, child_id)

    monkeypatch.setattr(SqlAlchemyPracticeRepository, "_next_draw_index", patched)
    return calls


def test_conflict_rolls_back_and_retries_once_on_postgres(pg_app, monkeypatch):
    env = pg_app
    child_id = env.login_child(grade="H1")
    env.started()  # 순번 1
    calls = _force_conflicts(monkeypatch, conflicts=1)
    env.ai.calls.clear()

    response = env.start()

    assert response.status_code == 201, response.text
    assert env.session_row(response.json()["session_id"]).draw_index == 2
    assert len(calls) == 2
    assert env.ai.names() == ["variant", "start"]  # AI 재호출 없음
    assert _live_draws(env, child_id) == [1, 2]
    assert env.count(PracticeTurn) == 2  # 실패한 첫 시도의 턴은 롤백됐다


def test_second_conflict_is_500_internal_on_postgres(pg_app, monkeypatch):
    env = pg_app
    child_id = env.login_child(grade="H1")
    env.started()  # 순번 1
    calls = _force_conflicts(monkeypatch, conflicts=2)

    response = env.start()

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL"
    assert len(calls) == 2  # 재시도는 1회뿐
    assert _live_draws(env, child_id) == [1]
    assert env.count(PracticeTurn) == 1


# ---- (d) 두 연결의 동시 저장 -------------------------------------------------------------


def _new_session(child_id: UUID) -> tuple[NewPracticeSession, NewPracticeTurn]:
    return (
        NewPracticeSession(
            child_id=child_id,
            mode="area",
            area="scam",
            subtype=None,
            scenario_id="scam_dm_parttime_01",
            is_normal=False,
            target_cue_ids=("urgency",),
            variant={"platform": "sms", "tone": "friendly"},
            scenario_title="제목",
            child_setup="설정",
            ai_role_name="상대",
            is_new_draw=True,
            started_at=T0,
        ),
        NewPracticeTurn(
            turn_index=0,
            ai_line="대사",
            choices=({"id": "c1", "text": "선택", "kind": "correct"},),
            substituted=False,
            target_clue_id=None,
            revealed_clue_ids=(),
            ai_status="ok",
        ),
    )


def test_two_connections_saving_concurrently_get_distinct_draw_index(pg_app, monkeypatch):
    """서로 다른 엔진(연결) 2개의 저장소가 같은 순번(1)을 계산한 뒤 동시에 넣는다 — 한쪽은 고유 인덱스 위반 후
    순번을 다시 계산해 2로 저장해야 한다."""
    env = pg_app
    child_id = env.login_child(grade="H1")
    url = env.client.app.state.engine.url.render_as_string(hide_password=False)
    engines = [create_engine(url), create_engine(url)]
    barrier = threading.Barrier(2, timeout=10.0)
    original = SqlAlchemyPracticeRepository._next_draw_index
    computed: list[int] = []
    lock = threading.Lock()

    def patched(self, db, cid):
        value = original(self, db, cid)
        with lock:
            computed.append(value)
            first_round = len(computed) <= 2
        if first_round:
            barrier.wait()  # 두 연결이 모두 같은 값을 계산한 뒤에 넣는다
        return value

    monkeypatch.setattr(SqlAlchemyPracticeRepository, "_next_draw_index", patched)
    results: list[UUID | BaseException | None] = [None, None]

    def worker(slot: int) -> None:
        repository = SqlAlchemyPracticeRepository(make_session_factory(engines[slot]))
        try:
            results[slot] = repository.create_session(*_new_session(child_id))
        except BaseException as exc:  # noqa: BLE001 — 스레드 밖에서 단언
            results[slot] = exc

    threads = [threading.Thread(target=worker, args=(slot,)) for slot in (0, 1)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
    finally:
        for engine in engines:
            engine.dispose()

    assert all(isinstance(result, UUID) for result in results), results
    assert computed[:2] == [1, 1]  # 실제로 같은 순번을 계산해 충돌했다
    assert len(computed) == 3  # 한쪽만 1회 재계산
    assert sorted(_live_draws(env, child_id)) == [1, 2]


# ---- (e) guardian_notices CHECK ---------------------------------------------------------


KF = "ck_guardian_notices_kind_fields"


def _insert_notice(engine: Engine, child_id: UUID, **values) -> None:
    row = {
        "id": uuid4(),
        "child_id": child_id,
        "kind": "safety",
        "level": "red",
        "area": "scam",
        "channel": None,
        "origin": "demo_seed",
        "occurred_at": T0,
    }
    row.update(values)
    with engine.begin() as conn:
        conn.execute(GuardianNotice.__table__.insert().values(**row))


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"level": "yellow", "area": "friend_pressure", "origin": "live"},
        {"kind": "trusted_contact", "level": None, "area": None, "channel": "call"},
        {"kind": "trusted_contact", "level": None, "area": None, "channel": "sms"},
    ],
)
def test_guardian_notices_valid_rows_accepted_on_postgres(pg_app, values):
    env = pg_app
    child_id = env.login_child()
    engine = env.client.app.state.engine

    _insert_notice(engine, child_id, **values)

    with engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(GuardianNotice.__table__)) == 1


@pytest.mark.parametrize(
    ("values", "constraints"),
    [
        ({"level": None}, {KF}),  # safety인데 level null
        ({"area": None}, {KF}),  # safety인데 area null
        ({"channel": "sms"}, {KF}),  # safety인데 channel 값
        ({"kind": "trusted_contact", "level": "red", "area": None, "channel": "sms"}, {KF}),
        ({"kind": "trusted_contact", "level": None, "area": "scam", "channel": "sms"}, {KF}),
        ({"kind": "trusted_contact", "level": None, "area": None, "channel": None}, {KF}),
        ({"kind": "other"}, {"ck_guardian_notices_kind", KF}),
        ({"level": "green"}, {"ck_guardian_notices_level"}),  # red·yellow만
        ({"area": "name_lending"}, {"ck_guardian_notices_area"}),
        ({"kind": "trusted_contact", "level": None, "area": None, "channel": "fax"}, {"ck_guardian_notices_channel"}),
        ({"origin": "real_check"}, {"ck_guardian_notices_origin"}),  # 2차 값 선추가 금지
    ],
)
def test_guardian_notices_check_rejects_on_postgres(pg_app, values, constraints):
    env = pg_app
    child_id = env.login_child()  # 실제 아이 — 외래 키 위반이 아니라 CHECK 위반으로 거부되는지 본다
    engine = env.client.app.state.engine

    with pytest.raises(IntegrityError) as caught:
        _insert_notice(engine, child_id, **values)

    # 어긋난 CHECK가 둘 이상인 경우(kind = other)는 PostgreSQL이 그중 하나를 보고한다 — 기대 집합 안인지 본다
    diag = caught.value.orig.diag
    assert diag.table_name == "guardian_notices"
    assert diag.constraint_name in constraints, diag.constraint_name
    with engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(GuardianNotice.__table__)) == 0
