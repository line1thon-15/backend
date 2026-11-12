"""성장 지표 3개 계산 유스케이스 (T-46 — F-29 ⑤⑥, F-31 데이터 측).

아이 성장(A19)과 보호자 리포트(A11, T-25)·보호자 학습 요약(T-76)이 같은 계산을 쓰도록 HTTP와 분리한
서비스다(Architecture 데이터 흐름 5번 "A19·A11이 같이 쓴다"). 결과는 domain `MetricResult` 그대로 —
API DTO 변환은 각 라우터가 한다.

리포지토리 호출은 허용 목록 4개뿐이다(ADR-0016 R4 — tests/unit/test_import_boundaries.py ⑤).
practice_turns를 읽는 것은 `first_answer_kinds` 하나(첫 답 kind만 — 문장·선택지 내용 없음).
"""

from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from app.domain.metrics import MetricResult, MetricSession, compute_metrics, metric_periods
from app.domain.service_time import SERVICE_TZ, service_date
from app.domain.weak_cues import CueOutcome, select_weak_cues
from app.services.ports import PracticeRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_service_day(day: date) -> datetime:
    """한국 시간 날짜의 0시를 UTC 시각으로."""
    return datetime.combine(day, time.min, tzinfo=SERVICE_TZ).astimezone(timezone.utc)


class GrowthMetricsService:
    def __init__(
        self,
        repository: PracticeRepository,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    def metrics(self, child_id: UUID) -> tuple[MetricResult, ...]:
        today = service_date(self._clock())
        periods = metric_periods(today)
        # 두 기간 전체 = [직전 기간 첫날 0시, 오늘 다음 날 0시) — 한국 시간 날짜 기준
        ended_from = _start_of_service_day(periods.previous[0])
        ended_to = _start_of_service_day(periods.current[1] + timedelta(days=1))

        stats = self._repository.ended_session_stats(child_id, ended_from, ended_to)
        first_ids = self._repository.first_session_ids(child_id, [s.scenario_id for s in stats])
        kinds = {
            item.session_id: item.kind
            for item in self._repository.first_answer_kinds(child_id, ended_from, ended_to)
        }
        sessions = [
            MetricSession(
                ended_on=service_date(s.ended_at),
                is_normal=s.is_normal,
                is_retry=s.mode == "retry",
                is_first_of_scenario=first_ids.get(s.scenario_id) == s.session_id,
                found=s.found,
                missed=s.missed,
                first_answer_kind=kinds.get(s.session_id),
            )
            for s in stats
        ]
        return compute_metrics(sessions, today)

    def needs_practice_cue_ids(self, child_id: UUID) -> tuple[str, ...]:
        """더 연습이 필요한 단서 ID(최대 3개, 순서 있음) — 보호자 약점 단서와 같은 규칙(T-25 재사용).

        단서 카드(label·sentence)로 바꾸는 것은 응답을 조립하는 쪽(T-90·T-25)이 콘텐츠로 한다.
        """
        return select_weak_cues(
            [
                CueOutcome(cue_id=o.cue_id, outcome=o.outcome, ended_at=o.ended_at, session_id=o.session_id)
                for o in self._repository.ended_cue_outcomes(child_id)
            ]
        )
