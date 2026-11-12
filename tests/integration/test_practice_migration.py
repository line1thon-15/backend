"""T-15 Alembic 리비전(practice_sessions·practice_turns·cue_results) upgrade·downgrade.

DB는 pytest tmp_path(OS 임시 디렉터리)의 SQLite 파일. alembic env.py는 Settings()로 DATABASE_URL을 읽으므로
환경 변수로 임시 DB를 가리킨다(.env 파일은 읽지 않게 monkeypatch로 env 값을 우선 지정).
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config

from app.db.base import Base
from app.db import models  # noqa: F401  (메타데이터 등록)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRACTICE_TABLES = {"practice_sessions", "practice_turns", "cue_results"}
REVISION = "20261112_04"
PREVIOUS_REVISION = "20261111_03"


@pytest.fixture
def alembic_env(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(REPO_ROOT / "alembic.ini"))
    engine = create_engine(url)
    yield config, engine
    engine.dispose()


def _tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def test_upgrade_creates_practice_tables_matching_models(alembic_env):
    config, engine = alembic_env

    command.upgrade(config, "head")

    inspector = inspect(engine)
    assert PRACTICE_TABLES <= set(inspector.get_table_names())
    for table in PRACTICE_TABLES:
        migrated = {column["name"] for column in inspector.get_columns(table)}
        modeled = {column.name for column in Base.metadata.tables[table].columns}
        assert migrated == modeled, table
    turn_uniques = {tuple(u["column_names"]) for u in inspector.get_unique_constraints("practice_turns")}
    assert ("session_id", "turn_index") in turn_uniques


def test_t15_revision_is_in_history(alembic_env):
    # head는 이후 리비전(T-25 guardian_notices 20261112_05)으로 바뀐다 — T-15 리비전이 이력에 있는지만 본다
    from alembic.script import ScriptDirectory

    config, _ = alembic_env

    script = ScriptDirectory.from_config(config)
    assert REVISION in {revision.revision for revision in script.walk_revisions()}


def test_downgrade_removes_only_practice_tables(alembic_env):
    config, engine = alembic_env
    command.upgrade(config, "head")

    command.downgrade(config, PREVIOUS_REVISION)

    tables = _tables(engine)
    assert tables & PRACTICE_TABLES == set()
    assert {"guardians", "children", "child_settings", "auth_sessions"} <= tables


def test_upgrade_again_after_downgrade(alembic_env):
    config, engine = alembic_env
    command.upgrade(config, "head")
    command.downgrade(config, PREVIOUS_REVISION)

    command.upgrade(config, "head")

    assert PRACTICE_TABLES <= _tables(engine)


def test_cue_results_has_session_cue_unique_constraint(alembic_env):
    config, engine = alembic_env

    command.upgrade(config, "head")

    uniques = {tuple(u["column_names"]) for u in inspect(engine).get_unique_constraints("cue_results")}
    assert ("session_id", "cue_id") in uniques
    model_uniques = {
        tuple(c.name for c in constraint.columns)
        for constraint in Base.metadata.tables["cue_results"].constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("session_id", "cue_id") in model_uniques
