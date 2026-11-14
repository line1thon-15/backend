"""약점 우선 출제 domain 규칙 (T-36 — F-18 ①).

근거: Architecture "연습 출제 규칙" 약점 우선 행 — 최근 기록에서 `missed` 횟수가 임계값 이상인 단서를 포함한
시나리오를 우선 후보로. 약점 단서 목록 자체는 공통 규칙 `select_weak_cues`(DECISIONS #122)가 정하고, 이 함수는
그 목록을 받아 후보 순서만 바꾼다. 학년 제한(F-14 ②)·변형 조건(F-12)은 그대로 먼저 적용된다.
"""

import random

from app.domain.practice_selection import AxisPair, ScenarioCandidate, draw_scenario


def candidate(scenario_id, cue_ids=(), min_grade=None, platforms=("p1", "p2"), tones=("t1", "t2")):
    return ScenarioCandidate(
        scenario_id=scenario_id,
        min_grade=min_grade,
        platforms=tuple(platforms),
        tones=tuple(tones),
        contexts=("c1",),
        cue_ids=tuple(cue_ids),
    )


POOL = [candidate(f"s{i}", cue_ids=(f"cue{i}", "shared")) for i in range(1, 7)]


def draw(candidates, weak, seed, *, grade="H1", previous=None):
    return draw_scenario(
        candidates,
        grade=grade,
        previous=previous or {},
        preferred_platforms=frozenset(),
        rng=random.Random(seed),
        weak_cue_ids=frozenset(weak),
    )


# ---- 정상 ------------------------------------------------------------------------


def test_scenario_with_weak_cue_is_drawn_first_for_every_seed():
    for seed in range(50):
        assert draw(POOL, {"cue4"}, seed).scenario_id == "s4"


def test_any_scenario_with_one_of_weak_cues_is_preferred():
    picked = {draw(POOL, {"cue2", "cue5"}, seed).scenario_id for seed in range(50)}
    assert picked == {"s2", "s5"}  # 우선 후보 안에서는 무작위


# ---- 경계 ------------------------------------------------------------------------


def test_no_weak_cues_keeps_previous_draw_order():
    # 약점이 없으면 T-15 출제와 같은 난수 순서(기존 출제 결과가 바뀌지 않음)
    for seed in range(20):
        rng = random.Random(seed)
        eligible = list(POOL)
        rng.shuffle(eligible)
        assert draw(POOL, set(), seed).scenario_id == eligible[0].scenario_id


def test_weak_cue_in_every_scenario_changes_nothing():
    for seed in range(20):
        assert draw(POOL, {"shared"}, seed) == draw(POOL, set(), seed)


def test_weak_cue_not_in_any_candidate_falls_back_to_normal_draw():
    for seed in range(20):
        assert draw(POOL, {"unknown_cue"}, seed) == draw(POOL, set(), seed)


# ---- 예외(우선 후보를 쓸 수 없음) ---------------------------------------------------


def test_grade_restriction_still_applies_before_weak_priority():
    pool = [candidate("adult", cue_ids=("cue1",), min_grade="H1"), candidate("open", cue_ids=("cue2",))]
    for seed in range(20):
        assert draw(pool, {"cue1"}, seed, grade="M1").scenario_id == "open"


def test_weak_scenario_without_new_variant_falls_back_to_others():
    # F-12: 직전과 platform·tone이 모두 같은 조합만 남으면 그 시나리오는 못 낸다 → 다음 후보
    pool = [
        candidate("weak", cue_ids=("cue1",), platforms=("p1",), tones=("t1",)),
        candidate("other", cue_ids=("cue2",)),
    ]
    previous = {"weak": AxisPair(platform="p1", tone="t1")}
    for seed in range(20):
        assert draw(pool, {"cue1"}, seed, previous=previous).scenario_id == "other"


def test_only_weak_scenario_unusable_and_nothing_else_is_none():
    pool = [candidate("weak", cue_ids=("cue1",), platforms=("p1",), tones=("t1",))]
    previous = {"weak": AxisPair(platform="p1", tone="t1")}
    assert draw(pool, {"cue1"}, 0, previous=previous) is None
