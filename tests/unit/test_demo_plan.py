"""시연 예시 기록 계획 (T-67 — F-28 ②③, F-29 ④⑤⑥, F-41 ②④, F-47 ⑤, N-11).

계획(`build_demo_plan`)은 시각을 인자로 받는 순수 함수다 — 날짜는 적재 시점 기준 상대값(Tasks T-67 "고정 날짜로 넣으면
7일 창을 벗어날 수 있음"). 콘텐츠 ID는 AI 콘텐츠 사본(T-87)의 실제 값만 쓴다.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.ai_client.ports import Variant
from app.content.loader import AREA_IDS, load_content
from app.demo.plan import build_demo_plan
from app.domain.service_time import service_date

CONTENT = load_content()
NOW = datetime(2026, 11, 13, 3, 0, tzinfo=timezone.utc)  # 한국 시간 2026-11-13 12:00


def test_plan_uses_only_real_content_ids_and_found_missed_outcomes():
    plan = build_demo_plan(NOW, CONTENT)

    assert len(plan.sessions) == 8
    for session in plan.sessions:
        entry = CONTENT.scenarios[session.scenario_id]  # 없는 ID면 KeyError
        scenario_clues = [clue.id for clue in entry.scenario.clues]
        assert session.area == entry.area
        assert session.area in AREA_IDS
        assert list(session.target_cue_ids) == scenario_clues
        assert session.cue_outcomes, session.scenario_id
        for cue_id, outcome in session.cue_outcomes:
            assert cue_id in scenario_clues
            assert cue_id in CONTENT.clues
            assert outcome in ("found", "missed")  # not_shown 행 없음 (DECISIONS #109)
        assert session.first_choice_kind in ("correct", "doubtful", "other")
        assert session.mode == "area"
        assert session.is_normal is False


def test_plan_turn_and_variant_follow_decisions_98_shape():
    plan = build_demo_plan(NOW, CONTENT)

    for session in plan.sessions:
        variant = Variant.model_validate(session.variant)  # 다시 도전·변형 선택이 읽어도 깨지지 않음
        assert variant.base_scenario_id == session.scenario_id
        kinds = [choice["kind"] for choice in session.turn_choices]
        assert sorted(kinds) == ["correct", "doubtful", "other"]
        assert set(session.turn_choices[0]) == {"id", "text", "kind"}
        chosen = [c for c in session.turn_choices if c["id"] == session.chosen_choice_id]
        assert [c["kind"] for c in chosen] == [session.first_choice_kind]
        assert session.target_clue_id in session.target_cue_ids
        assert set(session.revealed_clue_ids) <= set(session.target_cue_ids)


def test_plan_notices_have_only_time_level_area():
    plan = build_demo_plan(NOW, CONTENT)

    assert len(plan.notices) == 2
    for notice in plan.notices:
        assert notice.level in ("red", "yellow")
        assert notice.area in AREA_IDS
        assert notice.occurred_at <= NOW
    assert {n.level for n in plan.notices} == {"red", "yellow"}


def test_plan_dates_are_relative_to_now():
    """경계: 하루 뒤에 만든 계획은 모든 시각이 정확히 하루 뒤 — 고정 날짜가 아님."""
    first = build_demo_plan(NOW, CONTENT)
    later = build_demo_plan(NOW + timedelta(days=1), CONTENT)

    assert [s.ended_at + timedelta(days=1) for s in first.sessions] == [s.ended_at for s in later.sessions]
    assert [n.occurred_at + timedelta(days=1) for n in first.notices] == [n.occurred_at for n in later.notices]


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 11, 12, 15, 0, 30, tzinfo=timezone.utc),  # 한국 시간 11-13 00:00:30 (자정 직후)
        datetime(2026, 11, 13, 14, 59, 59, tzinfo=timezone.utc),  # 한국 시간 11-13 23:59:59 (자정 직전)
    ],
)
def test_plan_never_puts_times_after_now_and_keeps_today_session(now):
    """경계: 자정 근처에도 미래 시각이 없고, 오늘(한국 시간) 종료 세션이 있다(연속 기록이 오늘부터)."""
    plan = build_demo_plan(now, CONTENT)

    for session in plan.sessions:
        assert session.started_at < session.ended_at <= now
    assert service_date(max(s.ended_at for s in plan.sessions)) == service_date(now)


def test_plan_rejects_naive_now():
    with pytest.raises(ValueError):
        build_demo_plan(datetime(2026, 11, 13, 12, 0), CONTENT)


def test_plan_rejects_content_without_demo_scenarios():
    """예외: 콘텐츠에 계획이 쓰는 시나리오가 없으면 지어내지 않고 실패한다."""
    from dataclasses import replace

    empty = replace(CONTENT, scenarios={})

    with pytest.raises(ValueError, match="scam_dm_parttime_01"):
        build_demo_plan(NOW, empty)
