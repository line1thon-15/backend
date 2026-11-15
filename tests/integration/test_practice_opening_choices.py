"""T-100 — variant 응답의 `opening_choices`를 저장하고 같은 세션의 이후 요청에 그대로 보낸다.

근거: DECISIONS #137(1A)·#138(2A), ADR-0022 규칙 1~5, Tasks T-100 완료 조건 ②'(a)~(f).
AI는 httpx.MockTransport 가짜 서버(실제 네트워크 호출 0회)로 격리한다 — HTTP 왕복과 응답 스키마 검증은
실제 HttpPracticeAI 코드를 탄다. 응답 본문은 FakePracticeAI를 JSON으로 직렬화해 만든다.
DB는 테스트마다 pytest tmp_path의 SQLite 파일.
"""

import json
import random
from collections.abc import Callable, Iterator
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai_client.fake import FakePracticeAI
from app.ai_client.http_client import HttpPracticeAI
from app.ai_client.ports import (
    FeedbackRequest,
    JudgeRequest,
    OpeningChoices,
    StartRequest,
    TurnRequest,
    VariantRequest,
)
from app.core.config import Settings
from app.db.base import Base
from app.db.models import PracticeSession, PracticeTurn
from app.main import create_app
from tests.integration.test_practice_result import LEVELS, ResultEnv
from tests.integration.test_practice_sessions import SCENARIO_CLUES, choice_id_of

TOKEN = "test-internal-token"
OPENING = {
    "correct": "이렇게 많이 주는 건 이상해. 안 할래.",
    "doubtful": "좀 이상하긴 한데, 그래도 해 볼게.",
    "other": "좋아. 바로 할게.",
}


class FakeAIServer:
    """AI 서버처럼 동작하는 MockTransport 핸들러 — 경로별 요청 본문을 기록한다.

    `variant_patch`: variant 응답 JSON의 `variant` 객체를 고치는 함수(형태 위반 주입용).
    """

    def __init__(self, opening_choices: dict | None) -> None:
        self._fake = FakePracticeAI(
            scenario_clue_ids=SCENARIO_CLUES,
            opening_choices=OpeningChoices(**opening_choices) if opening_choices else None,
        )
        self.bodies: dict[str, list[dict]] = {}
        self.variant_patch: Callable[[dict], dict] | None = None

    def requests(self, name: str) -> list[dict]:
        return self.bodies.get(name, [])

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.headers.get("X-Internal-Token") != TOKEN:
            return httpx.Response(401, json={"error": "unauthorized"})
        body = json.loads(request.content)
        name = request.url.path.rsplit("/", 1)[-1]
        self.bodies.setdefault(name, []).append(body)
        if name == "variant":
            payload = self._fake.variant(VariantRequest.model_validate(body)).model_dump(mode="json")
            if self.variant_patch is not None:
                payload["variant"] = self.variant_patch(payload["variant"])
            return httpx.Response(200, json=payload)
        handlers = {
            "start": (StartRequest, self._fake.start),
            "turn": (TurnRequest, self._fake.turn),
            "judge": (JudgeRequest, self._fake.judge),
            "feedback": (FeedbackRequest, self._fake.feedback),
        }
        if name not in handlers:
            return httpx.Response(404, json={"error": "not_found"})
        model, handler = handlers[name]
        return httpx.Response(200, json=handler(model.model_validate(body)).model_dump(mode="json"))


def _make_env(tmp_path, opening_choices: dict | None) -> Iterator[tuple[ResultEnv, FakeAIServer]]:
    server = FakeAIServer(opening_choices)
    ai = HttpPracticeAI(
        base_url="http://ai.test:8081",
        token=TOKEN,
        timeout_seconds=5.0,
        transport=httpx.MockTransport(server),
    )
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 't100.db').as_posix()}", ai_client="http"),
        practice_ai=ai,
        rng_factory=lambda: random.Random(1234),
        card_level_by_key=LEVELS,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield ResultEnv(client, ai), server
    ai.close()
    app.state.engine.dispose()


@pytest.fixture
def with_opening(tmp_path) -> Iterator[tuple[ResultEnv, FakeAIServer]]:
    yield from _make_env(tmp_path, OPENING)


@pytest.fixture
def without_opening(tmp_path) -> Iterator[tuple[ResultEnv, FakeAIServer]]:
    yield from _make_env(tmp_path, None)


def _play_to_end(env: ResultEnv) -> str:
    """시작 → 첫 답(계속) → 끝날 때까지 정답 → 결과 조회(feedback 호출은 A18 결과에서). 그 세션 id."""
    view = env.started()
    session_id = view["session_id"]
    view = env.answer(session_id, choice_id_of(view, "other", env)).json()
    while view["status"] != "ended":
        view = env.answer(session_id, choice_id_of(view, "correct", env)).json()
    result = env.result(session_id)
    assert result.status_code == 200, result.text
    return session_id


# ---- (a) 저장 ---------------------------------------------------------------


def test_opening_choices_stored_in_session_variant(with_opening):
    env, _server = with_opening
    env.login_child(grade="H1")

    session_id = env.started()["session_id"]

    assert env.session_row(session_id).variant["opening_choices"] == OPENING


# ---- (b)(c) start·turn·judge·feedback 요청에 그대로 ---------------------------


def test_start_request_carries_received_opening_choices(with_opening):
    env, server = with_opening
    env.login_child(grade="H1")

    env.started()

    (start,) = server.requests("start")
    assert start["variant"]["opening_choices"] == OPENING


def test_later_requests_carry_same_opening_choices(with_opening):
    env, server = with_opening
    env.login_child(grade="H1")

    _play_to_end(env)

    for name in ("turn", "judge", "feedback"):
        bodies = server.requests(name)
        assert bodies, name
        assert all(body["variant"]["opening_choices"] == OPENING for body in bodies), name


# ---- (d) 하위 호환 ------------------------------------------------------------


def test_variant_without_opening_choices_still_works_and_sends_null(without_opening):
    env, server = without_opening
    env.login_child(grade="H1")

    session_id = _play_to_end(env)

    assert env.session_row(session_id).variant["opening_choices"] is None
    for name in ("start", "turn", "judge", "feedback"):
        bodies = server.requests(name)
        assert bodies, name
        for body in bodies:
            assert "opening_choices" in body["variant"], name  # 키 생략이 아니라 null (#138 2A)
            assert body["variant"]["opening_choices"] is None, name


def test_stored_variant_without_key_still_works_and_sends_null(with_opening):
    # T-100 이전에 저장된 세션: variant JSON에 opening_choices 키 자체가 없다 (데이터 이전 없음)
    env, server = with_opening
    env.login_child(grade="H1")
    view = env.started()
    session_id = view["session_id"]
    with env.session_factory() as db:
        row = db.get(PracticeSession, UUID(session_id))
        row.variant = {key: value for key, value in row.variant.items() if key != "opening_choices"}
        db.commit()
    assert "opening_choices" not in env.session_row(session_id).variant

    response = env.answer(session_id, choice_id_of(view, "other", env))

    assert response.status_code == 200, response.text
    (turn,) = server.requests("turn")
    assert turn["variant"]["opening_choices"] is None


# ---- (e) 형태·길이 위반 → 503·저장 0건·재요청 없음 ------------------------------


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param(lambda v: {**v, "opening_choices": {"correct": "a", "doubtful": "b"}}, id="missing-key"),
        pytest.param(lambda v: {**v, "opening_choices": {**OPENING, "doubtful": ""}}, id="empty"),
        pytest.param(lambda v: {**v, "opening_choices": {**OPENING, "other": "가" * 61}}, id="61-chars"),
        pytest.param(lambda v: {**v, "opening_choices": "정답"}, id="not-object"),
    ],
)
def test_invalid_opening_choices_is_503_without_saving_or_retry(with_opening, patch):
    env, server = with_opening
    env.login_child(grade="H1")
    server.variant_patch = patch

    response = env.start()

    assert response.status_code == 503, response.text
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert env.count(PracticeSession) == 0
    assert env.count(PracticeTurn) == 0
    assert len(server.requests("variant")) == 1  # 스키마 위반은 재요청하지 않는다 (ADR-0019 #133)
    assert server.requests("start") == []


def test_boundary_60_chars_is_accepted(with_opening):
    env, server = with_opening
    env.login_child(grade="H1")
    long = {**OPENING, "correct": "가" * 60}
    server.variant_patch = lambda v: {**v, "opening_choices": long}

    session_id = env.started()["session_id"]

    assert env.session_row(session_id).variant["opening_choices"] == long
    assert server.requests("start")[0]["variant"]["opening_choices"] == long


# ---- (f) start 선택지 일치는 검증하지 않는다 -----------------------------------


def test_start_choices_not_matching_opening_choices_is_not_an_error(with_opening):
    # FakePracticeAI.start는 opening_choices와 무관한 템플릿 선택지를 준다 — 백엔드는 일치를 검증하지 않는다 (ADR-0022 규칙 4)
    env, _server = with_opening
    env.login_child(grade="H1")

    response = env.start()

    assert response.status_code == 201, response.text
    texts = {choice["text"] for choice in response.json()["turn"]["choices"]}
    assert texts.isdisjoint(OPENING.values())
