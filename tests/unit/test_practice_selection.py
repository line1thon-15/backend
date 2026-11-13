"""출제·변형 선택 domain 순수 함수 (T-15 — F-14 ②, F-12, F-08, DECISIONS #102·#111, Architecture "연습 출제 규칙").

- 학년 제한: `min_grade`가 있으면 그 학년 이상인 아이에게만 후보(고수익 알바 = H1 → 고등학생만).
- 변형 값: 시나리오 `variation_axes` 안에서 platform·tone·context를 시드 난수로 고른다.
- F-12: 같은 시나리오 직전 세션과 platform 또는 tone이 1개 이상 다르다.
- F-08: favorite_apps에 맞는 플랫폼을 우선한다.
"""

import random

import pytest

from app.domain.practice_selection import (
    AxisPair,
    ScenarioCandidate,
    choose_variant_axes,
    draw_scenario,
    is_grade_eligible,
)


def candidate(scenario_id="s1", min_grade=None, platforms=("p1", "p2"), tones=("t1", "t2"), contexts=("c1", "c2")):
    return ScenarioCandidate(
        scenario_id=scenario_id,
        min_grade=min_grade,
        platforms=tuple(platforms),
        tones=tuple(tones),
        contexts=tuple(contexts),
    )


# ---- 학년 제한 (F-14 ②) --------------------------------------------------------


@pytest.mark.parametrize(
    ("grade", "expected"),
    [("E6", False), ("M3", False), ("H1", True), ("H3", True)],
)
def test_high_school_only_scenario(grade, expected):
    assert is_grade_eligible(grade=grade, min_grade="H1") is expected


@pytest.mark.parametrize("grade", ["E6", "M1", "H3"])
def test_scenario_without_min_grade_is_open_to_all(grade):
    assert is_grade_eligible(grade=grade, min_grade=None) is True


@pytest.mark.parametrize(("grade", "min_grade"), [("E5", None), ("H1", "X9"), ("", "H1")])
def test_unknown_grade_is_rejected(grade, min_grade):
    with pytest.raises(ValueError):
        is_grade_eligible(grade=grade, min_grade=min_grade)


def test_draw_returns_none_when_no_candidate_is_eligible():
    candidates = [candidate("high_job", min_grade="H1")]

    assert draw_scenario(candidates, grade="M3", previous={}, preferred_platforms=frozenset(), rng=random.Random(0)) is None


def test_draw_returns_none_for_empty_candidates():
    assert draw_scenario([], grade="H1", previous={}, preferred_platforms=frozenset(), rng=random.Random(0)) is None


def test_draw_picks_only_eligible_scenarios():
    candidates = [candidate("high_job", min_grade="H1"), candidate("open", min_grade=None)]

    picked = {
        draw_scenario(candidates, grade="E6", previous={}, preferred_platforms=frozenset(), rng=random.Random(seed)).scenario_id
        for seed in range(30)
    }

    assert picked == {"open"}


def test_high_school_child_can_draw_high_school_scenario():
    candidates = [candidate("high_job", min_grade="H1")]

    draw = draw_scenario(candidates, grade="H1", previous={}, preferred_platforms=frozenset(), rng=random.Random(0))

    assert draw is not None
    assert draw.scenario_id == "high_job"


# ---- 변형 값 (F-12·F-08) -----------------------------------------------------------


def test_axes_are_chosen_inside_variation_axes():
    cand = candidate(platforms=("p1", "p2"), tones=("t1",), contexts=("c1", "c2", "c3"))

    for seed in range(20):
        axes = choose_variant_axes(cand, previous=None, preferred_platforms=frozenset(), rng=random.Random(seed))
        assert axes.platform in cand.platforms
        assert axes.tone in cand.tones
        assert axes.context in cand.contexts


@pytest.mark.parametrize("seed", range(40))
def test_axes_differ_from_previous_in_platform_or_tone(seed):
    cand = candidate(platforms=("p1", "p2"), tones=("t1", "t2"))
    previous = AxisPair(platform="p1", tone="t1")

    axes = choose_variant_axes(cand, previous=previous, preferred_platforms=frozenset(), rng=random.Random(seed))

    assert (axes.platform, axes.tone) != ("p1", "t1")


def test_only_one_combination_left_is_chosen():
    cand = candidate(platforms=("p1",), tones=("t1", "t2"))

    axes = choose_variant_axes(
        cand, previous=AxisPair(platform="p1", tone="t1"), preferred_platforms=frozenset(), rng=random.Random(3)
    )

    assert (axes.platform, axes.tone) == ("p1", "t2")


def test_no_combination_left_returns_none():
    cand = candidate(platforms=("p1",), tones=("t1",))

    axes = choose_variant_axes(
        cand, previous=AxisPair(platform="p1", tone="t1"), preferred_platforms=frozenset(), rng=random.Random(0)
    )

    assert axes is None


def test_previous_outside_axes_does_not_block():
    # fallback(원본 시나리오) 값이 축 목록에 없는 플랫폼이어도 모든 조합이 '다름'
    cand = candidate(platforms=("p1",), tones=("t1",))

    axes = choose_variant_axes(
        cand, previous=AxisPair(platform="original", tone="t1"), preferred_platforms=frozenset(), rng=random.Random(0)
    )

    assert (axes.platform, axes.tone) == ("p1", "t1")


@pytest.mark.parametrize("seed", range(30))
def test_preferred_platform_is_used_when_available(seed):
    cand = candidate(platforms=("p1", "p2", "p3"), tones=("t1", "t2"))

    axes = choose_variant_axes(cand, previous=None, preferred_platforms=frozenset({"p3"}), rng=random.Random(seed))

    assert axes.platform == "p3"


def test_preferred_platform_yields_to_f12_difference():
    # 선호 플랫폼 조합이 모두 직전과 같으면 F-12를 우선해 다른 플랫폼을 쓴다
    cand = candidate(platforms=("p1", "p2"), tones=("t1",))

    axes = choose_variant_axes(
        cand, previous=AxisPair(platform="p1", tone="t1"), preferred_platforms=frozenset({"p1"}), rng=random.Random(0)
    )

    assert axes.platform == "p2"


def test_same_seed_gives_same_draw():
    candidates = [candidate("a"), candidate("b"), candidate("c")]

    first = draw_scenario(candidates, grade="H1", previous={}, preferred_platforms=frozenset(), rng=random.Random(7))
    second = draw_scenario(candidates, grade="H1", previous={}, preferred_platforms=frozenset(), rng=random.Random(7))

    assert first == second


def test_draw_skips_scenario_without_different_combination():
    candidates = [candidate("stuck", platforms=("p1",), tones=("t1",)), candidate("free")]
    previous = {"stuck": AxisPair(platform="p1", tone="t1")}

    picked = {
        draw_scenario(candidates, grade="H1", previous=previous, preferred_platforms=frozenset(), rng=random.Random(seed)).scenario_id
        for seed in range(30)
    }

    assert picked == {"free"}


def test_draw_uses_previous_of_same_scenario():
    candidates = [candidate("a", platforms=("p1", "p2"), tones=("t1",))]
    previous = {"a": AxisPair(platform="p1", tone="t1"), "other": AxisPair(platform="p2", tone="t1")}

    draw = draw_scenario(candidates, grade="H1", previous=previous, preferred_platforms=frozenset(), rng=random.Random(0))

    assert draw.axes.platform == "p2"
