from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import verify_password
from app.db.base import Base
from app.db.models import Child
from app.main import create_app


@pytest.fixture
def pin_reset_client(sqlite_url: str) -> Iterator[TestClient]:
    app = create_app(
        Settings(_env_file=None, database_url=sqlite_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def _register_guardian(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/v1/guardians",
        json={"email": email, "password": "correct-horse-42"},
    )
    assert response.status_code == 201


def _register_child(client: TestClient, pin: str = "1234") -> dict[str, str]:
    response = client.post(
        "/api/v1/children",
        json={
            "consent_agreed": True,
            "consent_version": "v1",
            "nickname": "sky",
            "grade": "E6",
            "pin": pin,
        },
    )
    assert response.status_code == 201
    return response.json()


def _child_login(client: TestClient, link_code: str, pin: str):
    return client.post(
        "/api/v1/auth/child/login",
        json={"link_code": link_code, "pin": pin},
    )


def test_pin_reset_replaces_pin_without_returning_plaintext(pin_reset_client):
    _register_guardian(pin_reset_client, "parent@example.com")
    child = _register_child(pin_reset_client)

    response = pin_reset_client.post(
        f"/api/v1/children/{child['child_id']}/pin-reset",
        json={"pin": "5678"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "5678" not in response.text

    with pin_reset_client.app.state.session_factory() as session:
        record = session.scalar(
            select(Child).where(Child.id == UUID(child["child_id"]))
        )

    assert record is not None
    assert record.pin_hash != "5678"
    assert verify_password("5678", record.pin_hash)

    old_pin_login = _child_login(pin_reset_client, child["link_code"], "1234")
    new_pin_login = _child_login(pin_reset_client, child["link_code"], "5678")

    assert old_pin_login.status_code == 401
    assert old_pin_login.json()["error"]["code"] == "INVALID_CODE_OR_PIN"
    assert new_pin_login.status_code == 200


def test_invalid_pin_reset_keeps_previous_pin(pin_reset_client):
    _register_guardian(pin_reset_client, "parent@example.com")
    child = _register_child(pin_reset_client)

    with pin_reset_client.app.state.session_factory() as session:
        record = session.scalar(
            select(Child).where(Child.id == UUID(child["child_id"]))
        )
        original_hash = record.pin_hash

    response = pin_reset_client.post(
        f"/api/v1/children/{child['child_id']}/pin-reset",
        json={"pin": "12a4"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    with pin_reset_client.app.state.session_factory() as session:
        record = session.scalar(
            select(Child).where(Child.id == UUID(child["child_id"]))
        )

    assert record is not None
    assert record.pin_hash == original_hash
    assert _child_login(pin_reset_client, child["link_code"], "1234").status_code == 200


def test_link_code_reissue_invalidates_old_code_and_returns_new_code(
    pin_reset_client,
    monkeypatch,
):
    choices = iter("AAAAAABBBBBB")
    monkeypatch.setattr(
        "app.services.children.secrets.choice",
        lambda _alphabet: next(choices),
    )
    _register_guardian(pin_reset_client, "parent@example.com")
    child = _register_child(pin_reset_client)

    response = pin_reset_client.post(
        f"/api/v1/children/{child['child_id']}/link-code"
    )

    assert response.status_code == 200
    assert set(response.json()) == {"link_code"}
    new_link_code = response.json()["link_code"]
    assert new_link_code == "BBBBBB"
    assert "pin" not in response.text

    old_code_login = _child_login(pin_reset_client, child["link_code"], "1234")
    new_code_login = _child_login(pin_reset_client, new_link_code, "1234")

    assert old_code_login.status_code == 401
    assert new_code_login.status_code == 200


def test_other_guardian_cannot_reset_pin_or_reissue_link_code(pin_reset_client):
    _register_guardian(pin_reset_client, "first-parent@example.com")
    child = _register_child(pin_reset_client)
    other_client = TestClient(pin_reset_client.app)

    try:
        _register_guardian(other_client, "second-parent@example.com")
        reset_response = other_client.post(
            f"/api/v1/children/{child['child_id']}/pin-reset",
            json={"pin": "5678"},
        )
        code_response = other_client.post(
            f"/api/v1/children/{child['child_id']}/link-code"
        )
    finally:
        other_client.close()

    assert reset_response.status_code == 404
    assert reset_response.json()["error"]["code"] == "CHILD_NOT_FOUND"
    assert code_response.status_code == 404
    assert code_response.json()["error"]["code"] == "CHILD_NOT_FOUND"