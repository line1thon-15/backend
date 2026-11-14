"""factory.py — AI_CLIENT=http|fake 구현 선택 (Architecture "백엔드–AI 내부 API" 구현 선택 행)."""

import pytest
from pydantic import ValidationError

from app.ai_client.factory import build_practice_ai
from app.ai_client.fake import FakePracticeAI
from app.core.config import Settings


def make_settings(**overrides) -> Settings:
    return Settings(_env_file=None, database_url="sqlite://", **overrides)


def test_fake_setting_builds_fake_practice_ai():
    practice_ai = build_practice_ai(make_settings(ai_client="fake"))

    assert isinstance(practice_ai, FakePracticeAI)


def test_ai_client_defaults_to_fake(monkeypatch):
    monkeypatch.delenv("AI_CLIENT", raising=False)

    assert make_settings().ai_client == "fake"


def test_ai_client_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("AI_CLIENT", "http")

    assert make_settings().ai_client == "http"


def test_unknown_ai_client_value_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(ai_client="gemini")


def test_http_setting_builds_http_practice_ai():
    # T-94: AI_CLIENT=http → HttpPracticeAI (이전에는 NotImplementedError — 하네스 범위)
    from app.ai_client.http_client import HttpPracticeAI
    from app.core.config import AIServiceSettings

    ai_service = AIServiceSettings(_env_file=None, url="http://ai.test:8081", token="t", timeout_seconds=3.0)

    practice_ai = build_practice_ai(make_settings(ai_client="http"), ai_service_settings=ai_service)

    assert isinstance(practice_ai, HttpPracticeAI)


def test_http_setting_reads_ai_service_settings_from_environment(monkeypatch):
    from app.ai_client.http_client import HttpPracticeAI

    monkeypatch.setenv("AI_SERVICE_URL", "http://ai.test:8081")
    monkeypatch.setenv("AI_SERVICE_TOKEN", "env-token")
    monkeypatch.setenv("AI_SERVICE_TIMEOUT_SECONDS", "3")

    practice_ai = build_practice_ai(make_settings(ai_client="http"))

    assert isinstance(practice_ai, HttpPracticeAI)


def test_http_setting_without_token_fails_fast(monkeypatch, tmp_path):
    # 토큰 없이 http로 띄우면 첫 요청이 아니라 시작 시점에 실패한다 (.env 영향 차단: 빈 임시 폴더에서 실행)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AI_SERVICE_TOKEN", raising=False)

    with pytest.raises(ValidationError):
        build_practice_ai(make_settings(ai_client="http"))


def test_fake_setting_ignores_ai_service_placeholders(monkeypatch):
    # .env.example 플레이스홀더(<seconds>)가 남아 있어도 fake 경로는 AI 서비스 설정을 읽지 않는다
    monkeypatch.setenv("AI_SERVICE_TIMEOUT_SECONDS", "<seconds>")
    monkeypatch.delenv("AI_SERVICE_TOKEN", raising=False)

    practice_ai = build_practice_ai(make_settings(ai_client="fake"))

    assert isinstance(practice_ai, FakePracticeAI)


def test_fake_uses_content_scenario_clues():
    from app.ai_client.ports import VariantRequest
    from app.content.loader import load_content

    content = load_content()
    practice_ai = build_practice_ai(
        make_settings(ai_client="fake"),
        {sid: [clue.id for clue in entry.scenario.clues] for sid, entry in content.scenarios.items()},
    )

    for scenario_id, entry in content.scenarios.items():
        variant = practice_ai.variant(
            VariantRequest(scenario_id=scenario_id, platform="p", tone="t", context="c")
        ).variant
        assert [clue.id for clue in variant.clues] == [clue.id for clue in entry.scenario.clues]
