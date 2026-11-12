"""연습 결과 카드 `level`·다시 도전 가능 여부 — 백엔드 domain 순수 함수 (T-16, F-13 ①③, F-12, F-26).

근거: Architecture 내부 API "`feedback` 응답 → PracticeResultView 매핑" 행 ③, DECISIONS #75·#101.
- 키 K1 위험+found / K2 위험+missed / K3 위험+단서 없는 카드(closing_line) / K4 정상+trusted_correctly / K5 정상+over_warned.
- 키→SignalLevel 값은 PRD OQ 63(색 매핑)·OQ 24(노랑 문구)가 미정이라 정하지 않는다 — 설정 상수 1곳
  `CARD_LEVEL_BY_KEY`는 비어 있고, 답 전에는 테스트가 값을 주입한다. 표에 없는 조합·값 없는 키는
  `CardLevelUndefined`(서비스가 500 INTERNAL로 — 임의 색을 보이지 않는다).
"""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

SIGNAL_LEVELS: frozenset[str] = frozenset({"red", "yellow", "green"})

# PRD OQ 63·24 답 전 — 값을 지어내지 않는다
CARD_LEVEL_BY_KEY: Mapping[str, str] = MappingProxyType({})


class CardLevelUndefined(Exception):
    """결과 카드 level을 정할 수 없음 — 표에 없는 조합이거나 키에 값이 없음."""


def card_level_key(*, is_normal: bool, card_result: str | None, normal_outcome: str | None) -> str:
    """card_result: 단서 카드면 found·missed, 단서 없는 카드(closing_line)면 None."""
    if not is_normal:
        if normal_outcome is None:
            if card_result == "found":
                return "K1"
            if card_result == "missed":
                return "K2"
            if card_result is None:
                return "K3"
    elif card_result is None:
        if normal_outcome == "trusted_correctly":
            return "K4"
        if normal_outcome == "over_warned":
            return "K5"
    raise CardLevelUndefined(
        f"no card level key for is_normal={is_normal} card_result={card_result} normal_outcome={normal_outcome}"
    )


def card_level(key: str, mapping: Mapping[str, str]) -> str:
    value = mapping.get(key)
    if value not in SIGNAL_LEVELS:
        raise CardLevelUndefined(f"no signal level configured for {key}")
    return value


def has_retry_axes(
    *,
    platforms: Sequence[str],
    tones: Sequence[str],
    contexts: Sequence[str],
    current: tuple[str, str],
) -> bool:
    """다시 도전 변형이 남았는가 — 이 세션과 platform 또는 tone이 1개 이상 다른 조합 (F-12, #102 VA4).

    출제 쪽 `practice_selection.choose_variant_axes`와 같은 조건(난수 없이 존재 여부만).
    """
    if not contexts:
        return False
    return any((platform, tone) != current for platform in platforms for tone in tones)
