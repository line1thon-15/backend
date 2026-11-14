import tempfile
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    return f"sqlite:///{(Path(tempfile.gettempdir()) / 'line1thon-backend-local.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default_factory=_default_database_url)
    ai_client: Literal["http", "fake"] = "fake"
    cookie_secure: bool = False


class AIServiceSettings(BaseSettings):
    """AI 서비스 연결 설정 — `AI_CLIENT=http`일 때만 읽는다 (T-94, Architecture "시크릿과 환경 변수").

    `Settings`와 분리한 이유: fake 경로(테스트·로컬·E2E 기본)는 이 값을 쓰지 않으므로,
    `.env`에 플레이스홀더(`<seconds>` 등)가 남아 있어도 fake 서버 시작이 깨지지 않게 한다.
    """

    model_config = SettingsConfigDict(
        env_prefix="AI_SERVICE_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    url: str = "http://localhost:8081"  # AI_SERVICE_URL — 기준 URL (경로 /internal/v1/... 는 클라이언트가 붙인다)
    token: SecretStr = Field(min_length=1)  # AI_SERVICE_TOKEN — 시크릿, AI 쪽 AI_INTERNAL_TOKEN과 같은 값
    # AI_SERVICE_TIMEOUT_SECONDS — AI 쪽 Gemini 호출 시간 초과(기본 20초)보다 길어야 한다 (Architecture 권고)
    timeout_seconds: float = Field(default=30.0, gt=0)