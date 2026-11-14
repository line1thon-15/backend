"""보호자 리포트 서비스의 학습 요약 (T-76 — F-47 ①②③⑥, DECISIONS #52·#103·#114·#119).

리포지토리·AI는 테스트 대역. 확인하는 것:
- 기간 = 지표 이번 기간(한국 시간 7일, Architecture LearningSummaryInput 행 #88) — 리포지토리에 넘기는 UTC 경계
- 영역마다 AI `summary` 1회, 요청 = {영역 표시 이름, 연습 횟수, 찾은/놓친 단서 이름, growth_level null}
- `growth_level`은 항상 null (Tasks T-76 — T-86 리뷰 권고 #2)
- 하나라도 null·전송 실패·검증 실패 → `unavailable`·items [] / 기록 없음 → `insufficient`, AI 미호출
- 저장·캐시 없음 — 조회마다 다시 호출
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.ai_client.ports import AIUnavailableError, SummaryRequest, SummaryResponse
from app.core.errors import AppError
from app.domain.guardian_summary import SummarySession
from app.services.guardian_report import GuardianReportService, GuardianSummary, GuardianSummaryItem
from app.services.ports import ReportChild

AREAS = ("scam", "identity_lending", "friend_pressure")
AREA_NAMES = {"scam": "사기", "identity_lending": "명의 빌려주기", "friend_pressure": "친구의 무리한 부탁"}
CLUE_LABELS = {"advance_payment": "돈을 먼저 내래요", "urgency": "빨리 하래요", "guilt_pressure": "미안하게 만들어요"}
# 한국 시간 2026-11-12 12:00 → 이번 기간 [11-06, 11-12]
NOW = datetime(2026, 11, 12, 3, 0, tzinfo=timezone.utc)
PERIOD_FROM = datetime(2026, 11, 5, 15, 0, tzinfo=timezone.utc)  # 11-06 00:00 KST
PERIOD_TO = datetime(2026, 11, 12, 15, 0, tzinfo=timezone.utc)  # 11-13 00:00 KST (미포함)


class FakeRepo:
    def __init__(self, sessions: list[SummarySession], owned: bool = True) -> None:
        self.child = ReportChild(child_id=uuid4(), nickname="하늘이")
        self.sessions = sessions
        self.owned = owned
        self.summary_calls: list[tuple] = []

    def get_owned_child(self, guardian_id, child_id):
        return self.child if self.owned else None

    def ended_sessions(self, child_id):
        return []

    def ended_cue_outcomes(self, child_id):
        return []

    def notices(self, child_id):
        return []

    def ended_summary_sessions(self, child_id, ended_from, ended_to):
        self.summary_calls.append((child_id, ended_from, ended_to))
        return list(self.sessions)


class RecordingSummaryAI:
    def __init__(self, replies: dict[str, object] | None = None) -> None:
        # 영역 표시 이름 → 응답 문자열 / None / 예외
        self.replies = replies or {}
        self.requests: list[SummaryRequest] = []

    def summary(self, request: SummaryRequest) -> SummaryResponse:
        self.requests.append(request)
        reply = self.replies.get(request.area, f"{request.area} 연습을 {request.practice_count}번 했어요.")
        if isinstance(reply, Exception):
            raise reply
        return SummaryResponse(summary=reply)


def make_service(repo: FakeRepo, ai: RecordingSummaryAI) -> GuardianReportService:
    return GuardianReportService(
        repo,
        AREAS,
        CLUE_LABELS,
        summary_ai=ai,
        area_names=AREA_NAMES,
        clock=lambda: NOW,
    )


def two_area_sessions() -> list[SummarySession]:
    return [
        SummarySession(area="scam", found=("urgency",), missed=("advance_payment",)),
        SummarySession(area="scam", found=("urgency",), missed=()),
        SummarySession(area="friend_pressure", found=(), missed=("guilt_pressure",)),
    ]


def test_summary_per_area_ok():
    repo, ai = FakeRepo(two_area_sessions()), RecordingSummaryAI()

    report = make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(
        status="ok",
        unit="area",
        items=(
            GuardianSummaryItem(area="scam", sentences=("사기 연습을 2번 했어요.",)),
            GuardianSummaryItem(area="friend_pressure", sentences=("친구의 무리한 부탁 연습을 1번 했어요.",)),
        ),
    )


def test_summary_requests_carry_only_computed_values():
    repo, ai = FakeRepo(two_area_sessions()), RecordingSummaryAI()

    make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert [r.model_dump() for r in ai.requests] == [
        {
            "area": "사기",
            "practice_count": 2,
            "found_clues": ["빨리 하래요"],
            "missed_clues": ["돈을 먼저 내래요"],
            "growth_level": None,
        },
        {
            "area": "친구의 무리한 부탁",
            "practice_count": 1,
            "found_clues": [],
            "missed_clues": ["미안하게 만들어요"],
            "growth_level": None,
        },
    ]


def test_growth_level_is_always_null():
    # Tasks T-76 — T-86 리뷰 권고 #2: Fake가 받은 요청으로 단언
    repo, ai = FakeRepo(two_area_sessions()), RecordingSummaryAI()

    make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert ai.requests and all(r.growth_level is None for r in ai.requests)


def test_summary_period_is_current_metric_period_in_service_time():
    repo, ai = FakeRepo(two_area_sessions()), RecordingSummaryAI()

    make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert repo.summary_calls == [(repo.child.child_id, PERIOD_FROM, PERIOD_TO)]


def test_no_records_in_period_is_insufficient_without_ai_call():
    repo, ai = FakeRepo([]), RecordingSummaryAI()

    report = make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(status="insufficient", unit="area", items=())
    assert ai.requests == []


@pytest.mark.parametrize(
    "bad_reply",
    [
        None,  # AI 실패 응답 summary=null
        "   ",  # S1 공백만
        "친구의 무리한 부탁 연습 정답률이 90이에요.",  # S2 입력에 없는 숫자
        "가" * 201,  # S3 길이 상한
        AIUnavailableError("timeout"),  # 전송 실패
    ],
)
def test_any_area_failure_makes_whole_summary_unavailable(bad_reply):
    repo = FakeRepo(two_area_sessions())
    ai = RecordingSummaryAI({"친구의 무리한 부탁": bad_reply})

    report = make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(status="unavailable", unit="area", items=())
    # 나머지 리포트는 그대로
    assert report.child == repo.child


def test_first_area_failure_stops_further_calls():
    repo = FakeRepo(two_area_sessions())
    ai = RecordingSummaryAI({"사기": AIUnavailableError("down")})

    report = make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert report.summary.status == "unavailable"
    assert [r.area for r in ai.requests] == ["사기"]


def test_summary_is_not_cached_between_reports():
    repo, ai = FakeRepo(two_area_sessions()), RecordingSummaryAI()
    service = make_service(repo, ai)

    service.get_report(uuid4(), repo.child.child_id)
    service.get_report(uuid4(), repo.child.child_id)

    assert len(ai.requests) == 4


def test_other_guardians_child_does_not_call_ai():
    repo, ai = FakeRepo(two_area_sessions(), owned=False), RecordingSummaryAI()

    with pytest.raises(AppError) as exc:
        make_service(repo, ai).get_report(uuid4(), uuid4())

    assert exc.value.code == "CHILD_NOT_FOUND"
    assert ai.requests == []
    assert repo.summary_calls == []
