"""보호자 리포트 A11 (T-25 — F-30 ①②③④, N-05).

- 인가: `get_owned_child(guardian_id, child_id)` 한 쿼리 — 없거나 남의 아이면 404 `CHILD_NOT_FOUND`.
- 원천: practice_sessions·cue_results(`status = ended`만). practice_turns는 읽지 않는다.
- `notices`: guardian_notices(2026-11-12 사용자 답 "T-25에 포함 (추천)"). 최신 순.
- `metrics`: 라우터가 T-46 계산 서비스로 채운다(T-90).
- 약점 단서: 공통 함수 `select_weak_cues`(DECISIONS #122).
- `summary`(T-76 — F-47, DECISIONS #52·#103·#114·#119): 조회마다 이번 지표 기간(#88)의 종료 세션으로 영역별 입력을
  조립해 AI `summary`를 영역마다 1회 부른다. 저장·캐시 없음. 기록 부족 → `insufficient`(AI 미호출), 하나라도
  null·전송 실패·검증 실패(S1~S3) → `unavailable`·items 없음 — 리포트 나머지는 정상.
- 요약 호출(T-98 — ADR-0020, DECISIONS #134): 영역별 호출을 동시에 보내고 전체 상한
  `SUMMARY_DEADLINE_SECONDS`(25초)을 넘으면 `unavailable`. 엔드포인트·포트는 동기 그대로.
"""

import logging
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from time import monotonic
from typing import Protocol
from uuid import UUID

from app.ai_client.ports import AIUnavailableError, SummaryAI, SummaryRequest
from app.core.errors import AppError
from app.domain.guardian_report import AreaProgress, area_progress
from app.domain.guardian_summary import SummarySession, accept_summary, summary_inputs
from app.domain.metrics import metric_periods
from app.domain.service_time import SERVICE_TZ, service_date
from app.domain.weak_cues import select_weak_cues
from app.services.ports import GuardianNoticeRecord, GuardianReportRepository, ReportChild

logger = logging.getLogger(__name__)


class GuardianSummaryRepository(Protocol):
    def ended_summary_sessions(
        self, child_id: UUID, ended_from: datetime, ended_to: datetime
    ) -> list[SummarySession]:
        """`status = ended`이고 `ended_from <= ended_at < ended_to`인 세션 — 영역과 단서 판정 ID만."""
        ...


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_service_day(day: date) -> datetime:
    """한국 시간 날짜의 0시를 UTC 시각으로."""
    return datetime.combine(day, time.min, tzinfo=SERVICE_TZ).astimezone(timezone.utc)


@dataclass(frozen=True)
class WeakCueLabel:
    cue_id: str
    label: str


@dataclass(frozen=True)
class GuardianSummaryItem:
    area: str
    sentences: tuple[str, ...]


@dataclass(frozen=True)
class GuardianSummary:
    status: str  # ok | insufficient | unavailable
    unit: str  # overall | area — 1차는 area (DECISIONS #114)
    items: tuple[GuardianSummaryItem, ...] = ()


# 학습 요약 전체 상한(초) — 첫 제출 직전부터 단조 시계로 잰다 (ADR-0020 규칙 3, 2026-11-15 사용자 "25초로 확정").
# 환경 변수가 아닌 설정 상수 1곳. 테스트는 생성자 인자로 작은 값을 넣는다.
SUMMARY_DEADLINE_SECONDS = 25.0

INSUFFICIENT_SUMMARY = GuardianSummary(status="insufficient", unit="area")
UNAVAILABLE_SUMMARY = GuardianSummary(status="unavailable", unit="area")


@dataclass(frozen=True)
class GuardianReportData:
    child: ReportChild
    areas: list[AreaProgress]
    weak_cues: list[WeakCueLabel]
    notices: tuple[GuardianNoticeRecord, ...] = ()
    metrics: tuple = ()
    summary: GuardianSummary = field(default=INSUFFICIENT_SUMMARY)


class GuardianReportService:
    def __init__(
        self,
        repository: GuardianReportRepository,
        area_ids: Sequence[str],
        clue_labels: Mapping[str, str],
        summary_ai: SummaryAI,
        area_names: Mapping[str, str],
        clock: Callable[[], datetime] = _utcnow,
        summary_deadline_seconds: float | None = None,
    ) -> None:
        self._summary_deadline_seconds = (
            SUMMARY_DEADLINE_SECONDS if summary_deadline_seconds is None else summary_deadline_seconds
        )
        # repository는 GuardianReportRepository + GuardianSummaryRepository 둘 다 구현한다
        self._repository = repository
        self._area_ids = tuple(area_ids)
        self._clue_labels = clue_labels  # 순서 = 콘텐츠 단서 순서(요약 단서 목록 순서)
        self._summary_ai = summary_ai
        self._area_names = area_names  # Area ID → 영역 표시 이름(콘텐츠 areas[].name — AI 계약 `area`)
        self._clock = clock

    def get_report(self, guardian_id: UUID, child_id: UUID) -> GuardianReportData:
        child = self._repository.get_owned_child(guardian_id, child_id)
        if child is None:
            raise AppError(code="CHILD_NOT_FOUND", status_code=404, message="child not found")

        areas = area_progress(self._area_ids, self._repository.ended_sessions(child.child_id))
        # 콘텐츠에 없는 단서(콘텐츠 교체 등)는 이름을 보일 수 없어 뺀다 — 원문·ID 추측 표시 없음
        labeled = [
            WeakCueLabel(cue_id=cue_id, label=self._clue_labels[cue_id])
            for cue_id in select_weak_cues(self._repository.ended_cue_outcomes(child.child_id))
            if cue_id in self._clue_labels
        ]
        return GuardianReportData(
            child=child,
            areas=areas,
            weak_cues=labeled,
            notices=tuple(self._repository.notices(child.child_id)),
            summary=self._summary(child.child_id),
        )

    def _summary(self, child_id: UUID) -> GuardianSummary:
        # 기간 = 지표 이번 기간(오늘 포함 한국 시간 7일 — Architecture LearningSummaryInput 행, DECISIONS #88)
        period = metric_periods(service_date(self._clock())).current
        sessions = self._repository.ended_summary_sessions(
            child_id,
            _start_of_service_day(period[0]),
            _start_of_service_day(period[1] + timedelta(days=1)),
        )
        inputs = summary_inputs(sessions, self._area_ids, tuple(self._clue_labels))
        if inputs is None:
            return INSUFFICIENT_SUMMARY

        requests = [
            SummaryRequest(
                area=self._area_names[item.area],
                practice_count=item.practice_count,
                found_clues=[self._clue_labels[cue] for cue in item.found_cue_ids],
                missed_clues=[self._clue_labels[cue] for cue in item.missed_cue_ids],
                growth_level=None,  # 항상 null — 등급 문자열을 만들지 않음 (F-29 ③, G1)
            )
            for item in inputs
        ]
        texts = self._collect_summaries(requests)
        if texts is None:
            return UNAVAILABLE_SUMMARY
        # items 순서 = 입력 영역 순서(완료 순서 아님 — ADR-0020 규칙 4)
        return GuardianSummary(
            status="ok",
            unit="area",
            items=tuple(
                GuardianSummaryItem(area=item.area, sentences=(text,)) for item, text in zip(inputs, texts)
            ),
        )

    def _collect_summaries(self, requests: Sequence[SummaryRequest]) -> list[str] | None:
        """영역별 요약을 동시에 부르고 전체 상한 안에 모두 통과하면 입력 순서대로 문장을, 아니면 None.

        ADR-0020(T-98): 하나라도 AI 실패·null·검증 실패(S1~S3)·상한 초과면 None — 실패를 아는 즉시 반환한다
        (DECISIONS #103·#119 해석 6, 부분 결과 없음). 워커는 `summary` 호출만, 검증은 이 (요청) 스레드에서 한다.
        `with` 블록은 빠져나갈 때 모든 호출을 기다려 상한을 무력화하므로 쓰지 않는다 — 기다리지 않고 닫는다.
        이미 보낸 호출은 끊을 수 없어 AI 클라이언트 시간 초과까지 백그라운드에서 끝나고 결과·예외는 버려진다.
        """
        executor = ThreadPoolExecutor(max_workers=len(requests), thread_name_prefix="guardian-summary")
        try:
            started = monotonic()
            deadline = started + self._summary_deadline_seconds
            index_of: dict[Future, int] = {
                executor.submit(self._summary_ai.summary, request): index for index, request in enumerate(requests)
            }
            texts: list[str | None] = [None] * len(requests)
            pending = set(index_of)
            while pending:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    # 로그에는 개수·상한·경과만 — 영역·단서 이름 등 요청 값 금지 (Architecture "로그" 행)
                    logger.warning(
                        "guardian summary deadline exceeded areas=%d deadline=%s elapsed=%.2f",
                        len(requests),
                        self._summary_deadline_seconds,
                        monotonic() - started,
                    )
                    return None
                done, pending = wait(pending, timeout=remaining, return_when=FIRST_COMPLETED)
                for future in done:
                    request = requests[index_of[future]]
                    try:
                        text = future.result().summary  # AIUnavailableError 밖의 예외는 그대로 전파 (→ 500)
                    except AIUnavailableError:
                        return None
                    input_values = [
                        request.area,
                        str(request.practice_count),
                        *request.found_clues,
                        *request.missed_clues,
                    ]
                    if not accept_summary(text, input_values):
                        return None
                    texts[index_of[future]] = text
            return [text for text in texts if text is not None]
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
