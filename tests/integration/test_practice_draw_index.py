"""새 출제 순번 `draw_index` 중복 방지 (T-99 ① — DECISIONS #140, ADR-0023 규칙 7 a~e).

근거: ADR-0023 결정 A — 고유 인덱스 `uq_practice_sessions_child_origin_draw` = `(child_id, origin, draw_index)`,
순번 = 그 아이 `origin = 'live'` 비NULL `draw_index` 최댓값 + 1(없으면 1, 예시 행은 세지 않음), 세션을 넣는 같은
저장 트랜잭션 안에서 계산, 이 인덱스 위반이면 순번만 다시 계산해 1회 재시도(AI 재호출 없음), 또 위반이면 500 `INTERNAL`.
리뷰 원문(PR #33 후속 권고 2): "P2: 동시 출제 요청 시 `count_new_draws() + 1`에 따른 `draw_index` 중복 가능성 검토 및
회귀 테스트 추가."

규칙 7 (f) 마이그레이션은 `test_draw_index_migration.py`. DB는 테스트마다 OS 임시 디렉터리(pytest tmp_path)의 SQLite 파일.
"""

import random
import threading
from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select

from app.core.config import Settings
from app.db.base import Base
from app.db.models import PracticeSession
from app.demo.plan import build_demo_plan
from app.demo.seed import seed_into_child
from app.main import create_app
from app.repositories.demo_seed import SqlAlchemyDemoSeedRepository
from app.repositories.practice import SqlAlchemyPracticeRepository
from tests.integration.helpers.practice_env import CONTENT, Env, RecordingPracticeAI

DEMO_NOW = datetime(2026, 11, 13, 3, 0, tzinfo=timezone.utc)
INDEX_NAME = "uq_practice_sessions_child_origin_draw"


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    ai = RecordingPracticeAI()
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'draw.db').as_posix()}", ai_client="fake"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
    )
    Base.metadata.create_all(app.state.engine)
    # 500 응답 자체를 단언하기 위해 서버 예외를 테스트로 다시 던지지 않는다
    with TestClient(app, raise_server_exceptions=False) as client:
        yield Env(client, ai)
    app.state.engine.dispose()


def live_draw_indexes(env: Env, child_id: UUID) -> list[int | None]:
    with env.session_factory() as db:
        return list(
            db.scalars(
                select(PracticeSession.draw_index)
                .where(PracticeSession.child_id == child_id, PracticeSession.origin == "live")
                .order_by(PracticeSession.started_at, PracticeSession.id)
            )
        )


def demo_count(env: Env, child_id: UUID) -> int:
    with env.session_factory() as db:
        return db.scalar(
            select(func.count())
            .select_from(PracticeSession)
            .where(PracticeSession.child_id == child_id, PracticeSession.origin == "demo_seed")
        )


def end_with_correct(env: Env, session_id: str) -> None:
    choice = next(c["id"] for c in env.turn_rows(session_id)[0].choices if c["kind"] == "correct")
    assert env.answer(session_id, choice).status_code == 200


# ---- 모델 -------------------------------------------------------------------------


def test_model_has_unique_index_on_child_origin_draw(env):
    indexes = {index["name"]: index for index in inspect(env.client.app.state.engine).get_indexes("practice_sessions")}

    assert INDEX_NAME in indexes
    assert indexes[INDEX_NAME]["column_names"] == ["child_id", "origin", "draw_index"]
    assert indexes[INDEX_NAME]["unique"]


# ---- (a) 동시 새 출제 --------------------------------------------------------------


def test_concurrent_new_draws_get_distinct_draw_index(env):
    """같은 아이의 새 출제 2건이 둘 다 AI 응답을 기다리는 동안 겹치게 한다(barrier) — 순번이 서로 달라야 한다."""
    child_id = env.login_child(grade="H1")
    barrier = threading.Barrier(2, timeout=5.0)

    def start_after_both_waiting(request, response):
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            pass
        return response

    env.ai.overrides["start"] = start_after_both_waiting
    results: list = [None, None]

    def worker(slot: int, mode: dict) -> None:
        results[slot] = env.client.post("/api/v1/practice/sessions", json=mode)

    threads = [
        threading.Thread(target=worker, args=(0, {"mode": "area", "area": "scam"})),
        threading.Thread(target=worker, args=(1, {"mode": "mission"})),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert [r.status_code for r in results] == [201, 201], [r.text for r in results]
    draws = sorted(live_draw_indexes(env, child_id))
    assert draws == [1, 2]


# ---- (b) 예시 행과의 관계 ----------------------------------------------------------


def test_first_live_draw_is_one_when_child_has_eight_demo_sessions(env):
    child_id = env.login_child(grade="H1")
    seed_into_child(SqlAlchemyDemoSeedRepository(env.session_factory), CONTENT, child_id, DEMO_NOW)
    assert demo_count(env, child_id) == 8

    view = env.started()

    assert env.session_row(view["session_id"]).draw_index == 1


def test_demo_seed_appends_to_child_with_live_draws(env):
    child_id = env.login_child(grade="H1")
    env.started()
    env.started()

    result = seed_into_child(SqlAlchemyDemoSeedRepository(env.session_factory), CONTENT, child_id, DEMO_NOW)

    assert result.sessions == 8
    assert demo_count(env, child_id) == 8
    assert live_draw_indexes(env, child_id) == [1, 2]
    # 예시 순번(0부터)은 그대로 — 실제 순번 1과 겹쳐도 출처가 달라 충돌하지 않는다 (ADR-0023 규칙 6)
    with env.session_factory() as db:
        demo = sorted(
            db.scalars(
                select(PracticeSession.draw_index).where(
                    PracticeSession.child_id == child_id, PracticeSession.origin == "demo_seed"
                )
            )
        )
    assert demo == list(range(8))


# ---- (c) 예시 계획 행 수가 줄어든 재적재 --------------------------------------------


def test_next_live_draw_after_smaller_demo_reseed_is_live_max_plus_one(env):
    child_id = env.login_child(grade="H1")
    repository = SqlAlchemyDemoSeedRepository(env.session_factory)
    seed_into_child(repository, CONTENT, child_id, DEMO_NOW)
    env.started()
    env.started()
    live_max = max(live_draw_indexes(env, child_id))
    plan = build_demo_plan(DEMO_NOW, CONTENT)
    assert repository.replace_demo_records(child_id, replace(plan, sessions=plan.sessions[:6]))
    assert demo_count(env, child_id) == 6

    response = env.start()

    assert response.status_code == 201, response.text
    assert env.session_row(response.json()["session_id"]).draw_index == live_max + 1
    draws = live_draw_indexes(env, child_id)
    assert len(draws) == len(set(draws)) == 3


# ---- (d) 다시 도전은 NULL ----------------------------------------------------------


def test_retries_store_null_draw_index_many_times(env):
    child_id = env.login_child(grade="H1")
    original = env.started()["session_id"]
    end_with_correct(env, original)

    first = env.client.post("/api/v1/practice/sessions", json={"mode": "retry", "retry_of": original})
    second = env.client.post("/api/v1/practice/sessions", json={"mode": "retry", "retry_of": original})

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert env.session_row(first.json()["session_id"]).draw_index is None
    assert env.session_row(second.json()["session_id"]).draw_index is None
    # 다시 도전은 순번을 쓰지 않는다 — 다음 새 출제는 2
    assert env.session_row(env.started()["session_id"]).draw_index == 2
    assert sorted(d for d in live_draw_indexes(env, child_id) if d is not None) == [1, 2]


# ---- (e) 충돌 시 1회 재시도 --------------------------------------------------------


def _force_conflicts(monkeypatch, conflicts: int) -> list[int]:
    """처음 `conflicts`번은 이미 있는 순번 1을 돌려줘 고유 인덱스 위반을 일으킨다. 반환값 = 계산 호출 기록."""
    original = SqlAlchemyPracticeRepository._next_draw_index
    calls: list[int] = []

    def patched(self, db, child_id):
        calls.append(1)
        if len(calls) <= conflicts:
            return 1
        return original(self, db, child_id)

    monkeypatch.setattr(SqlAlchemyPracticeRepository, "_next_draw_index", patched)
    return calls


def test_one_conflict_retries_once_without_new_ai_calls(env, monkeypatch):
    child_id = env.login_child(grade="H1")
    env.started()  # 순번 1
    calls = _force_conflicts(monkeypatch, conflicts=1)
    env.ai.calls.clear()

    response = env.start()

    assert response.status_code == 201, response.text
    assert env.session_row(response.json()["session_id"]).draw_index == 2
    assert env.ai.names() == ["variant", "start"]  # AI 재호출 없음
    assert len(calls) == 2  # 처음 계산 + 재시도 1회
    assert live_draw_indexes(env, child_id) == [1, 2]
    assert len(env.turn_rows(response.json()["session_id"])) == 1


def test_two_conflicts_is_500_internal_and_saves_nothing(env, monkeypatch):
    child_id = env.login_child(grade="H1")
    env.started()  # 순번 1
    calls = _force_conflicts(monkeypatch, conflicts=2)
    env.ai.calls.clear()

    response = env.start()

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL"
    assert len(calls) == 2  # 재시도는 1회뿐
    assert env.ai.names() == ["variant", "start"]
    assert live_draw_indexes(env, child_id) == [1]
