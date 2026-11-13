# ADR-0017: 백엔드–AI 내부 API v1을 AI 저장소 1차 구현 계약(`contracts/`)으로 재정렬한다

> 상태: 제안 (방향 "AI 계약에 맞춤"은 사용자 결정 — 아래 맥락. 세부 대응·검증 규칙도 2026-11-11 사용자 확정 — DECISIONS #111~#115·#118·#119, 끝의 "덧붙임"·"덧붙임 2". 상태 "승인" 전환은 사용자. ~~세부 대응·검증 규칙은 architect 설계로 사용자 확인 대상.~~ Architecture.md 머리글 상태 "승인"은 그대로, 바뀐 부분만 확인). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-11
> 대상 코드(인용 — architect가 읽기 전용 사본으로 확인): ai 저장소 커밋 331d2c6, 브랜치 feature/ai(PR·병합 없음). `contracts/*.json`, `app/schemas.py`, `app/server.py`, `app/practice.py`, `app/choices.py`, `app/judge.py`, `app/variation.py`, `app/scenarios.py`, `app/summary.py`, `app/content.py`, `content/clues.json`, `content/scenarios/scam.json`, `.env.example`. `.env`는 열지 않음.

## 맥락

- AI 담당 공지 원문(메인 세션 전달, 축어):
  > ai 저장소에 1차 구현 올렸습니다. 들어 있는 것)P0 AI 기능: T-12 대화, T-13 변형, T-14 판별·피드백, T-75 보호자 요약, 테스트 환경(T-01) 콘텐츠가 없어서 제가 임시로 T-03~05(단서 체계, 사기 시나리오 2개, 안전 테스트 세트)는 제가 초안으로 만들었습니다. 후에 콘텐츠는 더 다듬겠지만 단서 ID와 구조는 이대로 쓸 예정이라 연결에 쓰셔도 돼요. (content/clues.json) 말씀하신 내용 반영) 아이 입력은 선택지 3개(정답·의심되는 답·다른 답). start·turn 응답의 choices로 가고 순서는 섞여 있습니다. kind는 화면에 보여 주지 마세요. 종료는 백엔드에서 판단해 주세요. 단 status: "safe_reply"(아이가 자해·폭력 피해를 말함)이면 바로 멈춰 주세요. 연결할 때 참고) 요청·응답 샘플은 contracts/ 폴더에 있어요. 경로와 필드는 제안안이라, 바꾸고 싶은 부분 있으면 편하게 말씀해 주세요. mvp대로 AI 서버는 상태를 저장하지 않게 만들었습니다. 대화 기록, revealed_clue_ids, variant를 저장해 두셨다가 매번 같이 보내 주셔야 해요. 아이가 고른 선택지는 다음 요청의 아이 메시지에 choice_kind와 clue_id(직전 응답의 target_clue_id)로 넣어 주세요. 그러면 판별이 그 기록으로 바로 돼요. T-13 변형은 POST /internal/v1/practice/variant → 받은 variant를 그대로 저장 → 같은 연습의 start·turn·judge·feedback에 넣어 주시면 돼요.
- 추가 전달 원문: "참고하실 ai파트 코드가 필요하실 것 같아서 우선적으로 1차 구현 올렸습니다. 완성본은 아니고 아직 수정이 필요한데 테스트겸 로컬에서 api를 제 제미나이 키를 넣어서 돌려보다가 Gemini 무료 키 하루 제한을 다 써서 아직은 오늘 대화 기능만 실제 응답을 확인했습니다.  키가 없어도 .env에서 AI_PROVIDER=fake로 하면 고정 응답으로 돌아가서 연결 테스트는 바로 하실 수 있어요."
- 메인 세션 추천 원문: "AI 계약을 대부분 그대로 받아들이고, 아래 두 가지만 의견을 맞추는 방향을 추천합니다. `growth_level` / 정상 상황 판별"
- 메인 세션 질문 원문: "#87·#89·#92만 먼저 확정하고, 나머지는 AI 계약에 맞춰 architect에게 다시 맡길까요?" → 사용자 답변 원문(2026-11-11): "그렇게 해"
- 기존 설계(Architecture "백엔드–AI 내부 API" 2026-11-08까지)는 백엔드가 `ScenarioSpec`(목표 단서·상황 씨앗·변형·힌트 단계)을 매번 보내고 AI가 선택지마다 `judgment`·`cue_ids`를 붙이는 구조였다. AI 구현은 AI가 자기 콘텐츠(`content/`)에서 `scenario_id`로 시나리오를 찾고, 단서를 턴마다 하나씩 드러내며, 선택지에는 `kind`만 붙이고 턴마다 `target_clue_id` 1개를 준다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. AI 계약 채택 — 경로·필드·상태 전달 방식을 AI `contracts/`대로, 백엔드가 맞춘다. 합의가 필요한 몇 항목만 AI 담당에 제안 (**사용자 방향 "AI 계약에 맞춰"**) | AI 쪽 코드가 이미 있고 테스트가 있음(`tests/test_*.py` 13개 파일 존재만 확인 — 실행 결과는 architect 미확인). 연동일(11/12, 인용) 전 재작업이 백엔드 한쪽에만 생김. 백엔드 미구현 구간(T-15·T-16)이라 바꿀 코드가 적다 | 백엔드 T-01 완료 코드(`app/ai_client/ports.py`·`fake.py`·`tests/unit/test_fake_practice_ai.py`)를 다시 써야 함. 콘텐츠 원천이 AI 저장소로 옮겨 감. 우리 결정 몇 개(목표 단서 개념, 힌트, 요약 형태)가 계약과 어긋나 새 결정이 필요 |
| B. 기존 설계 유지 — AI가 우리 규격(`opening`·`next-turn`·`ScenarioSpec`)으로 고친다 | 확정된 결정·문서 변경이 적다 | AI 쪽 재작업이 크고 연동일 전에 끝나는지 불확실. 사용자 방향과 반대 |
| C. 혼합 — AI 계약을 받되 백엔드 `ai_client` 안에 옛 포트(`PracticeAI.opening` 등)를 남기고 어댑터로 변환 | services 코드가 옛 포트 그대로 | 옛 개념(`cue_ids`·`ScenarioSpec`)과 새 개념(`target_clue_id`·`revealed_clue_ids`)이 1:1이 아니라 변환이 정보를 지어내야 함(예: 선택지별 `cue_ids`). 계층이 하나 늘어남 |

## 결정

**대안 A.** 백엔드 포트(`app/ai_client/ports.py`)를 AI 계약 모양으로 다시 정의하고, services는 그 포트만 쓴다(계층 규칙 그대로 — `httpx`는 `http_client.py`만). 세부는 Architecture.md "백엔드–AI 내부 API" 절의 "1차 내부 API v1 (2026-11-11 — AI 계약 채택)" 하위 절이 원본이다. 핵심만:

1. **경로**: `GET /health`(토큰 없음), `POST /internal/v1/practice/variant`·`/start`·`/turn`·`/judge`·`/feedback`, `POST /internal/v1/summary`. 옛 `opening`·`next-turn`·`summaries/guardian`·`/internal/v1/health`는 1차에서 쓰지 않는다.
2. **선택지 태그 이름**: 우리 `ChoiceJudgment`(`suspicious`/`trusting`/`neutral`)를 AI `ChoiceKind`(`correct`/`doubtful`/`other`)로 바꾼다. 대응: PRD의 '의심' 태그(거절·확인·믿는 사람에게 묻기) = `correct`, '믿음'(돈·정보 주기 — 그대로 따름) = `other`, '중립' = `doubtful`(AI 설명 원문 "이상하다고 느끼지만 끝까지 대처하지 못하는 답"). **주의**: AI의 `doubtful`("의심되는 답")은 PRD의 '의심' 태그가 아니다. 종료 규칙(DECISIONS #80)·판정(F-13 ④)·지표 (다)(#87)는 이름만 바뀌고 규칙은 같다.
3. **선택지 구성 제약**(DECISIONS #83·#86 후속): `ok`·`blocked` 응답의 `choices`는 정확히 3개, `kind`가 `correct`·`doubtful`·`other` 각 1개, `id` 중복 없음 — 위반은 503. #86의 "의심 1개 이상 + 그 밖 1개 이상"을 더 좁게 만족한다.
4. **단서 연결**: 선택지별 `cue_ids`는 없다. 턴마다 `target_clue_id`(그 턴 선택지가 다루는 단서, null 가능)와 누적 `revealed_clue_ids`가 온다. 백엔드는 턴 행에 둘 다 저장하고, 아이 답을 다음 요청의 아이 메시지 `{role:"child", text: 고른 선택지 문장, choice_kind, clue_id: 그 턴의 target_clue_id}`로 넣는다.
5. **상태 저장**: AI는 상태가 없다. 백엔드가 세션에 `variant`(AI `Variant` 객체 전체)·`title`·`child_setup`·`ai_role_name`을, 턴에 `ai_line`·`choices`(`{id,text,kind}`)·`target_clue_id`·`revealed_clue_ids`·`chosen_choice_id`·`ai_status`를 저장하고 매 요청 `messages`·`revealed_clue_ids`·`variant`를 다시 만든다.
6. **종료**: 백엔드 규칙(#80) 그대로 — 위험 상황에서 `correct`를 고르면 종료, 아이 4번째 답이면 종료, 그 외 계속. AI의 `all_clues_revealed`는 입력으로 쓰지 않는다(F-11 ⑥). **예외 1개**: `turn` 응답 `status = "safe_reply"`(아이 글에서 자해·폭력 피해 감지)는 AI 담당 요청 원문 "바로 멈춰 주세요"에 따라 즉시 멈춘다 — 처리 규칙은 Architecture "safe_reply·blocked 처리" 행. 이것은 PRD F-11 ④⑤⑥에 없는 종료 조건이라 PRD 변경이 필요하다(planner).
7. **판정·피드백·요약 대응**과 검증 규칙(J·V·S 번호)은 Architecture 해당 행. `judge`는 AI 서비스에 그대로 둔다(#57).
8. **변형 선택**은 백엔드가 계속 정한다(ADR-0009 결정 유지): 백엔드 domain이 AI 시나리오의 `variation_axes` 안에서 `platform`·`tone`·`context`를 골라 `variant` 요청에 명시한다. AI는 글만 쓴다.

## 결과 (트레이드오프 포함)

- 얻는 것: 연동일 전 AI 쪽 재작업 없음. 판정이 아이가 고른 선택지 기록만으로 결정적으로 된다(AI `judge`의 `source = "choices"`).
- 감수하는 것:
  - T-01 완료 코드 재작업(포트·Fake·단위 테스트). planner가 재작업 T-xx를 만든다(DECISIONS #84와 같은 방식).
  - 단서가 턴마다 하나씩 드러나고 `correct`를 고르면 바로 끝나므로, 한 세션에서 찾을 수 있는 단서는 많아야 1개이고 나머지는 `not_shown`이 된다. PRD F-13 ④("나머지 목표 단서는 '놓침'")·F-28 ②("목표 단서를 모두 찾은")·F-29 ⑤의 "목표 단서" 해석을 다시 정해야 한다 → [ADR-0018](0018-not-shown-and-normal-judgment.md)(사용자 확인 대상).
  - 정상 상황은 AI 계약에 실행 경로가 없다(`content/scenarios/scam.json`의 `normal_situations` 4건은 초안 데이터로 있으나 `load_all_scenarios`가 색인하지 않고 `judge` 응답에 `normal_outcome`이 없다) → ADR-0018·AI 담당 합의.
  - 힌트(F-18 ② — 옛 `TurnResult.hint`)·성장 지표의 요약 입력(F-47 ②)·요약 단위(PRD OQ 56)가 AI 계약에 없다 → Architecture "AI 담당 합의 필요" 목록.
  - AI가 Gemini 실패·한도 초과 때 503을 내지 않고 고정 문장으로 대체한다(`source = "fallback"`). 백엔드는 이를 정상 응답으로 받으므로 장애가 화면에 "다시 시도"로 드러나지 않는다 — `variant`의 fallback만 F-12 검사(변형 차이)에 걸려 503이 될 수 있다.
  - AI 서비스 오류 본문 형식이 `{"error": "<code>"}`(문자열)라 옛 규격 `{"error":{"code","message"}}`와 다르다 — 백엔드는 비2xx면 본문을 해석하지 않고 `AIUnavailableError`로 바꾸므로 동작 영향은 없다.
- 되돌리기: 대안 B로 가려면 새 ADR. 옛 규격 행은 Architecture에 "[대체됨]" 표시로 남겨 둔다.

## 덧붙임 (2026-11-11 — 세부 사용자 확정)

메인 세션이 사용자에게 물은 질문과 답(원문):

| 질문 원문 | 답변 원문 | 기록 |
|---|---|---|
| "콘텐츠(단서·시나리오) 원본을 어느 저장소에 둘까요?" | "AI 저장소 원본 (추천)" | DECISIONS #111 (#107) |
| "영역 ID — AI는 identity_lending·friend_pressure를 씁니다. 백엔드가 이 ID로 맞출까요? (공개 API 값이 바뀌어 프론트에 알려야 함)" | "AI ID로 맞춤 (추천)" | #112 (#108) |
| "safe_reply(아이가 자해·폭력 피해를 말함) 처리 — architect 안: 안내 턴을 저장하고 세션을 'stopped'로 멈춤, 결과 화면(Y5)으로 가지 않고 판별도 안 함, 성장 집계에서 제외. 이대로 할까요?" | "이대로 (추천)" | #113 (#99) — 결정 6의 예외 확정. PRD F-11 갱신은 planner |
| "보호자 학습 요약 단위 — AI의 요약 API는 영역 1개씩 받습니다. 요약을 영역별로 만들까요? (기존 기본값은 '전체 1개', PRD OQ 56 미결)" | "영역별 요약 (추천)" | #114 (#103) |
| "나머지 대응 규칙(#96~#102·#104: 경로·필드 이름을 AI 계약에 맞춤, 백엔드가 대화 기록·드러난 단서·변형을 저장해 매번 보냄, 선택지 3개·kind 3종 각 1개 검증)는 확정할까요?" | "확정 (추천)" | #115 |

`not_shown`·정상 상황은 [ADR-0018](0018-not-shown-and-normal-judgment.md) 덧붙임(#109·#110). 결정 1~8 본문은 바뀌지 않는다.

## 덧붙임 2 (2026-11-11 — PRD OQ 64·planner 해석 사용자 확정)

| 질문 원문 | 답변 원문 | 기록 |
|---|---|---|
| "아이가 자해·폭력 피해를 말해 연습이 안전 안내로 멈춘 뒤 처리를 어떻게 할까요?" (선택지 설명 원문 "안내는 사람이 쓴 고정 문구(믿는 어른·상담 전화 안내)로 보이고 '홈으로' 버튼. 보호자 알림은 1차에 만들지 않음(실제 알림 생성은 2차). 선택지 입력만 있는 1차에서는 거의 안 생김(추정)") | "고정 문구+홈, 알림 없음 (추천)" | DECISIONS #118 — 결정 6 예외의 세부 갱신: 안내 턴 `ai_line` = 백엔드 고정 문구(`safety_stop.json`), AI `reply`는 저장·표시·로그 안 함, `safe_reply` 본문 검증 없음, 보호자 알림 미생성 |
| 해석 4·5·6(F-42 원본 대체, 요약 입력에서 지표·직전 기간 제외, 한 영역 실패면 요약 전체 실패) | "그렇게 봄 (추천)" / "1차는 빼고 감 (추천)" / "전체 실패 표시 (추천)" | DECISIONS #119 — #102·#103 내용 그대로, G5는 1차 요청 안 함 |

결정 1~8 본문은 바뀌지 않는다(결정 6은 "처리 규칙은 Architecture 행"을 가리키므로 그 행에서 갱신).
