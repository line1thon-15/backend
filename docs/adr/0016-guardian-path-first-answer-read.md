# ADR-0016: 성장 지표 "AI보다 먼저"의 원천 — 보호자 경로의 `practice_turns` 읽기에 좁은 예외를 둔다

> 상태: 제안 (방향은 사용자 결정 — 아래 맥락. 예외의 경계·강제 수단은 2026-11-11 사용자 확정 — 끝의 "덧붙임", DECISIONS #93. 태그 이름은 ADR-0017에 따라 `kind`로 읽는다. Architecture.md 머리글 상태 "승인"은 그대로, 바뀐 부분만 확인). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-11

## 맥락

- PRD F-29 ⑤ (다)(인용, 2026-11-11 PRD OQ 12 해소): "AI보다 먼저 판단한 비율 = 첫 답(첫 대사에 대한 답 — F-11 ⑤의 1번째 답)에서 '의심' 선택지를 고른 세션 수 ÷ 세션 수. 1차 기록 근거는 연습의 첫 답이다". 사용자 답 원문 "추천 정의 묶음 (추천)", 선택지 설명 원문 "③ AI보다 먼저 = 첫 답에서 의심 선택지를 고른 세션 비율(결과 피드백 전 판단)".
- 첫 답의 선택은 `practice_turns`(`turn_index` 0 행의 `chosen_choice_id`와 `choices[].judgment`)에만 있다. 기존 규칙(Architecture.md 엔티티 표 `practice_turns` 행): "**보호자용 API는 이 테이블을 읽지 않는다** (F-30 ③)". G3 응답에는 지표가 들어간다(`GuardianReport.metrics`, F-31) — 그대로면 G3가 지표 (다)를 계산할 수 없다(planner 발견, PRD 결정 기록 (2026-11-11 성장 지표·배지·판정·안전 알림) 절 "현재 설계와의 차이").
- 메인 세션이 사용자에게 제시한 두 방법(원문): "방법 1: 이 규칙에 예외를 둡니다." / "방법 2: 세션 테이블에 '첫 답이 의심이었는지' 값을 따로 저장합니다(추정: 이쪽이 더 안전합니다)."
- 사용자 답변 원문(2026-11-11, 메인 세션 전달): "9건 확정, 진행하고, 방법 1로 가는 방향으로 가보자"
- PRD 제약(인용): F-30 ② "실제 메시지 원문(마스킹된 추출 텍스트 포함)·업로드 이미지·감정 상태는 G3와 보호자용 API 응답 어디에도 나오지 않는다", F-30 ③ "연습 대화 전문은 보이지 않는다." — 둘 다 **응답에 나오는 것**을 금지한다. 서버가 집계 목적으로 행을 읽는 것은 금지하지 않는다. 따라서 방법 1은 PRD와 충돌하지 않는다(architect 판단 — 반박 사유 없음). 기존 규칙은 이 PRD 요구를 지키기 위해 설계가 더 강하게 둔 장치였다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| 방법 1. 규칙에 예외 1개 — 지표 계산용 리포지토리 메서드 하나만 `turn_index` 0 행에서 고른 선택지의 `judgment` 범주값을 꺼낸다 (**사용자 선택**) | 스키마·마이그레이션 변경 없음. 원천이 하나(`practice_turns`)라 세션 쪽 파생 값과 어긋날 일이 없음. 기존 행·예시 데이터에도 그대로 적용 | 보호자 요청 처리 중 서버 메모리에 대화 행(선택지 문장 포함 JSON)이 올라온다 — 응답 누출은 아니지만 "읽지 않는다"는 구조적 보장이 "읽되 범주값만 내보낸다"는 코드·테스트 보장으로 약해진다. 그래서 아래 강제 수단 4개가 필요 |
| 방법 2. `practice_sessions`에 `first_answer_suspicious: bool \| null` 열을 두고 A17 첫 답 처리 때 저장 | 보호자 경로가 `practice_turns`를 계속 읽지 않음 — 기존 구조적 보장 유지 | 열 추가 + Alembic 마이그레이션 + A17 저장 로직 + 예시 데이터에 값 추가. 같은 사실이 두 곳에 있어(턴 행과 세션 열) 어긋날 수 있음 |

## 결정

- **방법 1** — 사용자 답변 "방법 1로 가는 방향으로 가보자"에 따른다.
- 예외의 경계(이 밖은 기존 규칙 그대로 — 보호자 경로는 `practice_turns`를 읽지 않는다):
  1. `practice_turns`를 보호자 경로에서 읽는 코드는 리포지토리 메서드 **하나** `PracticeRepo.first_answer_judgments(child_id, ended_from, ended_to)`(이름은 권고)뿐이다. 이 메서드는 아이용 성장(A19)과 보호자 리포트(A11)의 지표 계산이 같이 쓴다.
  2. 조회는 `turn_index = 0` 행만, 열은 `session_id`·`chosen_choice_id`·`choices`만 SELECT 한다 — `ai_line`은 SELECT 하지 않는다. `choices`는 JSON 한 열이라 고른 선택지의 `judgment`만 DB에서 이식성 있게 꺼낼 수 없으므로(SQLite·Postgres JSON 경로 문법이 다름 — ADR-0005·D-2 공통 타입 원칙) 리포지토리 안에서 파싱하고 즉시 버린다.
  3. 반환 타입은 `FirstAnswerJudgment{session_id: UUID, judgment: ChoiceJudgment}` 목록뿐이다 — 문자열 내용 필드(대사·선택지 문장·선택지 ID) 없음. services·domain은 이 범주값만 받는다.
  4. 보호자 응답(`GuardianReport`)과 요약 입력(`LearningSummaryInput`)에 나가는 것은 지표 (다)의 비율 값(`current`·`previous`·`trend[].value`)뿐이다. 대사·선택지 문장·`chosen_choice_id`·`judgment` 0건.
- 강제·회귀 검사(Architecture "테스트 전략"에 반영):
  - R1 반환 타입: `FirstAnswerJudgment`의 필드 집합이 정확히 `{session_id, judgment}`임을 단위 테스트로 단언.
  - R2 읽는 열: 리포지토리 통합 테스트에서 SQLAlchemy `before_cursor_execute` 이벤트로 이 메서드가 실행한 SQL을 수집해 `ai_line`이 0건임을 단언.
  - R3 값 기반 누출: 예시 세션의 `turn_index` 0 `ai_line`·선택지 `text`에 고유 표지 문자열을 넣고 A11 응답 본문 전체와 Fake `SummaryAI`가 받은 `LearningSummaryInput` 직렬화 문자열에 표지 0건을 단언. 기존 보호자 응답 금지 키 검사에 `chosen_choice_id`·`judgment`·`choices`를 추가.
  - R4 호출 경계: `tests/unit/test_import_boundaries.py`에 AST 검사 추가 — `app/services/`의 리포트·성장 모듈이 호출하는 `PracticeRepo` 메서드 중 `practice_turns`를 읽는 것은 `first_answer_judgments`뿐(허용 목록).

## 결과 (트레이드오프 포함)

- 얻는 것: 스키마 무변경으로 G3에 지표 (다)를 보인다(F-31). 원천 단일.
- 감수하는 것:
  - 보호자 요청 처리 중 선택지 문장이 리포지토리 메모리에 잠시 올라온다 — 메서드 안에서만 존재하고 반환·로그되지 않는다(로그 금지 규칙은 Architecture "보안·개인정보" 로그 행 그대로). 구조가 아니라 R1~R4 테스트가 보장한다. 메인 세션이 제시한 추정 "방법 2가 더 안전합니다"는 이 차이를 가리킨다.
  - 예시 데이터(T-67)는 지표 (다)를 보이려면 `practice_turns`의 `turn_index` 0 행(고른 선택지와 그 `judgment`)도 넣어야 한다.
  - 종료된 세션에 `turn_index` 0의 고른 선택지가 없으면(데이터 오류 — A17은 첫 답을 저장하지 않고는 세션을 끝내지 않는다) domain이 예외를 던져 500 `INTERNAL` — 임의로 세지 않는다. 예시 데이터 적재 테스트가 이 불변식을 확인한다.
- 되돌리기: 방법 2로 바꾸려면 새 ADR로 대체한다. 그때도 지표 계산 domain 함수의 입력(세션별 첫 답 `judgment`)은 같아 domain은 바뀌지 않는다.

## 덧붙임 (2026-11-11 — 사용자 확정, 태그 이름 대응)

- **사용자 확정**: 메인 세션 질문 원문 "#87·#89·#92만 먼저 확정하고, 나머지는 AI 계약에 맞춰 architect에게 다시 맡길까요?" → 사용자 답변 원문 "그렇게 해"(2026-11-11, 메인 세션 전달). 질문 직전 메인 세션이 보인 대조 원문: "#87 첫 답 예외 읽기 | 확정 가능 | 우리 `judgment`(suspicious)가 AI의 `kind`(correct)로 이름만 바뀝니다". 이 ADR의 결정(방법 1, 예외 경계 1~4, 강제 R1~R4)은 DECISIONS #87 그대로 확정된다(DECISIONS #93).
- **태그 이름 대응(결정 내용 변경 없음)** — [ADR-0017](0017-ai-contract-alignment.md)로 선택지 태그가 AI 계약 이름으로 바뀐다: `ChoiceJudgment`(`suspicious`/`trusting`/`neutral`) → `ChoiceKind`(`correct`/`other`/`doubtful`), `choices[].judgment` → `choices[].kind`. 이 ADR 본문의 이름은 다음과 같이 읽는다:
  - `FirstAnswerJudgment{session_id, judgment}` → `FirstAnswerKind{session_id, kind: ChoiceKind}`(이름 권고). R1의 필드 집합은 `{session_id, kind}`.
  - 지표 (다)의 분자 조건 "`judgment = suspicious`" → "`kind = correct`".
  - R3의 보호자 응답 금지 키에 `kind`·`target_clue_id`·`revealed_clue_ids`를 더한다(`practice_turns`의 새 열 — Architecture 엔티티 표).
  - 조회 열: `session_id`·`chosen_choice_id`·`choices`(R2의 "`ai_line` 0건"은 그대로).
- 이 ADR 상태는 "제안" 그대로다 — 상태 "승인" 전환은 사용자만 한다(architect 역할 원본). 확정 사실은 위 기록과 DECISIONS #93에 남긴다.
