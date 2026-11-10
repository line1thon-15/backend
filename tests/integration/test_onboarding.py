from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.db.models import Child, ChildSettings
from app.main import create_app


@pytest.fixture
def onboarding_client(tmp_path) -> Iterator[TestClient]:
    database_url = f"sqlite:///{(tmp_path / 'onboarding.db').as_posix()}"
    app = create_app(
        Settings(_env_file=None, database_url=database_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def _register_child(client: TestClient) -> tuple[str, UUID]:
    guardian = client.post(
        "/api/v1/guardians",
        json={"email": "parent@example.com", "password": "correct-horse-42"},
    )
    assert guardian.status_code == 201

    child = client.post(
        "/api/v1/children",
        json={
            "consent_agreed": True,
            "consent_version": "v1",
            "nickname": "하늘이",
            "grade": "E6",
            "pin": "1234",
        },
    )
    assert child.status_code == 201
    child_id = UUID(child.json()["child_id"])

    login = client.post(
        "/api/v1/auth/child/login",
        json={"link_code": child.json()["link_code"], "pin": "1234"},
    )
    assert login.status_code == 200
    return child.json()["link_code"], child_id


@pytest.mark.parametrize("font_scale", ["normal", "large", "xlarge"])
def test_onboarding_saves_settings_and_start_difficulty(onboarding_client, font_scale):
    _, child_id = _register_child(onboarding_client)

    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json={
            "display": {
                "font_scale": font_scale,
                "high_contrast": False,
                "tts_enabled": False,
            },
            "favorite_apps": [],
            "trusted_contact": {"name": "엄마", "phone": "010-1234-5678"},
            "diagnosis_answers": [
                {"question_id": "q1", "option_id": "그래요"},
                {"question_id": "q2", "option_id": "가끔"},
                {"question_id": "q3", "option_id": "아니에요"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"start_difficulty": 2}

    with onboarding_client.app.state.session_factory() as session:
        settings = session.get(ChildSettings, child_id)
        child = session.get(Child, child_id)

    assert settings is not None
    assert settings.font_scale == font_scale
    assert settings.trusted_contact_name == "엄마"
    assert settings.trusted_contact_phone == "010-1234-5678"
    assert settings.favorite_apps == []
    assert child is not None
    assert child.start_difficulty == 2
    assert child.onboarding_completed_at is not None


def test_onboarding_requires_child_login(onboarding_client):
    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json={
            "display": {
                "font_scale": "normal",
                "high_contrast": False,
                "tts_enabled": False,
            },
            "favorite_apps": [],
            "trusted_contact": {"name": "엄마", "phone": None},
            "diagnosis_answers": [
                {"question_id": "q1", "option_id": "그래요"},
                {"question_id": "q2", "option_id": "가끔"},
                {"question_id": "q3", "option_id": "아니에요"},
            ],
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
