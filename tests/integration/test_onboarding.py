from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

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


def _valid_diagnosis_answers() -> list[dict[str, str]]:
    return [
        {"question_id": "q1", "option_id": "q1_a"},
        {"question_id": "q2", "option_id": "q2_b"},
        {"question_id": "q3", "option_id": "q3_c"},
    ]


def _onboarding_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "display": {
            "font_scale": "normal",
            "high_contrast": False,
            "tts_enabled": False,
        },
        "favorite_apps": [],
        "trusted_contact": {"name": "엄마", "phone": "010-1234-5678"},
        "diagnosis_answers": _valid_diagnosis_answers(),
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("font_scale", ["normal", "large", "xlarge"])
@pytest.mark.parametrize(
    ("answers", "expected_difficulty"),
    [
        (
            [
                {"question_id": "q1", "option_id": "q1_a"},
                {"question_id": "q2", "option_id": "q2_a"},
                {"question_id": "q3", "option_id": "q3_a"},
            ],
            1,
        ),
        (_valid_diagnosis_answers(), 2),
        (
            [
                {"question_id": "q1", "option_id": "q1_c"},
                {"question_id": "q2", "option_id": "q2_c"},
                {"question_id": "q3", "option_id": "q3_c"},
            ],
            3,
        ),
    ],
)
def test_onboarding_saves_settings_and_json_difficulty(
    onboarding_client,
    font_scale,
    answers,
    expected_difficulty,
):
    _, child_id = _register_child(onboarding_client)

    payload = _onboarding_payload(
        display={
            "font_scale": font_scale,
            "high_contrast": False,
            "tts_enabled": False,
        },
        diagnosis_answers=answers,
    )
    response = onboarding_client.put("/api/v1/me/onboarding", json=payload)

    assert response.status_code == 200
    assert response.json() == {"start_difficulty": expected_difficulty}

    with onboarding_client.app.state.session_factory() as session:
        settings = session.get(ChildSettings, child_id)
        child = session.get(Child, child_id)

    assert settings is not None
    assert settings.font_scale == font_scale
    assert settings.trusted_contact_name == "엄마"
    assert settings.trusted_contact_phone == "010-1234-5678"
    assert settings.favorite_apps == []
    assert child is not None
    assert child.start_difficulty == expected_difficulty
    assert child.onboarding_completed_at is not None


def test_onboarding_requires_child_login(onboarding_client):
    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_onboarding_rejects_guardian_session(onboarding_client):
    credentials = {"email": "parent@example.com", "password": "correct-horse-42"}
    registration = onboarding_client.post("/api/v1/guardians", json=credentials)
    assert registration.status_code == 201

    login = onboarding_client.post("/api/v1/auth/guardian/login", json=credentials)
    assert login.status_code == 200

    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"


@pytest.mark.parametrize(
    "answers",
    [
        [
            {"question_id": "unknown_question", "option_id": "q1_a"},
            {"question_id": "q2", "option_id": "q2_b"},
            {"question_id": "q3", "option_id": "q3_c"},
        ],
        [
            {"question_id": "q1", "option_id": "unknown_option"},
            {"question_id": "q2", "option_id": "q2_b"},
            {"question_id": "q3", "option_id": "q3_c"},
        ],
        [
            {"question_id": "q1", "option_id": "q2_a"},
            {"question_id": "q2", "option_id": "q2_b"},
            {"question_id": "q3", "option_id": "q3_c"},
        ],
    ],
)
def test_onboarding_rejects_unknown_or_mismatched_diagnosis_ids(
    onboarding_client,
    answers,
):
    _register_child(onboarding_client)

    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(diagnosis_answers=answers),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["fields"] == ["diagnosis_answers"]


def test_onboarding_rejects_unknown_favorite_app_type(onboarding_client):
    _register_child(onboarding_client)

    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(favorite_apps=["unknown_app"]),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["fields"] == ["favorite_apps"]


def test_onboarding_saves_valid_favorite_app_types(onboarding_client):
    _, child_id = _register_child(onboarding_client)

    response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(favorite_apps=["sns", "game"]),
    )

    assert response.status_code == 200
    with onboarding_client.app.state.session_factory() as session:
        settings = session.get(ChildSettings, child_id)

    assert settings is not None
    assert settings.favorite_apps == ["sns", "game"]


def test_onboarding_resaving_updates_existing_settings(onboarding_client):
    _, child_id = _register_child(onboarding_client)

    first_response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(favorite_apps=["sns"]),
    )
    second_response = onboarding_client.put(
        "/api/v1/me/onboarding",
        json=_onboarding_payload(
            display={
                "font_scale": "large",
                "high_contrast": True,
                "tts_enabled": True,
            },
            trusted_contact={"name": "아빠", "phone": "010-9876-5432"},
            favorite_apps=["game", "messenger"],
            diagnosis_answers=[
                {"question_id": "q1", "option_id": "q1_c"},
                {"question_id": "q2", "option_id": "q2_c"},
                {"question_id": "q3", "option_id": "q3_c"},
            ],
        ),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == {"start_difficulty": 3}

    with onboarding_client.app.state.session_factory() as session:
        settings_count = session.scalar(
            select(func.count())
            .select_from(ChildSettings)
            .where(ChildSettings.child_id == child_id)
        )
        settings = session.get(ChildSettings, child_id)
        child = session.get(Child, child_id)

    assert settings_count == 1
    assert settings is not None
    assert settings.font_scale == "large"
    assert settings.high_contrast is True
    assert settings.tts_enabled is True
    assert settings.trusted_contact_name == "아빠"
    assert settings.trusted_contact_phone == "010-9876-5432"
    assert settings.favorite_apps == ["game", "messenger"]
    assert child is not None
    assert child.start_difficulty == 3
