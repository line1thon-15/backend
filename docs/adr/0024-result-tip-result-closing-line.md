# ADR-0024: A18 결과 응답에 단서 한 줄 팁(`tip`)·카드 판정(`result`)·마무리 한마디(`closing_line`) 추가 — 하위 호환 추가만

> 상태: 승인 (2026-11-15 사용자 승인 — 메인 세션 질문 원문 "T-102 결과 API 설계를 확정할까요? (요약: 칩에 tip 필수 추가·A18만 / 카드에 result(found·missed, 마무리 카드는 null) / 최상위 closing_line 추가(마지막 카드와 같은 문장) / tip 없거나 공백이면 서버 시작 실패 / AI 글자 수 상한은 백엔드가 검사 안 함. 기존 필드는 모두 유지)", 사용자 답 원문 "추천안대로 확정 (Recommended)"(선택지 설명 원문 "DECISIONS #143~#149와 ADR-0024를 확정하고 T-102를 바로 시작합니다." — 1A·2A·3A·4A·5A, DECISIONS #143~#145·#147·#148), 메인 세션 지시로 architect가 기입). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-15
> 관련: PRD F-13 ⑦·Open Question 69, Tasks T-102 완료 조건 ①. DECISIONS #101(사용자 확정 #115 — `closing_line` → 마지막 K3 카드, "공개 형태 그대로")에 공개 필드를 **더하는** 결정이다 — #101의 매핑·검증(V1'~V3')·K3 카드는 그대로 두고, ADR-0017(제안) 본문은 수정하지 않는다.

## 맥락

- AI 팀원 메시지 원문(사용자가 붙여 넣음, 메인 세션 축어 전달): "결과 화면을 Figma처럼 짧게 맞추려고 AI 쪽을 고쳤어요. 화면에서 두 가지만 부탁드려요. ① '다음엔 이것도 찾아봐요' 칩 아래 설명은 단서 description(긴 뜻 풀이) 대신 새 필드 tip을 보여 주세요. 예: "쉬운 일에 큰돈을 준다면 의심해 봐요" ② '다음엔 이렇게'에는 피드백 카드 중 result가 "missed"인 카드만 보여 주세요. 찾은 단서는 위 칩으로 충분해요. closing_line(짧은 응원 한 문장)은 상단 '잘했어요!' 아래에 두면 Figma와 비슷해져요."
- 사용자 답 원문 "작업 등록"(메인 세션 질문 원문 "결과 API에 tip·result·closing_line을 추가하는 작업을 등록할까요?"). 화면 표시 방식은 PRD Open Question 69(미답) — 이 ADR은 서버가 값을 담는 형태만 정한다.
- AI 쪽 사실(메인 세션 gh api 확인 — architect 미열람, 인용): ai dev `25a3ef4`(PR #6, 커밋 `86ca9bd`) `content/clues.json` 단서마다 `tip`(ai 저장소 계약 문서 API_CONTRACT.md 원문 "`tip`(28자 이내 한 줄 팁)"), feedback 카드 `text` 45자·`closing_line` 30자·`normal_feedback` 55자 상한, `contracts/practice.feedback.response.json`·`practice.normal.feedback.response.json`은 문구만 변경(필드 구조 동일).
- 백엔드 사실(architect 직접 확인, 작업 트리 = 브랜치 `docs/t102-result-tip`):
  - `app/api/practice.py:90-95` `CueCardView{cue_id, label, sentence}`, `:98-102` `ResultCardView{level, sentence}`, `:105-113` `PracticeResultView` — 모두 `extra="forbid"`.
  - `app/api/me.py:35`·`:65` A19 `GrowthView.needs_practice_cues`는 **별도** `CueCardView` 클래스(같은 이름, 다른 모듈). Architecture 응답 DTO 표는 두 곳 모두 `CueCard` 하나로 적고 있다.
  - `app/services/practice.py:624-626` 공개 `cards` = AI 카드 순서대로 `{level: levels[card.result], sentence: card.text}` + 마지막 `{level: levels[None], sentence: response.closing_line}`. AI 카드 `result`는 `level` 결정에만 쓰이고 공개 응답에서 사라진다.
  - `app/services/practice.py:645-660` `_cue_cards` — `label` = `clues.json` `name`, `sentence` = `description`, docstring "콘텐츠 설명으로만 만든다 — AI 문장을 섞지 않는다 (#101 …)".
  - `app/services/practice_validation.py:144-152` `check_feedback` V1'~V3' — 길이 검사 없음. `:151` V3'가 카드 `result` = 저장된 판정을 보장.
  - `app/content/schemas.py:17-18` AI 사본 모델은 `extra="ignore"`, `:33-38` `AiClue{id, areas, name, description, safe_action}` — `name`·`description`에도 공백·길이 검사 없음.
  - `app/ai_client/ports.py:194-197` `FeedbackResponse{cards, closing_line: str, source}` — `normal_feedback`은 정의하지 않아 버려진다(`_InboundModel`).
  - `tests/contracts/ai/SOURCE.txt:6` 계약 샘플은 ai `contracts/` 24개 중 12개만 복사 — `practice.normal.*`은 범위 밖.

## 검토한 대안

결정 1 — `tip`을 어디에 어떻게 싣나 (DECISIONS #143)

| 대안 | 장점 | 단점 |
|---|---|---|
| 1A. A18 `found`·`missed` 칩에 필수 `tip: str` 추가, `sentence`(= `description`) 유지 (**추천**) | 하위 호환 추가. 콘텐츠 시작 검증으로 값이 항상 있어 프론트가 null 분기를 두지 않는다. OQ 69 답이 "tip으로 바꿈"이든 "그대로"든 서버 변경 없음 | 응답이 조금 길어진다(단서 1개당 28자 안팎 — 인용 상한) |
| 1B. `tip: str \| null`(콘텐츠에 없으면 null) | 콘텐츠에 `tip`이 빠져도 서버가 뜬다 | 프론트에 null 분기가 생기고, 누락이 화면에서야 드러난다. 사본은 고정 커밋이라 실행 중 바뀌지 않음 — 시작 검증이 더 이른 발견 |
| 1C. `sentence` 값을 `tip`으로 교체 | 필드 수 그대로 | 기존 값이 바뀐다 — 하위 호환 깨짐(PRD F-13 ⑦ "기존 응답 값은 그대로 유지"와 충돌), 화면 결정(OQ 69)을 서버가 선점 |
| 1D. 1A + A19 `needs_practice_cues`에도 `tip` 추가 | 두 `CueCard`가 같은 모양 | PRD F-13 ⑦은 A18만 요구 — 요구사항에 없는 확장(architect 금지 사항) |

결정 2 — 카드 판정 `result`와 마무리 카드 (DECISIONS #144)

| 대안 | 장점 | 단점 |
|---|---|---|
| 2A. `ResultCardView.result: "found" \| "missed" \| null` 추가, 마지막 마무리 카드(K3)는 `cards`에 그대로 두고 `result: null` (**추천**) | 하위 호환 — 기존 카드 수·순서·`level`·`sentence` 그대로. AI 팀원 요청 ②의 필터(`result === "missed"`)가 그대로 동작하고 마무리 카드는 자연히 빠진다 | "null = 마무리 카드"라는 약속을 프론트가 알아야 한다 |
| 2B. 마무리 카드를 `cards`에서 빼고 최상위 `closing_line`으로만 | 중복 없음, `result`가 항상 non-null | 기존 `cards` 개수·마지막 카드가 바뀐다 — 하위 호환 깨짐(planner·메인 세션 지적과 같음) |
| 2C. `result` 대신 `kind: "found" \| "missed" \| "closing"`(항상 non-null) | 판별 값이 명시적 | AI 계약·AI 팀원 요청의 이름(`result`, `"missed"`)과 다른 이름을 하나 더 만든다. 내부 API의 `kind`(선택지 태그 — 클라이언트 비노출 원칙, Architecture ChoiceKind 행)와 이름이 겹쳐 혼동 |

결정 3 — 최상위 `closing_line` (DECISIONS #145)

| 대안 | 장점 | 단점 |
|---|---|---|
| 3A. `PracticeResultView.closing_line: str` 추가 — 마지막 카드 `sentence`와 같은 값(중복 제공) (**추천**) | 하위 호환. 프론트가 카드 목록에서 마지막 카드를 찾지 않고 바로 쓴다(OQ 69 ③ 배치에 대응). 값의 원천은 하나(AI 응답 `closing_line`) | 같은 문장이 두 자리에 있다 — 프론트가 둘 다 보이면 중복 표시(Y5 행에 주의 기록) |
| 3B. 최상위 필드 없이 "`result: null` 카드 = 마무리"로만 | 필드 추가 없음 | PRD F-13 ⑦ (다) "마무리 한마디(`closing_line`)가 카드와 별도로 담긴다"를 충족하지 못함 |
| 3C. `closing_line: str \| null` | 정상 상황을 켤 때 AI가 마무리 문장을 안 줄 경우에 대비 | 1차 위험 상황에서는 V2'로 항상 값이 있다 — 쓰이지 않는 null 분기. 정상 상황 응답 규격은 아직 없다(#110) |

결정 4 — 콘텐츠 `tip` 검증 (DECISIONS #147)

| 대안 | 장점 | 단점 |
|---|---|---|
| 4A. `AiClue.tip: str` 필수 + 공백만이면 거부, 길이는 검사하지 않음 — 위반이면 서버 시작 실패(기존 콘텐츠 검증 규칙) (**추천**) | 결정 1A(필수)를 보장. 고정 커밋 사본이라 재고정 때 테스트에서 바로 드러난다(운영 중 발생 없음). 길이 정책은 AI 콘텐츠 소유자 몫 — `name`·`description`도 길이 검사 없음(같은 관례) | AI가 `tip`을 빠뜨린 커밋으로 재고정하면 서버가 뜨지 않는다 — 재고정 작업에서 발견·보고 |
| 4B. 4A + 길이 ≤ 28자 | AI 계약 문서 상한을 백엔드가 이중 확인 | AI가 상한을 바꾸면 백엔드 수정 필요. 화면 맞춤 정책을 백엔드가 강제(N-12의 "AI는 글" 경계와 거리) |
| 4C. 선택(`str \| None`) — 없거나 공백이면 null로 응답 | 콘텐츠 누락에도 서버가 뜬다 | 결정 1B와 같은 단점 |

결정 5 — AI 글자 수 상한(feedback `text` 45·`closing_line` 30·`normal_feedback` 55)을 백엔드 V2'에 넣나 (DECISIONS #148)

| 대안 | 장점 | 단점 |
|---|---|---|
| 5A. 넣지 않는다 — V1'~V3' 그대로 (**추천**) | 길이 초과 문장 하나로 결과 화면 전체가 503(#75 ⑤ "부분 응답 없음")이 되는 일을 막는다 — 시연 위험 회피. AI가 만든 문장의 형태는 AI 몫(N-12) | 상한을 넘는 문장이 오면 화면이 길어진다 — 프론트 표시(줄임·줄바꿈)로 흡수 |
| 5B. 넣는다 — 초과면 V2' 위반 → A18 전체 503 | 계약 위반을 바로 잡는다 | 위 503 위험. 요약(#103 S3)과 달리 feedback은 실패가 화면 전체 오류다 |
| 5C. 초과 시 로그 경고만 | 관찰 가능 | 로그 규칙·테스트가 하나 더 생긴다 — 요구사항 없음 |

## 결정

1A + 2A + 3A + 4A + 5A. 결정적 이유: PRD F-13 ⑦ "기존 응답 값은 그대로 유지한다(하위 호환)"와 Architecture "고정 후 변경 규칙"(하위 호환 추가만 허용)을 지키면서, 화면 표시 방식(OQ 69)이 어느 쪽으로 나도 서버를 다시 바꾸지 않게 한다.

규칙(T-102):

1. A18 `PracticeResultView.found[]`·`missed[]` 항목 = `ResultCueCard{cue_id, label, sentence, tip}` — `tip`은 사본 `clues.json`의 그 단서 `tip` 값 그대로(백엔드가 만들거나 고치지 않음 — N-12). A19 `GrowthView.needs_practice_cues`의 `CueCard{cue_id, label, sentence}`는 바꾸지 않는다.
2. `PracticeResultView.cards[]` 항목 = `{level, sentence, result}` — AI 카드에서 온 카드는 `result` = 그 AI 카드의 `result`(V3'로 저장된 판정과 같음이 보장됨), 마지막 마무리 카드(K3)는 `result: null`. 키는 항상 있다(값만 null). 카드 개수·순서·`level`·`sentence`는 #101 그대로.
3. `PracticeResultView.closing_line: str` = AI `feedback` 응답 `closing_line` 그대로 — 마지막 카드 `sentence`와 같은 값.
4. 콘텐츠: `AiClue.tip: str` 필수, 공백만이면 검증 실패 → 서버 시작 실패. 길이 검사 없음.
5. AI feedback 응답 검증은 V1'~V3' 그대로 — 글자 수 검사를 더하지 않는다. `normal_feedback`은 지금처럼 읽지 않는다(정상 상황 꺼짐 — #110).
6. 실패 처리: `feedback` 실패·검증 실패 → A18 전체 503(#75 ⑤ 그대로) — 새 필드만 비운 부분 응답 없음.
7. 정상 상황(K4·K5): 1차 경로 없음(#110). 켤 때(T-34·T-35, AI G2·G3) 정한다 — 예정: `found`·`missed` [](tip 없음), K4·K5 카드 `result: null`, `closing_line`의 원천은 그때 AI 정상 상황 feedback 규격으로 정함(DECISIONS #146).

## 결과 (트레이드오프 포함)

- 얻는 것: AI 팀원 요청 ①②과 F-13 ⑦에 필요한 값이 모두 응답에 실린다. 기존 필드·값·카드 수 변경 없음 — 이미 연동한 소비자가 깨지지 않는다. 새 AI 호출·새 오류 코드·DB 변경 없음.
- 감수하는 것: ① 마무리 한마디가 `cards` 마지막 카드와 `closing_line` 두 자리에 있다 — 프론트가 둘 다 보이면 같은 문장이 두 번 보인다(OQ 69 ②를 받으면 `result === "missed"` 필터로 마무리 카드는 빠진다). ② `result: null`의 의미("마무리 카드")를 프론트가 알아야 한다. ③ `tip` 누락 커밋으로 재고정하면 서버가 시작하지 않는다(재고정 작업에서 발견). ④ AI 글자 수 상한을 넘는 문장도 그대로 나간다.
- 바뀌지 않는 것: #75 ①(출처 구분 — `CueCard`는 콘텐츠, `cards`는 AI)·③(`level`)·⑤(실패 → 503), #101 매핑·V1'~V3', #120 `CARD_LEVEL_BY_KEY`, A19 `CueCard`.
- 남는 위험: 정상 상황을 켤 때 AI가 마무리 문장을 주지 않는 규격이면 `closing_line: str`을 nullable로 바꾸는 비호환 변경이 필요해질 수 있다(3C를 고르지 않은 대가 — 그때 새 결정).
