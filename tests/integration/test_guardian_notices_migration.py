"""T-25 guardian_notices 테이블 — Alembic 20261112_05 upgrade·downgrade와 CHECK 제약.

근거: Architecture 엔티티 guardian_notices 행(열·CHECK — DECISIONS #92·#95), 테스트 전략 ⑥ "guardian_notices CHECK:
safety인데 level 또는 area null 삽입 → DB 오류, trusted_contact인데 level 값 → DB 오류". 2026-11-12 사용자 답
"T-25에 포함 (추천)". DB는 pytest tmp_path SQLite 파일, DATABASE_URL은 monkeypatch 환경 변수(.env 미사용).
"""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db import models  # noqa: F401  (메타데이터 등록)
from app.db.base import Base

REPO_ROOT = Path(__file__).resolve().parents[2]
REVISION = "20261112_05"
PREVIOUS_REVISION = "20261112_04"
TABLE = "guardian_notices"
T0 = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def alembic_env(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'notices.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(REPO_ROOT / "alembic.ini"))
    engine = create_engine(url)
    yield config, engine
    engine.dispose()


@pytest.fixture
def migrated(alembic_env):
    config, engine = alembic_env
    command.upgrade(config, "head")
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
    return engine


def test_head_is_t25_revision_after_practice_tables(alembic_env):
    config, _ = alembic_env
    script = ScriptDirectory.from_config(config)

    assert script.get_current_head() == REVISION
    assert script.get_revision(REVISION).down_revision == PREVIOUS_REVISION


def test_upgrade_creates_table_matching_model(alembic_env):
    config, engine = alembic_env

    command.upgrade(config, "head")

    inspector = inspect(engine)
    migrated = {column["name"] for column in inspector.get_columns(TABLE)}
    modeled = {column.name for column in Base.metadata.tables[TABLE].columns}
    assert migrated == modeled == {"id", "child_id", "kind", "level", "area", "channel", "origin", "occurred_at"}
    assert any(index["column_names"] == ["child_id"] for index in inspector.get_indexes(TABLE))
    assert [fk["referred_table"] for fk in inspector.get_foreign_keys(TABLE)] == ["children"]


def test_no_content_columns(alembic_env):
    # 본문·원문·이미지·감정 열 없음 (F-41 ③⑤)
    config, engine = alembic_env
    command.upgrade(config, "head")

    columns = {column["name"] for column in inspect(engine).get_columns(TABLE)}

    assert not columns & {"text", "message", "body", "masked_text", "image", "image_url", "emotion", "detail", "cue_id"}


def test_downgrade_removes_only_guardian_notices(alembic_env):
    config, engine = alembic_env
    command.upgrade(config, "head")

    command.downgrade(config, PREVIOUS_REVISION)

    tables = set(inspect(engine).get_table_names())
    assert TABLE not in tables
    assert {"guardians", "children", "practice_sessions", "practice_turns", "cue_results"} <= tables


def test_upgrade_again_after_downgrade(alembic_env):
    config, engine = alembic_env
    command.upgrade(config, "head")
    command.downgrade(config, PREVIOUS_REVISION)

    command.upgrade(config, "head")

    assert TABLE in set(inspect(engine).get_table_names())


def _insert(engine, **values) -> None:
    row = {
        "id": uuid4().hex,
        "child_id": uuid4().hex,
        "kind": "safety",
        "level": "red",
        "area": "scam",
        "channel": None,
        "origin": "demo_seed",
        "occurred_at": T0.isoformat(),
    }
    row.update(values)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(
            text(
                "INSERT INTO guardian_notices (id, child_id, kind, level, area, channel, origin, occurred_at) "
                "VALUES (:id, :child_id, :kind, :level, :area, :channel, :origin, :occurred_at)"
            ),
            row,
        )


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"level": "yellow", "area": "friend_pressure", "origin": "live"},
        {"kind": "trusted_contact", "level": None, "area": None, "channel": "call"},
        {"kind": "trusted_contact", "level": None, "area": None, "channel": "sms"},
    ],
)
def test_valid_rows_are_accepted(migrated, values):
    _insert(migrated, **values)


@pytest.mark.parametrize(
    "values",
    [
        {"level": None},  # safety인데 level null
        {"area": None},  # safety인데 area null
        {"channel": "sms"},  # safety인데 channel 값
        {"kind": "trusted_contact", "level": "red", "area": None, "channel": "sms"},  # trusted_contact인데 level 값
        {"kind": "trusted_contact", "level": None, "area": "scam", "channel": "sms"},  # trusted_contact인데 area 값
        {"kind": "trusted_contact", "level": None, "area": None, "channel": None},  # trusted_contact인데 channel null
        {"kind": "other"},
        {"level": "green"},  # red·yellow만
        {"area": "name_lending"},
        {"origin": "real_check"},  # 2차 값 선추가 금지
    ],
)
def test_invalid_rows_are_rejected(migrated, values):
    with pytest.raises(IntegrityError):
        _insert(migrated, **values)


def test_model_metadata_has_same_check_constraint(tmp_path):
    # 테스트·앱이 create_all로 만든 테이블에도 같은 제약이 걸린다
    engine = create_engine(f"sqlite:///{(tmp_path / 'model.db').as_posix()}")
    Base.metadata.create_all(engine)
    try:
        with pytest.raises(IntegrityError):
            _insert(engine, level=None)
        _insert(engine)
    finally:
        engine.dispose()
