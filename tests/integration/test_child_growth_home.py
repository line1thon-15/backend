"""아이용 성장·홈 API 조립 (T-90 — F-28, F-29, N-12).

근거: Architecture "API 규격" A13 `GET /me/home`·A19 `GET /me/growth`, "응답 DTO" GrowthView·BadgeView·MetricView·CueCard,
"성장 계산 규칙" 절, "오류 응답 규격"(401 `UNAUTHENTICATED`·403 `FORBIDDEN_ROLE`), "보안·개인정보" 역할 분리 행,
DECISIONS #88(`level` null)·#122~#124·#127, Tasks T-90 행.

이 작업은 조립만 한다(N-12) — 기대값은 T-45(`BadgeService`)·T-46(`GrowthMetricsService`) 계산 규칙으로 손계산했다.
연습 기록은 DB에 직접 넣는다(AI 호출 없음). DB는 테스트마다 pytest tmp_path SQLite 파일.
시계는 주입: 2026-11-12T03:00Z = 한국 시간 2026-11-12 12:00 → 이번 기간 [11-06, 11-12], 직전 [10-30, 11-05].
"""

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.content.loader import load_content
from app.core.config import Settings
from app.db.base import Base
from app.db.models import ChildSettings, CueResult, PracticeSession, PracticeTurn
from app.main import create_app
from app.repositories.badges import SqlAlchemyBadgeRepository
from app.services.badges import BadgeService

CONTENT = load_content()
NOW = datetime(2026, 11, 12, 3, 0, tzinfo=timezone.utc)
AREAS = ["scam", "identity_lending", "friend_pressure"]
METRIC_IDS = ["missed_ratio", "first_seen_accuracy", "ahead_of_ai_ratio"]
GROWTH_KEYS = {"areas", "streak_days", "needs_practice_cues", "metrics"}
HOME_KEYS = {"areas", "badges", "streak_days", "trusted_contact"}
METRIC_KEYS = {"metric_id", "label", "status", "level", "current", "previous", "trend"}
# 2026-11-12 사용자 답 "쉬운 말 문구 (추천)" — 선택지 설명 원문 "① '놓친 신호' ② '처음 본 상황에서 찾은 신호'
# ③ '먼저 알아챈 횟수'. 느린학습자용 쉬운 말(N-03). 아이 Y8과 보호자 G3가 같은 문구를 써요."
EXPECTED_LABELS = {
    "missed_ratio": "놓친 신호",
    "first_seen_accuracy": "처음 본 상황에서 찾은 신호",
    "ahead_of_ai_ratio": "먼저 알아챈 횟수",
}


def kst(month: int, day: int, hour: int = 12) -> datetime:
    """한국 시간 날짜·시각 → UTC aware."""
    return datetime(2026, month, day, hour, 0, tzinfo=timezone(timedelta(hours=9))).astimezone(timezone.utc)


class Env:
    def __init__(self, client: TestClient) -> None:
        self.client = client
        self.session_factory = client.app.state.session_factory
        self._count = 0

    def new_guardian(self) -> dict:
        self._count += 1
        self.client.cookies.clear()
        response = self.client.post(
            "/api/v1/guardians",
            json={"email": f"guardian{self._count}@example.com", "password": "correct-horse-42"},
        )
        assert response.status_code == 201, response.text
        cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        return cookies

    def new_child(self, guardian_cookies: dict) -> tuple[str, dict]:
        """아이 등록 → (child_id, 아이 로그인 쿠키)."""
        self.client.cookies.clear()
        self.client.cookies.update(guardian_cookies)
        response = self.client.post(
            "/api/v1/children",
            json={"consent_agreed": True, "consent_version": "v1", "nickname": "하늘이", "grade": "H1", "pin": "1234"},
        )
        assert response.status_code == 201, response.text
        child = response.json()
        self.client.cookies.clear()
        login = self.client.post(
            "/api/v1/auth/child/login", json={"link_code": child["link_code"], "pin": "1234"}
        )
        assert login.status_code == 200, login.text
        cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        return child["child_id"], cookies

    def get(self, path: str, cookies: dict | None):
        self.client.cookies.clear()
        if cookies:
            self.client.cookies.update(cookies)
        response = self.client.get(path)
        self.client.cookies.clear()
        return response

    def seed_session(
        self,
        child_id: str,
        *,
        ended_at: datetime,
        cues: dict[str, str],
        first_kind: str = "correct",
        area: str = "scam",
        scenario_id: str,
        status: str = "ended",
        is_normal: bool = False,
    ) -> UUID:
        with self.session_factory.begin() as db:
            row = PracticeSession(
                child_id=UUID(child_id),
                mode="area",
                area=area,
                subtype=None,
                scenario_id=scenario_id,
                is_normal=is_normal,
                target_cue_ids=list(cues),
                variant={"opening_line": "x", "title": "x"},
                scenario_title="title",
                child_setup="setup",
                ai_role_name="민수",
                status=status,
                origin="live",
                started_at=ended_at - timedelta(minutes=5),
                ended_at=ended_at,
            )
            db.add(row)
            db.flush()
            db.add(
                PracticeTurn(
                    session_id=row.id,
                    turn_index=0,
                    ai_line="line",
                    choices=[{"id": "c1", "text": "choice", "kind": first_kind}],
                    chosen_choice_id="c1",
                    substituted=False,
                    target_clue_id=None,
                    revealed_clue_ids=[],
                    ai_status="ok",
                )
            )
            for cue_id, outcome in cues.items():
                db.add(
                    CueResult(
                        session_id=row.id,
                        child_id=UUID(child_id),
                        cue_id=cue_id,
                        outcome=outcome,
                        recorded_at=ended_at,
                    )
                )
            return row.id

    def seed_trusted_contact(self, child_id: str, name: str | None, phone: str | None) -> None:
        with self.session_factory.begin() as db:
            db.add(
                ChildSettings(
                    child_id=UUID(child_id),
                    trusted_contact_name=name,
                    trusted_contact_phone=phone,
                    favorite_apps=[],
                )
            )

    def seed_example_history(self, child_id: str) -> None:
        """예시 기록 — 기대값은 각 테스트 docstring의 손계산.

        직전 기간 3세션(scam, 한국 11-02·03·04): urgency 놓침 + keep_secret 찾음, 첫 답 doubtful
        이번 기간 3세션(scam, 한국 11-10·11·12): urgency·keep_secret 찾음, 첫 답 correct
        기간 밖 2세션(friend_pressure, 한국 10-20·21): personal_info 놓침, 첫 답 doubtful
        시나리오는 모두 다르다(처음 받은 세션).
        """
        for n, day in enumerate((2, 3, 4)):
            self.seed_session(
                child_id,
                ended_at=kst(11, day),
                cues={"urgency": "missed", "keep_secret": "found"},
                first_kind="doubtful",
                scenario_id=f"prev_{n}",
            )
        for n, (day, hour) in enumerate(((10, 12), (11, 12), (12, 10))):
            self.seed_session(
                child_id,
                ended_at=kst(11, day, hour),
                cues={"urgency": "found", "keep_secret": "found"},
                first_kind="correct",
                scenario_id=f"cur_{n}",
            )
        for n, day in enumerate((20, 21)):
            self.seed_session(
                child_id,
                ended_at=kst(10, day),
                cues={"personal_info": "missed"},
                first_kind="doubtful",
                area="friend_pressure",
                scenario_id=f"old_{n}",
            )


@pytest.fixture
def env(tmp_path) -> Iterator[Env]:
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'me.db').as_posix()}", ai_client="fake"),
        clock=lambda: NOW,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield Env(client)
    app.state.engine.dispose()


@pytest.fixture
def child(env) -> tuple[str, dict]:
    return env.new_child(env.new_guardian())


def cue_card(cue_id: str) -> dict:
    clue = CONTENT.clues[cue_id]
    return {"cue_id": cue_id, "label": clue.name, "sentence": clue.description}


SCAM_BADGE = {"badge_id": "independent:scam", "area": "scam", "label": "혼자 할 수 있어요"}


# ==== A19 정상 (F-28·F-29 ①⑤⑥) =====================================================


def test_growth_assembles_badges_streak_metrics_and_needs_practice_cues(env, child):
    """손계산 기대값.

    - areas: scam 종료 6세션(이번 3세션이 놓침 0·찾음 2 → 배지), friend_pressure 2세션, identity_lending 0
    - streak_days: 종료 날짜 11-12·11-11·11-10(11-09 없음) → 3
    - missed_ratio: 직전 3/6 = 0.5, 이번 0/6 = 0.0
    - first_seen_accuracy: 직전 3/6 = 0.5, 이번 6/6 = 1.0
    - ahead_of_ai_ratio: 직전 0/3 = 0.0, 이번 3/3 = 1.0
    - needs_practice_cues: personal_info(놓침 2·최근 놓침)만. urgency는 놓침 3이지만 최근 판정 찾음 → 제외
    """
    child_id, cookies = child
    env.seed_example_history(child_id)

    response = env.get("/api/v1/me/growth", cookies)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == GROWTH_KEYS
    assert body["areas"] == [
        {"area": "scam", "practice_count": 6, "badges": [SCAM_BADGE]},
        {"area": "identity_lending", "practice_count": 0, "badges": []},
        {"area": "friend_pressure", "practice_count": 2, "badges": []},
    ]
    assert body["streak_days"] == 3
    assert body["needs_practice_cues"] == [cue_card("personal_info")]
    assert body["metrics"] == [
        {
            "metric_id": "missed_ratio",
            "label": "놓친 신호",
            "status": "ok",
            "level": None,
            "current": 0.0,
            "previous": 0.5,
            "trend": [{"date": "2026-11-05", "value": 0.5}, {"date": "2026-11-12", "value": 0.0}],
        },
        {
            "metric_id": "first_seen_accuracy",
            "label": "처음 본 상황에서 찾은 신호",
            "status": "ok",
            "level": None,
            "current": 1.0,
            "previous": 0.5,
            "trend": [{"date": "2026-11-05", "value": 0.5}, {"date": "2026-11-12", "value": 1.0}],
        },
        {
            "metric_id": "ahead_of_ai_ratio",
            "label": "먼저 알아챈 횟수",
            "status": "ok",
            "level": None,
            "current": 1.0,
            "previous": 0.0,
            "trend": [{"date": "2026-11-05", "value": 0.0}, {"date": "2026-11-12", "value": 1.0}],
        },
    ]


def test_metric_label_constant_is_fixed_per_metric_id():
    """설정 상수 1곳(app.domain.metrics.METRIC_LABELS) — 지표 ID별 문구 대응을 고정한다."""
    from app.domain.metrics import METRIC_IDS, METRIC_LABELS

    assert dict(METRIC_LABELS) == EXPECTED_LABELS
    assert set(METRIC_LABELS) == set(METRIC_IDS)


def test_growth_metric_labels_are_injected_constants(tmp_path):
    """`MetricView.label`은 설정 상수(Architecture) — 주입하면 그 값이 실린다(기본값은 METRIC_LABELS)."""
    labels = {"missed_ratio": "L1", "first_seen_accuracy": "L2", "ahead_of_ai_ratio": "L3"}
    app = create_app(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'lbl.db').as_posix()}", ai_client="fake"),
        clock=lambda: NOW,
        metric_labels=labels,
    )
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        local = Env(client)
        _child_id, cookies = local.new_child(local.new_guardian())
        response = local.get("/api/v1/me/growth", cookies)
    app.state.engine.dispose()

    assert response.status_code == 200, response.text
    assert [(m["metric_id"], m["label"]) for m in response.json()["metrics"]] == list(labels.items())


# ==== A19 빈 값 (Tasks T-90 "기록 없음") ==============================================


def test_growth_without_records_is_empty_and_insufficient(env, child):
    _child_id, cookies = child

    response = env.get("/api/v1/me/growth", cookies)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["areas"] == [{"area": area, "practice_count": 0, "badges": []} for area in AREAS]
    assert body["streak_days"] == 0
    assert body["needs_practice_cues"] == []
    assert [m["metric_id"] for m in body["metrics"]] == METRIC_IDS
    assert [m["label"] for m in body["metrics"]] == [EXPECTED_LABELS[i] for i in METRIC_IDS]
    for metric in body["metrics"]:
        assert set(metric) == METRIC_KEYS
        assert metric["status"] == "insufficient"
        assert metric["current"] is None and metric["previous"] is None
        assert metric["trend"] == []
        assert metric["level"] is None


# ==== A19 경계 ======================================================================


def test_growth_counts_only_ended_sessions_and_two_badge_sessions_give_no_badge(env, child):
    """경계: 배지 성공 세션 2개 → 배지 없음(3 필요). 멈춘(stopped) 세션은 진행 수·연속 기록에서 빠진다."""
    child_id, cookies = child
    for n, day in enumerate((11, 12)):
        env.seed_session(child_id, ended_at=kst(11, day, 9), cues={"urgency": "found"}, scenario_id=f"s{n}")
    env.seed_session(
        child_id, ended_at=kst(11, 10, 9), cues={"urgency": "found"}, scenario_id="stopped", status="stopped"
    )

    body = env.get("/api/v1/me/growth", cookies).json()

    assert body["areas"][0] == {"area": "scam", "practice_count": 2, "badges": []}
    assert body["streak_days"] == 2


def test_growth_one_miss_is_not_a_needs_practice_cue(env, child):
    """경계: 놓침 1회 → 더 연습이 필요한 단서 아님(2회 필요)."""
    child_id, cookies = child
    env.seed_session(child_id, ended_at=kst(11, 12, 9), cues={"urgency": "missed"}, scenario_id="s0")

    body = env.get("/api/v1/me/growth", cookies).json()

    assert body["needs_practice_cues"] == []


# ==== A13 (F-28 — 배지·연속 기록 = T-45 계산값) ========================================


def test_home_badges_and_streak_equal_badge_service(env, child):
    child_id, cookies = child
    env.seed_example_history(child_id)
    env.seed_trusted_contact(child_id, "엄마", "010-1234-5678")
    expected = BadgeService(SqlAlchemyBadgeRepository(env.session_factory), clock=lambda: NOW).badges_and_streak(
        UUID(child_id)
    )

    response = env.get("/api/v1/me/home", cookies)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == HOME_KEYS
    assert body["badges"] == [
        {"badge_id": b.badge_id, "area": b.area, "label": b.label} for b in expected.badges
    ]
    assert body["badges"] == [SCAM_BADGE]
    assert body["streak_days"] == expected.streak_days == 3
    assert body["areas"] == [{"area": area} for area in AREAS]
    assert body["trusted_contact"] == {"name": "엄마", "phone": "010-1234-5678"}


def test_home_without_records_or_settings(env, child):
    _child_id, cookies = child

    response = env.get("/api/v1/me/home", cookies)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "areas": [{"area": area} for area in AREAS],
        "badges": [],
        "streak_days": 0,
        "trusted_contact": None,
    }


def test_home_trusted_contact_null_when_not_saved(env, child):
    """설정 행은 있지만 믿는 사람이 비어 있으면 null — 반쪽 값을 만들지 않는다."""
    child_id, cookies = child
    env.seed_trusted_contact(child_id, None, None)

    assert env.get("/api/v1/me/home", cookies).json()["trusted_contact"] is None


# ==== 인증·인가 / 다른 아이 기록 (Architecture 오류 응답 규격·역할 분리) =================

PATHS = ["/api/v1/me/growth", "/api/v1/me/home"]


@pytest.mark.parametrize("path", PATHS)
def test_unauthenticated_is_401(env, path):
    response = env.get(path, None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("path", PATHS)
def test_unknown_session_token_is_401(env, path):
    response = env.get(path, {"sid": "not-a-real-session"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("path", PATHS)
def test_guardian_session_is_403_forbidden_role(env, path):
    guardian = env.new_guardian()

    response = env.get(path, guardian)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"


def test_other_child_records_do_not_leak(env):
    """같은 보호자의 다른 아이 기록이 섞이지 않는다 — 아이 A만 기록, 아이 B는 빈 응답."""
    guardian = env.new_guardian()
    child_a, cookies_a = env.new_child(guardian)
    _child_b, cookies_b = env.new_child(guardian)
    env.seed_example_history(child_a)
    env.seed_trusted_contact(child_a, "엄마", "010-1234-5678")

    growth_b = env.get("/api/v1/me/growth", cookies_b).json()
    home_b = env.get("/api/v1/me/home", cookies_b).json()
    growth_a = env.get("/api/v1/me/growth", cookies_a).json()

    assert growth_b["areas"] == [{"area": area, "practice_count": 0, "badges": []} for area in AREAS]
    assert growth_b["streak_days"] == 0
    assert growth_b["needs_practice_cues"] == []
    assert all(m["status"] == "insufficient" for m in growth_b["metrics"])
    assert home_b == {
        "areas": [{"area": area} for area in AREAS],
        "badges": [],
        "streak_days": 0,
        "trusted_contact": None,
    }
    # 대조: 아이 A에는 기록이 실제로 있다(빈 응답이 늘 나오는 구현이 아님을 확인)
    assert growth_a["streak_days"] == 3
