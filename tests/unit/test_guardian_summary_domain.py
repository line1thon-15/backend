"""보호자 학습 요약 입력 조립·응답 검증 — domain 순수 함수 (T-76 — F-47 ②③⑥).

근거: Architecture.md:363 `POST /internal/v1/summary` 행(영역마다 1회, 검증 S1~S3), :274 GuardianSummaryView,
A-18(가정 `SUMMARY_MIN_ENDED_SESSIONS` = 1), DECISIONS #103·#114(영역별, found_clues 중복 제거).
미정 값(메인 세션에 질문 중 — 2026-11-14): S3 상한 200자, missed_clues 중복 제거, 단서 순서 = 콘텐츠 순서.
"""

import pytest

from app.domain.guardian_summary import (
    SUMMARY_MAX_CHARS,
    SUMMARY_MIN_ENDED_SESSIONS,
    AreaSummaryInput,
    SummarySession,
    accept_summary,
    summary_inputs,
)

AREAS = ("scam", "identity_lending", "friend_pressure")
CUE_ORDER = ("advance_payment", "urgency", "keep_secret", "lend_identity", "guilt_pressure")


def session(area: str, found=(), missed=()) -> SummarySession:
    return SummarySession(area=area, found=tuple(found), missed=tuple(missed))


# ==== 조립 ==========================================================================


def test_one_input_per_area_with_records_in_area_order():
    sessions = [
        session("friend_pressure", found=["guilt_pressure"]),
        session("scam", found=["urgency"], missed=["advance_payment"]),
        session("scam", found=["urgency", "advance_payment"]),
    ]

    result = summary_inputs(sessions, AREAS, CUE_ORDER)

    assert result == (
        AreaSummaryInput(
            area="scam",
            practice_count=2,
            found_cue_ids=("advance_payment", "urgency"),
            missed_cue_ids=("advance_payment",),
        ),
        AreaSummaryInput(
            area="friend_pressure",
            practice_count=1,
            found_cue_ids=("guilt_pressure",),
            missed_cue_ids=(),
        ),
    )


def test_area_without_records_gets_no_input():
    result = summary_inputs([session("identity_lending", missed=["lend_identity"])], AREAS, CUE_ORDER)

    assert [item.area for item in result] == ["identity_lending"]


def test_found_and_missed_are_deduplicated_and_in_content_order():
    sessions = [
        session("scam", found=["urgency"], missed=["keep_secret", "advance_payment"]),
        session("scam", found=["advance_payment", "urgency"], missed=["keep_secret"]),
    ]

    (item,) = summary_inputs(sessions, AREAS, CUE_ORDER)

    assert item.found_cue_ids == ("advance_payment", "urgency")
    assert item.missed_cue_ids == ("advance_payment", "keep_secret")


def test_session_without_cues_still_counts_as_practice():
    # 정상 상황 세션 등 단서 판정 0개 — 연습 횟수에는 들어간다
    (item,) = summary_inputs([session("scam"), session("scam", found=["urgency"])], AREAS, CUE_ORDER)

    assert item.practice_count == 2
    assert item.found_cue_ids == ("urgency",)
    assert item.missed_cue_ids == ()


def test_cue_missing_from_content_is_dropped():
    (item,) = summary_inputs([session("scam", found=["retired_cue"], missed=["urgency"])], AREAS, CUE_ORDER)

    assert item.found_cue_ids == ()
    assert item.missed_cue_ids == ("urgency",)


def test_no_sessions_is_insufficient():
    assert SUMMARY_MIN_ENDED_SESSIONS == 1  # A-18 가정 기본값
    assert summary_inputs([], AREAS, CUE_ORDER) is None


def test_unknown_area_is_rejected():
    with pytest.raises(ValueError):
        summary_inputs([session("romance")], AREAS, CUE_ORDER)


# ==== 응답 검증 S1~S3 ================================================================


def test_accepts_plain_summary():
    assert accept_summary("사기 연습을 꾸준히 했어요.", ["사기", "3", "돈 요구"]) is True


@pytest.mark.parametrize("text", [None, "", "   \n\t"])
def test_s1_rejects_null_or_blank(text):
    assert accept_summary(text, ["사기"]) is False


def test_s2_accepts_numbers_present_in_input():
    assert accept_summary("사기 연습을 3번 했어요.", ["사기", "3"]) is True


def test_s2_rejects_numbers_not_in_input():
    assert accept_summary("사기 연습을 3번 했고 정답률은 80이에요.", ["사기", "3"]) is False


def test_s3_length_limit_boundary():
    assert SUMMARY_MAX_CHARS == 200
    assert accept_summary("가" * SUMMARY_MAX_CHARS, []) is True
    assert accept_summary("가" * (SUMMARY_MAX_CHARS + 1), []) is False
