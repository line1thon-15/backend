"""세션 힌트 단계 저장 (T-36 — F-18 ②) 통합 테스트.

목표 단서별 힌트 단계(`hint_levels` — max(0, HINT_MAX − 연속 found), HINT_MAX 잠정 2)를 세션 값 하나로 합칠 때
**가장 큰 값**을 저장한다. 사용자 결정(2026-11-14, 메인 세션 전달 원문) — 질문: "T-36: 힌트 단계는 목표 단서마다
계산되는데(연속으로 찾을수록 힌트가 줄어듦), DB와 AI 요청에는 연습 세션당 값 하나만 들어갈 수 있어요. 한 상황에
목표 단서가 여러 개일 때 어떻게 합칠까요? (1차 화면에는 힌트가 안 나오고 저장만 돼요)" / 답: "가장 큰 값 (추천)".

- 출제 시점(세션 생성)에 종료 세션 기록으로 계산해 `practice_sessions.hint_level`에 저장한다. 다시 도전도 같은 규칙.
- 1차 AI 계약에 hint_level이 없어(#104 ④) AI 요청에는 보내지 않는다.
- 멈춘 세션 기록은 계산에 들어가지 않는다(리포지토리가 종료 세션만 넘김).
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.hint_level import HINT_MAX
from tests.integration.test_practice_sessions import SCENARIO_CLUES, choice_id_of
from tests.integration.test_practice_weak_priority import SCAM, env, unique_cue  # noqa: F401 — fixture 재사용

ALL_SCAM_CUES = sorted({c for sid in SCAM for c in SCENARIO_CLUES[sid]})


def found_everywhere(env, child_id, times: int, **kwargs) -> None:
    for _ in range(times):
        env.past_session(child_id, {cue: "found" for cue in ALL_SCAM_CUES}, **kwargs)


def stored_hint(env, view) -> int | None:
    return env.session_row(view["session_id"]).hint_level


# ---- 정상 ------------------------------------------------------------------------


def test_new_child_session_has_full_hint(env):
    env.login_child()
    assert stored_hint(env, env.started()) == HINT_MAX


def test_all_target_cues_found_once_lowers_hint_by_one(env):
    child_id = env.login_child()
    found_everywhere(env, child_id, 1)
    assert stored_hint(env, env.started()) == HINT_MAX - 1


# ---- 경계 ------------------------------------------------------------------------


def test_all_target_cues_found_hint_max_times_is_zero(env):
    child_id = env.login_child()
    found_everywhere(env, child_id, HINT_MAX + 1)
    assert stored_hint(env, env.started()) == 0


def test_largest_cue_level_wins_when_one_cue_still_needs_help(env):
    # 다른 단서는 모두 0이어도 놓친 단서 하나가 있으면 그 단서의 단계(HINT_MAX)를 저장 — "가장 큰 값"
    # (그 단서를 2번 놓쳐 약점 우선으로 그 시나리오가 확정적으로 출제된다)
    target = SCAM[0]
    cue = unique_cue(target)
    child_id = env.login_child()
    found_everywhere(env, child_id, HINT_MAX)
    env.past_session(child_id, {cue: "missed"})
    env.past_session(child_id, {cue: "missed"})
    view = env.started()
    row = env.session_row(view["session_id"])
    assert row.scenario_id == target
    assert row.hint_level == HINT_MAX


def test_shared_cue_missed_gives_full_hint_for_any_scenario(env):
    # 두 scam 시나리오 공통 단서를 마지막에 놓치면 어느 시나리오가 나와도 HINT_MAX
    shared = sorted(set(SCENARIO_CLUES[SCAM[0]]) & set(SCENARIO_CLUES[SCAM[1]]))
    assert shared
    child_id = env.login_child()
    found_everywhere(env, child_id, HINT_MAX)
    env.past_session(child_id, {shared[0]: "missed"})
    assert stored_hint(env, env.started()) == HINT_MAX


# ---- 예외(집계 제외)·다시 도전 -------------------------------------------------------


def test_finds_in_stopped_sessions_do_not_lower_hint(env):
    child_id = env.login_child()
    found_everywhere(env, child_id, HINT_MAX, status="stopped")
    assert stored_hint(env, env.started()) == HINT_MAX


def test_retry_session_recomputes_hint_with_same_rule(env):
    child_id = env.login_child()
    first = env.started()
    assert stored_hint(env, first) == HINT_MAX
    ended = env.answer(first["session_id"], choice_id_of(first, "correct", env))
    assert ended.status_code == 200, ended.text
    # 끝난 세션보다 뒤 시각에 모든 단서를 HINT_MAX번 찾은 기록 → 다시 도전 시점엔 0
    later = datetime.now(timezone.utc) + timedelta(days=1)
    for day in range(HINT_MAX):
        found_everywhere(env, child_id, 1, ended_at=later + timedelta(days=day))
    retry = env.client.post(
        "/api/v1/practice/sessions", json={"mode": "retry", "retry_of": first["session_id"]}
    )
    assert retry.status_code == 201, retry.text
    assert stored_hint(env, retry.json()) == 0


def test_hint_level_is_not_sent_to_ai(env):
    env.login_child()
    env.started()
    for name in ("variant", "start"):
        for request in env.ai.requests(name):
            assert "hint_level" not in request.model_dump()
