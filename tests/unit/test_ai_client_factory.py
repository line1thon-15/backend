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


def test_http_client_is_not_available_in_harness_scope():
    with pytest.raises(NotImplementedError):
        build_practice_ai(make_settings(ai_client="http"))
