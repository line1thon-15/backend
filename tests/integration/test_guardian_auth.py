from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import verify_password
from app.db.base import Base
from app.db.models import AuthSession, Guardian
from app.main import create_app


@pytest.fixture
def auth_client(sqlite_url: str) -> Iterator[TestClient]:
    app = create_app(
        Settings(_env_file=None, database_url=sqlite_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


@pytest.fixture
def auth_client_no_raise(sqlite_url: str) -> Iterator[TestClient]:
    app = create_app(
        Settings(_env_file=None, database_url=sqlite_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.state.engine.dispose()


def test_guardian_registration_creates_account_and_session(auth_client):
    response = auth_client.post(
        "/api/v1/guardians",
        json={"email": "Parent@Example.com", "password": "correct-horse-42"},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"guardian_id"}
    assert response.cookies.get("sid")

    cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "path=/api" in cookie_header
    assert "samesite=lax" in cookie_header

    with auth_client.app.state.session_factory() as session:
        guardian = session.scalar(select(Guardian))
        auth_session = session.scalar(select(AuthSession))

    assert guardian is not None
    assert guardian.email == "parent@example.com"
    assert guardian.password_hash != "correct-horse-42"
    assert verify_password("correct-horse-42", guardian.password_hash)
    assert auth_session is not None
    assert auth_session.token_hash != response.cookies.get("sid")
    assert len(auth_session.token_hash) == 64


def test_guardian_registration_rejects_duplicate_email_case_insensitively(auth_client):
    payload = {"email": "Parent@Example.com", "password": "correct-horse-42"}
    first = auth_client.post("/api/v1/guardians", json=payload)
    second = auth_client.post(
        "/api/v1/guardians",
        json={"email": "parent@example.com", "password": "another-pass-42"},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_TAKEN"


def test_guardian_login_rejects_invalid_credentials(auth_client):
    response = auth_client.post(
        "/api/v1/auth/guardian/login",
        json={"email": "missing@example.com", "password": "wrong-pass-42"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert "sid" not in response.cookies


def test_guardian_login_returns_account_and_session(auth_client):
    registered = auth_client.post(
        "/api/v1/guardians",
        json={"email": "parent@example.com", "password": "correct-horse-42"},
    )

    response = auth_client.post(
        "/api/v1/auth/guardian/login",
        json={"email": "PARENT@example.com", "password": "correct-horse-42"},
    )

    assert registered.status_code == 201
    assert response.status_code == 200
    assert response.json() == {
        "guardian_id": registered.json()["guardian_id"],
        "has_children": False,
    }
    assert response.cookies.get("sid")


def test_request_validation_uses_common_error_envelope(auth_client):
    response = auth_client.post(
        "/api/v1/guardians",
        json={"email": "not-an-email", "password": "short"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert set(body) == {"error"}
    assert set(body["error"]["details"]["fields"]) == {"email", "password"}
    assert "not-an-email" not in response.text
    assert "short" not in response.text


def test_unknown_route_uses_common_error_envelope(auth_client):
    response = auth_client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unhandled_error_returns_internal_and_logs_request_id(
    auth_client_no_raise,
    monkeypatch,
    caplog,
):
    def fail_registration(_email: str, _password: str):
        raise RuntimeError("sensitive internal details")

    monkeypatch.setattr(
        auth_client_no_raise.app.state.auth_service,
        "register_guardian",
        fail_registration,
    )
    response = auth_client_no_raise.post(
        "/api/v1/guardians",
        json={"email": "parent@example.com", "password": "correct-horse-42"},
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL"
    assert "sensitive internal details" not in response.text
    assert "unhandled request error request_id=" in caplog.text