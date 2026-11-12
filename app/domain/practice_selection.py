"""출제·변형 선택 — 백엔드 domain 순수 함수 (F-14 ②, F-12, F-08, DECISIONS #102·#111, ADR-0009).

- 학년 제한: 시나리오 `min_grade`가 있으면 그 학년 이상인 아이에게만 후보로 둔다.
- 변형 값: 시나리오 `variation_axes` 안에서 platform·tone·context를 주입 난수로 고른다.
- F-12: 같은 시나리오 직전 세션과 platform 또는 tone이 1개 이상 다르다(context만 다른 것은 세지 않음).
- F-08: 선호 플랫폼(favorite_apps의 앱 유형에 맞는 것)을 우선하되 F-12가 먼저다.
약점 우선(F-18)·정상 상황 비율(F-17)·시작 난이도(F-07)는 이 작업 범위 밖(1차 꺼짐·OQ 14).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from random import Random

GRADE_ORDER: tuple[str, ...] = ("E6", "M1", "M2", "M3", "H1", "H2", "H3")


@dataclass(frozen=True)
class ScenarioCandidate:
    scenario_id: str
    min_grade: str | None
    platforms: tuple[str, ...]
    tones: tuple[str, ...]
    contexts: tuple[str, ...]


@dataclass(frozen=True)
class AxisPair:
    platform: str
    tone: str


@dataclass(frozen=True)
class VariantAxes:
    platform: str
    tone: str
    context: str


@dataclass(frozen=True)
class Draw:
    scenario_id: str
    axes: VariantAxes


def _grade_rank(grade: str) -> int:
    try:
        return GRADE_ORDER.index(grade)
    except ValueError:
        raise ValueError(f"unknown grade: {grade!r}") from None


def is_grade_eligible(*, grade: str, min_grade: str | None) -> bool:
    rank = _grade_rank(grade)
    if min_grade is None:
        return True
    return rank >= _grade_rank(min_grade)


def choose_variant_axes(
    candidate: ScenarioCandidate,
    *,
    previous: AxisPair | None,
    preferred_platforms: frozenset[str],
    rng: Random,
) -> VariantAxes | None:
    combos = [(p, t) for p in candidate.platforms for t in candidate.tones]
    if previous is not None:
        combos = [(p, t) for p, t in combos if p != previous.platform or t != previous.tone]
    if not combos or not candidate.contexts:
        return None
    preferred = [(p, t) for p, t in combos if p in preferred_platforms]
    platform, tone = rng.choice(preferred or combos)
    return VariantAxes(platform=platform, tone=tone, context=rng.choice(candidate.contexts))


def draw_scenario(
    candidates: Sequence[ScenarioCandidate],
    *,
    grade: str,
    previous: Mapping[str, AxisPair],
    preferred_platforms: frozenset[str],
    rng: Random,
) -> Draw | None:
    eligible = [c for c in candidates if is_grade_eligible(grade=grade, min_grade=c.min_grade)]
    rng.shuffle(eligible)
    for candidate in eligible:
        axes = choose_variant_axes(
            candidate,
            previous=previous.get(candidate.scenario_id),
            preferred_platforms=preferred_platforms,
            rng=rng,
        )
        if axes is not None:
            return Draw(scenario_id=candidate.scenario_id, axes=axes)
    return None
