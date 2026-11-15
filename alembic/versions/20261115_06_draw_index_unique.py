"""T-99 ① 새 출제 순번 중복 방지: practice_sessions 고유 인덱스 (child_id, origin, draw_index).

DECISIONS #140, ADR-0023 규칙 1·5 (2026-11-15 사용자 답 "추천안대로 확정").
- 인덱스를 만들기 전에 기존 중복 묶음을 다시 매긴다: 묶음마다 `started_at`, 같으면 `id` 순으로 첫 행은 그대로,
  나머지는 그 아이·그 출처의 현재 최댓값 + 1부터 차례로. 방언 전용 SQL 없이 행을 읽어 개별 UPDATE(SQLite·PostgreSQL 공통).
- 출력은 다시 매긴 행 수만(아이 ID 등 식별값 금지).
- 다시 도전(`draw_index` NULL)은 두 DB 모두 고유 인덱스에서 서로 같지 않은 값으로 보므로 자동 제외.
- downgrade는 인덱스만 지운다(번호는 되돌리지 않는다).
"""

from itertools import groupby

from alembic import op
import sqlalchemy as sa


revision = "20261115_06"
down_revision = "20261112_05"
branch_labels = None
depends_on = None

INDEX_NAME = "uq_practice_sessions_child_origin_draw"

_sessions = sa.table(
    "practice_sessions",
    sa.column("id", sa.Uuid(as_uuid=True)),
    sa.column("child_id", sa.Uuid(as_uuid=True)),
    sa.column("origin", sa.String(16)),
    sa.column("draw_index", sa.Integer()),
    sa.column("started_at", sa.DateTime(timezone=True)),
)


def _renumber_duplicates(bind) -> int:
    rows = bind.execute(
        sa.select(_sessions.c.id, _sessions.c.child_id, _sessions.c.origin, _sessions.c.draw_index)
        .where(_sessions.c.draw_index.is_not(None))
        .order_by(
            _sessions.c.child_id,
            _sessions.c.origin,
            _sessions.c.draw_index,
            _sessions.c.started_at,
            _sessions.c.id,
        )
    ).all()
    maximum: dict[tuple, int] = {}
    for row in rows:
        key = (row.child_id, row.origin)
        maximum[key] = max(maximum.get(key, row.draw_index), row.draw_index)

    renumbered = 0
    for (child_id, origin, _draw_index), group in groupby(rows, key=lambda r: (r.child_id, r.origin, r.draw_index)):
        _first, *rest = list(group)
        for row in rest:
            maximum[(child_id, origin)] += 1
            bind.execute(
                sa.update(_sessions).where(_sessions.c.id == row.id).values(draw_index=maximum[(child_id, origin)])
            )
            renumbered += 1
    return renumbered


def upgrade() -> None:
    renumbered = _renumber_duplicates(op.get_bind())
    print(f"draw_index renumbered rows: {renumbered}")
    op.create_index(INDEX_NAME, "practice_sessions", ["child_id", "origin", "draw_index"], unique=True)


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="practice_sessions")
