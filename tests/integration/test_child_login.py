from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.core.config import Settings
from app.core.security import hash_session_token
from app.db.base import Base
from app.db.models import AuthSession, Child
from app.main import create_app


@pytest.fixture
def child_login_client(sqlite_url: str) -> Iterator[TestClient]:
    app = create_app(
        Settings(_env_file=None, database_url=sqlite_url, ai_client="fake")
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def _create_child(client: TestClient) -> dict[str, str]:
    guardian = client.post(
        "/api/v1/guardians",
        json={
            "email": "parent@example.com",
            "password": "correct-horse-42",
        },
    )
    assert guardian.status_code == 201

    response = client.post(
        "/api/v1/children",
        json={
            "consent_agreed": True,
            "consent_version": "v1",
            "nickname": "sky",
            "grade": "E6",
            "pin": "1234",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_child_login_creates_child_session_and_marks_first_login(
    child_login_client,
):
    child = _create_child(child_login_client)

    response = child_login_client.post(
        "/api/v1/auth/child/login",
        json={
            "link_code": child["link_code"].lower(),
            "pin": "1234",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"first_login": True}
    session_token = response.cookies.get("sid")
    assert session_token

    with child_login_client.app.state.session_factory() as session:
        auth_session = session.scalar(
            select(AuthSession).where(
                AuthSession.subject_type == "child",
                AuthSession.subject_id == UUID(child["child_id"]),
            )
        )

    assert auth_session is not None
    assert auth_session.token_hash == hash_session_token(session_token)
    assert auth_session.token_hash != session_token


def test_child_login_reports_returning_child_after_onboarding(
    child_login_client,
):
    child = _create_child(child_login_client)
    child_id = UUID(child["child_id"])

    with child_login_client.app.state.session_factory.begin() as session:
        session.execute(
            update(Child)
            .where(Child.id == child_id)
            .values(onboarding_completed_at=datetime.now(timezone.utc))
        )

    response = child_login_client.post(
        "/api/v1/auth/child/login",
        json={"link_code": child["link_code"], "pin": "1234"},
    )

    assert response.status_code == 200
    assert response.json() == {"first_login": False}


def test_child_login_does_not_reveal_whether_code_or_pin_was_wrong(
    child_login_client,
):
    child = _create_child(child_login_client)

    invalid_code = child_login_client.post(
        "/api/v1/auth/child/login",
        json={"link_code": "AAAAAA", "pin": "1234"},
    )
    invalid_pin = child_login_client.post(
        "/api/v1/auth/child/login",
        json={"link_code": child["link_code"], "pin": "9999"},
    )

    assert invalid_code.status_code == 401
    assert invalid_pin.status_code == 401
    assert invalid_code.json() == invalid_pin.json()
    assert invalid_code.json()["error"]["code"] == "INVALID_CODE_OR_PIN"

    with child_login_client.app.state.session_factory() as session:
        child_session_count = session.scalar(
            select(func.count())
            .select_from(AuthSession)
            .where(AuthSession.subject_type == "child")
        )

    assert child_session_count == 0