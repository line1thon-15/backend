"""draw_index 고유 인덱스 Alembic 리비전 (T-99 ① — DECISIONS #140, ADR-0023 규칙 1·5·7(f)).

DB는 pytest tmp_path(OS 임시 디렉터리)의 SQLite 파일. alembic env.py는 Settings()로 DATABASE_URL을 읽으므로
monkeypatch 환경 변수로 임시 DB를 가리킨다(.env 미사용). PostgreSQL 쪽은 `test_postgres_constraints.py`(CI 전용).
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db import models  # noqa: F401  (메타데이터 등록)
from tests.integration.helpers.draw_index_cases import (
    RENUMBERED,
    draw_indexes_by_id,
    expected_by_id,
    insert_duplicate_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REVISION = "20261115_06"
PREVIOUS_REVISION = "20261112_05"
INDEX_NAME = "uq_practice_sessions_child_origin_draw"


@pytest.fixture
def alembic_env(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'draw_index.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(REPO_ROOT / "alembic.ini"))
    engine = create_engine(url)
    yield config, engine
    engine.dispose()


def _index(engine):
    return {index["name"]: index for index in inspect(engine).get_indexes("practice_sessions")}.get(INDEX_NAME)


def test_head_is_draw_index_revision_after_guardian_notices(alembic_env):
    config, _ = alembic_env
    script = ScriptDirectory.from_config(config)

    assert script.get_current_head() == REVISION
    assert script.get_revision(REVISION).down_revision == PREVIOUS_REVISION


def test_upgrade_creates_unique_index(alembic_env):
    config, engine = alembic_env

    command.upgrade(config, "head")

    index = _index(engine)
    assert index is not None
    assert index["column_names"] == ["child_id", "origin", "draw_index"]
    assert index["unique"]


def test_upgrade_renumbers_existing_duplicates(alembic_env, capsys):
    config, engine = alembic_env
    command.upgrade(config, PREVIOUS_REVISION)
    insert_duplicate_rows(engine)
    capsys.readouterr()

    command.upgrade(config, "head")

    assert draw_indexes_by_id(engine) == expected_by_id()
    assert _index(engine) is not None
    # 출력에는 다시 매긴 행 수만 — 아이 ID 등 식별값 금지 (ADR-0023 규칙 5)
    out = capsys.readouterr().out
    assert f"draw_index renumbered rows: {RENUMBERED}" in out
    assert "00000000-0000-0000-0000-00000000000a" not in out and "0000000000000000000000000000000a" not in out


def test_upgrade_without_duplicates_renumbers_nothing(alembic_env, capsys):
    config, engine = alembic_env
    command.upgrade(config, PREVIOUS_REVISION)
    capsys.readouterr()

    command.upgrade(config, "head")

    assert "draw_index renumbered rows: 0" in capsys.readouterr().out


def test_downgrade_drops_index_and_keeps_numbers(alembic_env):
    config, engine = alembic_env
    command.upgrade(config, PREVIOUS_REVISION)
    insert_duplicate_rows(engine)
    command.upgrade(config, "head")

    command.downgrade(config, PREVIOUS_REVISION)

    assert _index(engine) is None
    assert draw_indexes_by_id(engine) == expected_by_id()  # 번호는 되돌리지 않는다

    command.upgrade(config, "head")
    assert _index(engine) is not None
