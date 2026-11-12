"""결과 카드 `level` 결정 — domain 순수 함수 (T-16, Architecture "`feedback` 응답 → PracticeResultView 매핑" ③, #101).

키 K1~K5: K1 위험+found / K2 위험+missed / K3 위험+단서 없는 카드(closing_line) / K4 정상+trusted_correctly /
K5 정상+over_warned. 키→SignalLevel 값은 PRD OQ 63·24 미정 — 테스트가 값을 주입한다(값을 확정하지 않음).
표에 없는 조합은 `CardLevelUndefined`(서비스가 500 INTERNAL로).
"""

import pytest

from app.domain.practice_result import (
    CARD_LEVEL_BY_KEY,
    CardLevelUndefined,
    card_level,
    card_level_key,
    has_retry_axes,
)

# 테스트 주입 값 — 확정 값이 아니다 (PRD OQ 63·24)
INJECTED = {"K1": "green", "K2": "red", "K3": "yellow", "K4": "green", "K5": "yellow"}


@pytest.mark.parametrize(
    ("is_normal", "card_result", "normal_outcome", "key"),
    [
        (False, "found", None, "K1"),
        (False, "missed", None, "K2"),
        (False, None, None, "K3"),
        (True, None, "trusted_correctly", "K4"),
        (True, None, "over_warned", "K5"),
    ],
)
def test_card_level_key_table(is_normal, card_result, normal_outcome, key):
    assert card_level_key(is_normal=is_normal, card_result=card_result, normal_outcome=normal_outcome) == key


@pytest.mark.parametrize(
    ("is_normal", "card_result", "normal_outcome"),
    [
        (True, None, None),  # 정상 상황인데 normal_outcome null — 불허 (#91)
        (True, "found", "trusted_correctly"),  # 정상 상황 카드는 단서가 없다
        (True, "missed", "over_warned"),
        (False, "found", "trusted_correctly"),  # 위험 상황에는 normal_outcome이 없다
        (False, None, "over_warned"),
        (False, "not_shown", None),  # 드러나지 않은 단서는 카드가 아니다 (N1)
    ],
)
def test_card_level_key_outside_table_raises(is_normal, card_result, normal_outcome):
    with pytest.raises(CardLevelUndefined):
        card_level_key(is_normal=is_normal, card_result=card_result, normal_outcome=normal_outcome)


@pytest.mark.parametrize("key", ["K1", "K2", "K3", "K4", "K5"])
def test_card_level_uses_injected_mapping(key):
    assert card_level(key, INJECTED) == INJECTED[key]


def test_card_level_follows_a_different_injection():
    other = {key: "red" for key in INJECTED}
    assert [card_level(key, other) for key in INJECTED] == ["red"] * 5


def test_card_level_missing_key_raises():
    with pytest.raises(CardLevelUndefined):
        card_level("K3", {"K1": "green"})


@pytest.mark.parametrize("value", ["blue", "", "RED", None])
def test_card_level_rejects_non_signal_level_value(value):
    with pytest.raises(CardLevelUndefined):
        card_level("K1", {"K1": value})


def test_default_mapping_is_empty_until_oq63():
    # 값을 지어내지 않는다 — PRD OQ 63·24 답 전까지 설정 상수는 비어 있다
    assert dict(CARD_LEVEL_BY_KEY) == {}
    with pytest.raises(CardLevelUndefined):
        card_level("K1", CARD_LEVEL_BY_KEY)


# ---- 다시 도전 가능 여부 (F-12: 직전과 platform 또는 tone이 1개 이상 다른 조합이 남았는가) -------


def test_has_retry_axes_when_another_pair_exists():
    assert has_retry_axes(platforms=("a", "b"), tones=("t",), contexts=("c",), current=("a", "t")) is True


def test_has_retry_axes_false_when_only_current_pair():
    assert has_retry_axes(platforms=("a",), tones=("t",), contexts=("c1", "c2"), current=("a", "t")) is False


def test_has_retry_axes_false_without_contexts():
    assert has_retry_axes(platforms=("a", "b"), tones=("t",), contexts=(), current=("a", "t")) is False
