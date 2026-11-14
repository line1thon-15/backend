"""AI_CLIENT=http + 가짜 AI 서버로 같은 시나리오 다시 도전 (T-95 — PR #25 팀원 리뷰 권고, 2026-11-14 사용자 결정).

AI 서버의 `AI_PROVIDER=fake`는 고정 문장이라 변형이 항상 실패 → `source="fallback"` + 원본(`base_as_variant`)을
돌려준다(ai dev e82ea66 `app/variation.py:76`). 그 상태에서 다시 도전하면 직전과 같은 platform·tone이 와서
이전에는 VA4로 503이었다. 여기서는 그 응답을 httpx.MockTransport 가짜 서버로 재현한다 — 실제 네트워크 호출 0회.
variant 외 경로는 FakePracticeAI 응답을 JSON으로 직렬화해 돌려준다(HTTP 왕복은 실제 HttpPracticeAI 코드를 탄다).
"""

import json
import random
from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai_client.fake import FakePracticeAI
from app.ai_client.http_client import HttpPracticeAI
from app.ai_client.ports import (
    FeedbackRequest,
    JudgeRequest,
    StartRequest,
    TurnRequest,
    VariantRequest,
)
from app.core.config import Settings
from app.db.base import Base
from app.db.models import PracticeSession
from app.main import create_app
from tests.integration.test_practice_result import LEVELS, ResultEnv
from tests.integration.test_practice_sessions import SCENARIO_CLUES

TOKEN = "test-internal-token"
# AI fallback = 원본 시나리오 값 — variation_axes 밖일 수 있다
BASE_PAIR = ("original_platform", "원래 말투")


class FakeAIServer:
    """AI 서버(AI_PROVIDER=fake)처럼 동작하는 MockTransport 핸들러 — variant는 항상 fallback(원본)."""

    def __init__(self) -> None:
        self._fake = FakePracticeAI(scenario_clue_ids=SCENARIO_CLUES)
        self.variant_requests: list[dict] = []
        self.paths: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.headers.get("X-Internal-Token") != TOKEN:
            return httpx.Response(401, json={"error": "unauthorized"})
        body = json.loads(request.content)
        path = request.url.path
        self.paths.append(path)
        if path == "/internal/v1/practice/variant":
            self.variant_requests.append(body)
            response = self._fake.variant(VariantRequest.model_validate(body))
            response = response.model_copy(
                update={
                    "source": "fallback",
                    "variant": response.variant.model_copy(update={"platform": BASE_PAIR[0], "tone": BASE_PAIR[1]}),
                }
            )
        elif path == "/internal/v1/practice/start":
            response = self._fake.start(StartRequest.model_validate(body))
        elif path == "/internal/v1/practice/turn":
            response = self._fake.turn(TurnRequest.model_validate(body))
        elif path == "/internal/v1/practice/judge":
            response = self._fake.judge(JudgeRequest.model_validate(body))
        elif path == "/internal/v1/practice/feedback":
            response = self._fake.feedback(FeedbackRequest.model_validate(body))
        else:
            return httpx.Response(404, json={"error": "not_found"})
        return httpx.Response(200, json=response.model_dump(mode="json"))


@pytest.fixture
def http_env(tmp_path) -> Iterator[tuple[ResultEnv, FakeAIServer]]:
    server = FakeAIServer()
    ai = HttpPracticeAI(
        base_url="http://ai.test:8081",
        token=TOKEN,
        timeout_seconds=5.0,
        transport=httpx.MockTransport(server),
    )
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'http.db').as_posix()}", ai_client="http"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
        card_level_by_key=LEVELS,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield ResultEnv(client, ai), server
    ai.close()
    app.state.engine.dispose()


def test_same_scenario_retry_with_fallback_ai_server_is_201(http_env):
    env, server = http_env
    env.login_child(grade="H1")
    original_id = env.ended(("correct",))
    original = env.session_row(original_id)
    assert (original.variant["platform"], original.variant["tone"]) == BASE_PAIR
    server.variant_requests.clear()

    response = env.retry(original_id)

    assert response.status_code == 201, response.text
    assert response.json()["is_retry"] is True
    # 1회 재요청: 두 번째 요청은 직전(= 원본)·첫 응답과 다른 platform·tone (ADR-0019 결정 4)
    assert len(server.variant_requests) == 2
    first, second = server.variant_requests
    assert first["scenario_id"] == second["scenario_id"] == original.scenario_id
    assert (second["platform"], second["tone"]) != BASE_PAIR
    row = env.session_row(response.json()["session_id"])
    assert row.scenario_id == original.scenario_id
    assert (row.variant["platform"], row.variant["tone"]) == BASE_PAIR  # 같은 모습 허용


def test_retry_chain_with_fallback_ai_server_keeps_working(http_env):
    # 다시 도전의 다시 도전도 막히지 않는다 (결과 화면 can_retry → A15)
    env, _server = http_env
    env.login_child(grade="H1")
    first_id = env.ended(("correct",))
    retry = env.retry(first_id)
    assert retry.status_code == 201, retry.text
    retry_view = retry.json()
    retry_id = retry_view["session_id"]
    from tests.integration.test_practice_sessions import choice_id_of

    ended = env.answer(retry_id, choice_id_of(retry_view, "correct", env)).json()
    assert ended["status"] == "ended", ended

    again = env.retry(retry_id)

    assert again.status_code == 201, again.text
    assert env.count(PracticeSession) == 3
