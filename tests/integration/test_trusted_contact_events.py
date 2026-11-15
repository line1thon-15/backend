"""믿는 사람 연락 기록 A14 `POST /me/trusted-contact-events` → 보호자 리포트 A11 `notices` (T-40 — F-23 ③, F-30).

근거: Architecture "API 규격" A14 행(`{channel:"call"|"sms"}` → 200 `{ok: true}`, guardian_notices에 `trusted_contact` 기록),
엔티티 guardian_notices 행(CHECK — `trusted_contact`면 `level`·`area` NULL·`channel` NOT NULL, `origin` `live`),
"응답 DTO" NoticeView(`kind = "trusted_contact"`이면 `level`·`area` null·`channel` 값), "보호자용 응답 금지 필드",
"역할 분리"(아이 전용 — 보호자 세션 403 `FORBIDDEN_ROLE`, 세션 없음 401 `UNAUTHENTICATED`).
범위 밖: PRD Open Question 9(외부 즉시 전달) — 보류. 원문·연락처(이름·번호)는 알림에 넣지 않는다(최소 정보).
"""

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.db.base import Base
from app.db.models import ChildSettings, GuardianNotice
from app.main import create_app
from tests.integration.helpers.guardian_report_keys import NOTICE_KEYS, forbidden_keys_found

NOW = datetime(2026, 11, 15, 3, 0, tzinfo=timezone.utc)
CONTACT_NAME = "엄마T40"
CONTACT_PHONE = "010-4040-4040"
EVENTS = "/api/v1/me/trusted-contact-events"


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class Env:
    def __init__(self, client: TestClient, clock: Clock) -> None:
        self.client = client
        self.clock = clock
        self.session_factory = client.app.state.session_factory
        self._count = 0

    def new_guardian(self) -> dict:
        self._count += 1
        self.client.cookies.clear()
        response = self.client.post(
            "/api/v1/guardians",
            json={"email": f"t40guardian{self._count}@example.com", "password": "correct-horse-42"},
        )
        assert response.status_code == 201, response.text
        cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        return cookies

    def new_child(self, guardian_cookies: dict) -> tuple[str, dict]:
        """아이 등록 → (child_id, 아이 세션 쿠키). 믿는 사람 연락처도 저장해 둔다(응답 누출 검사용)."""
        self.client.cookies.clear()
        self.client.cookies.update(guardian_cookies)
        response = self.client.post(
            "/api/v1/children",
            json={"consent_agreed": True, "consent_version": "v1", "nickname": "하늘이", "grade": "H1", "pin": "1234"},
        )
        assert response.status_code == 201, response.text
        child = response.json()
        self.client.cookies.clear()
        login = self.client.post("/api/v1/auth/child/login", json={"link_code": child["link_code"], "pin": "1234"})
        assert login.status_code == 200, login.text
        cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        with self.session_factory.begin() as db:
            settings = db.get(ChildSettings, UUID(child["child_id"]))
            if settings is None:
                settings = ChildSettings(child_id=UUID(child["child_id"]))
                db.add(settings)
            settings.trusted_contact_name = CONTACT_NAME
            settings.trusted_contact_phone = CONTACT_PHONE
        return child["child_id"], cookies

    def post_event(self, body, cookies: dict | None):
        self.client.cookies.clear()
        if cookies:
            self.client.cookies.update(cookies)
        response = self.client.post(EVENTS, json=body)
        self.client.cookies.clear()
        return response

    def report(self, child_id: str, cookies: dict):
        self.client.cookies.clear()
        self.client.cookies.update(cookies)
        response = self.client.get(f"/api/v1/children/{child_id}/report")
        self.client.cookies.clear()
        return response

    def notices_in_db(self) -> list[GuardianNotice]:
        with self.session_factory() as db:
            rows = db.execute(select(GuardianNotice).order_by(GuardianNotice.occurred_at)).scalars().all()
            db.expunge_all()
            return list(rows)


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    clock = Clock(NOW)
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 't40.db').as_posix()}", ai_client="fake"),
        clock=clock,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield Env(client, clock)
    app.state.engine.dispose()


@pytest.fixture
def family(env):
    guardian = env.new_guardian()
    child_id, child_cookies = env.new_child(guardian)
    return guardian, child_id, child_cookies


# ==== 정상 (F-23 ③) ================================================================


@pytest.mark.parametrize("channel", ["call", "sms"])
def test_event_records_trusted_contact_notice(env, family, channel):
    _guardian, child_id, child_cookies = family

    response = env.post_event({"channel": channel}, child_cookies)

    assert response.status_code == 200, response.text
    assert response.json() == {"ok": True}
    rows = env.notices_in_db()
    assert len(rows) == 1
    row = rows[0]
    assert row.child_id == UUID(child_id)
    assert row.kind == "trusted_contact"
    assert row.channel == channel
    assert row.level is None
    assert row.area is None
    assert row.origin == "live"
    assert row.occurred_at.replace(tzinfo=timezone.utc) == NOW


def test_recorded_event_appears_in_guardian_report_with_minimum_fields(env, family):
    guardian, child_id, child_cookies = family
    assert env.post_event({"channel": "sms"}, child_cookies).status_code == 200

    response = env.report(child_id, guardian)

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["notices"]) == 1
    notice = body["notices"][0]
    assert set(notice) == NOTICE_KEYS
    UUID(notice["notice_id"])
    assert notice["kind"] == "trusted_contact"
    assert notice["channel"] == "sms"
    assert notice["level"] is None
    assert notice["area"] is None
    assert datetime.fromisoformat(notice["occurred_at"]).replace(tzinfo=timezone.utc) == NOW
    # 보호자용 응답 금지 키 0건 + 믿는 사람 이름·번호 미노출(최소 정보)
    assert forbidden_keys_found(body) == set()
    assert CONTACT_NAME not in response.text
    assert CONTACT_PHONE not in response.text


# ==== 경계 ========================================================================


def test_repeated_presses_each_recorded_newest_first(env, family):
    guardian, child_id, child_cookies = family
    assert env.post_event({"channel": "call"}, child_cookies).status_code == 200
    env.clock.now = NOW + timedelta(minutes=3)
    assert env.post_event({"channel": "sms"}, child_cookies).status_code == 200

    notices = env.report(child_id, guardian).json()["notices"]

    assert [n["channel"] for n in notices] == ["sms", "call"]
    assert len({n["notice_id"] for n in notices}) == 2


def test_event_is_visible_only_on_own_child_report(env, family):
    guardian, child_id, child_cookies = family
    _sibling_id, _ = env.new_child(guardian)
    sibling_id = _sibling_id
    other_guardian = env.new_guardian()
    other_child_id, _ = env.new_child(other_guardian)
    assert env.post_event({"channel": "call"}, child_cookies).status_code == 200

    # 같은 보호자의 다른 아이·다른 보호자의 아이 리포트에는 없음
    assert env.report(sibling_id, guardian).json()["notices"] == []
    assert env.report(other_child_id, other_guardian).json()["notices"] == []
    # 다른 보호자는 이 아이 리포트 자체를 못 본다(기존 IDOR 규칙 — 404)
    assert env.report(child_id, other_guardian).status_code == 404


# ==== 예외 ========================================================================


@pytest.mark.parametrize(
    "body",
    [
        {"channel": "email"},
        {"channel": "CALL"},
        {"channel": ""},
        {"channel": None},
        {},
        {"channel": "call", "phone": CONTACT_PHONE},
    ],
    ids=["unknown", "uppercase", "empty", "null", "missing", "extra-field"],
)
def test_invalid_body_is_422_and_records_nothing(env, family, body):
    _guardian, _child_id, child_cookies = family

    response = env.post_event(body, child_cookies)

    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert env.notices_in_db() == []


def test_guardian_session_is_403_forbidden_role(env, family):
    guardian, _child_id, _child_cookies = family

    response = env.post_event({"channel": "call"}, guardian)

    assert response.status_code == 403, response.text
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert env.notices_in_db() == []


@pytest.mark.parametrize("cookies", [None, {"sid": "not-a-real-session-token"}], ids=["no-session", "unknown-token"])
def test_without_child_session_is_401(env, family, cookies):
    response = env.post_event({"channel": "call"}, cookies)

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert env.notices_in_db() == []
