"""AI 서비스를 HTTP로 부르는 PracticeAI·SummaryAI 구현 (AI_CLIENT=http, Tasks T-94).

계약: Architecture "1차 내부 API v1" — 기준 URL `{AI_SERVICE_URL}`, 경로 `/internal/v1/...`, JSON,
헤더 `X-Internal-Token`. 실패 처리: Architecture "백엔드 쪽 처리" 행 — 비2xx·연결 실패·시간 초과·
응답 스키마 위반은 모두 `AIUnavailableError`(→ 503 `AI_UNAVAILABLE`), 자동 재시도 없음.
응답 검증 규칙(VA·ST·TU·J'·V'·S)은 services 몫이다 — 여기서는 Pydantic 스키마 검증까지만 한다.

httpx는 이 파일에서만 import한다 (tests/unit/test_import_boundaries.py ②).
"""

import json
import math
import logging
from typing import TypeVar
from uuid import uuid4

import httpx
from pydantic import BaseModel, ValidationError

from app.ai_client.ports import (
    AIUnavailableError,
    FeedbackRequest,
    FeedbackResponse,
    JudgeRequest,
    JudgeResponse,
    StartRequest,
    StartResponse,
    SummaryRequest,
    SummaryResponse,
    TurnRequest,
    TurnResponse,
    VariantRequest,
    VariantResponse,
)
from app.core.config import AIServiceSettings

logger = logging.getLogger(__name__)

TOKEN_HEADER = "X-Internal-Token"
REQUEST_ID_HEADER = "X-Request-ID"

_ResponseT = TypeVar("_ResponseT", bound=BaseModel)


class HttpPracticeAI:
    """httpx 동기 클라이언트 1개를 재사용한다. `transport`는 테스트에서 모의 전송을 넣는 자리다."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not token or not token.strip():
            raise ValueError("AI service token must not be blank")
        if not (math.isfinite(timeout_seconds) and timeout_seconds > 0):
            raise ValueError("AI service timeout must be a positive finite number")
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            headers={TOKEN_HEADER: token},
            transport=transport,
            follow_redirects=False,
        )

    @classmethod
    def from_settings(
        cls, settings: AIServiceSettings, transport: httpx.BaseTransport | None = None
    ) -> "HttpPracticeAI":
        return cls(
            base_url=settings.url,
            token=settings.token.get_secret_value(),
            timeout_seconds=settings.timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    # ---- PracticeAI ---------------------------------------------------------

    def variant(self, request: VariantRequest) -> VariantResponse:
        return self._post("/internal/v1/practice/variant", request, VariantResponse)

    def start(self, request: StartRequest) -> StartResponse:
        return self._post("/internal/v1/practice/start", request, StartResponse)

    def turn(self, request: TurnRequest) -> TurnResponse:
        return self._post("/internal/v1/practice/turn", request, TurnResponse)

    def judge(self, request: JudgeRequest) -> JudgeResponse:
        return self._post("/internal/v1/practice/judge", request, JudgeResponse)

    def feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        return self._post("/internal/v1/practice/feedback", request, FeedbackResponse)

    # ---- SummaryAI ----------------------------------------------------------

    def summary(self, request: SummaryRequest) -> SummaryResponse:
        return self._post("/internal/v1/summary", request, SummaryResponse)

    # ---- 공통 ---------------------------------------------------------------

    def _post(self, path: str, request: BaseModel, response_model: type[_ResponseT]) -> _ResponseT:
        # 로그·예외 메시지에는 경로·상태·오류 종류만 남긴다 — 본문(아이 답 등)·토큰 금지 (Architecture "로깅")
        request_id = str(uuid4())
        try:
            response = self._client.post(
                path,
                json=request.model_dump(mode="json"),
                headers={REQUEST_ID_HEADER: request_id},
            )
        except httpx.TimeoutException as exc:
            raise self._unavailable(path, request_id, f"timeout ({type(exc).__name__})") from None
        except (httpx.HTTPError, httpx.InvalidURL, httpx.StreamError) as exc:
            # HTTPError 밖의 httpx 예외(잘못된 URL·스트림 오류)도 AI 실패로 본다 (T-94 리뷰 #1·#4)
            raise self._unavailable(path, request_id, f"transport error ({type(exc).__name__})") from None

        if not response.is_success:
            # 비2xx는 본문을 해석하지 않는다 (Architecture "AI 오류" 행)
            raise self._unavailable(path, request_id, f"status {response.status_code}")

        try:
            payload = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise self._unavailable(path, request_id, "response is not JSON") from None
        if not isinstance(payload, dict):
            raise self._unavailable(path, request_id, "response is not a JSON object")
        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            raise self._unavailable(
                path, request_id, f"response schema mismatch ({exc.error_count()} errors)"
            ) from None

    @staticmethod
    def _unavailable(path: str, request_id: str, reason: str) -> AIUnavailableError:
        logger.warning("AI service call failed path=%s request_id=%s reason=%s", path, request_id, reason)
        return AIUnavailableError(f"AI service call failed: {path} — {reason}")
