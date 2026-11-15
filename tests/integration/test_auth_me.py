from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.config import Settings
from app.core.security import hash_session_token
from app.db.base import Base
from app.db.models import AuthSession
from app.main import create_app


@pytest.fixture
def auth_me_client(tmp_path) -> Iterator[TestClient]:
    database_url = f"sqlite:///{(tmp_path / 'auth-me.db').as_posix()}"
    app = create_app(
        Settings(_env_file=None, database_url=database_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def _register_guardian(client: TestClient) -> tuple[str, str]:
    credentials = {
        "email": "parent@example.com",
        "password": "correct-horse-42",
    }
    response = client.post("/api/v1/guardians", json=credentials)
    assert response.status_code == 201
    return response.json()["guardian_id"], credentials["email"]


def _login_child(client: TestClient) -> UUID:
    _register_guardian(client)
    registration = client.post(
        "/api/v1/children",
        json={
            "consent_agreed": True,
            "consent_version": "v1",
            "nickname": "하늘이",
            "grade": "E6",
            "pin": "1234",
        },
    )
    assert registration.status_code == 201
    child_id = UUID(registration.json()["child_id"])
    login = client.post(
        "/api/v1/auth/child/login",
        json={"link_code": registration.json()["link_code"], "pin": "1234"},
    )
    assert login.status_code == 200
    return child_id


def test_auth_me_returns_guardian_identity(auth_me_client: TestClient):
    guardian_id, email = _register_guardian(auth_me_client)

    response = auth_me_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "role": "guardian",
        "guardian_id": guardian_id,
        "email": email,
    }


def test_auth_me_returns_child_identity_and_saved_display_settings(
    auth_me_client: TestClient,
):
    _login_child(auth_me_client)

    first_response = auth_me_client.get("/api/v1/auth/me")
    assert first_response.status_code == 200
    assert first_response.json() == {
        "role": "child",
        "nickname": "하늘이",
        "grade": "E6",
        "onboarding_completed": False,
        "display": {
            "font_scale": "normal",
            "high_contrast": False,
            "tts_enabled": False,
        },
    }

    save_response = auth_me_client.put(
        "/api/v1/me/onboarding",
        json={
            "display": {
                "font_scale": "xlarge",
                "high_contrast": True,
                "tts_enabled": True,
            },
            "trusted_contact": {"name": "엄마", "phone": "010-1234-5678"},
            "diagnosis_answers": [
                {"question_id": "q1", "option_id": "q1_a"},
                {"question_id": "q2", "option_id": "q2_b"},
                {"question_id": "q3", "option_id": "q3_c"},
            ],
            "favorite_apps": [],
        },
    )
    assert save_response.status_code == 200

    response = auth_me_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "role": "child",
        "nickname": "하늘이",
        "grade": "E6",
        "onboarding_completed": True,
        "display": {
            "font_scale": "xlarge",
            "high_contrast": True,
            "tts_enabled": True,
        },
    }


@pytest.mark.parametrize("session_token", [None, "not-a-valid-session-token"])
def test_auth_me_rejects_missing_or_invalid_session(
    auth_me_client: TestClient,
    session_token: str | None,
):
    if session_token is not None:
        auth_me_client.cookies.set("sid", session_token)

    response = auth_me_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("session_state", ["expired", "revoked"])
def test_auth_me_rejects_expired_or_revoked_session(
    auth_me_client: TestClient,
    session_state: str,
):
    _register_guardian(auth_me_client)
    session_token = auth_me_client.cookies.get("sid")
    assert session_token is not None

    values = (
        {"expires_at": datetime(2000, 1, 1, tzinfo=timezone.utc)}
        if session_state == "expired"
        else {"revoked_at": datetime.now(timezone.utc)}
    )
    with auth_me_client.app.state.session_factory.begin() as session:
        session.execute(
            update(AuthSession)
            .where(AuthSession.token_hash == hash_session_token(session_token))
            .values(**values)
        )

    response = auth_me_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
