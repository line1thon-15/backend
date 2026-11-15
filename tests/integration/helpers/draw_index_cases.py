"""draw_index 마이그레이션 재번호 검증 데이터 (T-99 ① — ADR-0023 규칙 5·7(f)). SQLite·PostgreSQL 테스트가 같이 쓴다.

규칙 5: `(child_id, origin, draw_index)`가 같은 비NULL 행 묶음마다 `started_at`, 같으면 `id` 순으로 첫 행은 그대로,
나머지는 그 아이·그 출처의 현재 최댓값 + 1부터 차례로 다시 매긴다. 다시 도전(NULL)은 건드리지 않는다.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import Engine, select

from app.db.base import Base

T0 = datetime(2026, 11, 10, 3, 0, tzinfo=timezone.utc)
CHILD_A = UUID(int=0xA)
CHILD_B = UUID(int=0xB)

# (id 정수값, child, origin, draw_index, started_at 오프셋(분), 기대 draw_index)
ROWS = [
    # 아이 A live 순번 1 묶음 3행: 가장 이른 시각 2행 중 id 작은 쪽이 1을 유지, 나머지는 live 최댓값(2) + 1부터
    (0x101, CHILD_A, "live", 1, 0, 1),
    (0x102, CHILD_A, "live", 1, 0, 3),
    (0x100, CHILD_A, "live", 1, 10, 4),
    (0x103, CHILD_A, "live", 2, 20, 2),
    # 다시 도전은 NULL 그대로 여러 행
    (0x104, CHILD_A, "live", None, 30, None),
    (0x105, CHILD_A, "live", None, 31, None),
    # 아이 A 예시 순번 0 묶음 2행: 이른 행이 0 유지, 나머지는 예시 최댓값(1) + 1
    (0x201, CHILD_A, "demo_seed", 0, 0, 0),
    (0x200, CHILD_A, "demo_seed", 0, 5, 2),
    (0x202, CHILD_A, "demo_seed", 1, 6, 1),
    # 아이 B는 중복 없음 — 그대로. 같은 순번이라도 아이가 다르면 묶음이 아니다
    (0x301, CHILD_B, "live", 1, 0, 1),
]
RENUMBERED = sum(1 for _id, _c, _o, before, _m, after in ROWS if before != after)


def insert_duplicate_rows(engine: Engine, children: dict[UUID, UUID] | None = None) -> None:
    """인덱스가 없는 리비전(20261112_05) 상태의 DB에 중복 순번 행을 넣는다.

    `children`을 주지 않으면 아이 행 없이 CHILD_A·CHILD_B를 그대로 쓴다 — 외래 키 검사가 꺼진 SQLite 기본 연결 전용.
    PostgreSQL은 외래 키를 검사하므로 실제로 만든 아이 ID로 바꿔 넣는다(`{CHILD_A: 실제 ID, CHILD_B: 실제 ID}`)."""
    children = children or {}
    table = Base.metadata.tables["practice_sessions"]
    with engine.begin() as conn:
        for row_id, child_id, origin, draw_index, minutes, _expected in ROWS:
            conn.execute(
                table.insert().values(
                    id=UUID(int=row_id),
                    child_id=children.get(child_id, child_id),
                    mode="area" if draw_index is not None else "retry",
                    area="scam",
                    subtype=None,
                    scenario_id="scam_dm_parttime_01",
                    is_normal=False,
                    target_cue_ids=[],
                    variant={"platform": "sms", "tone": "friendly"},
                    scenario_title="제목",
                    child_setup="설정",
                    ai_role_name="상대",
                    retry_of=None,
                    draw_index=draw_index,
                    hint_level=None,
                    status="ended",
                    normal_outcome=None,
                    origin=origin,
                    started_at=T0 + timedelta(minutes=minutes),
                    ended_at=T0 + timedelta(minutes=minutes + 1),
                )
            )


def draw_indexes_by_id(engine: Engine) -> dict[int, int | None]:
    table = Base.metadata.tables["practice_sessions"]
    with engine.connect() as conn:
        return {row.id.int: row.draw_index for row in conn.execute(select(table.c.id, table.c.draw_index))}


def expected_by_id() -> dict[int, int | None]:
    return {row_id: expected for row_id, _c, _o, _d, _m, expected in ROWS}
