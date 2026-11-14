"""보호자 리포트 A11 (T-25 — F-30 ①②③④, N-05).

- 인가: `get_owned_child(guardian_id, child_id)` 한 쿼리 — 없거나 남의 아이면 404 `CHILD_NOT_FOUND`.
- 원천: practice_sessions·cue_results(`status = ended`만). practice_turns는 읽지 않는다.
- `notices`: guardian_notices(2026-11-12 사용자 답 "T-25에 포함 (추천)"). 최신 순.
- `metrics`: 라우터가 T-46 계산 서비스로 채운다(T-90).
- 약점 단서: 공통 함수 `select_weak_cues`(DECISIONS #122).
- `summary`(T-76 — F-47, DECISIONS #52·#103·#114·#119): 조회마다 이번 지표 기간(#88)의 종료 세션으로 영역별 입력을
  조립해 AI `summary`를 영역마다 1회 부른다. 저장·캐시 없음. 기록 부족 → `insufficient`(AI 미호출), 하나라도
  null·전송 실패·검증 실패(S1~S3) → `unavailable`·items 없음 — 리포트 나머지는 정상.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
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
    ) -> None:
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

        items: list[GuardianSummaryItem] = []
        for item in inputs:
            request = SummaryRequest(
                area=self._area_names[item.area],
                practice_count=item.practice_count,
                found_clues=[self._clue_labels[cue] for cue in item.found_cue_ids],
                missed_clues=[self._clue_labels[cue] for cue in item.missed_cue_ids],
                growth_level=None,  # 항상 null — 등급 문자열을 만들지 않음 (F-29 ③, G1)
            )
            try:
                text = self._summary_ai.summary(request).summary
            except AIUnavailableError:
                return UNAVAILABLE_SUMMARY
            input_values = [
                request.area,
                str(request.practice_count),
                *request.found_clues,
                *request.missed_clues,
            ]
            # 하나라도 실패하면 요약 칸 전체 실패 — 남은 영역은 부르지 않는다 (DECISIONS #103·#119)
            if not accept_summary(text, input_values):
                return UNAVAILABLE_SUMMARY
            items.append(GuardianSummaryItem(area=item.area, sentences=(text,)))
        return GuardianSummary(status="ok", unit="area", items=tuple(items))
