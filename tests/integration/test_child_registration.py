import re
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
def child_client(sqlite_url: str) -> Iterator[TestClient]:
    app = create_app(
        Settings(_env_file=None, database_url=sqlite_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def _register_guardian(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/guardians",
        json={"email": email, "password": "correct-horse-42"},
    )
    assert response.status_code == 201
    return response.json()["guardian_id"]


def _child_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "consent_agreed": True,
        "consent_version": "v1",
        "nickname": "sky",
        "grade": "E6",
        "pin": "1234",
    }
    payload.update(overrides)
    return payload


def test_child_registration_requires_guardian_session(child_client):
    response = child_client.post(
        "/api/v1/children",
        json=_child_payload(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_child_registration_requires_consent(child_client):
    _register_guardian(child_client, "parent@example.com")

    response = child_client.post(
        "/api/v1/children",
        json=_child_payload(consent_agreed=False),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CONSENT_REQUIRED"


def test_child_registration_returns_link_code_and_stores_only_pin_hash(
    child_client,
):
    guardian_id = _register_guardian(child_client, "parent@example.com")

    response = child_client.post(
        "/api/v1/children",
        json=_child_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"child_id", "nickname", "grade", "link_code"}
    assert body["nickname"] == "sky"
    assert body["grade"] == "E6"
    assert re.fullmatch(r"[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{6}", body["link_code"])
    assert "pin" not in body
    assert "1234" not in response.text

    with child_client.app.state.session_factory() as session:
        child = session.scalar(
            select(Child).where(Child.id == UUID(body["child_id"]))
        )

    assert child is not None
    assert str(child.guardian_id) == guardian_id
    assert child.consent_version == "v1"
    assert child.consent_agreed_at is not None
    assert child.pin_hash != "1234"
    assert verify_password("1234", child.pin_hash)


@pytest.mark.parametrize("pin", ["123", "12a4", "竊묕폃竊볩폇"])
def test_child_registration_rejects_invalid_pin(child_client, pin):
    _register_guardian(child_client, "parent@example.com")

    response = child_client.post(
        "/api/v1/children",
        json=_child_payload(pin=pin),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "pin" in response.json()["error"]["details"]["fields"]
    assert pin not in response.text


def test_child_list_is_scoped_to_authenticated_guardian(child_client):
    first_guardian_id = _register_guardian(
        child_client,
        "first-parent@example.com",
    )
    first_child = child_client.post(
        "/api/v1/children",
        json=_child_payload(nickname="first"),
    )
    assert first_child.status_code == 201

    second_client = TestClient(child_client.app)
    try:
        second_guardian_id = _register_guardian(
            second_client,
            "second-parent@example.com",
        )
        second_child = second_client.post(
            "/api/v1/children",
            json=_child_payload(nickname="second"),
        )
        assert second_child.status_code == 201

        first_list = child_client.get("/api/v1/children")
        second_list = second_client.get("/api/v1/children")
    finally:
        second_client.close()

    assert first_guardian_id != second_guardian_id
    assert first_list.status_code == 200
    assert second_list.status_code == 200
    assert [item["nickname"] for item in first_list.json()["children"]] == ["first"]
    assert [item["nickname"] for item in second_list.json()["children"]] == ["second"]
    assert all(
        set(item) == {"child_id", "nickname", "grade"}
        for item in first_list.json()["children"]
    )