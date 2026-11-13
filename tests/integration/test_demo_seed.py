"""시연 예시 데이터 적재 (T-67 — F-28 ②③, F-29 ④⑤⑥, F-41 ②④, F-47 ⑤, N-11, DECISIONS #30·#132).

적재 후 실제 API(A19 `GET /me/growth`, A11 `GET /children/{id}/report`)로 조회해 시연 화면에 보일 값을 단언한다.
시계는 주입: 2026-11-13T03:00Z = 한국 시간 2026-11-13 12:00 → 이번 기간 [11-07, 11-13], 직전 [10-31, 11-06].

예시 기록(계획 `app/demo/plan.py`, 오늘 = D0, 모두 scam — 콘텐츠 사본의 시나리오가 scam 2개뿐):
  직전 기간 D12·D10·D9·D8 — 놓친 단서 6 / 판정 10, 첫 답 correct 1/4
  이번 기간 D4·D2·D1·D0 — 놓친 단서 1 / 판정 11, 첫 답 correct 3/4, 놓침 0·찾음 ≥1 세션 3개(D4·D1·D0)
  keep_secret은 D9·D2에서 놓침(최근 판정 놓침) → 더 연습이 필요한 단서
  advance_payment·suspicious_link는 2번 놓쳤지만 최근 판정 찾음 → 빠짐
"""

import json
import re
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.content.loader import load_content
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Child, CueResult, Guardian, GuardianNotice, PracticeSession, PracticeTurn
from app.demo.seed import (
    DEFAULT_ACCOUNT_FILE,
    DemoSeedConfigError,
    DemoSeedError,
    load_demo_account,
    main,
    seed_fixed_account,
    seed_into_child,
)
from app.main import create_app
from app.repositories.demo_seed import SqlAlchemyDemoSeedRepository

CONTENT = load_content()
NOW = datetime(2026, 11, 13, 3, 0, tzinfo=timezone.utc)
SCAM_BADGE = {"badge_id": "independent:scam", "area": "scam", "label": "혼자 할 수 있어요"}
# 시연 계정 비밀번호·PIN은 저장소 파일이 아니라 환경 변수로 받는다(2026-11-13 사용자 답 "환경 변수로 받기 (추천)").
# 아래는 이 테스트에서만 쓰는 값이다.
TEST_PASSWORD = "test-only-guardian-pw"
TEST_PIN = "7391"


@pytest.fixture(autouse=True)
def demo_secrets(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_GUARDIAN_PASSWORD", TEST_PASSWORD)
    monkeypatch.setenv("DEMO_CHILD_PIN", TEST_PIN)


class Env:
    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        self._apps = []

    def client(self, now: datetime = NOW) -> TestClient:
        app = create_app(Settings(_env_file=None, database_url=self.db_url, ai_client="fake"), clock=lambda: now)
        Base.metadata.create_all(app.state.engine)
        self._apps.append(app)
        return TestClient(app)

    @property
    def session_factory(self):
        return self._apps[0].state.session_factory

    def repository(self) -> SqlAlchemyDemoSeedRepository:
        return SqlAlchemyDemoSeedRepository(self.session_factory)

    def close(self) -> None:
        for app in self._apps:
            app.state.engine.dispose()

    def counts(self) -> dict[str, int]:
        with self.session_factory() as db:
            return {
                name: db.scalar(select(func.count()).select_from(model))
                for name, model in {
                    "guardians": Guardian,
                    "children": Child,
                    "sessions": PracticeSession,
                    "turns": PracticeTurn,
                    "cue_results": CueResult,
                    "notices": GuardianNotice,
                }.items()
            }


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    environment = Env(f"sqlite:///{(tmp_path / 'demo.db').as_posix()}")
    environment.client()  # 스키마 생성
    yield environment
    environment.close()


def login_guardian(client: TestClient, email: str, password: str) -> None:
    client.cookies.clear()
    response = client.post("/api/v1/auth/guardian/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.status_code


def login_child(client: TestClient, link_code: str, pin: str) -> None:
    client.cookies.clear()
    response = client.post("/api/v1/auth/child/login", json={"link_code": link_code, "pin": pin})
    assert response.status_code == 200, response.status_code


def metric(body: dict, metric_id: str) -> dict:
    return next(m for m in body["metrics"] if m["metric_id"] == metric_id)


def assert_demo_growth(body: dict, *, previous_end: str, today: str) -> None:
    """Y8에서 변화가 보이는 값 (F-28 ②③, F-29 ④⑤⑥)."""
    scam = next(a for a in body["areas"] if a["area"] == "scam")
    assert scam == {"area": "scam", "practice_count": 8, "badges": [SCAM_BADGE]}
    assert body["streak_days"] == 3
    assert [c["cue_id"] for c in body["needs_practice_cues"]] == ["keep_secret"]
    assert metric(body, "missed_ratio") == {
        "metric_id": "missed_ratio",
        "label": "놓친 신호",
        "status": "ok",
        "level": None,
        "current": pytest.approx(1 / 11),
        "previous": pytest.approx(0.6),
        "trend": [
            {"date": previous_end, "value": pytest.approx(0.6)},
            {"date": today, "value": pytest.approx(1 / 11)},
        ],
    }
    ahead = metric(body, "ahead_of_ai_ratio")
    assert (ahead["status"], ahead["previous"], ahead["current"]) == ("ok", 0.25, 0.75)
    # first_seen_accuracy: 콘텐츠 사본의 시나리오가 2개뿐이라 "처음 받은 시나리오" 세션이 기간마다 3개가 될 수 없다
    # — 사용자 결정(2026-11-13 "일단 비교 불가로 두기")대로 비교 불가. 시나리오가 늘어 바뀌면 이 단언이 알려 준다.
    first_seen = metric(body, "first_seen_accuracy")
    assert (first_seen["status"], first_seen["current"], first_seen["previous"]) == ("insufficient", None, None)


# ==== 정상: 고정 시연 계정 (DECISIONS #132 — 시연 기본 방식) ================================


def test_fixed_account_seed_shows_growth_on_y8(env):
    account = load_demo_account()
    result = seed_fixed_account(env.repository(), CONTENT, account, NOW)

    client = env.client()
    login_child(client, account.link_code, account.pin)
    response = client.get("/api/v1/me/growth")

    assert response.status_code == 200, response.text
    assert_demo_growth(response.json(), previous_end="2026-11-06", today="2026-11-13")
    assert result.sessions == 8 and result.notices == 2


def test_fixed_account_seed_shows_notices_and_summary_inputs_on_g3(env):
    account = load_demo_account()
    result = seed_fixed_account(env.repository(), CONTENT, account, NOW)

    client = env.client()
    login_guardian(client, account.guardian_email, account.guardian_password)
    response = client.get(f"/api/v1/children/{result.child_id}/report")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["child"]["nickname"] == account.child_nickname
    # F-41 ②④: 예시 안전 알림 — 발생 시각·위험도·영역만, 최신 순
    assert body["notices"] == [
        {
            "notice_id": body["notices"][0]["notice_id"],
            "kind": "safety",
            "occurred_at": "2026-11-11T01:30:00Z",  # 한국 시간 11-11 10:30 (D2)
            "level": "yellow",
            "area": "scam",
            "channel": None,
        },
        {
            "notice_id": body["notices"][1]["notice_id"],
            "kind": "safety",
            "occurred_at": "2026-11-04T01:30:00Z",  # 한국 시간 11-04 10:30 (D9)
            "level": "red",
            "area": "scam",
            "channel": None,
        },
    ]
    # F-47 ⑤ 요약 입력 항목이 계산될 수 있음: 연습 횟수·영역별 진행·약점 단서·지표
    scam = next(a for a in body["areas"] if a["area"] == "scam")
    assert scam["practice_count"] == 8
    assert scam["last_practiced_at"] == "2026-11-13T02:30:00Z"  # D0 = now − 30분
    assert body["weak_cues"] == [{"cue_id": "keep_secret", "label": CONTENT.clues["keep_secret"].name}]
    assert metric(body, "missed_ratio")["status"] == "ok"


def test_fixed_account_seed_marks_rows_demo_seed_and_child_is_high_school(env):
    account = load_demo_account()
    result = seed_fixed_account(env.repository(), CONTENT, account, NOW)

    with env.session_factory() as db:
        child = db.get(Child, result.child_id)
        origins = db.scalars(select(PracticeSession.origin)).all()
        notice_origins = db.scalars(select(GuardianNotice.origin)).all()
        guardian = db.get(Guardian, child.guardian_id)

    assert child.grade.startswith("H")  # 사기 시나리오가 고등학생 전용 (T-87)
    assert child.onboarding_completed_at is None  # 사용자 결정(2026-11-13 "미완료로 두기") — 첫 로그인 시 Y2
    assert child.link_code == account.link_code
    assert set(origins) == {"demo_seed"} and len(origins) == 8
    assert set(notice_origins) == {"demo_seed"}
    assert guardian.email == account.guardian_email
    assert guardian.password_hash != account.guardian_password  # 해시로 저장


def test_demo_account_file_has_no_real_personal_data():
    """N-11: 예시 값만 — 예약 도메인 이메일, 형식에 맞는 연결 코드·PIN."""
    raw = json.loads(Path(DEFAULT_ACCOUNT_FILE).read_text(encoding="utf-8"))
    account = load_demo_account()

    assert account.guardian_email.endswith("@example.com")
    assert len(account.link_code) == 6 and account.link_code.isalnum() and account.link_code.isupper()
    assert len(account.pin) == 4 and account.pin.isdigit()
    assert raw["note"]  # 예시 데이터 표시


def test_demo_account_file_has_no_password_or_pin():
    """비밀번호·PIN은 저장소 파일에 없고 환경 변수 값을 쓴다."""
    text = Path(DEFAULT_ACCOUNT_FILE).read_text(encoding="utf-8")
    raw = json.loads(text)
    account = load_demo_account()

    assert not {"guardian_password", "child_pin", "password", "pin"} & set(raw)
    assert (account.guardian_password, account.pin) == (TEST_PASSWORD, TEST_PIN)


# ==== 예외: 시연 계정 비밀번호·PIN 환경 변수 ==================================================


@pytest.mark.parametrize(
    "name, value",
    [
        ("DEMO_GUARDIAN_PASSWORD", None),  # 없음
        ("DEMO_CHILD_PIN", None),  # 없음
        ("DEMO_GUARDIAN_PASSWORD", ""),  # 빈 값
        ("DEMO_GUARDIAN_PASSWORD", "short7!"),  # 7자 — 로그인 API 최소 8자 미만
        ("DEMO_CHILD_PIN", "123"),  # 3자리
        ("DEMO_CHILD_PIN", "12345"),  # 5자리
        ("DEMO_CHILD_PIN", "12a4"),  # 숫자 아님
        ("DEMO_CHILD_PIN", "１２３４"),  # 전각 숫자
    ],
)
def test_cli_fixed_with_missing_or_invalid_secret_writes_nothing_and_exits_2(env, monkeypatch, capsys, name, value):
    if value is None:
        monkeypatch.delenv(name)
    else:
        monkeypatch.setenv(name, value)
    settings = Settings(_env_file=None, database_url=env.db_url, ai_client="fake")
    before = env.counts()

    code = main(["fixed"], settings=settings, clock=lambda: NOW)

    captured = capsys.readouterr()
    assert code == 2
    assert env.counts() == before
    assert name in captured.err  # 어느 변수가 문제인지는 알려 준다
    for secret in (TEST_PASSWORD, TEST_PIN, value):
        if secret:
            assert secret not in captured.out and secret not in captured.err  # 값은 노출하지 않는다


def test_load_demo_account_raises_config_error_without_value_in_message(monkeypatch):
    monkeypatch.setenv("DEMO_CHILD_PIN", "98765")

    with pytest.raises(DemoSeedConfigError) as exc:
        load_demo_account()

    assert "DEMO_CHILD_PIN" in str(exc.value)
    assert "98765" not in str(exc.value)


def test_cli_attach_does_not_need_demo_secrets(env, monkeypatch):
    """attach는 계정을 만들지 않으므로 비밀번호·PIN 환경 변수가 없어도 된다."""
    client = env.client()
    child_id, _ = register_family(client)
    monkeypatch.delenv("DEMO_GUARDIAN_PASSWORD")
    monkeypatch.delenv("DEMO_CHILD_PIN")
    settings = Settings(_env_file=None, database_url=env.db_url, ai_client="fake")

    assert main(["attach", "--child-id", child_id], settings=settings, clock=lambda: NOW) == 0
    assert env.counts()["sessions"] == 8


# ==== 정상: 지정 아이에 덧붙임 (DECISIONS #30) ============================================


def register_family(client: TestClient) -> tuple[str, str]:
    client.cookies.clear()
    assert client.post(
        "/api/v1/guardians", json={"email": "family@example.com", "password": "correct-horse-42"}
    ).status_code == 201
    response = client.post(
        "/api/v1/children",
        json={"consent_agreed": True, "consent_version": "v1", "nickname": "하늘이", "grade": "H1", "pin": "1234"},
    )
    assert response.status_code == 201, response.text
    client.cookies.clear()
    return response.json()["child_id"], response.json()["link_code"]


def test_attach_seed_adds_records_to_given_child_and_keeps_live_rows(env):
    client = env.client()
    child_id, link_code = register_family(client)
    with env.session_factory.begin() as db:
        db.add(
            PracticeSession(
                child_id=UUID(child_id), mode="area", area="scam", subtype=None,
                scenario_id="scam_dm_parttime_01", is_normal=False, target_cue_ids=[], variant={},
                scenario_title="t", child_setup="s", ai_role_name="r", status="in_progress",
                origin="live", started_at=NOW - timedelta(days=30), ended_at=None,
            )
        )

    result = seed_into_child(env.repository(), CONTENT, UUID(child_id), NOW)
    seed_into_child(env.repository(), CONTENT, UUID(child_id), NOW)  # 다시 실행해도 live 행은 그대로

    assert result.child_id == UUID(child_id)
    with env.session_factory() as db:
        live = db.scalars(select(PracticeSession).where(PracticeSession.origin == "live")).all()
    assert len(live) == 1
    login_child(client, link_code, "1234")
    body = client.get("/api/v1/me/growth").json()
    assert_demo_growth(body, previous_end="2026-11-06", today="2026-11-13")


# ==== 경계: 재실행 안전(멱등)·날짜 재기준 ==================================================


def test_fixed_seed_twice_does_not_duplicate(env):
    account = load_demo_account()
    first = seed_fixed_account(env.repository(), CONTENT, account, NOW)
    after_first = env.counts()

    second = seed_fixed_account(env.repository(), CONTENT, account, NOW)

    assert env.counts() == after_first
    assert after_first == {
        "guardians": 1, "children": 1, "sessions": 8, "turns": 8, "cue_results": 21, "notices": 2,
    }
    assert second.child_id == first.child_id


def test_rerun_next_day_recenters_dates_without_duplicates(env):
    account = load_demo_account()
    seed_fixed_account(env.repository(), CONTENT, account, NOW)
    counts = env.counts()
    tomorrow = NOW + timedelta(days=1)

    seed_fixed_account(env.repository(), CONTENT, account, tomorrow)

    assert env.counts() == counts
    client = env.client(tomorrow)
    login_child(client, account.link_code, account.pin)
    assert_demo_growth(client.get("/api/v1/me/growth").json(), previous_end="2026-11-07", today="2026-11-14")


def test_seed_right_after_midnight_still_has_today_streak(env):
    just_after_midnight = datetime(2026, 11, 12, 15, 0, 30, tzinfo=timezone.utc)  # 한국 시간 11-13 00:00:30
    account = load_demo_account()
    seed_fixed_account(env.repository(), CONTENT, account, just_after_midnight)

    client = env.client(just_after_midnight)
    login_child(client, account.link_code, account.pin)
    body = client.get("/api/v1/me/growth").json()

    assert body["streak_days"] == 3
    assert_demo_growth(body, previous_end="2026-11-06", today="2026-11-13")


# ==== 예외 ==============================================================================


def test_attach_to_unknown_child_fails_without_writing(env):
    before = env.counts()

    with pytest.raises(DemoSeedError):
        seed_into_child(env.repository(), CONTENT, uuid4(), NOW)

    assert env.counts() == before


def test_fixed_seed_fails_when_link_code_belongs_to_another_guardian(env):
    account = load_demo_account()
    client = env.client()
    child_id, _ = register_family(client)
    with env.session_factory.begin() as db:
        db.get(Child, UUID(child_id)).link_code = account.link_code
    before = env.counts()

    with pytest.raises(DemoSeedError):
        seed_fixed_account(env.repository(), CONTENT, account, NOW)

    assert env.counts() == before


# ==== 실행 진입점 ==========================================================================


def test_cli_fixed_then_attach(env, capsys):
    account = load_demo_account()
    settings = Settings(_env_file=None, database_url=env.db_url, ai_client="fake")

    assert main(["fixed"], settings=settings, clock=lambda: NOW) == 0
    assert main(["fixed"], settings=settings, clock=lambda: NOW) == 0
    out = capsys.readouterr().out
    without_ids = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "", out)
    assert "demo seed ok" in out
    assert account.guardian_password not in out and account.pin not in without_ids  # 비밀번호·PIN 출력 금지
    assert env.counts()["sessions"] == 8

    with env.session_factory() as db:
        child_id = db.scalar(select(Child.id))
    assert main(["attach", "--child-id", str(child_id)], settings=settings, clock=lambda: NOW) == 0
    assert env.counts()["sessions"] == 8


def test_cli_errors(env, capsys):
    settings = Settings(_env_file=None, database_url=env.db_url, ai_client="fake")

    assert main(["attach", "--child-id", str(uuid4())], settings=settings, clock=lambda: NOW) == 1
    with pytest.raises(SystemExit) as exc:
        main(["attach"], settings=settings, clock=lambda: NOW)
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        main(["attach", "--child-id", "not-a-uuid"], settings=settings, clock=lambda: NOW)
