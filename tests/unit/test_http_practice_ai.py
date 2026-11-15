"""HttpPracticeAI — 백엔드 → AI 서비스 HTTP 호출 (Tasks T-94, Architecture "1차 내부 API v1"·"백엔드 쪽 처리").

외부 호출은 httpx.MockTransport로 격리한다 — 실제 네트워크 호출 0회.
요청·응답 본문은 tests/contracts/ai/ 계약 샘플(ai 저장소 dev 25a3ef4 사본 — T-102 재고정)을 쓴다.
응답 검증 규칙(VA·ST·TU·J'·V'·S)은 services 몫이라 여기서는 Pydantic 스키마 검증까지만 본다.
"""

import json
import logging
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from app.ai_client.http_client import HttpPracticeAI
from app.ai_client.ports import (
    AIUnavailableError,
    FeedbackRequest,
    FeedbackResponse,
    JudgeRequest,
    JudgeResponse,
    PracticeAI,
    StartRequest,
    StartResponse,
    SummaryAI,
    SummaryRequest,
    SummaryResponse,
    TurnRequest,
    TurnResponse,
    VariantRequest,
    VariantResponse,
)
from app.core.config import AIServiceSettings

CONTRACT_DIR = Path(__file__).resolve().parents[1] / "contracts" / "ai"

BASE_URL = "http://ai.test:8081"
TOKEN = "test-internal-token"

# (포트 메서드, 경로, 샘플 이름, 요청 모델, 응답 모델)
OPERATIONS = [
    ("variant", "/internal/v1/practice/variant", "practice.variant", VariantRequest, VariantResponse),
    ("start", "/internal/v1/practice/start", "practice.start", StartRequest, StartResponse),
    ("turn", "/internal/v1/practice/turn", "practice.turn", TurnRequest, TurnResponse),
    ("judge", "/internal/v1/practice/judge", "practice.judge", JudgeRequest, JudgeResponse),
    ("feedback", "/internal/v1/practice/feedback", "practice.feedback", FeedbackRequest, FeedbackResponse),
    ("summary", "/internal/v1/summary", "summary", SummaryRequest, SummaryResponse),
]
OPERATION_IDS = [op[0] for op in OPERATIONS]


def load_sample(name: str) -> dict:
    return json.loads((CONTRACT_DIR / f"{name}.json").read_text(encoding="utf-8"))


def make_ai(handler, *, base_url: str = BASE_URL, timeout_seconds: float = 7.5) -> HttpPracticeAI:
    return HttpPracticeAI(
        base_url=base_url,
        token=TOKEN,
        timeout_seconds=timeout_seconds,
        transport=httpx.MockTransport(handler),
    )


def sample_request(sample: str, request_model: type[BaseModel]) -> BaseModel:
    return request_model.model_validate(load_sample(f"{sample}.request"))


# ---- ① 포트 메서드별 요청·응답 매핑 -----------------------------------------


@pytest.mark.parametrize(("method", "path", "sample", "request_model", "response_model"), OPERATIONS, ids=OPERATION_IDS)
def test_each_port_method_posts_json_to_contract_path_and_parses_response(
    method, path, sample, request_model, response_model
):
    seen: list[httpx.Request] = []
    response_body = load_sample(f"{sample}.response")

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=response_body)

    request = sample_request(sample, request_model)
    result = getattr(make_ai(handler), method)(request)

    assert len(seen) == 1
    sent = seen[0]
    assert sent.method == "POST"
    assert str(sent.url) == f"{BASE_URL}{path}"
    assert sent.headers["X-Internal-Token"] == TOKEN
    assert sent.headers["Content-Type"] == "application/json"
    assert sent.headers.get("X-Request-ID")
    sent_body = json.loads(sent.content)
    assert sent_body == request.model_dump(mode="json")
    # 계약 샘플에 값이 있는 최상위 필드는 그대로 실려 간다
    for key, value in load_sample(f"{sample}.request").items():
        if not isinstance(value, (dict, list)):
            assert sent_body[key] == value
    assert isinstance(result, response_model)
    assert result == response_model.model_validate(response_body)


def test_variant_response_values_survive_mapping():
    body = load_sample("practice.variant.response")

    result = make_ai(lambda request: httpx.Response(200, json=body)).variant(
        sample_request("practice.variant", VariantRequest)
    )

    assert result.source == body["source"]
    assert result.variant.base_scenario_id == body["variant"]["base_scenario_id"]
    assert [clue.id for clue in result.variant.clues] == [clue["id"] for clue in body["variant"]["clues"]]


def test_summary_null_is_returned_as_none():
    result = make_ai(lambda request: httpx.Response(200, json={"summary": None})).summary(
        sample_request("summary", SummaryRequest)
    )

    assert result == SummaryResponse(summary=None)


def test_unknown_response_fields_are_ignored():
    # AI dev(e82ea66)가 추가한 선택 필드(hint·normal_feedback 등)에 깨지지 않는다 — 하위 호환
    body = load_sample("practice.start.response") | {"hint": "새 선택 필드"}

    result = make_ai(lambda request: httpx.Response(200, json=body)).start(
        sample_request("practice.start", StartRequest)
    )

    assert result == StartResponse.model_validate(load_sample("practice.start.response"))


@pytest.mark.parametrize("base_url", [BASE_URL + "/", BASE_URL + "//"])
def test_trailing_slash_in_base_url_does_not_double_the_path(base_url):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"summary": "요약"})

    make_ai(handler, base_url=base_url).summary(sample_request("summary", SummaryRequest))

    assert str(seen[0].url) == f"{BASE_URL}/internal/v1/summary"


def test_each_call_gets_its_own_request_id():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"summary": "요약"})

    ai = make_ai(handler)
    request = sample_request("summary", SummaryRequest)
    ai.summary(request)
    ai.summary(request)

    assert seen[0].headers["X-Request-ID"] != seen[1].headers["X-Request-ID"]


def test_configured_timeout_is_applied_to_every_phase():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"summary": "요약"})

    make_ai(handler, timeout_seconds=2.5).summary(sample_request("summary", SummaryRequest))

    assert seen[0].extensions["timeout"] == {"connect": 2.5, "read": 2.5, "write": 2.5, "pool": 2.5}


def test_http_practice_ai_satisfies_both_ports():
    ai = make_ai(lambda request: httpx.Response(200, json={}))

    assert isinstance(ai, PracticeAI)
    assert isinstance(ai, SummaryAI)


@pytest.mark.parametrize("timeout_seconds", [0, -1.0])
def test_non_positive_timeout_is_rejected(timeout_seconds):
    with pytest.raises(ValueError):
        make_ai(lambda request: httpx.Response(200, json={}), timeout_seconds=timeout_seconds)


@pytest.mark.parametrize("token", ["", "   "])
def test_blank_token_is_rejected(token):
    with pytest.raises(ValueError):
        HttpPracticeAI(base_url=BASE_URL, token=token, timeout_seconds=1.0)


# ---- ② 실패 → AIUnavailableError ------------------------------------------


def _raise(exc_type):
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc_type("boom", request=request)

    return handler


FAILURES = [
    ("read_timeout", _raise(httpx.ReadTimeout)),
    ("connect_timeout", _raise(httpx.ConnectTimeout)),
    ("connect_error", _raise(httpx.ConnectError)),
    ("remote_protocol_error", _raise(httpx.RemoteProtocolError)),
    ("http_500", lambda request: httpx.Response(500, json={"error": "internal_error"})),
    ("http_503", lambda request: httpx.Response(503, text="Service Unavailable")),
    ("http_401", lambda request: httpx.Response(401, json={"error": "unauthorized"})),
    ("http_422", lambda request: httpx.Response(422, json={"error": "invalid_request", "fields": ["x"]})),
    ("http_302", lambda request: httpx.Response(302, headers={"Location": "http://elsewhere.test/"})),
    ("body_not_json", lambda request: httpx.Response(200, text="<html>oops</html>")),
    ("body_json_list", lambda request: httpx.Response(200, json=[1, 2, 3])),
    ("body_empty", lambda request: httpx.Response(200, content=b"")),
    ("schema_missing_field", lambda request: httpx.Response(200, json={"source": "model"})),
    (
        "schema_wrong_literal",
        lambda request: httpx.Response(
            200, json=load_sample("practice.variant.response") | {"source": "gemini"}
        ),
    ),
]


@pytest.mark.parametrize("handler", [f[1] for f in FAILURES], ids=[f[0] for f in FAILURES])
def test_transport_status_and_schema_failures_become_ai_unavailable(handler):
    ai = make_ai(handler)

    with pytest.raises(AIUnavailableError) as excinfo:
        ai.variant(sample_request("practice.variant", VariantRequest))

    # 오류 메시지·원인 체인에 토큰이 실리지 않는다 (시크릿 관리)
    assert TOKEN not in str(excinfo.value)


@pytest.mark.parametrize(("method", "path", "sample", "request_model", "response_model"), OPERATIONS, ids=OPERATION_IDS)
def test_every_port_method_maps_5xx_to_ai_unavailable(method, path, sample, request_model, response_model):
    ai = make_ai(lambda request: httpx.Response(502, text="bad gateway"))

    with pytest.raises(AIUnavailableError):
        getattr(ai, method)(sample_request(sample, request_model))


@pytest.mark.parametrize(("method", "path", "sample", "request_model", "response_model"), OPERATIONS, ids=OPERATION_IDS)
def test_every_port_method_maps_schema_mismatch_to_ai_unavailable(
    method, path, sample, request_model, response_model
):
    ai = make_ai(lambda request: httpx.Response(200, json={"unexpected": True}))

    with pytest.raises(AIUnavailableError):
        getattr(ai, method)(sample_request(sample, request_model))


# ---- ③ 설정 — 환경 변수 ----------------------------------------------------


def test_ai_service_settings_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_URL", "http://ai.example:9000")
    monkeypatch.setenv("AI_SERVICE_TOKEN", "env-token")
    monkeypatch.setenv("AI_SERVICE_TIMEOUT_SECONDS", "12.5")

    settings = AIServiceSettings(_env_file=None)

    assert settings.url == "http://ai.example:9000"
    assert settings.token.get_secret_value() == "env-token"
    assert settings.timeout_seconds == 12.5


def test_ai_service_settings_defaults(monkeypatch):
    monkeypatch.delenv("AI_SERVICE_URL", raising=False)
    monkeypatch.delenv("AI_SERVICE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.setenv("AI_SERVICE_TOKEN", "env-token")

    settings = AIServiceSettings(_env_file=None)

    assert settings.url == "http://localhost:8081"
    assert settings.timeout_seconds == 30.0


def test_ai_service_token_is_required(monkeypatch):
    monkeypatch.delenv("AI_SERVICE_TOKEN", raising=False)

    with pytest.raises(ValidationError):
        AIServiceSettings(_env_file=None)


@pytest.mark.parametrize("timeout", ["0", "-3", "<seconds>"])
def test_invalid_timeout_setting_is_rejected(monkeypatch, timeout):
    monkeypatch.setenv("AI_SERVICE_TOKEN", "env-token")
    monkeypatch.setenv("AI_SERVICE_TIMEOUT_SECONDS", timeout)

    with pytest.raises(ValidationError):
        AIServiceSettings(_env_file=None)


def test_token_is_not_exposed_in_settings_repr(monkeypatch):
    monkeypatch.setenv("AI_SERVICE_TOKEN", "env-token-secret")

    settings = AIServiceSettings(_env_file=None)

    assert "env-token-secret" not in repr(settings)
    assert "env-token-secret" not in str(settings)


def test_from_settings_uses_configured_values():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"summary": "요약"})

    settings = AIServiceSettings(
        _env_file=None, url="http://ai.example:9000", token="cfg-token", timeout_seconds=4.0
    )
    ai = HttpPracticeAI.from_settings(settings, transport=httpx.MockTransport(handler))
    ai.summary(sample_request("summary", SummaryRequest))

    assert str(seen[0].url) == "http://ai.example:9000/internal/v1/summary"
    assert seen[0].headers["X-Internal-Token"] == "cfg-token"
    assert seen[0].extensions["timeout"]["read"] == 4.0


# ---- 리뷰 반영 (2026-11-14 reviewer 권고 #1·#4) ------------------------------


@pytest.mark.parametrize("timeout", ["inf", "-inf", "nan", "Infinity"])
def test_non_finite_timeout_setting_is_rejected(monkeypatch, timeout):
    # #1: inf는 gt=0을 통과해 호출 시 OverflowError(→ 500)가 났다
    monkeypatch.setenv("AI_SERVICE_TOKEN", "env-token")
    monkeypatch.setenv("AI_SERVICE_TIMEOUT_SECONDS", timeout)

    with pytest.raises(ValidationError):
        AIServiceSettings(_env_file=None)


@pytest.mark.parametrize("timeout_seconds", [float("inf"), float("nan")])
def test_non_finite_timeout_is_rejected_by_client(timeout_seconds):
    with pytest.raises(ValueError):
        make_ai(lambda request: httpx.Response(200, json={}), timeout_seconds=timeout_seconds)


def _raise_plain(exc):
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return handler


OTHER_HTTPX_FAILURES = [
    ("unsupported_protocol", _raise(httpx.UnsupportedProtocol)),
    ("decoding_error", _raise(httpx.DecodingError)),
    ("write_timeout", _raise(httpx.WriteTimeout)),
    ("pool_timeout", _raise(httpx.PoolTimeout)),
    ("read_error", _raise(httpx.ReadError)),
    ("proxy_error", _raise(httpx.ProxyError)),
    ("stream_closed", _raise_plain(httpx.StreamClosed())),
    ("invalid_url", _raise_plain(httpx.InvalidURL("bad url"))),
]


@pytest.mark.parametrize("handler", [f[1] for f in OTHER_HTTPX_FAILURES], ids=[f[0] for f in OTHER_HTTPX_FAILURES])
def test_other_httpx_failures_become_ai_unavailable(handler):
    with pytest.raises(AIUnavailableError):
        make_ai(handler).variant(sample_request("practice.variant", VariantRequest))


SECRET_CHILD_TEXT = "아이비밀답변-T94"


def _turn_request_with_child_text() -> TurnRequest:
    body = load_sample("practice.turn.request")
    body["messages"][-1]["text"] = SECRET_CHILD_TEXT
    return TurnRequest.model_validate(body)


LOGGED_FAILURES = [
    ("http_500_echoing_request", lambda request: httpx.Response(500, content=request.content)),
    ("http_401", lambda request: httpx.Response(401, json={"error": "unauthorized"})),
    ("schema_mismatch_echoing_request", lambda request: httpx.Response(200, content=request.content)),
    ("body_not_json", lambda request: httpx.Response(200, text=f"<html>{SECRET_CHILD_TEXT}</html>")),
    ("timeout", _raise(httpx.ReadTimeout)),
    ("connect_error", _raise(httpx.ConnectError)),
]


@pytest.mark.parametrize("handler", [f[1] for f in LOGGED_FAILURES], ids=[f[0] for f in LOGGED_FAILURES])
def test_failure_logs_do_not_contain_token_or_request_body(caplog, handler):
    # #4: 로그에는 경로·상태·오류 종류만 — 토큰·아이 답(요청 본문)·응답 본문 금지 (Architecture "로깅")
    caplog.set_level(logging.DEBUG)

    with pytest.raises(AIUnavailableError) as excinfo:
        make_ai(handler).turn(_turn_request_with_child_text())

    assert caplog.records, "실패는 경고 로그 1건을 남겨야 한다"
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "/internal/v1/practice/turn" in logged
    for secret in (TOKEN, SECRET_CHILD_TEXT):
        assert secret not in logged
        assert secret not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
