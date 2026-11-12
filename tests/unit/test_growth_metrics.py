"""성장 지표 3개 domain 순수 함수 (T-46 — F-29 ②③⑤⑥).

근거: Architecture "성장 계산 규칙" 절·"공통 값 타입" 시각 행·"응답 DTO" MetricView 행,
DECISIONS #88·#89(→#94)·#93·#116·#117, ADR-0018 N1, 테스트 전략 2026-11-11 ②③ 항목.

오늘은 2026-11-12(한국 시간)로 고정한다 → 이번 기간 [11-06, 11-12], 직전 기간 [10-30, 11-05].
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.metrics import (
    METRIC_IDS,
    METRIC_MIN_SESSIONS,
    METRIC_PERIOD_DAYS,
    SERVICE_TZ,
    MetricSession,
    MissingFirstAnswerKind,
    TrendPoint,
    compute_metrics,
    metric_periods,
    service_date,
)

TODAY = date(2026, 11, 12)
CUR = date(2026, 11, 10)  # 이번 기간 안
PREV = date(2026, 11, 2)  # 직전 기간 안


def danger(
    ended_on: date,
    *,
    found: int = 1,
    missed: int = 0,
    first_kind: str | None = "correct",
    retry: bool = False,
    first_of_scenario: bool = True,
) -> MetricSession:
    return MetricSession(
        ended_on=ended_on,
        is_normal=False,
        is_retry=retry,
        is_first_of_scenario=first_of_scenario,
        found=found,
        missed=missed,
        first_answer_kind=first_kind,
    )


def normal(ended_on: date, first_kind: str | None = "correct") -> MetricSession:
    return MetricSession(
        ended_on=ended_on,
        is_normal=True,
        is_retry=False,
        is_first_of_scenario=True,
        found=0,
        missed=0,
        first_answer_kind=first_kind,
    )


def by_id(results) -> dict:
    return {result.metric_id: result for result in results}


def three_each(**kwargs) -> list[MetricSession]:
    return [danger(CUR, **kwargs) for _ in range(3)] + [danger(PREV, **kwargs) for _ in range(3)]


# ==== 상수·기간 창·한국 시간 ==========================================================


def test_constants_match_architecture():
    assert METRIC_PERIOD_DAYS == 7
    assert METRIC_MIN_SESSIONS == 3
    assert SERVICE_TZ.utcoffset(None) == timedelta(hours=9)
    assert METRIC_IDS == ("missed_ratio", "first_seen_accuracy", "ahead_of_ai_ratio")


def test_metric_periods_are_today_minus_6_and_the_7_days_before():
    periods = metric_periods(TODAY)

    assert periods.current == (date(2026, 11, 6), date(2026, 11, 12))
    assert periods.previous == (date(2026, 10, 30), date(2026, 11, 5))


@pytest.mark.parametrize(
    "moment, expected",
    [
        (datetime(2026, 11, 10, 15, 0, 0, tzinfo=timezone.utc), date(2026, 11, 11)),
        (datetime(2026, 11, 10, 14, 59, 59, tzinfo=timezone.utc), date(2026, 11, 10)),
    ],
)
def test_service_date_uses_korea_time(moment, expected):
    assert service_date(moment) == expected


def test_service_date_rejects_naive_datetime():
    with pytest.raises(ValueError):
        service_date(datetime(2026, 11, 10, 15, 0, 0))


@pytest.mark.parametrize(
    "ended_on, counted_in",
    [
        (date(2026, 11, 12), "current"),  # 오늘(이번 기간 끝)
        (date(2026, 11, 6), "current"),  # 이번 기간 첫날
        (date(2026, 11, 5), "previous"),  # 직전 기간 끝
        (date(2026, 10, 30), "previous"),  # 직전 기간 첫날
        (date(2026, 10, 29), None),  # 두 기간 밖
        (date(2026, 11, 13), None),  # 오늘 뒤
    ],
)
def test_period_boundaries_inclusive(ended_on, counted_in):
    # 경계 날짜 세션 1개 + 각 기간 3개를 채운 뒤, 그 1개가 어느 기간의 missed로 들어가는지 본다
    base = [danger(CUR, found=1) for _ in range(3)] + [danger(PREV, found=1) for _ in range(3)]
    probe = danger(ended_on, found=0, missed=1, first_kind="other")

    missed = by_id(compute_metrics(base + [probe], TODAY))["missed_ratio"]

    assert missed.status == "ok"
    expected_current = 1 / 4 if counted_in == "current" else 0.0
    expected_previous = 1 / 4 if counted_in == "previous" else 0.0
    assert missed.current == pytest.approx(expected_current)
    assert missed.previous == pytest.approx(expected_previous)


# ==== (가) missed_ratio ===============================================================


def test_missed_ratio_example_found7_missed3_is_0_3():
    # PRD F-29 ⑤ 예: 최근 7일 드러난 단서 10개(찾음 7 + 놓침 3) → 0.3
    sessions = [
        danger(CUR, found=3, missed=1),
        danger(CUR, found=2, missed=1),
        danger(CUR, found=2, missed=1),
    ] + [danger(PREV, found=1, missed=1) for _ in range(3)]

    missed = by_id(compute_metrics(sessions, TODAY))["missed_ratio"]

    assert missed.status == "ok"
    assert missed.current == pytest.approx(0.3)
    assert missed.previous == pytest.approx(0.5)
    assert missed.level is None


def test_not_shown_is_not_in_denominator_found1_each_gives_missed0_accuracy1():
    # 세션 3개 각 found 1(not_shown 3은 cue_results에 없음 — 입력에 오지 않음) → (가) 0, (나) 1.0
    results = by_id(compute_metrics(three_each(found=1, missed=0), TODAY))

    assert results["missed_ratio"].current == 0.0
    assert results["first_seen_accuracy"].current == 1.0


def test_zero_revealed_session_is_dropped_from_a_and_b_but_not_c():
    # ★ #117: 이번 기간 위험 상황 3개 중 1개가 찾음 0·놓침 0 → (가)(나) 이번 기간 비교 불가, (다)는 3개로 계산
    sessions = [
        danger(CUR, found=1, missed=0, first_kind="correct"),
        danger(CUR, found=0, missed=1, first_kind="other"),
        danger(CUR, found=0, missed=0, first_kind="correct"),
    ] + [danger(PREV) for _ in range(3)]

    results = by_id(compute_metrics(sessions, TODAY))

    assert results["missed_ratio"].status == "insufficient"
    assert results["first_seen_accuracy"].status == "insufficient"
    assert results["ahead_of_ai_ratio"].status == "ok"
    assert results["ahead_of_ai_ratio"].current == pytest.approx(2 / 3)


def test_normal_sessions_change_nothing():
    base = three_each(found=2, missed=1, first_kind="other")
    with_normals = base + [normal(CUR, "correct") for _ in range(3)] + [normal(PREV, "correct")]

    assert compute_metrics(with_normals, TODAY) == compute_metrics(base, TODAY)


# ==== (나) first_seen_accuracy ========================================================


def test_first_seen_accuracy_excludes_retry_and_repeated_scenarios():
    sessions = [
        danger(CUR, found=1, missed=1),
        danger(CUR, found=2, missed=0),
        danger(CUR, found=1, missed=0),
        # 아래 둘은 (나)에서 빠진다 — 다시 도전, 이전에 받은 시나리오
        danger(CUR, found=0, missed=5, retry=True),
        danger(CUR, found=0, missed=5, first_of_scenario=False),
    ] + [danger(PREV, found=1, missed=1) for _ in range(3)]

    results = by_id(compute_metrics(sessions, TODAY))
    accuracy = results["first_seen_accuracy"]

    assert accuracy.status == "ok"
    assert accuracy.current == pytest.approx(4 / 5)
    assert accuracy.previous == pytest.approx(0.5)
    # (가)는 다시 도전·반복 시나리오도 센다: missed 1+0+0+5+5 ÷ 드러남 2+2+1+5+5
    assert results["missed_ratio"].current == pytest.approx(11 / 15)


def test_first_seen_accuracy_insufficient_when_only_two_first_sessions():
    sessions = [
        danger(CUR),
        danger(CUR),
        danger(CUR, retry=True),
    ] + [danger(PREV) for _ in range(3)]

    results = by_id(compute_metrics(sessions, TODAY))

    assert results["first_seen_accuracy"].status == "insufficient"
    assert results["missed_ratio"].status == "ok"


# ==== (다) ahead_of_ai_ratio ==========================================================


def test_ahead_of_ai_correct2_other1_is_two_thirds_including_retry():
    sessions = [
        danger(CUR, first_kind="correct"),
        danger(CUR, first_kind="correct", retry=True),
        danger(CUR, first_kind="other"),
        normal(CUR, "correct"),  # 정상 상황 첫 답 correct는 분자·분모 모두 제외
    ] + [danger(PREV, first_kind="doubtful") for _ in range(3)]

    ahead = by_id(compute_metrics(sessions, TODAY))["ahead_of_ai_ratio"]

    assert ahead.status == "ok"
    assert ahead.current == pytest.approx(2 / 3)
    assert ahead.previous == 0.0


def test_missing_first_answer_kind_raises():
    sessions = three_each()
    sessions[0] = danger(CUR, first_kind=None)

    with pytest.raises(MissingFirstAnswerKind):
        compute_metrics(sessions, TODAY)


def test_missing_first_answer_kind_outside_periods_is_ignored():
    sessions = three_each() + [danger(date(2026, 10, 1), first_kind=None)]

    assert by_id(compute_metrics(sessions, TODAY))["ahead_of_ai_ratio"].status == "ok"


# ==== 비교 불가·추이·형태 =============================================================


def test_two_sessions_each_period_is_insufficient_without_numbers():
    sessions = [danger(CUR) for _ in range(2)] + [danger(PREV) for _ in range(2)]

    for result in compute_metrics(sessions, TODAY):
        assert result.status == "insufficient"
        assert result.current is None
        assert result.previous is None
        assert result.trend == ()
        assert result.level is None


def test_three_sessions_each_period_is_ok_with_two_point_trend():
    sessions = [danger(CUR, found=1, missed=1, first_kind="correct") for _ in range(3)] + [
        danger(PREV, found=0, missed=1, first_kind="other") for _ in range(3)
    ]

    results = compute_metrics(sessions, TODAY)

    assert [r.metric_id for r in results] == list(METRIC_IDS)
    missed = by_id(results)["missed_ratio"]
    assert missed.status == "ok"
    assert missed.trend == (
        TrendPoint(date=date(2026, 11, 5), value=1.0),
        TrendPoint(date=date(2026, 11, 12), value=0.5),
    )
    for result in results:
        assert result.status == "ok"
        assert result.level is None
        assert len(result.trend) == 2


def test_current3_previous2_is_insufficient():
    sessions = [danger(CUR) for _ in range(3)] + [danger(PREV) for _ in range(2)]

    for result in compute_metrics(sessions, TODAY):
        assert result.status == "insufficient"


def test_no_sessions_is_insufficient():
    for result in compute_metrics([], TODAY):
        assert result.status == "insufficient"
        assert result.current is None
