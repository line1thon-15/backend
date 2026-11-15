"""보호자 리포트 응답 키 검사 공용 헬퍼 (T-99 ② — PR #32 후속 권고 3 "테스트 헬퍼 의존성 정리").

원래 `test_guardian_report.py`에 있던 금지 키·NoticeView 키 정의와 검사 함수를 옮겼다(동작 변경 없음).
"""

# Architecture "보호자용 응답 금지 필드" + Tasks T-25 행 + 원문·마스킹·이미지·감정 상태의 흔한 키 이름.
# `feedback`·`sentences`(심화 연습 피드백 DeepFeedbackView) 중 `sentences`는 GuardianSummaryView가 쓰므로
# 심화 연습 피드백은 `feedback`·`deep_feedback` 키로 검사한다.
FORBIDDEN_KEYS = frozenset(
    {
        # 메시지 원문·마스킹 텍스트·이미지 (F-30 ②)
        "message_text", "raw_text", "original_text", "masked_text", "extracted_text", "text",
        "image", "image_url", "images", "upload", "uploads",
        # 감정 상태 (F-30 ②, F-25)
        "emotion", "emotion_level", "emotion_score", "emotion_temperature", "temperature", "mood",
        # 연습 대화 문장·고른 선택지·태그 (F-30 ③, DECISIONS #87·#93)
        "ai_line", "choices", "chosen_choice_id", "judgment", "kind", "target_clue_id",
        "revealed_clue_ids", "messages", "history", "reply", "opening_line", "variant",
        # 심화 연습 (F-48 ④)
        "answer_text", "feedback", "deep_feedback",
    }
)


NOTICE_KEYS = {"notice_id", "kind", "occurred_at", "level", "area", "channel"}
# 사용자 답 "금지 범위 좁히기 (추천)" — 설명 원문 "금지 키 'kind'는 알림 목록(notices) 밖에서만 검사해요."
NOTICE_ALLOWED_FORBIDDEN = frozenset({"kind"})


def all_keys(value) -> list[str]:
    if isinstance(value, dict):
        keys = list(value)
        for item in value.values():
            keys.extend(all_keys(item))
        return keys
    if isinstance(value, list):
        return [key for item in value for key in all_keys(item)]
    return []


def forbidden_keys_found(body: dict) -> set[str]:
    """응답 전체의 금지 키. 단 최상위 `notices[]` 항목의 바로 아래 `kind`만 허용."""
    found = set(all_keys({k: v for k, v in body.items() if k != "notices"})) & FORBIDDEN_KEYS
    for notice in body.get("notices", []):
        found |= (set(notice) - NOTICE_ALLOWED_FORBIDDEN) & FORBIDDEN_KEYS
        for value in notice.values():
            found |= set(all_keys(value)) & FORBIDDEN_KEYS
    return found
