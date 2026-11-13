"""성장 지표 3개 — 백엔드 domain 순수 함수 (T-46, F-29 ⑤⑥, F-31 데이터 측).

근거: Architecture "성장 계산 규칙" 절·"공통 값 타입" 시각 행·"응답 DTO" MetricView 행,
DECISIONS #88·#94(한국 시간)·#93(지표 (다) 원천 = 첫 답 kind)·#116(최종 규격)·#117(★), ADR-0018 N1.

- 입력은 종료(`status = ended`) 세션만 — `in_progress`·`stopped`는 리포지토리가 넘기지 않는다(#113).
- 시계를 직접 읽지 않는다. 오늘(한국 시간 날짜)과 세션 날짜를 인자로 받는다(#89 → #94).
- `level`(지표 신호등)은 PRD OQ 63 ② 미결이라 항상 None — 규칙을 지어내지 않는다.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from types import MappingProxyType

from app.domain.service_time import SERVICE_TZ, service_date  # noqa: F401 — 한국 시간 1곳 (#94)

METRIC_PERIOD_DAYS = 7
METRIC_MIN_SESSIONS = 3

MISSED_RATIO = "missed_ratio"
FIRST_SEEN_ACCURACY = "first_seen_accuracy"
AHEAD_OF_AI_RATIO = "ahead_of_ai_ratio"
METRIC_IDS: tuple[str, ...] = (MISSED_RATIO, FIRST_SEEN_ACCURACY, AHEAD_OF_AI_RATIO)

# MetricView.label 설정 상수 1곳 — 아이 Y8(A19)과 보호자 G3(A11)가 같은 문구를 쓴다(T-90).
# 2026-11-12 사용자 답 "쉬운 말 문구 (추천)", 선택지 설명 원문 "① '놓친 신호' ② '처음 본 상황에서 찾은 신호'
# ③ '먼저 알아챈 횟수'. 느린학습자용 쉬운 말(N-03). 아이 Y8과 보호자 G3가 같은 문구를 써요."
METRIC_LABELS: Mapping[str, str] = MappingProxyType(
    {
        MISSED_RATIO: "놓친 신호",
        FIRST_SEEN_ACCURACY: "처음 본 상황에서 찾은 신호",
        AHEAD_OF_AI_RATIO: "먼저 알아챈 횟수",
    }
)

# 지표 (다)의 분자 — 첫 답에서 PRD '의심' 선택지(AI 계약 kind = correct)를 고른 세션 (#93·#97·#115)
AHEAD_KIND = "correct"


class MissingFirstAnswerKind(Exception):
    """기간 안 위험 상황 종료 세션인데 첫 답(turn_index 0)의 kind가 없음 — 임의로 세지 않는다(500)."""


@dataclass(frozen=True)
class MetricPeriods:
    current: tuple[date, date]  # [오늘 − 6일, 오늘] 양끝 포함
    previous: tuple[date, date]  # [오늘 − 13일, 오늘 − 7일] 양끝 포함


def metric_periods(today: date) -> MetricPeriods:
    current_start = today - timedelta(days=METRIC_PERIOD_DAYS - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=METRIC_PERIOD_DAYS - 1)
    return MetricPeriods(current=(current_start, today), previous=(previous_start, previous_end))


@dataclass(frozen=True)
class MetricSession:
    """종료 세션 1개의 지표 입력 — 날짜·범주값·개수만 (문장·선택지 내용 없음)."""

    ended_on: date  # ended_at의 한국 시간 날짜
    is_normal: bool
    is_retry: bool  # mode = retry
    is_first_of_scenario: bool  # 같은 아이·같은 시나리오 세션 중 가장 먼저 받은 세션
    found: int
    missed: int
    first_answer_kind: str | None  # turn_index 0에서 고른 선택지 kind


@dataclass(frozen=True)
class TrendPoint:
    date: date
    value: float


@dataclass(frozen=True)
class MetricResult:
    metric_id: str
    status: str  # "ok" | "insufficient"
    current: float | None
    previous: float | None
    trend: tuple[TrendPoint, ...]
    level: str | None = None  # PRD OQ 63 ② 미결 — 항상 None


@dataclass(frozen=True)
class _Ratio:
    sessions: int
    value: float | None


def _revealed(session: MetricSession) -> int:
    return session.found + session.missed


def _missed_ratio(sessions: Sequence[MetricSession]) -> _Ratio:
    # 분모 세션 = 위험 상황 종료 세션 중 드러난 단서 ≥ 1 (★ #117)
    counted = [s for s in sessions if not s.is_normal and _revealed(s) >= 1]
    revealed = sum(_revealed(s) for s in counted)
    return _Ratio(len(counted), sum(s.missed for s in counted) / revealed if revealed else None)


def _first_seen_accuracy(sessions: Sequence[MetricSession]) -> _Ratio:
    counted = [
        s
        for s in sessions
        if not s.is_normal and not s.is_retry and s.is_first_of_scenario and _revealed(s) >= 1
    ]
    revealed = sum(_revealed(s) for s in counted)
    return _Ratio(len(counted), sum(s.found for s in counted) / revealed if revealed else None)


def _ahead_of_ai_ratio(sessions: Sequence[MetricSession]) -> _Ratio:
    # 분모 세션 = 위험 상황 종료 세션 전부(다시 도전 포함, ★ 적용 안 함)
    counted = [s for s in sessions if not s.is_normal]
    if any(s.first_answer_kind is None for s in counted):
        raise MissingFirstAnswerKind("ended danger session without first answer kind")
    ahead = sum(1 for s in counted if s.first_answer_kind == AHEAD_KIND)
    return _Ratio(len(counted), ahead / len(counted) if counted else None)


_CALCULATORS: dict[str, Callable[[Sequence[MetricSession]], _Ratio]] = {
    MISSED_RATIO: _missed_ratio,
    FIRST_SEEN_ACCURACY: _first_seen_accuracy,
    AHEAD_OF_AI_RATIO: _ahead_of_ai_ratio,
}


def _within(session: MetricSession, period: tuple[date, date]) -> bool:
    return period[0] <= session.ended_on <= period[1]


def compute_metrics(sessions: Sequence[MetricSession], today: date) -> tuple[MetricResult, ...]:
    """지표 3개를 METRIC_IDS 순서로 계산한다.

    지표마다 이번·직전 기간의 분모 세션 수를 세어, 어느 한 기간이라도 METRIC_MIN_SESSIONS 미만이면
    insufficient(숫자 없음, trend 없음). 둘 다 이상이면 ok + trend 2점(직전 기간 마지막 날, 오늘).
    """
    periods = metric_periods(today)
    current_sessions = [s for s in sessions if _within(s, periods.current)]
    previous_sessions = [s for s in sessions if _within(s, periods.previous)]

    results: list[MetricResult] = []
    for metric_id in METRIC_IDS:
        calculate = _CALCULATORS[metric_id]
        current = calculate(current_sessions)
        previous = calculate(previous_sessions)
        if min(current.sessions, previous.sessions) < METRIC_MIN_SESSIONS:
            results.append(MetricResult(metric_id, "insufficient", None, None, ()))
            continue
        assert current.value is not None and previous.value is not None  # 분모 세션 ≥ 3이면 분모 > 0
        results.append(
            MetricResult(
                metric_id,
                "ok",
                current.value,
                previous.value,
                (
                    TrendPoint(date=periods.previous[1], value=previous.value),
                    TrendPoint(date=periods.current[1], value=current.value),
                ),
            )
        )
    return tuple(results)
