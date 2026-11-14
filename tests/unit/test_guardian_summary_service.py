"""보호자 리포트 서비스의 학습 요약 (T-76 — F-47 ①②③⑥, DECISIONS #52·#103·#114·#119).

리포지토리·AI는 테스트 대역. 확인하는 것:
- 기간 = 지표 이번 기간(한국 시간 7일, Architecture LearningSummaryInput 행 #88) — 리포지토리에 넘기는 UTC 경계
- 영역마다 AI `summary` 1회, 요청 = {영역 표시 이름, 연습 횟수, 찾은/놓친 단서 이름, growth_level null}
- `growth_level`은 항상 null (Tasks T-76 — T-86 리뷰 권고 #2)
- 하나라도 null·전송 실패·검증 실패 → `unavailable`·items [] / 기록 없음 → `insufficient`, AI 미호출
- 저장·캐시 없음 — 조회마다 다시 호출
"""

import logging
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.ai_client.ports import AIUnavailableError, SummaryRequest, SummaryResponse
from app.core.errors import AppError
from app.domain.guardian_summary import SummarySession
from app.services import guardian_report as guardian_report_module
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


def test_first_area_failure_is_unavailable():
    # T-98(ADR-0020 결과 ①): 병렬 제출이라 "첫 실패 뒤 남은 영역 미호출"은 더 이상 보장하지 않는다 — 결과만 확인
    repo = FakeRepo(two_area_sessions())
    ai = RecordingSummaryAI({"사기": AIUnavailableError("down")})

    report = make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(status="unavailable", unit="area", items=())


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


# ==== 병렬 호출 + 요약 전체 상한 (T-98 — ADR-0020, DECISIONS #134) =====================
# 실제 시간 대기 대신 작은 주입 상한 + Event/Barrier 대역. 막힌 대역은 teardown에서 풀어 스레드를 남기지 않는다.

BLOCK_LIMIT = 3.0  # 대역이 막혀 있는 최대 시간 — 주입 상한보다 충분히 길다
SMALL_DEADLINE = 0.2


def three_area_sessions() -> list[SummarySession]:
    return [*two_area_sessions(), SummarySession(area="identity_lending", found=("urgency",), missed=())]


class GatedSummaryAI:
    """영역 표시 이름별 동작: "block"(gate가 열릴 때까지 막힘) / "null"(summary=null) / 예외 / 기본은 즉시 정상."""

    def __init__(self, behaviors: dict[str, object] | None = None) -> None:
        self.behaviors = behaviors or {}
        self.gate = threading.Event()
        self._lock = threading.Lock()
        self.requests: list[SummaryRequest] = []
        self.finished: list[str] = []

    def summary(self, request: SummaryRequest) -> SummaryResponse:
        with self._lock:
            self.requests.append(request)
        behavior = self.behaviors.get(request.area)
        if behavior == "block":
            self.gate.wait(timeout=BLOCK_LIMIT)
        elif behavior == "null":
            return SummaryResponse(summary=None)
        elif isinstance(behavior, BaseException):
            raise behavior
        with self._lock:
            self.finished.append(request.area)
        return SummaryResponse(summary=f"{request.area} 연습을 {request.practice_count}번 했어요.")


@pytest.fixture
def gated():
    made: list[GatedSummaryAI] = []

    def _make(behaviors: dict[str, object] | None = None) -> GatedSummaryAI:
        ai = GatedSummaryAI(behaviors)
        made.append(ai)
        return ai

    yield _make
    for ai in made:
        ai.gate.set()


def make_deadline_service(repo: FakeRepo, ai, deadline: float) -> GuardianReportService:
    return GuardianReportService(
        repo,
        AREAS,
        CLUE_LABELS,
        summary_ai=ai,
        area_names=AREA_NAMES,
        clock=lambda: NOW,
        summary_deadline_seconds=deadline,
    )


def test_summary_calls_run_concurrently():
    # ① 세 영역 호출이 동시에 진행돼야 Barrier(3)를 넘는다 — 순차면 첫 호출이 Barrier에서 시간 초과
    barrier = threading.Barrier(3, timeout=2.0)

    class BarrierAI(RecordingSummaryAI):
        def summary(self, request):
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                raise AIUnavailableError("not concurrent") from None
            return super().summary(request)

    repo, ai = FakeRepo(three_area_sessions()), BarrierAI()

    report = make_deadline_service(repo, ai, deadline=5.0).get_report(uuid4(), repo.child.child_id)

    assert report.summary.status == "ok"
    assert len(ai.requests) == 3


def test_summary_items_keep_input_area_order_not_completion_order():
    # ② 두 번째 영역이 먼저 끝나도 items는 입력 영역 순서
    friend_done = threading.Event()
    completion: list[str] = []

    class ReverseAI(RecordingSummaryAI):
        def summary(self, request):
            if request.area == "사기" and not friend_done.wait(timeout=2.0):
                raise AIUnavailableError("friend never finished")
            response = super().summary(request)
            completion.append(request.area)
            if request.area == "친구의 무리한 부탁":
                friend_done.set()
            return response

    repo, ai = FakeRepo(two_area_sessions()), ReverseAI()

    report = make_deadline_service(repo, ai, deadline=5.0).get_report(uuid4(), repo.child.child_id)

    assert completion == ["친구의 무리한 부탁", "사기"]
    assert report.summary.status == "ok"
    assert [item.area for item in report.summary.items] == ["scam", "friend_pressure"]


def test_all_areas_over_deadline_is_unavailable_without_waiting(gated):
    # ③ 전체 상한 초과 → unavailable, 막힌 호출을 기다리지 않고 반환
    ai = gated({"사기": "block", "친구의 무리한 부탁": "block"})
    repo = FakeRepo(two_area_sessions())

    started = time.monotonic()
    report = make_deadline_service(repo, ai, SMALL_DEADLINE).get_report(uuid4(), repo.child.child_id)
    elapsed = time.monotonic() - started

    assert report.summary == GuardianSummary(status="unavailable", unit="area", items=())
    assert ai.finished == []  # 막힌 호출이 아직 끝나지 않았는데 반환됨
    assert elapsed < BLOCK_LIMIT


def test_in_flight_calls_finish_in_background_and_are_discarded_after_deadline(gated):
    # PR #31 팀원 리뷰 P2 ② — shutdown(wait=False)는 이미 보낸 호출을 끊지 않는다: 상한 뒤에도 백그라운드에서
    # 끝까지 실행되지만, 반환된 결과(unavailable)는 바뀌지 않는다(결과 버림, ADR-0020 결정 5)
    ai = gated({"사기": "block", "친구의 무리한 부탁": "block"})
    repo = FakeRepo(two_area_sessions())

    report = make_deadline_service(repo, ai, SMALL_DEADLINE).get_report(uuid4(), repo.child.child_id)
    assert ai.finished == []

    ai.gate.set()
    deadline = time.monotonic() + BLOCK_LIMIT
    while len(ai.finished) < 2 and time.monotonic() < deadline:
        time.sleep(0.01)

    assert sorted(ai.finished) == sorted(["사기", "친구의 무리한 부탁"])  # 호출은 백그라운드에서 끝까지 실행됨
    assert report.summary == GuardianSummary(status="unavailable", unit="area", items=())  # 결과는 버려짐


def test_one_area_over_deadline_makes_whole_summary_unavailable(gated):
    # ④ 일부만 초과해도 전체 unavailable — 부분 결과 없음
    ai = gated({"친구의 무리한 부탁": "block"})
    repo = FakeRepo(two_area_sessions())

    report = make_deadline_service(repo, ai, SMALL_DEADLINE).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(status="unavailable", unit="area", items=())
    assert "친구의 무리한 부탁" not in ai.finished
    assert report.child == repo.child


@pytest.mark.parametrize("failure", [AIUnavailableError("down"), "null"], ids=["transport_failure", "null_summary"])
def test_known_failure_returns_without_waiting_other_areas(gated, failure):
    # ⑤ 한 영역 실패를 알면 다른 영역(막힘)을 기다리지 않고 바로 반환 — 상한(2초) 전에
    ai = gated({"사기": "block", "친구의 무리한 부탁": failure})
    repo = FakeRepo(two_area_sessions())

    started = time.monotonic()
    report = make_deadline_service(repo, ai, deadline=2.0).get_report(uuid4(), repo.child.child_id)
    elapsed = time.monotonic() - started

    assert report.summary == GuardianSummary(status="unavailable", unit="area", items=())
    assert "사기" not in ai.finished  # 막힌 영역을 기다리지 않았다
    assert elapsed < 2.0


def test_single_area_calls_ai_once_and_is_ok():
    # ⑥ 영역 1개(현재 출제 범위) → 1회 호출 ok
    repo = FakeRepo([SummarySession(area="scam", found=("urgency",), missed=())])
    ai = RecordingSummaryAI()

    report = make_deadline_service(repo, ai, deadline=5.0).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(
        status="ok", unit="area", items=(GuardianSummaryItem(area="scam", sentences=("사기 연습을 1번 했어요.",)),)
    )
    assert len(ai.requests) == 1


def test_insufficient_with_deadline_service_calls_ai_zero_times():
    # ⑦ 기록 부족 → AI 0회 (상한 주입과 무관)
    repo, ai = FakeRepo([]), RecordingSummaryAI()

    report = make_deadline_service(repo, ai, deadline=5.0).get_report(uuid4(), repo.child.child_id)

    assert report.summary == GuardianSummary(status="insufficient", unit="area", items=())
    assert ai.requests == []


def test_default_deadline_is_25_seconds():
    # ⑧ 기본 상한 = 25초 (ADR-0020 규칙 3)
    assert guardian_report_module.SUMMARY_DEADLINE_SECONDS == 25


def test_service_without_deadline_argument_uses_module_constant(gated, monkeypatch):
    # ⑧ 생성자 인자를 안 주면 설정 상수를 쓴다 — 상수를 작게 바꿔 막힌 호출에서 상한으로 끝나는지 확인
    monkeypatch.setattr(guardian_report_module, "SUMMARY_DEADLINE_SECONDS", SMALL_DEADLINE)
    ai = gated({"사기": "block"})
    repo = FakeRepo(two_area_sessions())

    report = make_service(repo, ai).get_report(uuid4(), repo.child.child_id)

    assert report.summary.status == "unavailable"
    assert "사기" not in ai.finished


def test_non_ai_unavailable_error_propagates():
    # ⑨ AIUnavailableError가 아닌 예외(프로그래밍 오류)는 전파 → 라우터에서 500
    repo = FakeRepo(two_area_sessions())
    ai = RecordingSummaryAI({"친구의 무리한 부탁": RuntimeError("bug")})

    with pytest.raises(RuntimeError, match="bug"):
        make_deadline_service(repo, ai, deadline=5.0).get_report(uuid4(), repo.child.child_id)


def test_deadline_exceeded_logs_counts_only(gated, caplog):
    # ADR-0020 규칙 7: 상한 초과 warning 1줄 — 영역 수·상한값·경과 시간만, 영역·단서 이름 금지
    ai = gated({"사기": "block"})
    repo = FakeRepo(two_area_sessions())

    with caplog.at_level(logging.WARNING, logger="app.services.guardian_report"):
        make_deadline_service(repo, ai, SMALL_DEADLINE).get_report(uuid4(), repo.child.child_id)

    records = [r for r in caplog.records if r.name == "app.services.guardian_report"]
    assert len(records) == 1
    message = records[0].getMessage()
    assert "areas=2" in message and "deadline=0.2" in message and "elapsed=" in message
    for forbidden in ("사기", "친구", "빨리 하래요", "돈을 먼저 내래요"):
        assert forbidden not in message
