# Architecture — 서비스명 미정 (프로젝트: 2026_line1thon)

> 소유자: architect | 상태: 승인 (2026-11-08 사용자 승인 — 원문 "승인했어", 기입 지시 원문 "대신 기입해", 메인 세션이 사용자 지시로 기입) | 최종 수정: 2026-11-12 (Y5 카드 색 PRD OQ 63 ①·노랑 문구 OQ 24 사용자 확정 — DECISIONS #120·#121, "변경 기록" 2026-11-12 행) / 2026-11-11 (바뀐 부분은 "변경 기록" 2026-11-11 세 행. 둘째 행: AI 저장소 계약 채택. 셋째 행: 그 세부와 `not_shown`·정상 상황·콘텐츠·Area·safe_reply·요약 단위 사용자 확정 — DECISIONS #109~#116. 넷째 행: ★·PRD OQ 64·해석 4~7 사용자 확정 — DECISIONS #117~#119)
> 상태는 초안/승인 두 가지. "승인"으로 바꾸는 것은 사용자만 한다 — 승인 전 구현 착수 금지 (AGENTS.md 파이프라인 규칙).
> 입력 근거: docs/PRD.md(상태 "승인" — 2026-11-06 사용자 원문 "승인하고 설계"), docs/Tasks.md(최종 수정 2026-11-06), 메인 세션의 실행환경 확인(2026-11-06, 아래 표에 원문), 2026-11-06 사용자 답변·팀 GitHub 조직 line1thon-15 실제 구성(메인 세션 gh CLI 확인 — 아래 "변경 기록").
> 표기: **[가정]** = 팀 확인 전 가정 / **[사용자 확인 필요]** = 계정·비용·외부 서비스 선택 / **[OQ n]** = PRD Open Question n이 정해져야 확정되는 부분 / **[A-n]** = 이 문서 끝 "설계가 올린 질문" / **[팀 요청 F-n·AI-n]** = "팀원 요청 사항" 표 / **[정본: docs 저장소]** = 팀 GitHub docs 저장소에 게시해야 하는 공유 규격 / (인용) = architect가 이번 세션에 직접 재확인하지 않은 값.

## 변경 기록

| 날짜 | 근거 원문 | 바뀐 절 |
|---|---|---|
| 2026-11-06 (첫 초안) | PRD·Tasks·실행환경 확인 | 전체 |
| 2026-11-06 (갱신) | 사용자 답변 원문: "필요한 건 추가 해. 이때 각 팀원 별로 해야 하는 작업을 나누는 노션 페이지를 만들어 주고,https://github.com/line1thon-15 깃허브 링크 줄게. 내가 접근할 곳은 backend 부분 쪽이야" (메인 세션 해석: A-3 설치 허용, A-1·A-2·A-5·A-7 보류 — 기본값·추천안으로 진행). 팀 GitHub 조직 line1thon-15 실제 구성(메인 세션 2026-11-06 gh CLI 확인, 인용): 저장소 frontend("프론트엔드 레포지토리 (React + Tailwind)", 최근 커밋 2026-11-04) / ai("AI 레포지토리 (LLM 생활 판단 연습·피드백)", 비어 있음) / backend("백엔드 레포지토리", 비어 있음) / docs("1호선톤 15조 팀 공용 문서 저장소 (컨벤션·기획·API)") | 설계 범위, 실행환경 사전 확인, 설치 불허 시 대안, 기술 스택, 저장소와 브랜치(신규), 구조 개요, 모듈 경계와 책임, 데이터 흐름, API 규격(A5·A14 응답), 백엔드–AI 내부 API(구 "AI 모듈 경계"), 콘텐츠 파일 규격, 계층 규칙, 화면 메커니즘, 보안·개인정보, 시크릿과 환경 변수, AI 제공사 정책 기록, 테스트 전략·T-01 범위, 배포, 에러 처리(경계 간 전파), 관측성(로깅), 2차 확장 지점, 팀 공유 규격(신규), 팀원 요청 사항(신규), 미결 질문, 설계 리스크, 주요 결정. 바뀌지 않은 절: 공통 값 타입, 엔티티, 응답 DTO, 오류 응답 규격(코드 목록), 연습 출제 규칙 |
| 2026-11-06 (AI-4 반영) | 사용자 원문 "지금 하고, 너가 할 수 있는 거 외에 팀원들과 논의해야 하는 부분에 대해서 작성해 내가 팀원들에게 물어보고 올게"(메인 세션의 "약관 확인은 AI 담당이 아니라 제가 할 수 있다, 지금 확인할까요?"에 대한 답). 메인 세션 2026-11-06 Browser pane 확인: Gemini API 추가 서비스 약관 한국어판(시행일 2026년 3월 23일) | AI 제공사 정책 기록(무료/유료 데이터 조건 행), 팀원 요청 사항(AI-4), 설계가 올린 질문(A-13 추가) |
| 2026-11-06 (AI 파트 범위 반영) | 팀 노션 "AI 파트" 페이지 원문(메인 세션 Browser pane 수집, 인용 — 해당 절 표에 항목별 원문), 팀 타임라인 원문 "11/11 - 각 파트 개발 완료 / 11/12 - 연동 / 11/14 - 제출", 사용자 원문 "추천대로 반영"(분담: AI는 글 생성, 백엔드는 계산·저장) | 모듈 경계(ai 행), 데이터 흐름 5번, 응답 DTO(GuardianReport·GrowthView), 백엔드–AI 내부 API(opening 검수 보강, 힌트·요약·추천 이유 행, 포트), AI 파트 범위 대응(신규), 계약 고정과 연동 일정(신규), 에러 처리(경계 간 전파), 팀원 요청 사항(AI-1), 설계가 올린 질문(A-14~A-16), 설계 리스크(D-8) |
| 2026-11-06 (judge 위치·요약 비저장 확정) | 사용자 원문 "추천안대로" — 승인된 메인 세션 추천안 원문 2 "단서 찾음/놓침 판정(judge)을 누가 맡을지. … 추천: AI 담당에 그대로 두기. 팀 AI 파트 페이지에 "판단 분석"이 AI 몫으로 적혀 있어서, 옮기면 AI 담당과 다시 합의해야 합니다." / 3 "보호자 학습 요약을 저장할지. … 추천: 설계대로 저장하지 않기. 테이블을 새로 만들 필요가 없습니다. 다만 G3를 볼 때마다 AI를 호출하므로 조금 느리고 선불 크레딧이 줄어듭니다. 시연 계정은 예시 데이터라 영향이 작습니다." | 백엔드–AI 내부 API(judge 행·요약 실패 처리 행), AI 파트 범위 대응(3 행), 설계 리스크(D-8 상태) |
| 2026-11-07 (아이 PIN 보호자 입력) | 프론트 B 제안 원문(사용자 전달): "지금 디자인에서는 아이 로그인 코드가 등록 전부터 화면에 보이는데, 이름/학년/PIN 입력하고 연결 완료 누른 다음에 코드가 발급되는 순서로 가면 어떨까 싶어요 이렇게 하면 아이 등록 API 응답에 로그인 코드만 같이 담아주시면 돼서 백엔드 쪽에서도 조금 더 편해질 것 같습니다." / 사용자 원문 "보호자 입력으로 반영" — 승인된 메인 세션 추천안(G4 재설정도 보호자 입력, A9 응답에 PIN 없음) | 공통 값 타입(PIN 행), 데이터 흐름 1번, API 규격(A7·A9), 화면 메커니즘(G2·G4 행), 보안·개인정보(비밀번호·PIN 행, 알려진 한계), 테스트 전략(다른 저장소 frontend 행의 시연 흐름 표현), 설계가 올린 질문(A-5) |
| 2026-11-07 (심화 연습 F-48) | 사용자 원문 "심화 연습은 기획서 확인하고, 없어도 일단 추가하는 방향으로", PRD F-48(인수 기준 ①~⑦, 사용자 확인 대상)·화면 Y5-1~Y5-5·R-8·OQ 50~54, Tasks T-78~T-81(인용 — planner 반영분) | 데이터 흐름 4-1번(신규), API 규격(A20~A23, 감정 값 문장), 응답 DTO(DeepEntryView·DeepFeedbackView, 보호자 금지 필드), 백엔드–AI 내부 API(`deep/feedback`, 심화 연습 안전 처리, 포트), 화면 메커니즘(Y5 행, Y5-1~Y5-5 행), 보안·개인정보(AI로 가는 데이터, 로그), AI 제공사 정책 기록(STT 행), 테스트 전략(커버 범위), 관측성(로깅), 팀원 요청 사항(F-8 신규, AI-1), 설계가 올린 질문(A-17), 설계 리스크(D-9·D-10), 주요 결정(ADR-0014) |
| 2026-11-07 (AI 담당 답변 반영 — 사용자 확인 대상) | AI 담당 답변 원문(사용자 전달 "ai파트 답장이야", 반영 방식 지시 없음): "1. 동의합니다. AI 레포에서 별도 HTTP 서버(8081)를 운영하는 방식으로 진행하겠습니다." / "2. … 이번 MVP에서는 ①을 구현하고, ②는 향후 발전 방향으로 가져가면 좋겠습니다." / "3. 좋습니다." / "4. 보호자 학습 요약은 백엔드에서 연습 횟수, 발견한 단서, 놓친 단서, 영역별 성장 수준 등 계산된 데이터를 전달해 주시면, AI가 이를 바탕으로 보호자가 이해하기 쉬운 1~2문장의 요약을 생성하는 방식으로 진행하면 좋겠습니다." 질문 다섯째 항목(심화 연습 피드백·안전 필터)은 답 없음. PRD 결정 기록 (2026-11-07 AI 담당 답변) 절·F-47·G3·OQ 55~57, Tasks T-14·T-46·T-75~T-78(인용 — planner 반영분) | 기술 스택(백엔드–AI 구성 행), 데이터 흐름 5번, 응답 DTO(GuardianReport `summary`), 백엔드–AI 내부 API(`practice/feedback`·`LearningSummaryInput`·`summaries/guardian`·`summaries/child-growth`·요약 공통 제약·`deep/feedback`·심화 연습 안전 처리·요약 실패 처리), AI 파트 범위 대응(3·8·9행), 테스트 전략(커버 범위), 에러 처리(경계 간 전파), 팀원 요청 사항(AI-1), 설계가 의존하는 미결 질문(OQ 55·56·57 행), 설계가 올린 질문(A-8·A-14·A-15 해소, A-18 신규), 설계 리스크(D-8), 주요 결정(ADR-0011 상태 칸) |
| 2026-11-07 (심화 연습 AI 피드백 2차 — PRD OQ 55 해소, OQ 59 판단 — 사용자 확인 대상) | PRD OQ 55에 대한 사용자 답변 원문 "AI 피드백만 2차로"(메인 세션 질문 원문 "심화 연습(F-48)은 어떻게 할까요?", 버튼 선택지 원문 "1차 유지, AI에 재확인" / "AI 피드백만 2차로"). "화면 유지"는 메인 세션 해석(추정 — PRD 결정 기록 (2026-11-07 심화 연습 AI 피드백 2차) 절). planner가 넘긴 항목 원문(메인 세션 전달): "(a) Architecture.md:615의 OQ 55 행. … `deep/feedback`, 심화 연습 안전 처리, AI-1의 `deep/feedback` 요청의 차수를 2차로 바꿔야 합니다." / "(b) 1차 흐름에서 AI 호출을 빼는 갱신이 필요한 곳: 데이터 흐름 4-1번(:170), A21(:235)의 `AI_UNAVAILABLE`, 화면 메커니즘 Y5-2~Y5-4(:407~409), AI로 가는 데이터(:443), D-10(:655)." / "(c) PRD OQ 59 판단." / "(d) DECISIONS #70 … 의 후속 기록." PRD F-48·화면 Y5-2~Y5-4·R-8·N-04·OQ 50·59, Tasks T-51·T-78~T-82(인용 — planner 반영분) | 데이터 흐름 4-1번, API 규격(A20~A23 차수·조건), 응답 DTO(DeepEntryView·DeepFeedbackView), 백엔드–AI 내부 API(`deep/feedback`·심화 연습 안전 처리·포트 — [2차] 표시, 규격 유지), AI 파트 범위 대응(3행), 화면 메커니즘(Y5-1~Y5-4 행), 보안·개인정보(AI로 가는 데이터), 테스트 전략(커버 범위·frontend 행), 2차 확장 지점(심화 연습 AI 피드백 행), 팀원 요청 사항(F-8·AI-1), 설계가 의존하는 미결 질문(OQ 55 해소, OQ 59 신규), 설계가 올린 질문(A-17), 설계 리스크(D-10), ADR-0014 덧붙임 |
| 2026-11-08 (`feedback` → `PracticeResultView` 매핑 정의, PRD OQ 59 ① 사용자 확정 반영) | 승인 전 점검의 치명 결함(메인 세션 전달 원문 요지: 내부 feedback의 `cards[{cue_id\|null, sentence}]`가 공개 `PracticeResultView`의 어느 필드로 가는지 정의가 없다 — `cards[].level`, `cue_id: null` 카드, AI 문장과 `CueCard.sentence`의 관계, AI 실패 시 결과 화면). AI 담당 답변 원문(2026-11-07) "2. AI 파트 3번 '판단 이유'는 … 이번 MVP에서는 ①을 구현하고, ②는 향후 발전 방향으로 가져가면 좋겠습니다." / 메인 세션 질문 원문 "1차에 아이 답변을 서버로 보내지 않는 기본안으로 갈까요?"(PRD OQ 59 ①)에 대한 사용자 답변 원문 "기본안대로"(2026-11-07) | 데이터 흐름 4번, API 규격(A18 오류 목록, A21·A22 확정 표시), 응답 DTO(PracticeResultView), 백엔드–AI 내부 API(`practice/feedback` 행, 매핑 행 신규), 테스트 전략(frontend 행 확정 표시), 팀원 요청 사항(F-8 확정 표시), 설계가 의존하는 미결 질문(31·59 행), 설계가 올린 질문(A-17 확정 표시), 설계 리스크(D-10 확정 표시), DECISIONS #75·#76. A20(DECISIONS #73)·위험 표현 안내(DECISIONS #74)는 사용자 확인 대상 그대로 |
| 2026-11-08 (Tasks·PRD 정리 후속) | planner 보고 원문(메인 세션 전달): "① :512 스모크 기대값을 A1 `{status:"ok", db:"ok"}`로 맞추기. ② :520과 A-12(:645): Tasks 정리 결과(T-01 백엔드, T-83 프론트, T-84 AI, 실행 단위별 적용) 반영. AGENTS.md 해석은 사용자 확인 대기입니다. ③ :508-518 하네스 범위 표에 T-83·T-84 ID 표기. ④ A-17(:644)의 "Tasks T-79는 이 답 때문에 보류(인용)"는 T-79 보류 사유가 바뀌었으므로 갱신 필요. ⑤ :410, :620, DECISIONS #74의 "PRD OQ 59 ②"는 OQ 60으로 바꿔야 합니다." Tasks "파트별 하네스 분리" 절·T-01·T-79·T-83·T-84, PRD OQ 59·60(인용). 메인 세션 요청: ADR-0014 확정 덧붙임, 오류 코드 표 `AI_UNAVAILABLE`의 Y5 반영 | 오류 응답 규격(`AI_UNAVAILABLE`), 화면 메커니즘(Y5-2 행), T-01 하네스 범위(표·아래 문단), 설계가 의존하는 미결 질문(59 행), 설계가 올린 질문(A-12 부분 해소, A-17), DECISIONS #77, ADR-0014 덧붙임 |
| 2026-11-08 (A-12 해소) | 메인 세션 질문 원문 "하네스 규칙을 파트별로 적용하는 해석을 받아들일까요?"(앞선 설명 원문 "AGENTS.md에는 'T-01 하나가 끝나야 나머지를 시작한다'고 적혀 있습니다. 이번에는 이것을 '각 파트는 자기 하네스가 끝나면 시작한다'로 해석했습니다. 규칙의 취지(테스트 없이 구현 금지)는 지키지만, 글자 그대로와는 다릅니다."), 사용자 답변 원문 "받아들임" | T-01 하네스 범위(표 아래 문단), 설계가 올린 질문(A-12 해소), DECISIONS #78 |
| 2026-11-08 (#75 매핑·실패 처리 사용자 확정) | 메인 세션 질문 원문 "AI 실패 시 결과 화면 전체를 '다시 시도'로 보여주는 안으로 갈까요?"(앞선 설명 원문 "AI 설명을 받지 못했을 때 결과 화면 전체를 '다시 시도'로 보여줄지, 아니면 단서 카드는 그대로 보여줄지 정해 주세요. 단서 카드를 보여주는 쪽을 고르시면 화면 상태와 응답 필드를 하나씩 추가해야 합니다."), 사용자 답변 원문 "지금 안대로" | 백엔드–AI 내부 API(매핑 행 머리 표시), DECISIONS #79 |
| 2026-11-08 (연습 종료 조건 — PRD OQ 42 해소, OQ 62 ① 사용자 답) | 사용자 답변 원문(메인 세션 전달, PRD 결정 기록 (2026-11-08 연습 종료 조건) 절): ① 상한 "4번 (Recommended)" ② 조기 종료 "의심 답이면 바로 종료 (Recommended)" — 선택지 설명 원문 "아이가 거절·확인을 고르면 그 자리에서 끝내고 결과로 갑니다. 믿는 답을 고르면 상대가 더 조르면서 계속되어 다시 알아챌 기회가 생깁니다." ③ 판정 주체 "백엔드 규칙만 (Recommended)" — 선택지 설명 원문 "백엔드가 선택지 태그와 상한으로만 판정하고 AI의 종료 신호는 쓰지 않습니다." ④ OQ 62 ① 질문 원문 "연습 대화가 끝나는 답(의심 답, 또는 4번째 답)을 고른 뒤 화면은 어떻게 할까요?" → "바로 결과 화면 (Recommended)" ⑤ planner 임시 세부 3가지(중립 답은 4번째 전이면 계속 / 답 횟수 = 아이가 선택지를 고른 횟수, 첫 대사에 대한 답이 1번째 / 위험 상황에만 적용) → "그대로 (Recommended)". PRD F-11 ④⑤⑥·N-12·OQ 61·62, Tasks T-12·T-14·T-15·T-18(인용 — planner 반영분) | 모듈 경계(app/domain 행), 데이터 흐름 3번, 엔티티(practice_turns `turn_index` 기준), API 규격(A16·A17), 응답 DTO(PracticeSessionView·TurnView), 백엔드–AI 내부 API(`ChoiceOption`·`TurnResult`·`next-turn`·종료 행·선택지 태그 제약 행 신규), AI 파트 범위 대응(2행), 화면 메커니즘(Y4 행), 테스트 전략(커버 범위), 팀원 요청 사항(F-9·AI-5 신규), 설계가 의존하는 미결 질문(42 해소, 61·62 신규), 설계 리스크(D-11 신규), 주요 결정(ADR-0015), DECISIONS #80~#83 |
| 2026-11-08 (#81~#83 사용자 확정) | 사용자 답변 원문(메인 세션 전달): 질문 "[DECISIONS #81] AI가 보내던 종료 신호 필드(is_terminal)는 이제 쓰지 않습니다. architect는 이 필드를 삭제하기로 했습니다. 삭제하면 이미 끝난 T-01 코드 4곳을 고치는 재작업 작업이 하나 생깁니다. 삭제로 할까요?" → "삭제 (Recommended)" / 질문 "[DECISIONS #82] 아이가 답을 보내면(A17) 서버는 '계속(다음 대사 포함)' 또는 '종료(대사 없음)'를 돌려줍니다. AI 호출이 실패하면 그 답도 저장하지 않고, 아이는 같은 답으로 다시 시도합니다. 이미 끝난 연습에 답을 보내면 화면은 결과(Y5)로 갑니다. 이 방식으로 할까요?" → "이대로 (Recommended)" / 질문 "[DECISIONS #83] 위험 상황에서는 매 턴 선택지에 '의심' 답이 1개 이상, 그 밖의 답(믿음·중립)도 1개 이상 있어야 하고, 어기면 AI 실패(503 '다시 시도')로 처리합니다. 이 제약을 둘까요?" → "둔다 (Recommended)" | 백엔드–AI 내부 API(`TurnResult` 행, 선택지 태그 제약 행 — 확정 표시), 테스트 전략(커버 범위 — #83 확정 표시), 팀원 요청 사항(AI-5 ①④ 확정 표시), 주요 결정(ADR-0015 상태 칸 주석 — 상태 "제안"은 그대로), DECISIONS #84~#86, ADR-0015 덧붙임. 결정 내용 변경 없음 |
| 2026-11-11 (PRD OQ 12·13(배지·연속 기록)·31·36 해소 반영 — 사용자 확인 대상) | PRD 결정 기록 (2026-11-11 성장 지표·배지·판정·안전 알림) 절의 사용자 답 원문(인용): OQ 31 "한 번이라도 의심 (추천)", OQ 12 "추천 정의 묶음 (추천)", OQ 13 "3회 성공 + 하루 단위 (추천)", OQ 36 "시각·위험도·영역 (추천)", planner 해석 9건에 사용자 답 원문 "9건 확정, 진행하고, 방법 1로 가는 방향으로 가보자"(메인 세션 전달). 지표 (다) 원천 충돌(planner 발견 원문 "첫 답 선택은 `practice_turns`(turn_index 0의 `chosen_choice_id`와 `choices[].judgment`)에만 있습니다. 그런데 Architecture.md:212에는 '**보호자용 API는 이 테이블을 읽지 않는다** (F-30 ③)'고 되어 있습니다.")에 메인 세션이 제시한 "방법 1: 이 규칙에 예외를 둡니다." 채택. PRD F-13 ④⑤·F-28 ②③·F-29 ⑤⑥·F-41 ④⑤·OQ 63(인용 — planner 반영분) | 모듈 경계(domain·ai 행), 데이터 흐름 5번, 공통 값 타입(ChoiceJudgment·시각 행), 엔티티(practice_sessions `normal_outcome`, practice_turns 예외, guardian_notices 제약, 배지·연속 기록 행), 응답 DTO(PracticeResultView·BadgeView·MetricView·NoticeView, 보호자 금지 필드), 백엔드–AI 내부 API(`judge` 행, 매핑 행 머리·③, `LearningSummaryInput` 기간), 성장 계산 규칙(신규 절), AI 파트 범위 대응(3·8행), 테스트 전략(커버 범위), 팀원 요청 사항(AI-6 신규), 설계가 의존하는 미결 질문(12·13·31·36 해소, 63 신규), 설계가 올린 질문(A-18 메모, A-19~A-21 신규), 설계 리스크(D-12 신규), 주요 결정(ADR-0016), DECISIONS #87~#92 |
| 2026-11-11 (AI 저장소 1차 구현 계약 채택 — #87·#89·#92 사용자 확정, 나머지 사용자 확인 대상) | AI 담당 공지 원문(축어 — ADR-0017 맥락 절 전문): "ai 저장소에 1차 구현 올렸습니다. … 경로와 필드는 제안안이라, 바꾸고 싶은 부분 있으면 편하게 말씀해 주세요. mvp대로 AI 서버는 상태를 저장하지 않게 만들었습니다. 대화 기록, revealed_clue_ids, variant를 저장해 두셨다가 매번 같이 보내 주셔야 해요. …". 메인 세션 질문 원문 "#87·#89·#92만 먼저 확정하고, 나머지는 AI 계약에 맞춰 architect에게 다시 맡길까요?" → 사용자 답변 원문 "그렇게 해". 근거 코드: ai 저장소 커밋 331d2c6(feature/ai, 읽기 전용 사본 — architect 직접 확인) `contracts/*.json`·`app/schemas.py`·`app/server.py`·`app/practice.py`·`app/choices.py`·`app/judge.py`·`app/variation.py`·`app/scenarios.py`·`app/summary.py`·`app/content.py`·`content/clues.json`·`content/scenarios/scam.json`·`.env.example` | 데이터 흐름 3·4·5번(머리 메모), 공통 값 타입(ChoiceJudgment→ChoiceKind, Area 메모), 엔티티(practice_sessions·practice_turns·cue_results), 응답 DTO(PracticeSessionView `stopped`, 보호자 금지 필드), 오류 응답 규격(`SESSION_STOPPED`), 백엔드–AI 내부 API(머리 메모 + 신규 하위 절 "1차 내부 API v1 (2026-11-11 — AI 계약 채택)"·"기존 결정과의 충돌 정리"·"AI 담당 합의 필요"·"콘텐츠 소유"), 성장 계산 규칙(머리 메모), 콘텐츠 파일 규격(머리 메모), 팀원 요청 사항(AI-7 신규), 설계가 의존하는 미결 질문(61 행), 설계가 올린 질문(A-22~A-24 신규), 설계 리스크(D-13 신규), 주요 결정(ADR-0016 상태, ADR-0017·ADR-0018 신규), DECISIONS #93~#108, ADR-0016 덧붙임 |
| 2026-11-11 (AI 계약 세부·`not_shown`·정상 상황 사용자 확정) | 메인 세션 질문·사용자 답변 원문(전문은 DECISIONS #109~#115 근거 열): Q1 not_shown → "드러난 단서만 판정 (추천)" / Q2 정상 상황 → "끄고 AI에 요청 (추천)" / Q3 콘텐츠 원본 → "AI 저장소 원본 (추천)" / Q4 영역 ID → "AI ID로 맞춤 (추천)" / Q5 safe_reply → "이대로 (추천)" / Q6 요약 단위 → "영역별 요약 (추천)" / Q7 나머지 대응 규칙(#96~#102·#104) → "확정 (추천)" | 데이터 흐름(머리 메모), 공통 값 타입(Area·ChoiceKind), 엔티티(practice_sessions·practice_turns·cue_results), 응답 DTO(PracticeSessionView·GuardianSummaryView), 오류 응답 규격(`SESSION_STOPPED`), 백엔드–AI 내부 API(머리 메모, 1차 내부 API v1 머리·safe_reply·judge 행, 충돌 정리 표, AI 담당 합의 필요 G2·G3·G6·G7·G9, 콘텐츠 소유), 연습 출제 규칙(머리 메모), 성장 계산 규칙(머리·메모·(가)(나)(다)·배지 행 — DECISIONS #116), 콘텐츠 파일 규격(머리 메모), 테스트 전략(커버 범위 끝 2026-11-11 확정 추가), 설계가 의존하는 미결 질문(12·13·31·56·61 행), 설계가 올린 질문(A-22~A-24 해소), 주요 결정(ADR-0017·ADR-0018 상태), DECISIONS #109~#116, ADR-0017·ADR-0018 덧붙임. 머리글 상태 "승인"은 그대로 |
| 2026-11-11 (★·PRD OQ 64·planner 해석 4~7 사용자 확정) | 메인 세션 전달 사용자 답변 원문(전문은 DECISIONS #117~#119 근거 열): ★ "빼기 (추천)" / OQ 64 "고정 문구+홈, 알림 없음 (추천)"(설명 원문 "안내는 사람이 쓴 고정 문구(믿는 어른·상담 전화 안내)로 보이고 '홈으로' 버튼. 보호자 알림은 1차에 만들지 않음(실제 알림 생성은 2차). 선택지 입력만 있는 1차에서는 거의 안 생김(추정)") / 해석 5 "1차는 빼고 감 (추천)" / 해석 6 "전체 실패 표시 (추천)" / 해석 7 "넣지 않음 (추천)" / 해석 4 "그렇게 봄 (추천)". 팀 공지 방식 원문 "내가 결정하고, 이견 기한 안줘도 될 거 같아" | 엔티티(practice_turns `ai_line`), 응답 DTO(PracticeSessionView `stopped`), 백엔드–AI 내부 API(`turn` 행 safe_reply 검증, safe_reply·blocked 처리 행, AI 담당 합의 필요 머리·G5), 성장 계산 규칙(머리 메모 ★), 콘텐츠 파일 규격(`safety_stop.json`), 화면 메커니즘(Y4 행), 테스트 전략(커버 범위 ⑦), 팀원 요청 사항(F-10 신규, AI-7 ③), 설계가 의존하는 미결 질문(64 신규·해소), DECISIONS #117~#119, ADR-0017·ADR-0018 덧붙임. 결정을 뒤집은 것은 #99·#113의 안내 문장 출처뿐(AI `reply` → 백엔드 고정 문구) |
| 2026-11-12 (PRD OQ 63 ①·OQ 24 사용자 확정, T-16 리뷰 권고 #1 대응) | 메인 세션 질문·사용자 답변 원문(전문은 DECISIONS #120·#121 근거 열): OQ 63 ① "연습 결과(Y5) 카드 신호등 색을 어떻게 정할까요? …" → "판단 결과 기준 (추천)" / OQ 24 "노랑 신호의 화면 문구(PRD OQ 24)는 무엇으로 할까요?" → "믿는 사람에게 물어봐요 (추천)". T-16 리뷰 권고 #1 원문(메인 세션 전달) "매핑이 없어도 AI 호출이 한 번 소비된다 … 키→값 확인을 AI 호출 전에 하거나" — 결정은 메인 세션 지시 원문 "level 매핑 확인을 `feedback` 호출 전에 한다(값이 있어도 방어 유지)", 구현 T-89(인용) | 모듈 경계(app/domain 행 괄호), 공통 값 타입(SignalLevel 행), 응답 DTO(PracticeResultView 행), 백엔드–AI 내부 API(매핑 행 머리·③), 설계가 의존하는 미결 질문(24 해소, 63 ① 해소·② 미결), DECISIONS #120·#121. 머리글 상태 "승인"은 그대로. 오류 코드 묶음(T-15·T-16)은 이번 범위 밖 |

## 설계 범위

| 구분 | 범위 | 근거 |
|---|---|---|
| 설계 대상 | 1차 화면 11개(S0, Y1~Y5, Y8, G1~G4)와 PRD "기능 요구사항 — 1차" 표의 F-xx([2차] 표시 기준 제외), N-01~N-11의 1차 범위 | PRD.md:126, PRD.md:45-79 |
| 저장소별 설계 깊이 (2026-11-06 갱신) | **backend 저장소(이 폴더, 사용자 담당)**: 구조·데이터 모델·API·테스트를 확정 규격으로. **frontend·ai 저장소(다른 팀원 소유)**: 백엔드와 맞물리는 계약(공개 API·내부 API·프록시·쿠키)만 확정하고, 그 저장소 내부 구조는 권고로만 둔다 — "팀원 요청 사항" 표 | 사용자 원문 "내가 접근할 곳은 backend 부분 쪽이야", 팀 구성 원문 "팀은 총 6명으로, 디자인1, 프론트엔드 2, 백엔드 2, ai 1명으로 구성" |
| 설계하지 않음 | 2차(Y6·Y6-1·Y7, F-19~F-22·F-24·F-40·F-43, F-32~F-39), 보류(F-44·F-46, Y9) — 붙을 자리만 "2차 확장 지점" 절에 적는다 | PRD.md:81-106, architect 역할 원본 절차 1 "확장성 선반영 금지" |
| 시연 흐름 | S0 → 보호자 가입 → 아이 연결 → 사기 연습 2회(같은 단서, 다른 모습) → 아이 성장 기록 Y8(예시 데이터) → 보호자 리포트 G3(시연용 안전 알림 포함) | PRD.md:40, N-06(PRD.md:117) |

## 실행환경 사전 확인 (기술 선택 전)

메인 세션이 2026-11-06 이 PC에서 읽기 전용으로 확인해 전달한 원문이다(전부 (인용) — architect는 실행 권한으로 재확인하지 않았다. 단 `.gitignore`는 architect가 직접 읽었다). 명령은 Git Bash에서 실행됐다. 이 확인은 이 PC 한 대 기준이며 팀원 6명의 환경은 미확인이다.

| 확인 항목 | 읽기 전용 확인 방법과 전달된 근거 (원문) | 확인 결과 | 처리 (AGENTS.md "실행환경 사전 확인" 표) |
|---|---|---|---|
| Python 런타임 | `python --version` → `Python 3.13.2` (exit=0) / `py -0p` → `-V:3.13 * C:\Python\Python313\python.exe` | 사용 가능 (인용) | 관찰 근거 기록. 백엔드 코드 호환 기준은 Python 3.12 이상, 로컬·배포 기준 버전은 3.13 (DECISIONS #6) |
| pip | `pip --version` → `pip 24.3.1 from C:\Python\Python313\Lib\site-packages\pip (python 3.13)` | 사용 가능 (인용) | 의존성은 `requirements*.txt`로 관리해 pip·uv 어느 쪽으로도 설치 가능하게 한다 (DECISIONS #7) |
| uv | `uv --version` → `uv 0.12.1 (2026-07-31)` | 사용 가능 (인용) | 선택 사용 — 팀원 환경 미확인이라 필수 도구로 두지 않음 |
| poetry | `poetry --version` → `command not found` | 없음 (인용) | 사용하지 않음 |
| Node.js / npm | `node --version` → `v22.14.0` / `npm --version` → `10.9.2` | 사용 가능 (인용) | backend 저장소는 Node를 쓰지 않는다. frontend 저장소의 패키지 매니저는 프론트 담당 결정 |
| pnpm | `pnpm --version` → `command not found` | 없음 (인용) | 사용하지 않음 |
| Java | `java -version` → `openjdk version "21.0.6" 2025-01-21 LTS (Microsoft build)` | 있음 (인용) | 사용하지 않음 — 백엔드 원문 "그리고 백엔드는 파이썬 형태로 진행하기로 했어"(PRD.md:320)가 Spring Boot 희망을 대체 |
| Docker | `docker --version` → `command not found` | 없음 (인용) | 컨테이너 기반 로컬 DB·testcontainers를 쓰지 않는다. 테스트 DB는 SQLite, 배포는 PaaS의 네이티브 Python 빌드 (ADR-0005·ADR-0007) |
| Git / 저장소 (2026-11-06 갱신) | `git --version` → `git version 2.53.0.windows.1` / 세션 환경 정보 "Is a git repository: false" / 팀 GitHub 조직 line1thon-15에 저장소 4개(frontend·ai·backend·docs — 변경 기록 행) / `.gitignore:38-49`가 `.claude/`·`.codex/`·`.agents/`·`.artifacts/`·`AGENTS.md`·`CLAUDE.md`·하네스 스크립트를 제외하고 `docs/`는 추적 (architect 직접 확인) | git 있음, 이 폴더는 아직 git 저장소 아님, 원격 backend 저장소는 비어 있음 (인용) | 이 폴더를 backend 저장소의 작업 폴더로 쓴다 ("저장소와 브랜치" 절). git 초기화·원격 연결·push는 사용자가 한다(이번 설계 작업에서 하지 않음) |
| OS·셸 | Windows 11, PowerShell 5.1 + Git Bash | (인용) | 명령은 OS 무관하게 쓸 수 있는 형태(`python -m ...`)로 정한다 |
| 설치 허용 여부 (2026-11-06 갱신) | 사용자 원문 "필요한 건 추가 해" — 메인 세션이 A-1~A-7 분류("지금 필요: A-3 설치 허용, A-6 git 저장소 …")를 보여준 직후의 답 | **허용** — 메인 세션 해석: pip/uv·npm·Playwright 브라우저 설치 허용 (인용) | **"추가 설치가 필요하고 이미 허용됨" 행 적용** — 허용 범위: 이 PC에서 backend 저장소에 필요한 Python 패키지(아래 기술 스택). 설치 대상·이유는 기술 스택 표. frontend·ai 저장소의 설치는 각 담당 결정 |
| 팀원 환경 (6명) | 확인 안 됨 | 미확인 — 확인 방법: 각자 `python --version`, `node --version`, `npm --version` 출력 수집 [A-7 — 보류] | 기준 버전(Python 3.12+)으로 진행, 맞지 않는 팀원이 나오면 재검토 |
| 테스트 실행 수단 | pytest 설치 여부를 확인하지 않음 | 미확인 — 확인 방법: T-01에서 설치(허용됨) 후 스모크 실행 | 실제 하네스 성공은 T-01에서 검증 |
| frontend 저장소 실제 코드 (2026-11-06 신규) | 메인 세션 gh CLI 확인(인용): package.json — react ^19.1.0, react-dom ^19.1.0, react-router-dom ^7.6.0, vite ^7.0.0, @vitejs/plugin-react ^4.6.0, tailwindcss ^4.1.0, @tailwindcss/vite ^4.1.0. TypeScript 없음, 테스트 러너 없음, `.jsx` 파일, `vite.config.js`에 proxy 없음, README "VITE_API_URL=http://localhost:8080", `src/api/client.js` 원문은 ADR-0013 | 사실 (인용) | 백엔드 계약을 이 코드에 맞춘다(ADR-0012·ADR-0013). 프론트 테스트·E2E 러너가 없어 N-06 E2E는 프론트 담당의 구축이 필요 [A-11] |
| 브라우저 실물 확인 수단 | 메인 세션(Claude Code)에 Browser pane 도구(`mcp__Claude_Browser__*`: preview_start, navigate, read_page, computer 등)가 있고 이번 세션에서 외부 사이트 열람에 실제로 사용함 | 메인 세션: 사용 가능 (인용). 로컬 dev 서버 띄우기: 미검증. implementer·QA 서브에이전트의 도구 가용성: 미확인 | AGENTS.md "화면 검증 도구 실패 처리" 표 2행 — 서브에이전트에 도구가 없으면 메인 세션이 실제 확인하고 증거를 첨부한다. 화면은 frontend 저장소 코드를 로컬에서 띄워야 보이므로 프론트 저장소 체크아웃이 필요 |
| 배포 환경 | Vercel·Supabase MCP 연결이 세션에 존재(사용 여부 미정) | 미확인 — 계정·요금제·사용 여부 미확인 [A-2 — 보류] | 추천안(ADR-0007)으로 설계하고 T-27에서 확정 |
| Gemini API 키 | 확인 안 함 (실제 `.env` 읽기 금지 — AGENTS.md 시크릿 관리) | 미확인 | Gemini 키는 AI 서비스(ai 저장소)에만 필요(ADR-0011). backend 저장소의 자동 테스트는 키 없이 `AI_CLIENT=fake`로 돈다 |

### 설치 불허 시 대안

해당 없음 — 2026-11-06 설치 허용(위 표, 메인 세션 해석). 허용 해석이 틀렸다면 첫 초안의 대안 표(표준 라이브러리 `unittest`·`http.server`·`sqlite3`, E2E 자동화 불가로 N-06 미충족)를 다시 적용하고 사용자 선택을 받는다.

## 기술 스택

| 계층 | 선택 | 상태 | 선택 이유 (DECISIONS/ADR 참조) |
|---|---|---|---|
| 백엔드 언어 | Python (3.12 이상 호환, 기준 3.13) | 확정 (언어) | OQ 7 원문: AI "ai 파트가 파이썬 사용한다는데", 백엔드 "그리고 백엔드는 파이썬 형태로 진행하기로 했어"(PRD.md:320) |
| 백엔드 프레임워크 | FastAPI + Uvicorn (동기 엔드포인트) | 결정 (설치 허용됨) | Pydantic DTO로 API 규격 고정, OpenAPI 자동 문서가 팀 계약 확인 수단 — ADR-0002 |
| 백엔드–AI 구성 | ai 저장소 = 상태 없는 별도 HTTP 서비스, 백엔드는 `PracticeAI` 포트 + HTTP 어댑터·Fake 어댑터 | 결정 (설계) — AI 담당 합의 완료(2026-11-07 답변 원문 "동의합니다. AI 레포에서 별도 HTTP 서버(8081)를 운영하는 방식으로 진행하겠습니다." — A-8 해소). 사용자 승인은 Architecture 승인과 함께 | 팀 저장소·담당 분리와 일치, 백엔드에서 제공사 SDK 제거(N-10) — ADR-0011 |
| 백엔드→AI HTTP 클라이언트 | httpx | 결정 | FastAPI `TestClient`와 같은 라이브러리, `MockTransport`로 계약 테스트 — DECISIONS #45 |
| ORM·마이그레이션 | SQLAlchemy 2.x + Alembic, Postgres 드라이버 psycopg(v3) | 결정 (설치 허용됨) | ADR-0005 |
| DB (배포) | 관리형 PostgreSQL | 형태 결정, 서비스 [사용자 확인 필요] | PRD N-07 사용자 선택 원문 "Vercel + PaaS + 관리형 DB (Recommended)" — ADR-0005·ADR-0007 |
| DB (테스트·로컬) | SQLite (Python 내장) | 결정 | Docker 없음 — ADR-0005 |
| 비밀번호·PIN 해시 | Argon2id (`argon2-cffi`) | 결정 (설치 허용됨) | DECISIONS #16 |
| 설정 | `pydantic-settings` (환경 변수 → 설정 객체) | 결정 (설치 허용됨) | 환경 변수 단일 진입점(CodingRules "설정 및 상수") |
| 세션 | DB 저장 불투명 토큰 + httpOnly 쿠키, 프론트 쪽 `/api` 같은 출처 프록시 | 결정 (설계) — 프론트 합의 [A-11] | ADR-0013 |
| AI 제공사 | Gemini API — **ai 저장소(AI 서비스) 안에서만** 호출 | 제공사 확정(N-09), SDK·모델은 AI 담당 | ADR-0011. 현행 공식 Python SDK가 `google-genai`라는 것은 architect 기억(추정 — 이번 세션 미확인) |
| 프론트엔드 (사실) | React 19 + Vite 7 + JavaScript(.jsx) + Tailwind CSS v4 + React Router 7 | 사실 (인용) — 프론트 담당 소유 | ADR-0012 |
| TTS | 브라우저 내장 Web Speech API (프론트 구현) | 결정 (설계) → 프론트에 권고 | ADR-0008 |
| 콘텐츠 | 단서·시나리오·변형·진단: backend 저장소 JSON / 대체 문구·안전 규칙: ai 저장소 | 결정 (설계) | ADR-0010 갱신 메모, DECISIONS #46 |
| 단위·통합 테스트 (backend) | pytest + FastAPI `TestClient` + httpx `MockTransport` | 결정 (설치 허용됨) | ADR-0006 갱신 메모, DECISIONS #48 |
| 프론트 테스트·E2E | Vitest + React Testing Library / Playwright Test | 권고 — 프론트 담당 결정 [A-11] | N-06 "러너는 설계에서 확정" — 러너 종류는 Playwright로 정하되 구축은 frontend 저장소 |
| 패키지 관리 (backend) | `requirements.txt`·`requirements-dev.txt` (pip 또는 uv) | 결정 | DECISIONS #7 |
| 배포 | 프론트 Vercel / 백엔드·AI 각각 Python PaaS 웹 서비스(후보 Render) / 관리형 Postgres(후보 Neon·Supabase) | 형태 확정(N-07), 구체 서비스 [사용자 확인 필요 — A-2 보류, 추천안으로 진행] | ADR-0007(갱신 메모) |
| CI (backend) | GitHub Actions — `dev`·`main` 대상 PR에서 pytest | 결정 | DECISIONS #42 |

backend 저장소 설치 대상 (허용 범위 안): 런타임 `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic-settings`, `argon2-cffi`, `httpx`, `email-validator`(Pydantic `EmailStr`) / 개발 `pytest`. 이유는 위 표. 버전 고정은 T-01에서 실제 설치된 버전으로 `requirements*.txt`에 기록한다.

### 지원 브라우저·해상도 (N-01 "지원 브라우저·해상도 목록은 설계에서 확정")

| 구분 | 목록 |
|---|---|
| 브라우저 | Chrome 최신(Android·Windows·macOS), Safari 최신(iOS·iPadOS), Edge 최신(Windows) |
| 기준 해상도 (CSS px) | 모바일 360×800, 태블릿 768×1024, PC 1280×800 |
| 자동 검증 | Playwright Chromium 데스크톱 1280×800 + 모바일 에뮬레이션 360×800 — frontend 저장소에 권고 [팀 요청 F-6] |
| 수동 검증 | iOS Safari·태블릿은 T-52에서 실기기 또는 메인 세션 확인 (자동화 범위 밖) |

## 저장소와 브랜치 (2026-11-06 신규)

| 항목 | 결정 | 근거 |
|---|---|---|
| 이 폴더의 정체 | `C:\Projects\2026_line1thon` = line1thon-15/**backend** 저장소의 로컬 작업 폴더. 백엔드 코드는 저장소 **루트**의 `app/`·`alembic/`·`tests/`에 둔다 | 사용자 원문 "내가 접근할 곳은 backend 부분 쪽이야", DECISIONS #40 |
| 원격에 올라가는 것 | 백엔드 코드, `docs/`(이 설계 문서 포함 — 팀 규칙상 "백엔드 구현 상세 \| backend/docs"(인용)), `.env.example`. 하네스 파일은 `.gitignore`로 제외 | `.gitignore:38-49` |
| 다른 저장소 | frontend·ai·docs 저장소는 이 폴더에서 수정하지 않는다. 필요하면 각 담당에게 요청("팀원 요청 사항") | 담당 분리 |
| 팀 브랜치 컨벤션 | 팀 docs 저장소 원문(인용): "브랜치 전략: main(최종 데모) / dev(통합) / feature/*(작업). PR base는 dev입니다.", "main, dev에는 직접 push하지 않습니다.", "feature/기능명", "fix/버그명", "팀원 1명 이상 확인 후 merge", "API 응답 형식처럼 다른 파트에 영향이 가는 변경은 해당 파트 담당을 리뷰어로 지정", 커밋 "타입: 작업 내용" (feat/fix/style/refactor/docs/chore) | 이 저장소의 docs/GitWorkflow.md(main + feature, dev 없음)와 다르다 — GitWorkflow.md는 사용자 소유라 architect가 고치지 않는다 [A-9] |
| API 변경 리뷰 | 공개 API(A1~A19)·내부 API 규격을 바꾸는 PR은 팀 컨벤션대로 프론트·AI 담당을 리뷰어로 지정하고, 같은 PR 또는 같은 날 docs 저장소 정본도 갱신 | 위 컨벤션 원문, DECISIONS #43 |
| git 초기화·push | 이번 설계에서 하지 않음 — 사용자가 수행 | 메인 세션 지시 |

## 구조 개요 (2026-11-06 갱신 — backend 저장소 루트 기준)

```
line1thon-15/backend  (= C:\Projects\2026_line1thon)
├─ app/
│  ├─ main.py                 # 앱 팩토리, 라우터·예외 핸들러·미들웨어 등록
│  ├─ api/                    # HTTP 경계: 라우터, 요청/응답 DTO, 인증 의존성
│  ├─ services/               # 유스케이스 + Repository 포트(ports.py)
│  ├─ domain/                 # 순수 규칙: 출제 선택, 학년 제한, 정상 슬롯, 변형, 힌트, 배지, 지표, 신호등 매핑
│  ├─ repositories/           # SQLAlchemy 기반 포트 구현
│  ├─ db/                     # ORM 모델, 세션
│  ├─ ai_client/              # AI 서비스 호출 경계 (N-10) — 아래 "백엔드–AI 내부 API"
│  │  ├─ ports.py             # PracticeAI 포트 + 내부 API DTO (Pydantic)
│  │  ├─ http_client.py       # HttpPracticeAI — httpx를 쓰는 유일한 파일
│  │  ├─ fake.py              # FakePracticeAI — 결정적 응답, 테스트·E2E 기본
│  │  └─ factory.py           # AI_CLIENT=http|fake 로 구현 선택
│  ├─ content/                # 콘텐츠 로더·스키마 검증 + data/*.json (콘텐츠 담당 — OQ 3)
│  ├─ demo/                   # 예시 데이터(N-11) 적재 스크립트·데이터
│  └─ core/                   # 설정, 보안(해시·토큰), 오류 타입, 로깅, 요청 ID
├─ alembic/                   # 마이그레이션
├─ tests/
│  ├─ unit/                   # domain 순수 규칙, import 경계
│  ├─ integration/            # API + SQLite (IDOR·금지 필드 포함)
│  └─ contracts/ai/           # 내부 API 요청·응답 샘플 JSON + HttpPracticeAI 계약 테스트
├─ docs/                      # PRD·Tasks·Architecture·DECISIONS·adr (원격 추적)
├─ .github/workflows/ci.yml   # 백엔드 CI (T-01)
├─ requirements.txt
├─ requirements-dev.txt
├─ pyproject.toml             # pytest 설정 등 도구 설정만
├─ .env.example               # 플레이스홀더만 (T-01에서 변수 추가 — "시크릿과 환경 변수")
└─ .claude/launch.json        # 백엔드 dev 서버 실행 설정 (로컬 전용, .gitignore 제외 대상)
```

ai 저장소 권고 구조(AI 담당 결정 — [팀 요청 AI-1]): `app/main.py`(내부 API 라우터) / `app/practice/`(프롬프트·단서 틀 유지·검수·판정·피드백) / `app/safety/`(입·출력 필터) / `app/providers/{base,gemini,fake}.py`(제공사 SDK는 `gemini.py`에만) / `content/{fallbacks,safety_rules}.json` / `tests/`(N-04 안전 필터 세트 포함).

frontend 저장소: 기존 구조(`src/pages/` 피그마 프레임 1개당 파일 1개, `src/components/`, `src/api/client.js`)를 그대로 두고, 계약에 필요한 변경만 요청한다([팀 요청 F-1~F-4]).

## 모듈 경계와 책임 (2026-11-06 갱신)

backend 저장소(확정):

| 모듈 | 책임 (한 줄) | 의존 대상 | 담당 |
|---|---|---|---|
| app/api | HTTP 경계: 요청 검증(Pydantic), 쿠키 세션 → 주체 해석, DTO ↔ 서비스 입출력 변환, 오류 → HTTP 응답 | services, core | 백엔드 |
| app/services | 유스케이스(가입·로그인·아이 등록·재설정·첫 설정·연습·결과·성장·리포트·알림) 흐름 제어, 인가 판정 | domain, services/ports(Repository 포트), ai_client/ports, content | 백엔드 |
| app/domain | 프레임워크 없는 순수 규칙: 출제 선택(F-14 ②·F-17·F-18), 변형 선택(F-12), 힌트 단계, 연습 종료 판정(F-11 ④⑤⑥ — 2026-11-08, DECISIONS #80), 배지·연속 기록(F-28 ②③ — 2026-11-11, DECISIONS #90), 성장 지표(F-29 ⑤⑥ — 2026-11-11, DECISIONS #88), 한국 시간 날짜·기간 창 계산(DECISIONS #89), 신호등 등급 매핑(Y5 카드 값은 DECISIONS #120 — 2026-11-12, 지표 값은 PRD OQ 63 ② 미결) — 규칙은 "성장 계산 규칙" 절 | 없음 | 백엔드 |
| app/repositories | Repository 포트의 SQLAlchemy 구현 — SQL·ORM 코드는 여기에만 | db | 백엔드 |
| app/db | ORM 모델·엔진·세션 팩토리, Alembic 마이그레이션 | core(설정) | 백엔드 |
| app/ai_client | AI 서비스 호출 포트와 구현(HTTP·Fake), 응답 스키마 검증, 오류 → `AIUnavailableError` 변환. AI 제공사 SDK 없음 | core(설정), httpx(`http_client.py`만) | 백엔드 (계약은 AI 담당과 합의) |
| app/content | 단서·시나리오·변형 요소·진단 문항 JSON을 읽어 스키마 검증 후 읽기 전용 제공 | core | 백엔드(로더) + 콘텐츠(data — OQ 3) |
| app/demo | 시연 계정·예시 성장 기록·예시 안전 알림 적재(N-11, F-29 ④, F-41 ②) | services 또는 repositories | 백엔드 |
| app/core | 환경 변수 설정, 해시·토큰 생성, 오류 타입(AppError), 구조화 로깅, 요청 ID | 없음 | 백엔드 |

다른 저장소(계약만 확정, 내부는 권고):

| 저장소 | 책임 (한 줄) | 백엔드와의 계약 | 담당 |
|---|---|---|---|
| ai | 글 생성 전담(2026-11-06 분담 원칙): 상황 생성·상대역 대사·상황 변형·입출력 안전 필터(F-11 ②)·출제 전 검수(F-42)·찾음/놓침 판정(F-13 ④⑤ — 2026-11-11 PRD OQ 31 해소 규칙, DECISIONS #91)·피드백·힌트 문장·보호자 학습 요약 문장(선택: 아이 성장 요약·추천 이유 문장), Gemini 호출(N-09·N-10). 계산·저장은 하지 않음 | 백엔드–AI 내부 API [정본: docs 저장소] | AI |
| frontend | 화면 11개, 라우팅·가드, 화면 상태, TTS, 감정 온도계(서버 미전송) | 공개 API A1~A19, 쿠키·프록시 규칙 [정본: docs 저장소] | 프론트 |

## 데이터 흐름 (2026-11-06 갱신 — 3번 AI 호출 경로)

> **2026-11-11 메모 (AI 계약 채택 — 사용자 확정 2026-11-11, DECISIONS #96~#103 → #113~#115)**: 아래 3·4·5번의 AI 호출 이름은 옛 규격이다. 1차는 다음으로 읽는다 — 3번 A15: `PracticeAI.opening` → `variant`(백엔드가 값 지정) + `start`(검수는 AI `check_variant`, #102) / A17 계속: `next_turn` → `turn`(`safe_reply`면 세션 `stopped`, #99) / A17 종료: `judge`(요청 `messages`·`revealed_clue_ids`·`variant`, 검증 J1'~J4' — #100) / 4번 A18: `feedback`(`closing_line`은 마지막 카드 — #101) / 5번 G3: `SummaryAI.guardian_summary` → AI `summary` 영역마다 1회(#103). 종료 규칙(#80)·트랜잭션(#82·#85)·404·409 순서는 그대로. 상세는 "백엔드–AI 내부 API" 절의 "1차 내부 API v1 (2026-11-11 — AI 계약 채택)".

1. **보호자 가입 → 아이 연결 (F-01·F-02)**: G1 → `POST /api/v1/guardians`(api: DTO 검증) → services(이메일 소문자 정규화, 중복 확인, Argon2id 해시) → repositories(guardians 저장) → 세션 발급(auth_sessions에 토큰 해시 저장, 쿠키 설정) → G2 → `POST /api/v1/children`(동의 필수 검증, 보호자가 입력한 PIN 형식 검증) → PIN 해시 저장 + 연결 코드 생성 → 응답에 연결 코드만 담아 G2에 표시(PIN은 응답에 없음 — 2026-11-07 변경).
2. **아이 로그인 (F-03)**: Y1 → `POST /api/v1/auth/child/login` → 코드로 아이 조회 → PIN 해시 검증 → 세션 발급 → `first_login` = 첫 설정 미완료 여부 → Y2 또는 Y3.
3. **연습 (F-09·F-11~F-14·F-17·F-18·F-42)**: Y3 영역 선택 → Y4 진입 전 감정 온도계(F-25 — 프론트 상태만, 서버 전송 없음) → `POST /api/v1/practice/sessions` → services가 domain 출제 규칙으로 시나리오·변형·힌트 단계 결정 → `PracticeAI.opening`(운영: AI 서비스 `POST /internal/v1/practice/opening` — AI 서비스가 생성·안전 필터·출제 전 검수까지 하고 `review.passed`를 함께 반환) → 불통과면 services가 다음 후보 시나리오로 재시도, 후보 소진 시 `NO_SCENARIO_AVAILABLE` → practice_sessions·practice_turns 저장 → 첫 턴 응답. 이후 `POST .../turns`(A17)마다 선택 확인 → **백엔드 domain이 종료 여부를 정한다**(2026-11-08 PRD OQ 42 해소, DECISIONS #80 — 고른 선택지의 `judgment`와 아이 답 수만 사용, AI 신호 미사용): 계속이면 `PracticeAI.next_turn`(AI 서비스가 안전 필터 통과 출력만, 차단 시 대체 문구 + `substituted`) → 새 턴 저장 → 응답 `status: "in_progress"` + 다음 턴 / 종료면 `next_turn`을 부르지 않고(마무리 대사 없음 — PRD OQ 62 ① 사용자 답 "바로 결과 화면") `PracticeAI.judge`로 찾음/놓침 판정 → cue_results·`normal_outcome` 저장, 세션 `ended` → 응답 `status: "ended"`, `turn: null` → Y4가 Y5로 이동. 한 요청 안의 저장(선택 기록 포함)은 한 트랜잭션이며 AI 호출(`next_turn`·`judge`)이 실패하면 아무것도 저장하지 않고 503 `AI_UNAVAILABLE` — 아이는 같은 선택지로 다시 시도(DECISIONS #82). AI 서비스는 아무것도 저장하지 않는다.
4. **결과·다시 도전 (F-13·F-12)**: Y5 → `GET .../result` → 본인 세션(404)·종료(409) 확인 → 저장된 `cue_results`와 콘텐츠 `cues.json`으로 `found`·`missed` 단서 카드 구성(AI 미사용) → `PracticeAI.feedback`(저장된 `cue_results`·`normal_outcome`·대화 이력) → 응답 검증 후 `cards[]`로 배치, `level`은 백엔드 domain이 결정(2026-11-08 — 내부 API 표 "`feedback` 응답 → `PracticeResultView` 매핑" 행, DECISIONS #75) → `feedback` 실패·검증 실패면 503 `AI_UNAVAILABLE`(부분 응답 없음, Y5 에러 + 다시 시도) → "다시 도전" = `POST /practice/sessions {mode: "retry"}` → 같은 시나리오·같은 목표 단서, 변형 1개 이상 상이(domain).
4-1. **심화 연습 (F-48 — 2026-11-07 신규, 2026-11-07 PRD OQ 55 해소로 1차/2차 분리 — 사용자 확인 대상)**:
   - **1차 (PRD OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76 — 단 Y5-1의 A20 조건부는 DECISIONS #73, 위험 표현 안내는 DECISIONS #74로 사용자 확인 대상 그대로)**: Y5 → Y5-1(**새 API 요청 없음** — Y5가 이미 받은 A18 응답(본인·종료 세션임이 확인된 결과와 단서 카드)을 프론트 상태로 넘겨 쓴다. 새로고침·주소 직접 입력으로 그 상태가 없으면 Y5로 보낸다 — Y5가 A18로 다시 불러오며 404·409·에러를 처리. A18은 요청마다 `PracticeAI.feedback`을 호출하므로(4번) 심화 연습 화면에서 A18을 다시 요청하지 않는다. A20은 조건부, 아래 API 규격) → Y5-2 글 입력 또는 Y5-3 말하기(브라우저가 글자로 변환 — 음성은 우리 서버로 오지 않음, ADR-0014) → 제출하면 **서버 요청 없이** Y5-4로 화면 이동(답변 글은 프론트 메모리 상태로만 넘기고 브라우저 저장소에 남기지 않음) → Y5-4 표시(내용은 PRD OQ 50 ③ — 후보 (a) 고정 문구 = 프론트 상수, (b) Y5 단서 설명 다시 보기 = Y5가 받은 A18 응답(프론트 상태), (c) 아이 답변 다시 보기 = 프론트 상태. 어느 후보·조합도 답변을 서버로 보낼 필요가 없다) → Y5-5 다음 단계. 1차에는 아이가 쓴 글이 우리 서버·AI 서비스·Gemini 어디로도 가지 않는다(남는 외부 경로는 브라우저 음성 인식뿐 — D-9). 심화 연습 화면이 새로 일으키는 AI 호출 없음(상태가 없어 Y5로 돌아가면 Y5의 기존 A18 호출만 일어남).
   - **[2차 — T-82]**: Y5-2·Y5-3 제출 → `POST .../deep/answers {answer_text}`(A21) → services가 세션의 `ScenarioSpec`·`cue_results`를 다시 조립해 `PracticeAI.deep_feedback` 호출(AI 서비스가 입력 필터 → LLM → 출력 필터) → 피드백 문장 응답 → Y5-4 표시. 저장 여부(A-17)는 2차 착수 전 결정 — 기본 권고 A안(저장 안 함)이면 `answer_text`·피드백은 요청 처리 중 메모리에만 둔다.
5. **성장·리포트 (F-28~F-31·F-41)**: Y8 `GET /api/v1/me/growth`, G3 `GET /api/v1/children/{id}/report` → services가 cue_results·practice_sessions·guardian_notices를 읽어 domain 규칙으로 집계(배지·연속 기록·지표 3개 — "성장 계산 규칙" 절. 지표 (다)만 `PracticeRepo.first_answer_judgments`로 `practice_turns` `turn_index` 0의 고른 선택지 `judgment` 범주값을 받는다 — 보호자 경로의 유일한 `practice_turns` 읽기 예외, 2026-11-11 DECISIONS #87·ADR-0016) → (G3, 2026-11-06 추가, 2026-11-07 갱신) 기록이 기준 미만이면 AI를 호출하지 않고 `summary.status = "insufficient"`(A-18), 아니면 집계값만으로 `LearningSummaryInput`(영역별 연습 횟수·찾은/놓친 단서 수·직전 기간 값, 찾은 단서·약점 단서 목록, 지표)을 만들어 `SummaryAI.guardian_summary` 호출(실패·검증 실패 시 `summary.status = "unavailable"`) → 응답 DTO(금지 필드 없음)로 변환. 시연 계정 데이터는 demo 적재 스크립트가 같은 테이블에 `origin = demo_seed`로 넣는다.

## 데이터 모델과 인터페이스

implementer는 여기 정의된 규격만 사용한다. 값이 [OQ n]인 부분은 그 답이 나오기 전 임의로 채우지 않는다.

### 공통 값 타입

| 타입 | 값 | 근거 |
|---|---|---|
| Grade | `E6, M1, M2, M3, H1, H2, H3` (초6~고3). OQ 26 잔여(하한)에서 초5가 포함되면 `E5` 추가 — 목록은 설정 상수 1곳 | PRD.md:30 라운드 1 "초6~고등학생까지", [OQ 26] |
| 고등학생 판정 | `grade ∈ {H1, H2, H3}` | F-14 ② |
| Area | **2026-11-11 사용자 확정(DECISIONS #112 — 답 "AI ID로 맞춤 (추천)")**: `scam`(사기), `identity_lending`(명의 빌려주기), `friend_pressure`(친구의 무리한 부탁) — AI 콘텐츠 ID와 같음, 내부 API·공개 API·DB 공통. 공개 API 값이 바뀌므로 프론트 알림 필요. ~~`name_lending`·`friend_request`~~(옛 값 — 쓰지 않음) | F-09 ①, 2026-11-03 결정, DECISIONS #108·#112 |
| ScamSubtype | `game_item`, `allowance`, `high_paying_job` (scam에만) | F-14 ① |
| SignalLevel | `red`(위험) / `yellow`(내부 등급 '확인 필요', 화면 문구 "믿는 사람에게 물어봐요" — 2026-11-12 PRD OQ 24 사용자 확정, DECISIONS #121. 문구는 프론트가 표시하고 API 값은 `yellow` 그대로) / `green`(괜찮아 보여요) | F-26, PRD OQ 24 |
| ChoiceKind (2026-11-11 — 옛 이름 ChoiceJudgment, DECISIONS #97 → 사용자 확정 #115) | AI 계약 값 `correct` / `doubtful` / `other`. 대응: PRD '의심'(거절·확인·믿는 사람에게 묻기) = `correct`, '중립' = `doubtful`, '믿음'(그대로 따름) = `other`. **AI `doubtful`("의심되는 답")은 PRD '의심' 태그가 아니다.** 아래 옛 설명의 `suspicious`는 `correct`로 읽는다. 클라이언트로 보내지 않음(AI 공지 원문 "kind는 화면에 보여 주지 마세요.") |
| ChoiceJudgment (옛 이름 — 위 행으로 대체) | `suspicious` / `trusting` / `neutral` — 선택지에 붙는 내부 태그, 클라이언트로 보내지 않음. 연습 종료(DECISIONS #80)·찾음/놓침 판정(F-13 ④⑤, DECISIONS #91)·지표 (다)(F-29 ⑤, DECISIONS #87)의 입력 | F-17 ② "'괜찮아'를 고르면", F-13 ④⑤(2026-11-11 PRD OQ 31 해소) |
| FontScale | `normal`, `large`, `xlarge` | F-05 |
| AppType | 콘텐츠 `variants.json`이 정의하는 앱 유형 ID 목록(게임·SNS 종류) — 서버가 목록 밖 값 거부 | F-08 |
| 연결 코드 | 6자, 혼동 문자 제외 영숫자 `23456789ABCDEFGHJKMNPQRSTUVWXYZ`, 대소문자 무시, 전역 유일 | 설계 기본값 [A-5 — 보류, 기본값으로 진행] |
| PIN | 숫자 4자리, **보호자가 입력**(등록 A7·재설정 A9 — 2026-11-07 변경, 서버 생성 폐지), 서버는 형식 검증 후 Argon2id 해시만 저장. 쉬운 PIN(예: 1234) 제한 없음 — 운영 전 과제 | 2026-11-07 사용자 "보호자 입력으로 반영", DECISIONS #59 |
| 시각 | UTC `timestamptz` 저장, API는 ISO 8601(UTC) 문자열. **날짜 단위 집계**(연속 기록·지표 기간·요약 기간 — 2026-11-11)는 저장값을 바꾸지 않고 계산할 때만 한국 시간 날짜로 변환: `SERVICE_TZ` = UTC+09:00 고정 오프셋(설정 상수 1곳), 날짜 = `ended_at.astimezone(SERVICE_TZ).date()`, 오늘 = 주입 `Clock` 기준. API의 날짜 값(`MetricView.trend[].date`, `LearningSummaryInput.period`)은 이 한국 시간 날짜(`YYYY-MM-DD`) | F-28 ③ "(한국 시간 날짜)", PRD planner 해석 8(사용자 확정), DECISIONS #89 |
| ID | UUID v4 (SQLAlchemy `Uuid` 타입 — Postgres·SQLite 공통) | ADR-0005 |

### 엔티티 (DB 테이블)

| 엔티티/인터페이스 | 규격 (필드·타입·제약) | 사용 모듈 |
|---|---|---|
| guardians | `id` UUID PK / `email` varchar(254) unique, 소문자 정규화 / `password_hash` text (Argon2id) / `created_at` timestamptz | services(auth), repositories |
| children | `id` UUID PK / `guardian_id` UUID FK→guardians, not null, index / `nickname` varchar(20) not null (1~20자) / `grade` Grade not null / `link_code` varchar(6) unique not null / `pin_hash` text not null / `consent_agreed_at` timestamptz not null / `consent_version` varchar(20) not null / `onboarding_completed_at` timestamptz null (null = 첫 로그인 처리 대상) / `start_difficulty` smallint null (단계 수는 [OQ 14]) / `created_at`. **진단 여부·IQ 열 없음** (F-02 ③) | services(child, auth, report), repositories |
| child_settings | `child_id` UUID PK·FK / `font_scale` FontScale default `normal` / `high_contrast` bool default false / `tts_enabled` bool default false / `trusted_contact_name` varchar(20) null / `trusted_contact_phone` varchar(20) null (숫자·`-`·`+`만) / `favorite_apps` JSON list[AppType] default [] / `updated_at` | services(onboarding, home), repositories |
| auth_sessions | `id` UUID PK / `token_hash` char(64) unique (SHA-256 of 토큰) / `subject_type` enum(`guardian`,`child`) / `subject_id` UUID / `created_at` / `expires_at` / `revoked_at` null | api(의존성), services(auth) |
| practice_sessions | `id` UUID PK / `child_id` FK index / `mode` enum(`area`,`mission`,`retry`) / `area` Area / `subtype` ScamSubtype null / `scenario_id` varchar(40) (콘텐츠 ID) / `is_normal` bool / `target_cue_ids` JSON list[str] (정상 상황이면 []) / `variant` JSON `{tone, platform, persona}` / `retry_of` UUID FK self null / `draw_index` int null (새 출제 순번 — retry는 null) / `hint_level` smallint / `status` enum(`in_progress`,`ended`) / `normal_outcome` enum(`trusted_correctly`,`over_warned`) null (정상 상황만 — 2026-11-11 PRD OQ 31 해소: 종료된 정상 상황은 항상 둘 중 하나(F-13 ⑤), 위험 상황·진행 중은 null. `judge` 응답 검증 J2로 강제 — DECISIONS #91) / `origin` enum(`live`,`demo_seed`) / `started_at` / `ended_at` null. **2026-11-11 변경(AI 계약 채택 — DECISIONS #98·#99, 사용자 확정 2026-11-11 #113·#115)**: `scenario_id` varchar(64)(AI 스키마 상한) / `target_cue_ids` = 콘텐츠의 그 시나리오 단서 ID 전체(시나리오 순서) / `variant` JSON = AI `Variant` 객체 전체(`base_scenario_id, platform, tone, context, title, child_setup, opening_line, ai_role{name, persona, tone}, clues[{id, at_opening, reveal_when, reveal_line}]`) — 받은 그대로 저장해 같은 세션의 `start`·`turn`·`judge`·`feedback`에 보낸다 / 신규 `scenario_title` varchar(80)·`child_setup` varchar(300)·`ai_role_name` varchar(40)(`start` 응답 값 — A16 복구·`TurnView.speaker_name`) / `status`에 `stopped` 추가(safe_reply 즉시 중단 — 집계 제외, `ended_at`에 중단 시각) | services(practice, growth, report), domain(입력) |
| practice_turns | `id` UUID PK / `session_id` FK / `turn_index` int, unique(session_id, turn_index) — 첫 대사(`opening`)가 0, 이후 1씩 증가(2026-11-08 명시, DECISIONS #80 — 턴 `turn_index`에 답하면 아이 답 수는 `turn_index + 1`. 위험 상황 세션은 최대 4행) / `ai_line` text (안전 필터 통과 또는 대체 문구) / `choices` JSON list[`{id, text, judgment, cue_ids}`] / `chosen_choice_id` varchar(8) null / `substituted` bool (필터 차단 대체 여부) / `created_at`. **보호자용 API는 이 테이블을 읽지 않는다** (F-30 ③) — **예외 1개(2026-11-11, DECISIONS #87·ADR-0016, 사용자 답 "방법 1로 가는 방향으로 가보자")**: 성장 지표 (다)(F-29 ⑤) 집계용 리포지토리 메서드 `PracticeRepo.first_answer_judgments(child_id, ended_from, ended_to)`(이름 권고) 하나만 `turn_index = 0` 행의 `session_id`·`chosen_choice_id`·`choices`를 SELECT(`ai_line`은 SELECT 금지)하고, `choices` JSON은 리포지토리 안에서 파싱해 고른 선택지의 `judgment`만 꺼낸 뒤 버린다. 반환은 `FirstAnswerJudgment{session_id, judgment: ChoiceJudgment}` 목록뿐(문자열 내용 필드 없음). 대상은 `status = ended` 세션. A19·A11이 같이 쓰며, 보호자 응답·요약 입력에는 비율 값만 나간다(대사·선택지 문장·`chosen_choice_id`·`judgment` 0건 — F-30 ②③). 그 밖의 보호자 경로 코드는 이 테이블을 읽지 않는다. 강제는 테스트 전략 R1~R4. 보존 기간 [OQ 32]. **2026-11-11 사용자 확정(DECISIONS #93 — 위 예외·R1~R4)**. **2026-11-11 변경(AI 계약 채택 — DECISIONS #97·#98, 사용자 확정 2026-11-11 #115)**: `choices` JSON = `[{id, text, kind: ChoiceKind}]`(`judgment`·`cue_ids` 없음) / 신규 `target_clue_id` varchar(64) null(그 턴 선택지가 다루는 단서 — AI 응답값) / 신규 `revealed_clue_ids` JSON list[str](그 턴 응답 기준 누적값) / 신규 `ai_status` enum(`ok`,`blocked`,`safe_reply`) — 턴 0은 `ok` / `safe_reply` 턴은 `choices` [], `ai_line` = 백엔드 고정 문구 `safety_stop.json` `message`의 멈춘 시점 값(AI `reply`는 저장하지 않음 — DECISIONS #118). 예외 메서드 반환은 `FirstAnswerKind{session_id, kind}`(이름 권고, 지표 (다) 분자 = `kind = correct`). 요청마다 이 행들로 AI `messages`를 다시 만든다(내부 API "상태 재구성" 행) | services(practice, growth·report는 위 메서드만) |
| cue_results | `id` UUID PK / `session_id` FK / `child_id` FK index (집계용) / `cue_id` varchar(40) / `outcome` enum(`found`,`missed`) / `recorded_at`. **2026-11-11(AI 계약 채택 — 사용자 확정 2026-11-11 #115)**: `cue_id` varchar(64). AI `judge`의 `not_shown`은 저장하지 않는다 — **사용자 확정(2026-11-11 "드러난 단서만 판정 (추천)", DECISIONS #109 — ADR-0018 N1)**. 이 테이블 = 드러난 단서의 판정(`found`·`missed`)만, `not_shown` = `practice_sessions.target_cue_ids` − 이 테이블로 복원 가능 — `outcome` enum 그대로 | services(practice, growth, report), domain(지표·약점) |
| guardian_notices | `id` UUID PK / `child_id` FK index / `kind` enum(`safety`,`trusted_contact`) / `level` SignalLevel(`red`·`yellow`만) null / `area` Area null / `channel` enum(`call`,`sms`) null (trusted_contact만) / `origin` enum(`demo_seed`,`live`) / `occurred_at`. **CHECK 제약(2026-11-11 PRD OQ 36 해소, DECISIONS #92)**: `kind = 'safety'`이면 `level`·`area` NOT NULL·`channel` NULL / `kind = 'trusted_contact'`이면 `level`·`area` NULL·`channel` NOT NULL. **본문·원문·이미지·감정 열이 없다** — 원문을 담을 자리가 구조적으로 없음 (F-41 ③). 안전 알림 항목은 발생 시각(`occurred_at`)·위험도(`level`)·영역(`area`)으로 확정(F-41 ④) — **열 추가 금지**(단서 범주·문장 설명 포함, F-41 ⑤). 원문·마스킹 텍스트·이미지·감정 값은 어떤 경우에도 추가 금지 | services(notice, report), demo |
| (저장하지 않음) 감정 온도계 | 서버 테이블·API 필드 없음. 프론트 컴포넌트 상태로만 존재 (F-25 ③, N-05) | frontend |
| (저장하지 않음) 배지·연속 기록 | 1차는 practice_sessions·cue_results에서 매 요청 계산 — 2026-11-11 PRD OQ 13 일부 해소 후에도 유지(DECISIONS #28·#90: 두 조건 모두 누적 세션에서 다시 계산해도 같은 값, "획득 시점 고정" 요구 없음). 조건은 "성장 계산 규칙" 절. 보존 기간(OQ 32)이 옛 세션을 지우게 정해지면 테이블 추가를 architect에 요청(D-12) | domain, services(growth, home) |

### API 규격 (HTTP, 접두사 `/api/v1`, JSON) [정본: docs 저장소]

인증: 세션 쿠키 `sid`(HttpOnly, SameSite=Lax, Path=/api, 운영은 Secure) — ADR-0013. 프론트는 같은 출처 상대 경로(`/api/v1/...`)로만 호출한다(교차 출처 호출에는 쿠키가 실리지 않고 백엔드는 CORS를 켜지 않는다). 주체는 항상 세션에서 꺼내며, **아이 API는 경로·본문으로 아이 ID를 받지 않는다**. 보호자 API의 `{child_id}`는 매 요청 소유 확인. **모든 성공 응답은 JSON 본문을 가진다(204 없음 — DECISIONS #38)**.

| # | 메서드·경로 | 주체 | 요청 DTO | 응답 DTO (성공) | 주요 오류 코드 | 요구사항 |
|---|---|---|---|---|---|---|
| A1 | `GET /health` | 없음 | — | `{status:"ok", db:"ok"}` | 503 `DB_UNAVAILABLE` | 배포 헬스체크 |
| A2 | `POST /guardians` | 없음 | `{email: EmailStr, password: str(8~128)}` | 201 `{guardian_id}` + 세션 쿠키 (가입 즉시 로그인 상태) | 409 `EMAIL_TAKEN`, 422 `VALIDATION_ERROR` | F-01 ①② |
| A3 | `POST /auth/guardian/login` | 없음 | `{email, password}` | 200 `{guardian_id, has_children: bool}` + 쿠키 | 401 `INVALID_CREDENTIALS` (이메일 없음/비밀번호 틀림 구분 안 함) | F-01 ③ |
| A4 | `POST /auth/child/login` | 없음 | `{link_code: str(6), pin: str(4, 숫자)}` | 200 `{first_login: bool}` + 쿠키 | 401 `INVALID_CODE_OR_PIN` (코드/PIN 중 무엇이 틀렸는지 구분 안 함) | F-03 ①② |
| A5 | `POST /auth/logout` | 보호자·아이 | — | 200 `{ok: true}` (세션 revoke, 쿠키 삭제) — 2026-11-06 204에서 변경 | — | — |
| A6 | `GET /auth/me` | 보호자·아이 | — | 보호자 `{role:"guardian", guardian_id, email}` / 아이 `{role:"child", nickname, grade, onboarding_completed: bool, display:{font_scale, high_contrast, tts_enabled}}` | 401 `UNAUTHENTICATED` | 가드, F-05 적용 |
| A7 | `POST /children` | 보호자 | `{consent_agreed: true, consent_version: str, nickname: str(1~20), grade: Grade, pin: str(4, 숫자만)}` — PIN은 보호자가 입력(2026-11-07 변경) | 201 `{child_id, nickname, grade, link_code}` — 연결 코드는 서버가 생성해 등록 완료 응답에 담음, PIN은 응답에 없음(2026-11-07 변경) | 422 `CONSENT_REQUIRED`, 422 `VALIDATION_ERROR` | F-02 ①②③ |
| A8 | `GET /children` | 보호자 | — | `{children:[{child_id, nickname, grade}]}` (자기 아이만) | — | G2 빈 값, `/guardian` 분기 |
| A9 | `POST /children/{child_id}/pin-reset` | 보호자 | `{pin: str(4, 숫자만)}` — 보호자가 새 PIN 입력(2026-11-07 변경) | 200 `{ok: true}` — PIN 평문을 응답에 담지 않음(2026-11-07 변경). 해당 아이의 기존 세션 전부 revoke 유지 | 404 `CHILD_NOT_FOUND`, 422 `VALIDATION_ERROR` | F-04 |
| A10 | `POST /children/{child_id}/link-code` | 보호자 | — | `{link_code}` (기존 세션 전부 revoke) | 404 `CHILD_NOT_FOUND` | F-04 |
| A11 | `GET /children/{child_id}/report` | 보호자 | — | `GuardianReport` (아래) | 404 `CHILD_NOT_FOUND` | F-30 ①②③④, F-31, F-41 ②③, F-23 ③ |
| A12 | `PUT /me/onboarding` | 아이 | `{display:{font_scale, high_contrast, tts_enabled}, trusted_contact:{name, phone}, diagnosis_answers:[{question_id, option_id}] (3개), favorite_apps:[AppType]}` | `{start_difficulty}` (onboarding_completed_at 설정) | 422 `VALIDATION_ERROR` | F-05·F-06·F-07·F-08 (믿는 사람 형식은 [OQ 8]) |
| A13 | `GET /me/home` | 아이 | — | `{areas:[{area}], badges:[BadgeView], streak_days:int, trusted_contact:{name, phone}\|null}` | 401 | F-09 ①, F-23 ①, F-28 |
| A14 | `POST /me/trusted-contact-events` | 아이 | `{channel:"call"\|"sms"}` | 200 `{ok: true}` (guardian_notices에 `trusted_contact` 기록) — 2026-11-06 204에서 변경 | — | F-23 ③ |
| A15 | `POST /practice/sessions` | 아이 | `{mode:"area", area}` \| `{mode:"mission"}` \| `{mode:"retry", retry_of: session_id}` | 201 `PracticeSessionView` | 409 `NO_SCENARIO_AVAILABLE`, 503 `AI_UNAVAILABLE`, 404 `SESSION_NOT_FOUND`(retry_of가 남의 것) | F-09 ①, F-10, F-11, F-12, F-13 ③, F-14, F-17, F-18, F-42 |
| A16 | `GET /practice/sessions/{id}` | 아이(본인 세션만) | — | `PracticeSessionView` (현재 턴 — 새로고침 복구. 종료된 세션이면 `status: "ended"`, `turn: null` — 2026-11-08, DECISIONS #82) | 404 `SESSION_NOT_FOUND` | Y4 |
| A17 | `POST /practice/sessions/{id}/turns` | 아이(본인) | `{choice_id}` | `PracticeSessionView` (2026-11-08 `TurnView`에서 변경 — DECISIONS #82): 계속이면 `status: "in_progress"` + `turn` = 다음 턴, 종료면 `status: "ended"` + `turn: null`(마무리 대사 없음 — PRD OQ 62 ①). 종료 여부는 백엔드 domain이 정한다(DECISIONS #80). 처리 순서: 본인 세션(404) → 종료 세션(409) → 현재 턴의 선택지(422) → 종료 판정 → `next_turn` 또는 `judge`. 저장은 한 트랜잭션 — AI 실패면 선택 기록도 저장하지 않음(같은 `choice_id`로 다시 시도 가능) | 409 `SESSION_ENDED`, 422 `INVALID_CHOICE`, 503 `AI_UNAVAILABLE`(`next_turn` 또는 종료 시 `judge` 실패) | F-11 ①②④⑤⑥ |
| A18 | `GET /practice/sessions/{id}/result` | 아이(본인) | — | `PracticeResultView` | 409 `SESSION_NOT_ENDED`, 404, 503 `AI_UNAVAILABLE`(내부 `feedback` 실패·응답 검증 실패 — 부분 응답 없음, 2026-11-08 명시, DECISIONS #75) | F-13 ①②, F-26 |
| A19 | `GET /me/growth` | 아이 | — | `GrowthView` | — | F-28, F-29 ①②③④ |
| A20 (2026-11-07 신규, 2026-11-07 **조건부로 변경** — 사용자 확인 대상) | `GET /practice/sessions/{id}/deep` | 아이(본인) | — | 200 `DeepEntryView` — 심화 연습 진입(Y5-1). 기본 연습이 끝난 세션에서만. **1차 기본안: 만들지 않는다** — 현재 골격 `{session_id, available}`은 Y5가 이미 받은 A18 응답(본인 세션 확인 404·종료 전 409, 단서 카드)과 겹친다. Y5-1은 그 응답을 프론트 상태로 넘겨 쓰고, 상태가 없으면 Y5로 보낸다(데이터 흐름 4-1번). 감수: 새로고침·주소 직접 입력 시 Y5-1에 바로 머물 수 없고 Y5를 거친다. PRD OQ 50 ①②의 답이 서버만 줄 수 있는 내용(예: 서버가 고르는 질문)을 요구할 때만 이 행을 1차로 되살린다(DECISIONS #73) | 409 `SESSION_NOT_ENDED`, 404 `SESSION_NOT_FOUND` | F-48 ① |
| A21 (2026-11-07 신규) **[2차 — T-82, 2026-11-07 PRD OQ 55 해소]** | `POST /practice/sessions/{id}/deep/answers` | 아이(본인) | `{answer_text: str(1~500자)}` — 글로 답하기(Y5-2)와 말로 답하기(Y5-3, 브라우저에서 바뀐 글)가 **같은 요청**. 다른 필드는 거부(`extra="forbid"` → 422) — 감정 온도계 값·음성 데이터가 들어올 자리 없음(F-48 ③⑥) | 200 `DeepFeedbackView` | 409 `SESSION_NOT_ENDED`, 404, 422 `VALIDATION_ERROR`(값은 `details`에 넣지 않음), 503 `AI_UNAVAILABLE`(AI 실패 — 프론트가 입력 유지 후 다시 시도) | F-48 ② [2차]·③·⑤ [2차]·⑥ — **1차에는 만들지 않는다(PRD OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76)**: 1차 Y5-2·Y5-3 제출은 서버 요청 없이 Y5-4로 이동(데이터 흐름 4-1번). 규격은 2차 T-82가 그대로 쓰도록 남긴다. 예외: PRD OQ 50 ⑤가 1차 "저장"으로 정해지면 A21을 AI 호출 없는 제출 엔드포인트로 1차에 둔다 — 그때 1차 응답 형태와 A-17 B안 테이블은 새 결정으로 정한다(지금 정하지 않음, DECISIONS #72) |
| A22 (2026-11-07 신규, **조건부**) | `GET /practice/sessions/{id}/deep/result` | 아이(본인) | — | 200 `DeepFeedbackView` — **답변을 저장하는 안(A-17 B안)일 때만** 둔다. 저장하지 않는 안(A안·권고)에서는 Y5-4가 A21 응답을 그대로 표시하고 이 엔드포인트는 만들지 않는다. **1차(PRD OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76)**: 1차에는 답변이 서버로 오지 않아 저장할 대상이 없다 → 1차에는 만들지 않는다. A-17 판단은 2차(T-82) 착수 전으로 넘긴다 | 404 | F-48 ② |
| A23 (2026-11-07 신규, **조건부**) | `POST /practice/sessions/{id}/deep/next` | 아이(본인) | OQ 50 ④ 답 이후 확정 | OQ 50 ④ 답 이후 확정 | — | F-48 ⑦ — 다음 단계(Y5-5) 선택지가 화면 이동뿐이면(예: 다시 연습 = A15, 홈 = A13, 성장 = A19) 이 엔드포인트는 만들지 않는다. 선택을 서버에 기록하거나 새 출제가 필요할 때만. 2026-11-07 PRD OQ 55·59 판단 후에도 조건 그대로(아이 답변과 무관 — OQ 50 ④에만 의존) |

감정 온도계(F-25) 엔드포인트는 없다 — 의도된 부재다. 심화 연습(A20~A23)의 요청에도 감정 값 필드는 없다(F-48 ⑥).

### 응답 DTO

| DTO | 필드 |
|---|---|
| PracticeSessionView | `{session_id, mode, area, is_retry: bool, status: "in_progress"\|"ended", turn: TurnView\|null}` — `turn`은 `status = "in_progress"`이면 아이가 답할 현재 턴, `"ended"`이면 `null`(2026-11-08 — A15·A16·A17 공통, DECISIONS #82). 종료 사유(의심 답 / 4번째 답) 필드는 없다 — PRD OQ 62 ②(보류)가 표시를 요구하면 하위 호환 추가. **2026-11-11 사용자 확정(DECISIONS #99 → #113 "이대로 (추천)" — PRD F-11·Y4 상태 갱신은 planner)**: `status`에 `"stopped"` 추가 — AI `turn`이 `safe_reply`를 주면 `turn` = 안내 턴(`choices: []`, `hint: null`)으로 채워 Y4가 안내를 보이게 한다. `stopped` 세션은 결과(Y5)·다시 도전 없음. **2026-11-11 PRD OQ 64 사용자 답 "고정 문구+홈, 알림 없음 (추천)"(DECISIONS #118)**: 안내 턴의 `ai_line` = 백엔드 고정 문구(AI 문장 아님), `substituted: false`, `speaker_name`·`platform`은 세션 값 그대로 — 형태 변경 없음 |
| TurnView | `{turn_index, speaker_name, platform, ai_line, choices:[{id, text}], hint: str\|null, substituted: bool}` — 선택지의 `judgment`·`cue_ids`와 `target_cue_ids`·`is_normal`은 **보내지 않는다**(정답 노출 방지). **`is_terminal` 삭제(2026-11-08, DECISIONS #82)** — 화면에 보이는 턴은 항상 답할 턴이고, 종료는 `PracticeSessionView.status`로 알린다 |
| CueCard | `{cue_id, label, sentence}` — label·sentence는 콘텐츠 쉬운 말 1문장 (F-26 "1문장 1카드") |
| PracticeResultView | `{session_id, found:[CueCard], missed:[CueCard], normal_outcome: "trusted_correctly"\|"over_warned"\|null, cards:[{level: SignalLevel, sentence}], can_retry: bool}` — 형태는 그대로(2026-11-08 매핑 정의, 하위 호환 변경 없음). `found`·`missed`는 백엔드가 `cue_results`와 콘텐츠로 만든 `CueCard`(AI 미사용), `cards[]`는 내부 `feedback` 응답에서만 만든다. 배치·`level` 결정·검증·실패 처리는 내부 API 표 "`feedback` 응답 → `PracticeResultView` 매핑" 행(DECISIONS #75). `cards[].level`의 키→값은 같은 매핑 행 ③(2026-11-12 사용자 확정 — DECISIONS #120·#121). `normal_outcome`은 정상 상황이면 항상 non-null, 위험 상황이면 null(2026-11-11, DECISIONS #91) |
| BadgeView | `{badge_id, area\|null, label}` — 2026-11-11(PRD OQ 13 일부 해소, DECISIONS #90): 1차 배지는 영역별 "혼자 할 수 있어요" 하나뿐 — `badge_id = "independent:{area}"`, `area`는 항상 값 있음, `label`은 설정 상수. 형태는 그대로(`area\|null` 유지 — 하위 호환). 조건은 "성장 계산 규칙" 절 |
| MetricView | `{metric_id, label, status:"ok"\|"insufficient", level: SignalLevel\|null, current: number\|null, previous: number\|null, trend:[{date, value}]}` — `insufficient` = "비교 불가" 안내 (F-29 ②⑥, F-31). 2026-11-11(PRD OQ 12 해소, DECISIONS #88): `metric_id` ∈ `missed_ratio`·`first_seen_accuracy`·`ahead_of_ai_ratio`, `label`은 설정 상수, 값은 0~1 비율. `ok`이면 `current`·`previous` 둘 다 숫자이고 `trend` = 두 기간 2점(`date` = 각 기간 마지막 한국 시간 날짜, 오래된 순). `insufficient`이면 `current`·`previous` null, `trend` [] — 숫자를 하나도 싣지 않는다(F-29 ⑥ "숫자 대신"). `level`은 PRD OQ 63 답 전까지 항상 null. 계산식은 "성장 계산 규칙" 절. 검증되지 않은 능력 점수·자립 보증 수치 필드 없음 (F-29 ③) |
| GrowthView | `{areas:[{area, practice_count, badges:[BadgeView]}], streak_days, needs_practice_cues:[CueCard], metrics:[MetricView]}` — (선택, 2026-11-06) 아이용 성장 요약이 요구사항으로 확정되면(PRD OQ 49 — Y8에 AI 요약을 넣을지) `summary:{sentences:[str]}\|null` 추가 |
| GuardianReport | `{child:{child_id, nickname}, areas:[{area, practice_count, last_practiced_at\|null}], weak_cues:[{cue_id, label}], notices:[NoticeView], metrics:[MetricView], summary: GuardianSummaryView}` — `summary`는 2026-11-06 추가(F-47 보호자 학습 요약, N-12 — 생성 T-75, 백엔드 T-76, 표시 T-77). 2026-11-07 형태 변경(사용자 확인 대상): `null` 대신 아래 `GuardianSummaryView`로 항상 채운다 — 요약 실패와 기록 부족(F-47 ⑥, G3 빈 값·에러 상태)을 프론트가 구분해야 하므로. 요약 실패여도 나머지 필드는 정상 |
| GuardianSummaryView (2026-11-07 신규 — 사용자 확인 대상) | `{status:"ok"\|"insufficient"\|"unavailable", unit:"overall"\|"area", items:[{area: Area\|null, sentences:[str] (1~2개)}]}` — `ok`일 때만 `items`가 1개 이상, 그 외는 `[]`. `insufficient` = 기록 부족(F-47 ⑥ "아직 기록이 적어요" 안내, AI 미호출 — 기준 [A-18]), `unavailable` = AI 실패·검증 실패(G3 "요약 영역에만 실패 안내 + 다시 시도"). `unit="overall"`이면 `items`는 1개·`area: null`, `unit="area"`이면 연습 기록이 있는 영역마다 1개·`area` 값 있음(중복 없음). ~~단위는 PRD OQ 56 미확정 — 기본값 `overall`~~ **2026-11-11 사용자 확정(PRD OQ 56 답 "영역별 요약 (추천)", DECISIONS #114)**: 1차는 항상 `unit = "area"` — 이번 기간에 종료 세션이 있는 영역마다 `items` 1개(AI `summary` 영역마다 1회 호출). 형태는 그대로(`"overall"` 값은 타입에 남기되 1차는 보내지 않음) |
| NoticeView | `{notice_id, kind:"safety"\|"trusted_contact", occurred_at, level:"red"\|"yellow"\|null, area\|null, channel\|null}` — 2026-11-11 PRD OQ 36 해소(DECISIONS #92): 형태 그대로. `kind = "safety"`이면 `occurred_at`·`level`·`area`가 값을 갖고 `channel`은 null, `"trusted_contact"`이면 `level`·`area` null·`channel` 값. 필드 추가 금지(F-41 ⑤). 상세 화면·상세 API 없음 — `notice_id`는 목록 키용 식별자([A-21]) |
| DeepEntryView (2026-11-07 신규, 2026-11-07 A20과 함께 조건부) | `{session_id, available: bool}` 최소 골격. 질문 내용·Y5-1에 보일 내용 필드는 **OQ 50 ①② 답 이후 확정**(지어내지 않음). A20을 만들지 않는 1차 기본안에서는 쓰지 않는다 |
| DeepFeedbackView (2026-11-07 신규) **[2차 — T-82]** | `{session_id, feedback:{sentences:[str]}, substituted: bool}` 최소 골격 — `sentences`는 AI 쉬운 말 피드백 1~3문장(N-03), `substituted`는 안전 필터가 아이 입력 또는 AI 출력을 걸러 대체 안내를 보낸 경우 `true`. 아이 답변 원문은 응답에 다시 담지 않는다. 단서 카드·신호등 등 결과(Y5-4)에 더 보일 필드는 **OQ 50 ③ 답 이후 확정**. 점수·수치 필드 없음(N-12) |

**보호자용 응답 금지 필드 (F-30 ②③, F-41 ③, F-48 ④)**: 메시지 원문, 마스킹된 추출 텍스트, 업로드 이미지, 감정 온도계 값, 연습 대화 문장(`ai_line`·선택지 문장), 고른 선택지와 그 태그(`chosen_choice_id`·`choices`·`judgment` — 2026-11-11 추가, DECISIONS #87. AI 계약 이름 `kind`·`target_clue_id`·`revealed_clue_ids`·`messages`도 금지 — 2026-11-11, DECISIONS #93), **아이 자유 답변(`answer_text` — 글·말을 바꾼 글 포함)과 심화 연습 피드백 문장**(2026-11-07 추가). GuardianReport와 그 하위 DTO는 Pydantic 모델에 필드를 명시 나열하고 추가 필드를 금지(`extra="forbid"`)하며, 통합 테스트가 응답 JSON 전체에 금지 키가 0건임을 단언한다.

### 오류 응답 규격

모든 오류는 `{"error": {"code": "<CODE>", "message": "<개발자용 짧은 설명>"}}`. 화면에 보이는 문구는 프론트가 `code`로 고른다(N-03 — 서버 message를 아이에게 그대로 보이지 않음). 이를 위해 프론트 `client.js`가 오류 본문의 `code`를 보존해야 한다 [팀 요청 F-4].

| code | HTTP | 의미 |
|---|---|---|
| VALIDATION_ERROR | 422 | 입력 형식·범위 위반 (`details`에 필드명 목록, 값은 넣지 않음) |
| CONSENT_REQUIRED | 422 | 법정대리인 동의 미체크 |
| EMAIL_TAKEN | 409 | 이미 가입된 이메일 |
| NOT_FOUND | 404 | Route not found |
| INVALID_CREDENTIALS | 401 | 보호자 로그인 실패 |
| INVALID_CODE_OR_PIN | 401 | 아이 로그인 실패 |
| UNAUTHENTICATED | 401 | 세션 없음·만료·폐기 |
| FORBIDDEN_ROLE | 403 | 보호자 세션으로 아이 API 호출 또는 그 반대 |
| CHILD_NOT_FOUND | 404 | 없는 아이 **또는 다른 보호자의 아이** (존재 여부를 드러내지 않음 — F-02 ④·F-30 ④) |
| SESSION_NOT_FOUND | 404 | 없는 연습 세션 또는 다른 아이의 세션 |
| NO_SCENARIO_AVAILABLE | 409 | 출제 가능한 상황 없음(자동 검수 대체 후보 소진 포함 — Y4 빈 값) |
| SESSION_ENDED / SESSION_NOT_ENDED | 409 | 종료된 세션에 턴 요청 / 진행 중 세션의 결과 요청 |
| SESSION_STOPPED (2026-11-11 — DECISIONS #99, 사용자 확정 #113) | 409 | safe_reply로 멈춘 세션에 턴·결과 요청(A17·A18) — Y4는 안내 상태 유지, Y5로 가지 않음 |
| INVALID_CHOICE | 422 | 현재 턴에 없는 선택지 |
| AI_UNAVAILABLE | 503 | AI 서비스 실패(비2xx·연결 실패·시간 초과·응답 스키마 위반) — Y4 에러 + 다시 시도. Y5에서도 발생(2026-11-08): 결과 조회 A18의 내부 `feedback` 실패·응답 검증 실패 → Y5 에러 + 다시 시도, 부분 응답 없음(DECISIONS #75) |
| DB_UNAVAILABLE | 503 | 헬스체크 DB 실패 |
| INTERNAL | 500 | 그 외 — 스택 트레이스·DB 오류 원문은 응답에 넣지 않음 |

### 백엔드–AI 내부 API (N-10 — 2026-11-06 갱신, ADR-0011) [정본: docs 저장소]

백엔드와 AI 서비스의 계약은 아래 HTTP 규격이다. 백엔드 쪽 코드 표현은 `app/ai_client/ports.py`의 `PracticeAI` 포트와 Pydantic DTO이며, services는 포트만 안다. 규격 변경은 백엔드·AI 담당 합의 + docs 저장소 정본 갱신 + `tests/contracts/ai/` 샘플 갱신을 함께 한다.

공통: 기준 URL `{AI_SERVICE_URL}/internal/v1`, JSON, 헤더 `X-Internal-Token: {AI_SERVICE_TOKEN}`(health 제외), `X-Request-ID`(백엔드가 전달, AI 서비스 로그에 기록). AI 서비스는 상태가 없다(DB 없음) — 백엔드가 매 호출에 `spec`과 이력을 보낸다. 오류 응답 형식은 공개 API와 같은 `{"error":{"code","message"}}`.

> **2026-11-11 [대체됨 — 1차] (DECISIONS #96, ADR-0017 — 방향은 사용자 결정 "그렇게 해", 세부도 2026-11-11 사용자 확정 "확정 (추천)" — DECISIONS #115)**: 아래 표의 `ScenarioSpec`·`ChoiceOption`·`TurnResult`·`TurnHistoryItem`·`ReviewResult`·`CueOutcome`·`GET /internal/v1/health`·`opening`·`next-turn`·`judge`·`feedback`·`LearningSummaryInput`·`summaries/guardian`·"AI 서비스 오류 코드"·"선택지 태그 제약"·"백엔드 포트" 행은 1차에서 쓰지 않는다 — 이력으로 남긴다. 1차 규격은 이 표 다음의 "1차 내부 API v1 (2026-11-11 — AI 계약 채택)" 하위 절이 원본이다. 그대로 유효한 행: 공통 토큰 헤더·AI 상태 없음, "`feedback` 응답 → 공개 `PracticeResultView` 매핑"의 ①(출처 구분)·③(`level`은 백엔드)·⑤(실패 → A18 전체 503)·⑥, "요약 실패 처리", "백엔드 쪽 처리", "구현 선택", "연습 종료"(태그 이름만 `kind`), `child-growth`·`recommendations/reason`(선택·구현 금지), `deep/feedback`·심화 연습 안전 처리([2차]).

| 엔티티/인터페이스 | 규격 (필드·타입·제약) | 사용 모듈 |
|---|---|---|
| `ScenarioSpec` (공통 입력) | `scenario_id, area, subtype\|null, is_normal, target_cues:[{cue_id, label, explanation}], situation_seed:str, variant:{tone, platform, persona}, grade_band:"elementary"\|"middle"\|"high", difficulty:int\|null, hint_level:int`. **아이 식별 정보(ID·별명·연락처) 필드 없음** — AI 제공사로 개인정보가 넘어갈 경로를 규격으로 막는다 (N-05) | backend → ai |
| `ChoiceOption` | `{id:str("c1"…), text:str, judgment:ChoiceJudgment, cue_ids:list[str]}` — 제약: `cue_ids ⊆ target_cues[].cue_id`, 선택지 2~4개. **`judgment`가 연습 종료를 좌우한다**(2026-11-08, DECISIONS #80) — `suspicious`를 고르면 그 답에서 종료(위험 상황). 위험 상황 턴의 태그 구성 제약은 아래 "선택지 태그 제약" 행 | ai → backend |
| `TurnResult` | `{ai_line:str, speaker_name:str, choices:list[ChoiceOption], hint:str\|null, substituted:bool}` — **`is_terminal` 삭제(2026-11-08, DECISIONS #81, ADR-0015 — 사용자 확정(2026-11-08 '삭제'), DECISIONS #84)**: 종료는 백엔드가 정하므로 AI는 종료 신호를 만들지 않는다. 전환 허용: 응답에 `is_terminal`(또는 다른 규격 밖 필드)이 있어도 백엔드는 검증 실패로 보지 않고 무시한다 — `TurnResult`에 `extra="forbid"`를 두지 않는다(백엔드로 들어오는 모델. 나가는 모델의 `extra="forbid"`(N-05)와 다름) | ai → backend |
| `TurnHistoryItem` | `{turn_index, ai_line, choices:list[ChoiceOption], chosen_choice_id\|null}` | backend → ai |
| `ReviewResult` | `{passed:bool, reasons:list[str]}` (통과 기준 [OQ 25]) | ai → backend |
| `CueOutcome` | `{cue_id, outcome:"found"\|"missed"}` | ai → backend |
| `GET /internal/v1/health` | → 200 `{status:"ok"}` (토큰 불필요) | 배포 헬스체크 |
| `POST /internal/v1/practice/opening` | `{spec}` → 200 `{turn: TurnResult, review: ReviewResult}` — **LLM 기반 상황 생성**(AI 파트 1·5: `situation_seed`·목표 단서·변형을 받아 구체 상황과 첫 대사·선택지를 생성) + 안전 필터 + 출제 전 검수(F-42)를 한 번에. 검수 항목(2026-11-06 보강): ① 생성된 상황·대사에 `target_cues`가 모두 드러남(정상 상황이면 위험 단서 없음) ② 안전 규칙 위반 없음 ③ 실제 형식의 전화번호·URL·계좌번호 없음 ④ 선택지 제약 충족. 통과 기준 수치 [OQ 25] | `PracticeAI.opening` |
| `POST /internal/v1/practice/next-turn` | `{spec, history:list[TurnHistoryItem], chosen_choice_id, turn_index}` → 200 `{turn: TurnResult}` — `turn_index`는 생성할 새 턴의 번호(첫 대사 = 0이므로 위험 상황에서는 1~3, 2026-11-08 명시). **백엔드는 종료가 아닐 때만 호출한다**(DECISIONS #80) — 이 엔드포인트가 불리면 AI는 항상 답할 수 있는 다음 대사·선택지를 만든다. 종료하는 답 뒤의 마무리 대사는 요청하지 않는다(PRD OQ 62 ① "바로 결과 화면") | `PracticeAI.next_turn` |
| `POST /internal/v1/practice/judge` | `{spec, history:list[TurnHistoryItem]}` → 200 `{outcomes:list[CueOutcome], normal_outcome:"trusted_correctly"\|"over_warned"\|null}` (LLM 미사용 결정적 판정 권고). **규칙(2026-11-11 PRD OQ 31 해소 — F-13 ④⑤, DECISIONS #91)**: 위험 상황은 목표 단서마다, 그 단서가 `cue_ids`에 있는 `suspicious` 선택지를 `history`에서 한 번이라도 골랐으면 `found`, 아니면 `missed`(`trusting`·`neutral` 선택지의 단서는 세지 않음). 정상 상황은 `suspicious`를 한 번도 안 골랐으면 `trusted_correctly`, 한 번이라도 골랐으면 `over_warned`. **백엔드 응답 검증(위반 → `AIUnavailableError` → 503)**: J1 위험 상황 — `outcomes`의 `cue_id` 집합 = `spec.target_cues` 집합, 단서마다 정확히 1개, `normal_outcome = null` / J2 정상 상황 — `outcomes = []`, `normal_outcome ≠ null`. 응답 형태는 그대로(AI 담당 알림 AI-6). **위치 확정(2026-11-06 사용자 "추천안대로")**: N-12(AI는 글 생성, 백엔드는 계산·저장)의 예외로 AI 서비스에 둔다 — 이유: 팀 AI 파트 페이지에 "판단 분석"이 AI 몫으로 적혀 있고, 옮기면 AI 담당과 재합의 비용이 든다(DECISIONS #57). **경계(2026-11-06 명시)**: 응답은 범주값(`found`/`missed`, `trusted_correctly`/`over_warned`/null)만 — 점수·비율·성장 수치 필드를 두지 않으며, 백엔드가 응답 스키마로 거부한다. 약점 집계·성장 지표·힌트 단계는 이 결과를 저장한 뒤 백엔드가 계산한다 | `PracticeAI.judge` |
| `POST /internal/v1/practice/feedback` | `{spec, outcomes:list[CueOutcome], history:list[TurnHistoryItem], normal_outcome:"trusted_correctly"\|"over_warned"\|null}` → 200 `{cards:list[{cue_id\|null, sentence:str}]}` — 비난 표현 없는 쉬운 말 1문장(N-03). 쉬운 대처법 문장 포함(AI 파트 4). **2026-11-07 변경(사용자 확인 대상 — PRD OQ 57)**: AI 담당 답변 2의 MVP ①("아이가 고른 선택지가 왜 맞았는지/틀렸는지 AI가 설명")을 이 엔드포인트가 맡는다 — 별도 엔드포인트·별도 화면 영역을 만들지 않고, 카드 문장이 그 단서를 찾거나 놓친 **아이의 선택**과 이어서 설명한다(예 형식: 고른 선택지 → 그 선택이 단서를 찾은/놓친 이유). 이를 위해 요청에 `history`(대화 이력과 `chosen_choice_id` — `judge` 요청과 같은 값)와 `normal_outcome`(`judge` 응답값 — 정상 상황에서 "괜찮아"가 맞은 판단인지, F-17 ②)을 추가했다. `history`에는 AI가 만든 대사·선택지 문장과 선택지 ID만 있다 — 아이가 직접 쓴 글은 없다(N-05 변화 없음). 응답 형태·`PracticeResultView`는 그대로. 숫자 검증 대상 아님(점수 없음 — 1문장 카드). **2026-11-08**: 응답의 각 카드가 공개 `PracticeResultView`의 어디로 가는지, `level` 결정, 백엔드 검증, 실패 처리는 바로 아래 매핑 행(DECISIONS #75). AI는 `level`을 보내지 않는다(응답 형태 그대로 — AI 담당 재합의 불필요) | `PracticeAI.feedback` |
| `feedback` 응답 → 공개 `PracticeResultView` 매핑 (2026-11-08 신규 — 사용자 확정(2026-11-08 '지금 안대로'), DECISIONS #75·#79. `level` 키 K1~K5의 값은 2026-11-12 사용자 확정(PRD OQ 63 ① — DECISIONS #120), 노랑 화면 문구는 PRD OQ 24 사용자 확정(DECISIONS #121). 정상 상황 `normal_outcome = null`은 2026-11-11 불허로 정함 — `judge` 응답 검증 J2, DECISIONS #91) | **① 출처 구분**: `found`·`missed`의 `CueCard`는 백엔드가 `cue_results`(판정 결과)와 콘텐츠 `cues.json`으로 만든다 — `label` = `cues.json.label`, `sentence` = `cues.json.explanation`(사람이 쓴 단서 설명, AI 미사용, 요청마다 같음). `cards[]`는 `feedback` 응답에서만 만든다 — AI 문장은 그 단서를 찾거나 놓친 **아이의 선택**과 이어 설명하는 문장(MVP ①, DECISIONS #67)이며 `CueCard.sentence`를 덮어쓰거나 대체하지 않는다. 백엔드도 `CueCard.sentence`를 `cards[]`에 넣지 않는다. **② 배치**: 응답 `cards[i]` → `PracticeResultView.cards[i]` — 개수·순서 그대로(AI 응답 순서). `sentence`는 그대로 옮기고, `cue_id`는 `level` 결정과 검증에만 쓰며 공개 응답에 싣지 않는다(`cards[]` 형태 `{level, sentence}` 그대로). `cue_id: null` 카드도 같은 `cards[]`에 같은 규칙으로 놓인다 — 특정 단서에 묶이지 않는 문장(정상 상황에서 "괜찮아"가 맞은 판단이라는 피드백 F-17 ②, 쉬운 대처법 AI 파트 4 등). **③ `level` 결정**: AI가 아니라 백엔드 domain 순수 함수가 정한다(계산은 백엔드 — DECISIONS #50). 키 5개: K1 위험 상황(`is_normal = false`) + 카드 `cue_id`의 판정 `found` / K2 위험 상황 + `missed` / K3 위험 상황 + `cue_id: null` / K4 정상 상황(`is_normal = true`, `cue_id`는 항상 null) + 세션 `normal_outcome = trusted_correctly` / K5 정상 상황 + `over_warned`. **키→SignalLevel 값(2026-11-12 사용자 확정 — PRD OQ 63 ① 답 "판단 결과 기준 (추천)", DECISIONS #120)**: 설정 상수 1곳 `CARD_LEVEL_BY_KEY` = K1 `green` / K2 `yellow` / K3 `green` / K4 `green` / K5 `yellow` — 아이의 판단이 잘 됐는지를 색으로 보인다(놓침도 `red`가 아니라 `yellow` — N-03). 이 매핑에서 `red`는 쓰지 않는다. 감수: `green` 카드(K1)에 위험 단서 내용이 적혀 있어 '안전'으로 오해할 수 있다(사용자 선택지 설명의 단점 원문 그대로). 노랑의 화면 문구는 "믿는 사람에게 물어봐요"(PRD OQ 24 — DECISIONS #121)이며 프론트가 `level = "yellow"`를 받아 표시하는 문구다 — API 값은 `yellow`(내부 판정 이름 '확인 필요') 그대로, 문구는 응답에 싣지 않는다. **호출 순서(2026-11-12, T-16 리뷰 권고 #1 대응 — DECISIONS #120)**: 이번 세션 카드에 필요한 키(K1~K5)의 `CARD_LEVEL_BY_KEY` 값 존재 확인을 `feedback` 호출 **전에** 한다 — 매핑이 없으면 AI 호출을 소비하지 않고 500 `INTERNAL`. 값이 모두 채워져 있어도 이 방어는 유지한다. 구현은 T-89. 표에 없는 조합(예: 정상 상황인데 `normal_outcome = null` — 2026-11-11 불허, `judge` 응답 검증 J2가 먼저 503으로 막으므로 저장되지 않음)은 domain이 예외를 던져 500 `INTERNAL` — 임의 색을 보이지 않는다(방어용으로 유지). **④ 백엔드 검증**(`HttpPracticeAI` Pydantic + services, 하나라도 어기면 `AIUnavailableError` — DECISIONS #47): V1 `cards` 1개 이상 / V2 모든 `sentence`가 공백만이 아닌 문자열 / V3 `cue_id`가 null이 아니면 이번 요청에 보낸 `outcomes[].cue_id` 안에 있다 / V4 null이 아닌 `cue_id`는 중복 없음 / V5 요청 `outcomes`의 모든 `cue_id`에 카드가 정확히 1장(단서마다 아이의 선택과 이은 설명 — #67, F-26 "1문장 1카드"). 정상 상황은 `outcomes`가 비어 있어 V3에 따라 모든 카드가 `cue_id: null`. `cue_id: null` 카드 수 상한은 두지 않는다(근거 없음). **⑤ 실패 처리**: `feedback` 실패·검증 실패 → A18 전체 503 `AI_UNAVAILABLE`, 부분 응답 없음. 근거: (가) "경계 간 전파" 규칙 — 연습 API의 AI 실패는 503(DECISIONS #47), 필드를 비우는 처리는 부가 정보인 요약에만("요약 실패 처리" 행) — `feedback`은 MVP ①을 맡는 F-13 주 기능(#67, #62와 같은 이유) (나) PRD Y5 에러 상태는 "결과 불러오기 실패 시 다시 시도"이고 "단서 카드는 보이고 설명만 실패" 상태는 PRD에 없다 — 부분 응답은 PRD 화면 상태 추가(planner)와 공개 DTO 상태 필드 추가가 필요 (다) A18은 읽기 요청이고 `cue_results`·`normal_outcome`은 턴 종료 시 이미 저장됨(데이터 흐름 3번) — 다시 시도가 안전, 자동 재시도 없음(#47). 감수: AI 장애 때 AI 없이 만들 수 있는 `found`·`missed` 카드도 보이지 않는다. 순서: 404·409 확인 뒤에만 AI를 부른다. **⑥ 공개 DTO 영향**: `PracticeResultView` 형태 변경 없음 — 하위 호환이 깨지는 변경 아님. A18 오류 목록에 503 `AI_UNAVAILABLE` 명시(경계 간 전파 규칙상 이미 날 수 있던 오류). 프론트 영향(T-19): `cards[]`에는 단서 연결 정보가 없어 AI 카드를 `found`·`missed` 카드와 짝지을 수 없다 — 짝지어 보여야 하면 `cards[].cue_id` 추가(하위 호환 추가)를 새 결정으로 요청. Y5 에러 상태는 `AI_UNAVAILABLE`도 "다시 시도"로 처리. **⑦ T-16 테스트**: 키 K1~K5별 `level`(주입 값), V1~V5 위반 각각 → 503, `cue_id: null` 카드 배치, `found`·`missed`의 `sentence`가 `cues.json.explanation`과 같고 AI 문장이 섞이지 않음, 공개 응답 `cards[]`에 `cue_id` 키 없음, 404·409이면 Fake `feedback` 미호출 | app/services, app/domain, app/ai_client |
| 힌트 문장 (AI 파트 4·6, 2026-11-06 명시) | 별도 엔드포인트 없음 — `opening`·`next-turn`이 `spec.hint_level`(백엔드가 계산, F-18 ②)과 `spec.difficulty`에 맞춰 `TurnResult.hint`를 생성한다. 제약: `hint_level == 0`이면 `hint`는 `null`(백엔드가 검증, 위반 시 스키마 위반 처리). 설명 수준 조절(AI 파트 6)도 같은 두 값으로만 한다 — AI가 난이도를 새로 정하지 않음 | `PracticeAI.opening`·`next_turn` |
| `LearningSummaryInput` (요약 공통 입력, 2026-11-06 신규, 2026-11-07 갱신 — 사용자 확인 대상) | `{grade_band, period:{from:date, to:date}, areas:[{area, practice_count:int, found_count:int, missed_count:int, previous:{practice_count:int, found_count:int, missed_count:int}\|null}], found_cues:[{cue_id, area, label, found_count:int}], weak_cues:[{cue_id, area, label, explanation, missed_count:int}], metrics:[{metric_id, label, status:"ok"\|"insufficient", current:number\|null, previous:number\|null}]}` — 전부 백엔드가 계산한 값(T-76 조립, 원천은 `practice_sessions`·`cue_results`). **2026-11-07 추가**: AI 담당 답변 4 원문 "연습 횟수, 발견한 단서, 놓친 단서, 영역별 성장 수준 등 계산된 데이터"에 맞춰 ① 발견한 단서 = `found_cues`(신규)와 `areas[].found_count` ② 놓친 단서 = `weak_cues`(기존, `area` 추가)와 `areas[].missed_count` ③ **영역별 성장 수준 = 영역별 기록 수의 이번 기간 값과 직전 같은 길이 기간 값(`areas[].previous`)** — 기록된 횟수만 담고 비율·등급·점수·단계는 만들지 않는다(F-29 ③, F-47 ④, PRD OQ 49 해소 "백엔드 계산, AI는 문장만"). 직전 기간에 기록이 없으면 `previous: null`. 기간: **2026-11-11(PRD OQ 12 해소, DECISIONS #88)** `SUMMARY_PERIOD_DAYS`는 별도 값을 두지 않고 지표 기간 상수 `METRIC_PERIOD_DAYS`(= 7)를 그대로 쓴다 — `period` = 지표의 이번 기간(오늘 포함 한국 시간 7일, `from`·`to`는 한국 시간 날짜), `areas[].previous` = 지표의 직전 기간(그 앞 7일). 한 요청 안에서 요약 입력과 `metrics`의 기간이 같다. 기록 부족 기준 `SUMMARY_MIN_ENDED_SESSIONS`([A-18] = PRD OQ 58, 미결)는 이번에 바꾸지 않았다 — 지표의 3세션 기준과 같게 할지는 OQ 58 답에 따른다. `metrics`(F-29 지표 3개)는 영역 구분 없음 — OQ 12 답도 영역별 정의가 아니다(`metrics[].area` 추가 없음). `metrics[]`는 `MetricView`와 같은 값(`insufficient`이면 `current`·`previous` null). **아이 ID·별명·연락처·대화 문장·감정 값·알림 원문·심화 연습 답변 필드 없음** (N-05, F-30 ②③, F-48 ④) | backend → ai |
| `POST /internal/v1/summaries/guardian` (2026-11-06 신규 — F-47 보호자 학습 요약, T-75, AI 파트 8·9. 2026-11-07 갱신 — 사용자 확인 대상) | `{input: LearningSummaryInput, unit:"overall"\|"area"}` → 200 `{items:list[{area: Area\|null, sentences:list[str] (1~2개)}], substituted:bool}` — 주요 학습 내용·반복적인 어려움(약점 단서)·성장 현황을 보호자용 문장으로. 아이는 "아이"로 지칭(별명은 프론트가 따로 표시). **문장 수 1~2**(AI 담당 답변 4 원문 "1~2문장의 요약", PRD F-47 ①). **단위(PRD OQ 56 미확정)**: 백엔드가 `unit`을 정해 보낸다 — 기본값 `overall`(항목 1개, `area: null`). `area`면 `input.areas` 중 `practice_count > 0`인 영역마다 항목 1개(그 영역 이름은 프론트가 Area 값으로 표시 — AI가 영역 이름을 새로 짓지 않음, 예시의 "관계 영역"은 1차 Area에 없음). 어느 단위든 **G3 조회당 호출 1회**(항목 목록을 한 응답으로). 백엔드 검증: `unit`과 항목 수·`area` 값이 맞지 않으면 그 요약 전체를 버린다(`unavailable`) | `SummaryAI.guardian_summary` |
| `POST /internal/v1/summaries/child-growth` (2026-11-06 신규, **선택**) | `{input: LearningSummaryInput}` → 200 `{sentences:list[str] (1~3개), substituted:bool}` — 아이용 쉬운 말·비난 없는 성장 요약(N-03). 1차 포함 여부는 PRD OQ 49 잔여(Y8에 AI 요약을 넣을지 — 2026-11-07에도 답 없음) 답 후 — 확정 전 구현 금지. **문장 수 1~3 유지(2026-11-07 판단)**: AI 담당 답변 4의 "1~2문장"은 보호자 학습 요약에 대한 답이고 아이용 요약에 대한 근거가 없다 — Y8 요구사항이 생기면 그때 정한다. 입력은 위 갱신된 `LearningSummaryInput`을 그대로 쓴다 | `SummaryAI.growth_summary` |
| `POST /internal/v1/recommendations/reason` (2026-11-06 신규, **선택**) | `{grade_band, area, target_cues:[{cue_id, label}], reason_code:"weak_cue"\|"retry"\|"mission"}` → 200 `{sentence:str, substituted:bool}` — 백엔드가 이미 고른 다음 문제(ADR-0009)의 추천 이유를 문장화(AI 파트 7). AI는 문제를 고르지 않음. 요구사항 없음(PRD F 미생성 — 표시 요구사항이 없음, planner 2026-11-06) — 구현 금지 | `SummaryAI.recommendation_reason` |
| 요약·이유 문장 공통 제약 (2026-11-06 신규) | ① AI는 점수·등급·수준을 새로 만들지 않는다(PRD 서비스 원칙 "성장 산식이 검증되지 않은 능력 점수·자립 보증 수치는 표시하지 않고"). 백엔드 검증: 출력 문장에 나오는 숫자는 입력 값에 있는 숫자만 허용, 문장 수는 엔드포인트별 범위(2026-11-07 갱신: `summaries/guardian` 항목당 1~2 / `summaries/child-growth`·`deep/feedback` 1~3 / `recommendations/reason` 1), 문장 길이 상한(설정 상수) — 위반 시 그 요약은 버린다. 2026-11-07 판단 근거: 1~2는 AI 담당 답변 4(보호자 학습 요약)에만 근거가 있어 다른 행은 바꾸지 않음 ② 안전·자립을 보증하는 표현 금지(PRD 범위 제외) ③ 안전 필터 차단 시 `substituted:true` + 대체 문구 | ai, app/ai_client |
| `POST /internal/v1/deep/feedback` (2026-11-07 신규 — F-48, T-78) **[2차 — T-78·T-82, 2026-11-07 PRD OQ 55 해소: 사용자 답변 원문 "AI 피드백만 2차로"]**. 규격은 2차에서 그대로 쓰도록 남긴다 — 1차에는 AI 서비스 구현·백엔드 호출 모두 없음. AI 담당은 메인 세션 질문 다섯째 항목에 답하지 않았고 ②를 "향후 발전 방향"으로 답했다 — 2차 착수 전 AI 담당 합의 필요(DECISIONS #71) | `{spec: ScenarioSpec, outcomes:list[CueOutcome], answer_text:str}` → 200 `{sentences:list[str] (1~3개), substituted:bool}` — 방금 연습의 상황·단서·판정 결과를 맥락으로, 아이가 쓴 판단 이유에 쉬운 말·비난 없는 피드백 문장(N-03). **출력은 피드백 문장만** — 점수·등급·수치 없음(N-12, #57 judge 경계와 같음, 요약 공통 제약 ①의 숫자 검증 적용: 출력 숫자는 입력에 있는 것만). 질문 내용이 정해지면(OQ 50 ②) 요청에 질문 맥락 필드를 하위 호환으로 추가 | `PracticeAI.deep_feedback` |
| 심화 연습 안전 처리 (2026-11-07 신규 — F-48 ⑤) **[2차 — T-78·T-82, 2026-11-07 PRD OQ 55 해소 — 위 `deep/feedback` 행과 같이 규격 유지, 1차 구현 없음]**. 1차 아이 입력 처리는 이 행이 아니라 PRD OQ 59 판단(DECISIONS #72·#74 — 서버 처리 없음) | **입력 필터**(AI 서비스): `answer_text`가 안전 규칙(개인정보 형식 — 전화번호·계좌번호·주소 등, 위험 표현 — 목록 [OQ 25])에 걸리면 **LLM을 호출하지 않고** 200 + `substituted:true` + 대체 안내 문장. **출력 필터**: 걸린 출력은 버리고 200 + `substituted:true` + 대체 안내. 대체 안내 문구는 ai 저장소 `fallbacks.json`(콘텐츠 [OQ 3]). 아이 답변 원문은 AI 서비스·백엔드 어디에서도 로그에 남기지 않음. AI 비2xx·시간 초과·스키마 위반 → 백엔드 `AIUnavailableError` → 공개 API 503 `AI_UNAVAILABLE`(심화 연습은 주 기능이라 요약처럼 null로 넘기지 않음) | ai, app/ai_client, app/services |
| 요약 실패 처리 (2026-11-06 신규, 2026-11-07 갱신) | 요약·이유 문장은 부가 정보다 — AI 실패·검증 실패 시 백엔드는 해당 필드를 비우고(보호자 학습 요약은 `summary.status = "unavailable"`·`items: []`, 그 외 선택 요약은 `null`) 리포트·성장 화면 나머지는 정상 응답한다(연습 API처럼 503을 내지 않음). 보호자 학습 요약의 기록 부족은 실패가 아니다 — AI를 호출하지 않고 `status = "insufficient"`(A-18). 캐시 없음(1차) — 요청마다 생성, 보호자 학습 요약은 저장하지 않음(2026-11-06 사용자 확정 "추천안대로", DECISIONS #58) | app/services |
| AI 서비스 오류 코드 | 401 `INVALID_INTERNAL_TOKEN` / 422 `VALIDATION_ERROR` / 503 `PROVIDER_UNAVAILABLE` / 504 `PROVIDER_TIMEOUT` / 500 `INTERNAL`. 안전 필터 차단은 오류가 아니라 200 + `substituted:true` + 대체 문구 | ai → backend |
| 백엔드 쪽 처리 | `HttpPracticeAI`가 응답을 Pydantic으로 검증(위 제약 포함). 비2xx·연결 실패·시간 초과(`AI_SERVICE_TIMEOUT_SECONDS`)·검증 실패 → `AIUnavailableError` → 503 `AI_UNAVAILABLE`. 자동 재시도 없음(아이가 다시 시도) | app/ai_client |
| 구현 선택 | `AI_CLIENT=http\|fake` (`factory.py`). `fake`는 결정적 `FakePracticeAI` — 백엔드 테스트·로컬·E2E 기본 | app/ai_client |
| 단서 틀 유지 (F-11 ①)·안전 필터 (F-11 ②) | AI 서비스 책임. 백엔드는 `ChoiceOption.cue_ids ⊆ 목표 단서` 검증으로 이중 확인한다 | ai, app/services |
| 연습 종료 (F-11 ④⑤⑥ — 2026-11-08 PRD OQ 42 해소, DECISIONS #80, ADR-0015. 이전 규칙 "종료는 `is_terminal` 또는 `turn_index + 1 >= MAX_TURNS` 중 먼저 오는 것"은 대체됨) | **백엔드 domain 순수 함수**(권고 위치 `app/domain/practice_end.py`)가 정한다 — 입력은 세션의 `is_normal`, 고른 선택지의 `judgment`, 아이 답 수 `answer_count`(= 답한 턴의 `turn_index + 1`, 첫 대사에 대한 답이 1)뿐이다. AI 응답의 어떤 값도 입력이 아니다. **위험 상황(`is_normal = false`)**: `judgment = suspicious` → 종료 / `answer_count >= MAX_CHILD_ANSWERS` → 태그와 관계없이 종료 / 그 외(`trusting`·`neutral`이고 `answer_count` 1~3) → 계속. `MAX_CHILD_ANSWERS = 4`(설정 상수 1곳 — 사용자 답 "4번 (Recommended)"). 이전 상수 `MAX_TURNS`와 식 `turn_index + 1 >= MAX_TURNS`는 쓰지 않는다 — `turn_index`가 답한 턴인지 새로 만들 턴인지 식에 드러나지 않아 이름·식을 아이 답 수 기준으로 바꿨다(첫 대사 = 0 기준이면 답한 턴 `turn_index` 3 = 4번째 답에서 같은 결과). **정상 상황(`is_normal = true`)**: 규칙 없음 — [OQ 61]. 답 전에는 domain 함수가 정상 상황 입력에 예외를 던져 500 `INTERNAL`(임의 규칙으로 끝내지 않음). 정상 상황 출제(T-34·T-35)는 OQ 61 답 후에 켠다 | app/domain, app/services |
| 선택지 태그 제약 (2026-11-08 신규 — 사용자 확정(2026-11-08 '둔다'), DECISIONS #83·#86) | 위험 상황(`spec.is_normal = false`)의 `opening`·`next-turn` 응답 `TurnResult.choices`는 **`suspicious` 1개 이상 + `suspicious`가 아닌 것(`trusting`·`neutral`) 1개 이상**. 이유: 의심 선택지가 없으면 F-11 ④(의심 답이면 종료)를 고를 수 없고, 모두 의심이면 F-11 ⑤(계속)와 단서를 놓칠 기회가 사라진다. 백엔드 검증 위반 → `AIUnavailableError` → 503 `AI_UNAVAILABLE`(`cue_ids` 제약 위반과 같은 처리). 정상 상황의 태그 제약은 [OQ 61] — 두지 않는다. 태그가 내용과 맞는지(예: 거절 문장에 `suspicious`)는 백엔드가 검증할 수 없다 — AI 서비스 몫(AI-5, D-11) | app/ai_client, app/services |
| 백엔드 포트 (2026-11-06 갱신, 2026-11-07 `deep_feedback` 추가 — 2026-11-07 `deep_feedback`은 [2차 — T-82]: 1차에는 포트 메서드·Fake 구현을 만들지 않는다) | `PracticeAI`(`opening`, `next_turn`, `judge`, `feedback`, [2차] `deep_feedback`) + `SummaryAI`(`guardian_summary`, 선택: `growth_summary`·`recommendation_reason`). 둘 다 `app/ai_client/ports.py`, Fake 구현 필수 | app/ai_client |

#### 1차 내부 API v1 (2026-11-11 — AI 계약 채택, DECISIONS #96~#104, ADR-0017 — 2026-11-11 사용자 확정: #96~#98·#100~#102·#104 → #115, #99 → #113, #103 → #114, `not_shown` → #109, 정상 상황 → #110)

근거: ai 저장소 커밋 331d2c6(feature/ai, PR·병합 전) `contracts/*.json`·`app/schemas.py`·`app/server.py`(architect가 읽기 전용 사본으로 직접 확인). AI 공지 원문 "경로와 필드는 제안안이라, 바꾸고 싶은 부분 있으면 편하게 말씀해 주세요." — 아래 "AI 담당 합의 필요" 항목은 백엔드 제안이다. 공통: 기준 URL `{AI_SERVICE_URL}`, JSON, `X-Internal-Token`(`/health` 제외), 본문 상한 64KB(AI `MAX_BODY_BYTES`). AI는 상태가 없다 — 백엔드가 매 요청 `scenario_id`·`variant`·`messages`·`revealed_clue_ids`를 보낸다. 백엔드 포트: `PracticeAI`(`variant`, `start`, `turn`, `judge`, `feedback`) + `SummaryAI`(`summary`) — `app/ai_client/ports.py`, Fake 필수, services는 포트만 import(계층 규칙 그대로).

| 엔티티/인터페이스 | 규격 (AI 계약 원문 필드) + 백엔드 검증(위반 → `AIUnavailableError` → 503 `AI_UNAVAILABLE`) | 사용 모듈 |
|---|---|---|
| `Message` | `{role:"ai"\|"child", text:str(1~500), choice_kind: ChoiceKind\|null, clue_id:str(≤64)\|null}` — 아이가 고른 답은 `text` = 고른 선택지 문장, `choice_kind` = 그 선택지 `kind`, `clue_id` = 그 턴의 `target_clue_id` | backend → ai |
| `Choice` | `{id:"c1"…, text, kind: ChoiceKind}` — 순서는 AI가 섞음. **선택지 규칙 C(#97)**: `ok`·`blocked` 응답은 정확히 3개, `kind` `correct`·`doubtful`·`other` 각 1개, `id` 중복 없음, `text` 공백만이 아님 | ai → backend |
| `Variant` | `{base_scenario_id, platform, tone, context, title(≤80), child_setup(≤300), opening_line(≤200), ai_role:{name(≤40), persona, tone}, clues:[{id, at_opening, reveal_when, reveal_line}](1~10)}` — 백엔드는 받은 그대로 `practice_sessions.variant`에 저장하고 같은 세션의 이후 요청에 그대로 보낸다 | 양방향 |
| `GET /health` | → 200 `{status:"ok", provider}` (토큰 없음) | 배포 헬스체크 |
| `POST /internal/v1/practice/variant` | `{scenario_id, platform, tone, context}`(백엔드는 세 값을 항상 채운다 — domain이 시나리오 `variation_axes`에서 선택, #102) → `{variant: Variant, source:"model"\|"fallback"}`. 검증 VA1 `variant.base_scenario_id` = 요청 ID / VA2 `variant.clues[].id` 목록 = 콘텐츠 시나리오 단서 목록(순서 같음) / VA3 `source = model`이면 `platform`·`tone`·`context` = 요청값 / VA4 F-12 차이: 같은 아이의 같은 `scenario_id` 직전 세션(다시 도전이면 `retry_of`)과 `platform` 또는 `tone`이 1개 이상 다름 — `fallback`(원본 시나리오)이 이를 못 지키면 503(같은 요청 다시 시도). F-42 출제 전 검수 = AI 쪽 `check_variant`(단서 키워드·타이밍·안전 필터) + 불통과 시 원본 대체 — 백엔드 `review`·재시도 경로 없음 | `PracticeAI.variant` |
| `POST /internal/v1/practice/start` | `{scenario_id, variant}` → `{status:"ok", reply, ai_role_name, title, child_setup, revealed_clue_ids, target_clue_id\|null, choices:[Choice], choices_source}`. 검증 ST1 `status = ok` / ST2 선택지 규칙 C / ST3 `revealed_clue_ids` ⊆ 시나리오 단서 / ST4 `target_clue_id`는 null 또는 `revealed_clue_ids` 안 / ST5 `reply`·`title`·`child_setup`·`ai_role_name` 공백만이 아님. 저장: 세션(`variant`·`scenario_title`·`child_setup`·`ai_role_name`) + 턴 0(`ai_line = reply`, `choices`, `target_clue_id`, `revealed_clue_ids`, `ai_status = ok`). LLM 미사용(콘텐츠 첫 대사 + 템플릿 선택지 — `practice.py` `start`) | `PracticeAI.start` |
| `POST /internal/v1/practice/turn` | `{scenario_id, messages(1~40, 마지막은 아이), revealed_clue_ids(직전 턴 값), variant}` → `{status:"ok"\|"safe_reply"\|"blocked", reply, revealed_clue_ids, all_clues_revealed, target_clue_id\|null, choices, choices_source, masked, source:"model"\|"fallback"\|"fixed"}`. **종료가 아닐 때만 호출**(#80 — 백엔드 규칙). `all_clues_revealed`·`masked`·`choices_source`는 종료·검증 입력이 아니다(무시 — F-11 ⑥). 검증 `ok`·`blocked`: TU1 선택지 규칙 C / TU2 `revealed_clue_ids` ⊇ 보낸 값, ⊆ 시나리오 단서 / TU3 `target_clue_id` null 또는 `revealed_clue_ids` 안 / TU4 `reply` 공백만이 아님. `safe_reply`: `status`만 읽고 나머지 필드는 검증하지 않는다(~~`choices` [], `reply` 공백만이 아님~~ — 2026-11-11 DECISIONS #118: 본문이 이상해도 503이 아니라 멈춤). 처리는 아래 "safe_reply·blocked 처리" 행 | `PracticeAI.turn` |
| safe_reply·blocked 처리 (#99 — **2026-11-11 사용자 확정 #113 "이대로 (추천)"**. PRD F-11에 없는 종료 조건이라 planner PRD 변경 필요) | **safe_reply**(AI가 아이 글에서 자해·폭력 피해 감지 — AI 공지 원문 "바로 멈춰 주세요"): 같은 트랜잭션에서 고른 선택지 저장 + 새 턴(~~`ai_line = reply`~~ **`ai_line` = 백엔드 고정 문구** — 아래 2026-11-11 OQ 64 갱신, `choices` [], `target_clue_id` null, `revealed_clue_ids` = 직전 값, `ai_status = safe_reply`) + 세션 `status = stopped`·`ended_at` = 지금. `judge`·`feedback` 미호출, `cue_results` 없음. A17 응답 `PracticeSessionView{status:"stopped", turn: 안내 턴}`. 이후 A16 = 같은 응답, A17·A18 = 409 `SESSION_STOPPED`. 집계(지표·배지·연속 기록·요약)는 `status = ended`만 세므로 자동 제외. 보호자 알림 생성 없음(제품 결정 — 설계로 만들지 않음). **2026-11-11 갱신 — PRD OQ 64 사용자 답 "고정 문구+홈, 알림 없음 (추천)"(DECISIONS #118)**: ① AI `reply`는 저장·공개 응답·로그 어디에도 쓰지 않고 버린다 ② 안내 턴 `ai_line` = 백엔드 보충 파일 `app/content/data/safety_stop.json`의 `message`(사람이 쓴 고정 문구 — 믿는 어른·상담 전화 안내, 멈춘 시점 값 스냅숏) ③ 공개 `TurnView`는 `ai_line` = 고정 문구, `choices` [], `hint` null, `substituted` false ④ Y4는 안내 + "홈으로"(→ Y3) ⑤ 보호자 알림 1차 미생성 확정(`guardian_notices` 0행 — 실제 알림 생성은 2차 F-41 ②). **blocked**(욕설 등 — 고정 문장 + 템플릿 선택지): 일반 계속 턴과 같이 저장(`ai_status = blocked`), 아이 답 수 그대로. 1차 아이 입력은 AI가 만든 선택지 문장뿐이라 두 상태는 거의 나지 않는다(추정 — 확인 방법: ai 저장소에서 모든 `choice_templates`·`GENERIC` 문장을 `check_input`에 넣어 `allow` 단언) | app/services, app/domain |
| 상태 재구성 (#98) | `messages` = 턴 행을 `turn_index` 순으로: AI 대사 `{role:"ai", text: ai_line}` → 그 턴에 답이 있으면 `{role:"child", text: 고른 선택지 text, choice_kind: 그 선택지 kind, clue_id: 그 턴 target_clue_id}`. A17에서는 이번 답을 마지막 아이 메시지로 붙여 보낸다(저장은 AI 성공 후 한 트랜잭션 — #85). `revealed_clue_ids` = 가장 최근 턴 행 값. 위험 상황 최대 4답 → 메시지 최대 8개(+safe_reply 안내 1) — AI 상한 40 안 | app/services |
| `TurnView` 대응 | `turn_index` = 턴 행, `speaker_name` = 세션 `ai_role_name`, `platform` = `variant.platform`, `ai_line`, `choices:[{id, text}]`(`kind` 미전송), `hint` = **null(1차 — AI 계약에 힌트 없음, #104 ④)**, `substituted` = `ai_status = blocked` 또는 AI `source ∈ {fallback, fixed}`(턴 0은 false). 공개 DTO 형태 그대로 | app/api |
| `POST /internal/v1/practice/judge` | `{scenario_id, messages(마지막 아이 답 포함 전체), revealed_clue_ids, variant}` → `{results:[{clue_id, result:"found"\|"missed"\|"not_shown"}], source:"choices"\|"model"\|"fallback"\|"fixed"}`. 위치는 AI 서비스(#57 그대로). 규칙 = #91('의심' = `correct`를 고른 답의 `clue_id`만 찾음 — AI `FOUND_KINDS={"correct"}`와 같음). 검증 J1' `results[].clue_id` 목록 = 콘텐츠 시나리오 단서 목록(순서·개수 같음, 중복 없음) / J2' `not_shown` ⇔ 보낸 `revealed_clue_ids`에 없음 / J3' `found` = (아이 메시지 중 `choice_kind = correct`의 `clue_id`) ∩ `revealed_clue_ids`, 나머지 드러난 단서 = `missed` / J4' `source ∈ {"choices","fixed"}`. 저장: `found`·`missed`만 `cue_results`(**사용자 확정 N1 — DECISIONS #109**, `not_shown`은 저장·집계하지 않음). 정상 상황: AI 계약에 `normal_outcome` 없음 — 정상 상황 출제는 꺼진 그대로(**사용자 확정 M1 — #110**: AI 담당에 G2·G3 요청, #91 J2·null 불허는 정상 상황을 켤 때의 검증으로 보류) | `PracticeAI.judge` |
| `POST /internal/v1/practice/feedback` | `{scenario_id, results(시나리오 단서 순서 — 저장된 found·missed + 나머지 not_shown), messages, variant}` → `{cards:[{clue_id, result:"found"\|"missed", text}], closing_line, source:"model"\|"fallback"\|"mixed"\|"fixed"}`. 공개 `PracticeResultView.cards[]` 대응(#101): 응답 카드 순서대로 `{level: K1(found)\|K2(missed), sentence: text}` + 마지막에 `closing_line`을 `{level: K3, sentence}` 1장. 검증 V1' 카드 `clue_id` 집합 = 저장된 found∪missed, 단서마다 1장 / V2' `text`·`closing_line` 공백만이 아님 / V3' 카드 `result` = 저장된 판정. `source` 제한 없음. `CueCard` = 콘텐츠(`label` = `clues.json name`, `sentence` = `description`), AI 문장 미사용. 실패 → A18 전체 503(#75 ⑤ 그대로) | `PracticeAI.feedback` |
| `POST /internal/v1/summary` | `{area: 영역 표시 이름(콘텐츠 `areas[].name`), practice_count:int≥0, found_clues:[단서 name], missed_clues:[단서 name], growth_level: null}` → `{summary: str\|null}`. 호출: 이번 기간(#88 창)에 종료 세션이 있는 영역마다 1회(최대 3). 공개 `GuardianSummaryView` 형태 그대로 — `unit = "area"`, `items` = `[{area, sentences:[summary]}]`. 검증 S1 `summary`가 null이 아니고 공백만이 아님 / S2 숫자는 입력 값에 있는 것만(#53) / S3 길이 상한(설정 상수). 하나라도 실패 → `status = "unavailable"`·`items` [](#69 실패 처리). **`growth_level`은 항상 null**(F-29 ③·A-15 — AI 담당 합의 G1) | `SummaryAI.summary` |
| AI 오류 | 본문 `{"error":"<code>"}`(문자열): 401 `unauthorized`, 422 `invalid_request`(+`fields` — 필드명만)·`invalid_variant`, 404 `scenario_not_found`, 413 `payload_too_large`, 400 `invalid_json`·`bad_request`, 500 `internal_error`. 백엔드는 비2xx면 본문을 해석하지 않고 503. Gemini 실패·한도 초과는 AI가 오류 대신 고정 문장으로 대체(`source = "fallback"`) — 백엔드는 정상 응답으로 받는다 | app/ai_client |
| 환경 변수 | 백엔드 `AI_SERVICE_TOKEN` 값 = AI `AI_INTERNAL_TOKEN` 값(이름만 다름), AI 포트 8081(AI `.env.example` `AI_PORT=8081`, 인용). 로컬 연결 테스트는 AI `AI_PROVIDER=fake`(AI 추가 전달 원문 "키가 없어도 .env에서 AI_PROVIDER=fake로 하면 고정 응답으로 돌아가서 연결 테스트는 바로 하실 수 있어요.") | 배포·로컬 |
| 계약 샘플 | `tests/contracts/ai/` = ai 저장소 `contracts/*.json`(12개 — variant·start·turn·judge·feedback·summary 요청·응답)을 커밋 고정으로 복사. `live_ai` 계약 테스트는 같은 요청으로 실행 중인 AI 서비스(`AI_PROVIDER=fake`)를 호출해 위 검증을 통과하는지 확인 | tests |

#### 기존 결정과의 충돌 정리 (2026-11-11)

| 기존 결정 | AI 계약 | 처리 | 새 결정 |
|---|---|---|---|
| #80 종료 규칙(입력 `judgment`·답 수), ADR-0015 | 선택지 `kind`, AI는 종료 판정 안 함(`all_clues_revealed`는 참고값) | 규칙 그대로, 이름만 `correct`. `all_clues_revealed` 무시 | #97 |
| #80·F-11 ④⑤⑥(종료 조건 목록) | `safe_reply`면 즉시 멈춤 요청 | 종료 조건 추가 — PRD 변경 필요(planner) | #99 |
| #81·#84 `TurnResult.is_terminal` 삭제 | `TurnResponse` — 종료 필드 없음 | 같은 원칙으로 흡수 | #96 |
| #83·#86 태그 구성 제약 | 항상 3종 각 1개 | 더 좁은 제약으로(위반 503) | #97 |
| #55 `opening`(생성+검수), ADR-0009 변형은 백엔드 | `variant`(값 지정 가능) + `start`(LLM 없음), 검수 = `check_variant` | 백엔드가 값 지정 → 변형 결정권 유지, `review` 경로 없앰 | #102 |
| 다시 도전(F-13 ③·F-12) | `variant` fallback이 원본으로 돌아갈 수 있음 | 직전 세션과 `platform`·`tone` 차이 검사, 실패 503 | #102 |
| #57 judge는 AI, #91 J1·J2 | `found`/`missed`/`not_shown`, `normal_outcome` 없음, `source` 4종 | 위치 유지. J1'~J4'로 교체. `not_shown` = 저장·집계 안 함(N1), 정상 상황 = 끄고 AI에 요청(M1) — 2026-11-11 사용자 확정 | #100·#105·#106 → #109·#110·#115 |
| #67·#75·#79 feedback 매핑 | `cards[{clue_id, result, text}]` + `closing_line`, `cue_id: null` 카드 없음 | `closing_line` → K3 카드, V1'~V3'. 공개 형태 그대로 | #101 |
| #51 힌트 문장(`TurnResult.hint`) | 힌트 없음 | 1차 `hint` null, T-74 때 하위 호환 추가 제안 | #104 |
| #68·#69 `LearningSummaryInput`·`summaries/guardian`(`unit` 기본 `overall`) | `/internal/v1/summary` 영역 1개, `growth_level` 문자열, 지표·직전 기간 자리 없음 | 영역마다 호출, `growth_level` null, `unit = area` — 사용자 확정 | #103 → #114 |
| ADR-0010 콘텐츠(백엔드 `cues.json`·`scenarios.json`·`variants.json`) | ai `content/clues.json`·`scenarios/*.json`(AI가 `scenario_id`로 직접 읽음) | AI 원천 + 백엔드 읽기 전용 사본 + 오버레이 — 사용자 확정 | #107 → #111 |
| Area ID(`name_lending`·`friend_request`) | `identity_lending`·`friend_pressure` | AI ID로 맞춤 — 사용자 확정 | #108 → #112 |
| 옛 오류 코드(503 `PROVIDER_UNAVAILABLE`·504) | `{"error":"code"}`, 제공사 실패는 fallback | 비2xx → 503 그대로 | #104 |

#### AI 담당 합의 필요 (2026-11-11 — 각 항목 백엔드 제안 한 줄. 전달은 메인 세션·사용자)

2026-11-11 사용자 확정 반영: G2·G3 = **요청 확정**(사용자 답 "끄고 AI에 요청 (추천)", DECISIONS #110 — 백엔드는 정상 상황을 끈 채 AI 쪽 추가를 기다림), G6·G7 = 백엔드 방침 확정(#114·#112 — AI 변경 요청 없음, 확인만), G9 = 합의 전까지 백엔드 오버레이로 진행(#111). 나머지는 합의 전 백엔드 제안 그대로. 2026-11-11 추가: G5 = **1차 요청 안 함**(planner 해석 5 사용자 답 "1차는 빼고 감 (추천)", DECISIONS #119). safe_reply 안내 문장은 백엔드 고정 문구로 바꾸며 AI `reply`를 쓰지 않는다(#118) — AI 변경 요청 없음, 알림만(AI-7 ③).

| # | 항목 | 백엔드 제안 |
|---|---|---|
| G1 | `growth_level` 등급 문자열(샘플 `"익숙해지는 중"`) vs PRD F-29 ③·A-15("수준 등급·점수 만들지 않음") | 백엔드는 항상 `null`로 보낸다 — 필드 설명 예시("시작 단계, 익숙해지는 중")와 샘플 값을 지우거나 필드를 없애 주세요. |
| G2 **(요청 확정 — #110)** | 정상 상황 판정 `normal_outcome`(F-13 ⑤) | `judge` 응답에 선택 필드 `normal_outcome: "trusted_correctly"\|"over_warned"\|null`을 추가(위험 상황 null — 하위 호환), 규칙은 "`correct`를 한 번이라도 고르면 `over_warned`". |
| G3 **(요청 확정 — #110)** | 정상 상황 실행 경로 — `normal_situations` 초안 4건이 `start`·`turn`에서 `scenario_id`로 안 찾아짐 | 정상 상황도 `scenario_id`로 `variant`·`start`·`turn`·`judge`·`feedback`이 동작하게, 정상 상황 선택지 `kind`의 뜻(거절·확인 = `correct`, "괜찮아"류 = `other`)을 정의. |
| G4 | 힌트(F-18 ②, T-74) | `start`·`turn` 요청에 선택 필드 `hint_level:int`, 응답에 `hint:str\|null` 추가(`hint_level = 0`이면 null). |
| G5 **(1차 요청 안 함 — #119)** | 요약에 성장 지표(F-47 ②)·직전 기간 | 1차는 지표·직전 기간을 보내지 않는다(#103, 사용자 확정 #119) — AI에 요청하지 않음. 2차 이후 필요해지면 아래 제안으로 다시 합의: `summary` 요청에 선택 필드(예: `previous_practice_count:int\|null`, 지표 비율 `metrics:[{metric_id, current, previous}]`)를 추가할지 — 숫자는 입력 값만 쓰는 규칙 유지. 1차에 없어도 되면 그대로 둠. |
| G6 (백엔드 방침 확정 — #114) | 요약 단위(PRD OQ 56 — 답 "영역별 요약 (추천)") | 1차는 AI 계약대로 영역마다 1회 호출(최대 3회). AI 변경 요청 없음 — 확인만. ~~전체 1문장이 필요하면 `area: null` 허용 모드 추가.~~ |
| G7 (백엔드 방침 확정 — #112) | Area ID 이름 | 백엔드가 AI ID(`identity_lending`·`friend_pressure`)로 맞춘다(#108) — AI 변경 없음, 확인만. |
| G8 | `judge`의 `source`가 `model`·`fallback`이 되는 경로(아이 글 판정) | 1차는 선택지 입력뿐이라 백엔드가 `choices`·`fixed`만 받는다 — 선택지 메시지만 오면 항상 `choices`인지 확인. |
| G9 (합의 전 오버레이로 진행 — #111) | 시나리오 메타(F-14 하위 유형·고등학생 한정) | 백엔드 오버레이(`scenario_meta.json`)로 둘지, AI 시나리오에 `subtype`·`min_grade` 필드를 넣을지(넣으면 백엔드 오버레이 불필요). |
| G10 | 한 턴에 단서가 2개 이상 드러나면 `target_clue_id`는 마지막 것만 — 나머지는 답할 선택지 없이 `missed`가 됨 | 한 턴에 새 단서는 1개만 드러내도록 프롬프트·검증(`new_ids` 1개 제한) 요청. |

#### 콘텐츠 소유 (2026-11-11 — 사용자 확정 "AI 저장소 원본 (추천)", DECISIONS #107 → #111)

확정: 단서 체계·시나리오 원천 = ai 저장소 `content/`. 백엔드는 AI 커밋을 고정한 읽기 전용 사본 `app/content/data/ai/`(`clues.json`, `scenarios/*.json`)을 두고 서버 시작 시 검증(`version`, 시나리오 단서 ID ⊆ `clues.json`), 백엔드 전용 값은 오버레이 `scenario_meta.json`(`scenario_id` → `subtype`·`min_grade`)·`platform_app_types.json`(AI 플랫폼 ID → AppType)·`diagnosis.json`(그대로). 반대안: 백엔드 원천 + AI 복사 / AI 콘텐츠 조회 API — 비교는 DECISIONS #107. 콘텐츠 작성 담당(PRD OQ 3)·T-03~T-05 상태는 planner.

#### AI 파트 범위 대응 (2026-11-06 신규)

분담 원칙(사용자 원문 "추천대로 반영" — 메인 세션 질문 "추천 분담(AI는 글 생성, 백엔드는 계산·저장)으로 기획·설계에 반영할까요?"에 대한 답): **AI 서비스 = 글 생성**(대사·상황 변형·피드백·힌트 문장·추천 이유·보호자용 학습 요약 문장), **백엔드 = 계산·저장**(기록 저장, 약점 집계, 성장 지표 계산, 힌트 단계, 다음 문제 선택) — 백엔드가 계산 결과를 AI에 넘겨 문장화한다. AI 서비스는 상태 없음 유지. 아래 "AI 파트" 열은 팀 노션 "AI 파트" 페이지 원문(메인 세션 2026-11-06 수집, 인용).

| AI 파트 (원문) | 백엔드 몫 (계산·저장) | AI 서비스 몫 (글 생성) | 내부 API |
|---|---|---|---|
| 1 상황 생성 "LLM 기반 시나리오 생성" | 사람이 만든 단서 체계·상황 씨앗(콘텐츠 JSON, ADR-0010)에서 시나리오 선택(ADR-0009) | 씨앗·목표 단서·변형으로 구체 상황·대사 생성 + 검수. 목표 단서를 추가·변경하지 않음 | `opening` |
| 2 AI 대화 "맥락 유지" | 대화 이력 저장·매 호출 전달(AI 상태 없음). 연습 종료 판정(선택지 태그·아이 답 수 — 2026-11-08, DECISIONS #80) | 상대 역할 대사·선택지와 선택지 `judgment` 태그. 종료 신호는 만들지 않음(2026-11-08, DECISIONS #81) | `next-turn` |
| 3 판단 분석 "사용자의 선택과 판단 이유 분석" | 선택 기록 저장, 판정 결과 저장 | 선택지 태그 기반 찾음/놓침 판정(Tasks T-14 담당 AI, 규칙은 2026-11-11 PRD OQ 31 해소 — `judge` 행, DECISIONS #91) — N-12의 예외로 AI에 둠(2026-11-06 사용자 확정, DECISIONS #57), 응답은 범주값만. 1차 입력은 선택지뿐. **2026-11-07 A-14 해소(사용자 확인 대상)**: AI 담당 답변 "이번 MVP에서는 ①을 구현하고, ②는 향후 발전 방향으로" — ① "아이가 고른 선택지가 왜 맞았는지/틀렸는지 AI가 설명"은 `feedback` 카드 문장이 아이의 선택과 이어 설명하는 것으로 구현(요청에 `history`·`normal_outcome` 추가, PRD OQ 57). ② 아이가 이유를 직접 쓰고 AI가 분석 = 심화 연습 `deep/feedback`과 같은 성격 — 유지 여부는 PRD OQ 55 → **2026-11-07 해소: 2차**(사용자 답변 원문 "AI 피드백만 2차로" — `deep/feedback` [2차], T-78·T-82). 1차에는 아이가 쓴 글을 AI가 분석하는 경로가 없다 | `judge`, `feedback` |
| 4 피드백 "쉬운 설명, 힌트, 안전한 대처법" | — | 단서 카드 문장·대처법·힌트 문장 | `feedback`, `TurnResult.hint` |
| 5 상황 변형 "말투/플랫폼/맥락 변경" | 변형 값 결정(F-12 — LLM 없이 테스트 가능하게) | 변형 값에 맞춘 상황·대사 | `opening` |
| 6 난이도 조절 "힌트 및 설명 수준 조절" | `difficulty`·`hint_level` 계산(F-07·F-18, 수치 [OQ 14]) | 두 값에 맞춘 문장 수준 | `opening`·`next-turn` |
| 7 학습 개인화 "취약 영역 파악 및 다음 문제 추천" | 약점 집계·다음 문제 선택(ADR-0009) | (선택) 추천 이유 문장 | `recommendations/reason` (선택) |
| 8 성장 기록 분석 "영역별 성장 수준 분석 및 학습 요약 생성" | 성장 지표 계산(F-29·F-31 — 2026-11-11 PRD OQ 12 해소, "성장 계산 규칙" 절) — "수준" 등급·점수는 만들지 않음(F-29 ③). **2026-11-07 A-15 해소(사용자 확인 대상)**: AI 담당 답변 "좋습니다." — 영역별 성장 수준은 백엔드가 영역별 기록 수(이번·직전 기간)로 계산해 `LearningSummaryInput.areas`로 넘긴다 | 학습 요약 문장 — 받은 값을 문장으로만(새 등급·점수·비율을 만들지 않음) | `summaries/guardian`, `summaries/child-growth` (선택) |
| 9 보호자 알림 지원 "시연용으로 축소" | 예시 알림 적재(F-41 ②, `origin=demo_seed`). 요약 입력 계산(연습 횟수·찾은/놓친 단서·영역별 기록 수 — T-76) | 보호자 학습 요약 문장 — F-47 (T-75·T-76·T-77). **2026-11-07 "시연용 축소" 내용 확정(사용자 확인 대상)**: AI 담당 답변 4 — 백엔드 계산 데이터 → 보호자용 1~2문장. 단위(영역별/전체)는 PRD OQ 56 | `summaries/guardian` |
| 10 실제 메시지 분석 "(제외)" | 2차 확장 지점 | 2차 | 없음 (1차) |

#### 계약 고정과 연동 일정 (2026-11-06 신규)

팀 타임라인 원문(인용): "11/11 - 각 파트 개발 완료 / 11/12 - 연동 / 11/14 - 제출". 파트가 동시에 개발하므로 연동 전에 계약이 고정돼야 한다.

| 시점 | 할 일 | 상태 |
|---|---|---|
| 2026-11-07까지 (architect 제안 [A-16]) | 내부 API v1(이 표의 스키마) + `tests/contracts/ai/` 요청·응답 샘플 JSON, 공개 API v1(A1~A19)을 docs 저장소에 게시하고 AI·프론트 담당 합의 → **v1 고정** | 제안 — 팀 합의 필요 |
| 고정 후 ~ 11/11 | **Fake·샘플 우선**: 백엔드는 `FakePracticeAI`·`FakeSummaryAI`로만 개발·테스트, AI는 샘플 요청으로 자기 서비스를 테스트, 프론트는 백엔드 로컬(`AI_CLIENT=fake`) 또는 공개 API 샘플로 개발. 실제 AI 서비스 없이 각 파트가 완료 판정 가능해야 함 | 원칙 |
| 고정 후 변경 규칙 | 하위 호환 변경(선택 필드 추가)만 허용. 필드 삭제·이름·타입 변경은 양 담당 합의 + docs 저장소 정본·샘플 동시 갱신 + 팀 컨벤션대로 해당 파트 담당 리뷰어 지정 | 원칙 |
| 2026-11-12 연동 | 백엔드 `live_ai` 마커 테스트를 실행 중인 AI 서비스에 대해 실행(계약 샘플과 같은 요청), 프론트–백엔드 E2E 실행 | 원칙 |

### 연습 출제 규칙 (domain — ADR-0009)

> **2026-11-11 메모 (사용자 확정 — DECISIONS #111·#115)**: 아래 표의 `variants.json`·`{tone, platform, persona}`·`review` 재시도는 옛 규격이다. 1차는 다음으로 읽는다 — 변형 값 = 시나리오 `variation_axes` 안의 `platform`·`tone`·`context`(백엔드 domain이 시드 난수로 고름), F-12·다시 도전 차이 = 직전 세션과 `platform` 또는 `tone` 1개 이상 다름, 플랫폼 후보 = 오버레이 `platform_app_types.json`으로 `favorite_apps`에 맞는 것 우선, 학년 제한 `min_grade` = 오버레이 `scenario_meta.json`, 출제 전 검수 = AI `variant`의 `check_variant`(백엔드 `review`·`REVIEW_MAX_ATTEMPTS` 경로 없음 — `NO_SCENARIO_AVAILABLE`은 후보 없음에만). 정상 상황 비율 규칙은 정상 상황 출제를 켤 때 적용(#110 — 1차는 꺼짐). 상세는 "1차 내부 API v1"의 `variant` 행(#102).

| 규칙 | 결정 | 상태 |
|---|---|---|
| 학년 제한 (F-14 ②) | 시나리오의 `min_grade`가 `H1`이면 `grade ∈ {H1,H2,H3}`인 아이에게만 후보로 둔다. 고수익 알바 시나리오는 콘텐츠에서 `min_grade: "H1"` | 결정 |
| 정상 상황 비율 30% (F-17 ① "산정 방식은 설계에서 확정") | 아이별 새 출제 순번 `draw_index`(1부터, retry 제외)가 `draw_index mod 10 ∈ {4, 7, 0}`이면 정상 상황, 그 외는 위험 상황 → 10회마다 정확히 3회. 해당 영역에 정상 상황이 없으면 위험 상황으로 대체하고 순번은 소비 | 결정 |
| 다시 도전 (F-13 ③, F-12) | 직전 세션과 같은 `scenario_id`·같은 `target_cue_ids`, 변형 `{tone, platform, persona}`는 직전 변형과 1개 이상 다르게 선택. 정상 혼합 대상 아님 | 결정 |
| 변형 선택 (F-12) | 백엔드 domain이 시드 주입 난수로 결정해 AI에 넘긴다(AI가 정하지 않음 → F-12를 LLM 없이 테스트 가능) | 결정 |
| 플랫폼 (F-08) | `variants.json`의 플랫폼 중 `app_type ∈ favorite_apps`인 것에서 고름. 없으면 기본 플랫폼 목록 | 결정 |
| 약점 우선 (F-18 ①) | 최근 기록에서 `missed` 횟수가 임계값 이상인 단서를 포함한 시나리오를 우선 후보로. 임계값·기간은 설정 상수 [OQ 14] | 구조 결정, 수치 [OQ 14] |
| 힌트 감소 (F-18 ②) | 목표 단서별 연속 `found` 횟수 c에 대해 `hint_level = max(0, HINT_MAX − c)` — c가 늘면 힌트 단계가 줄거나 같음(단조). `HINT_MAX` 값 [OQ 14] | 구조 결정, 수치 [OQ 14] |
| 시작 난이도 (F-07) | 진단 3문항 점수 → `start_difficulty` 매핑은 콘텐츠 `diagnosis.json` | 구조 결정, 단계 수 [OQ 14] |
| 오늘의 미션 (F-10) | `mode:"mission"` = 영역 미지정 새 출제(위 규칙 그대로). 구성 규칙 [OQ 13 중 미션 — 보류] | 임시 구조 |
| 출제 전 검수 (F-42) | 생성 → `review` 불통과 → 다음 후보 시나리오로 재시도, 최대 `REVIEW_MAX_ATTEMPTS`(설정 상수) → 소진 시 `NO_SCENARIO_AVAILABLE` | 구조 결정, 통과 기준 [OQ 25] |

### 성장 계산 규칙 (domain — 2026-11-11 신규, PRD OQ 12·13·31 해소, DECISIONS #87~#91. 2026-11-11 최종 규격 DECISIONS #116 — 분모·배지는 사용자 확정 N1 #109)

공통: 대상 세션은 `status = ended`(`origin` 무관 — 예시 데이터 포함). 세션 날짜 = `ended_at`의 한국 시간 날짜, 오늘 = 주입 `Clock`의 한국 시간 날짜(공통 값 타입 "시각" 행). domain 함수는 날짜·범주값·개수만 받는 순수 함수(권고 위치 `app/domain/metrics.py`·`badges.py`). "위험 상황 세션" = `is_normal = false`. 상수는 설정 1곳: `METRIC_PERIOD_DAYS = 7`, `METRIC_MIN_SESSIONS = 3`, `BADGE_REQUIRED_SESSIONS = 3`.

> **2026-11-11 확정 (DECISIONS #116)**: 기간·한국 시간(#94), 지표 (다) 원천(#93, `kind = correct`), (가)(나) 분모와 배지 조건(**사용자 확정 N1 — #109, 답 "드러난 단서만 판정 (추천)"**)이 모두 정해졌다. `cue_results` = 드러난 단서의 판정(`found`·`missed`)만 — `not_shown`은 저장·집계하지 않는다. 따라서 아래 표의 "`cue_results` 수" = 그 세션들의 `found`+`missed` 수. 제외 대상: `in_progress`·`stopped`(#113) 세션은 모든 규칙에서, 정상 상황 세션은 지표 (가)(나)(다)·배지에서 빠진다(1차는 정상 상황 출제가 꺼져 있음 — #110). 연속 기록만 정상 상황 종료 세션을 센다. 사용자가 받아들인 단점(원문 "한 세션에서 단서 1개만 맞혀도 성공으로 셈"): 배지 세션 ≈ 드러난 단서를 놓치지 않고 바로 알아챈 세션. ★ ~~architect 판단 1건~~ **사용자 확정(2026-11-11 "빼기 (추천)", DECISIONS #117)**: `found`+`missed` = 0인 세션은 (가)(나)의 분모 세션에서 뺀다(0 나누기 방지 — 아래 표 (가)(나) 행) — "비교 불가"의 세션 수 계산에도 세지 않는다. 해석 7(`stopped`는 연속 기록의 연습한 날 아님)도 사용자 확정(#119).

| 규칙 | 결정 | 근거 |
|---|---|---|
| 기간 창 | 이번 기간 = [오늘 − 6일, 오늘], 직전 기간 = [오늘 − 13일, 오늘 − 7일] (한국 시간 날짜, 양끝 포함) | F-29 ⑤ (가) "최근 7일 vs 직전 7일", planner 해석 7·8(사용자 확정) |
| 지표 (가) `missed_ratio` | 기간 안 위험 상황 세션의 `missed` 수 ÷ 그 세션들의 (`found`+`missed`) 수. 분모 세션 = 기간 안 위험 상황 종료 세션 중 `found`+`missed` ≥ 1인 세션(★) | F-29 ⑤ (가), 해석 1(정상 상황은 단서 0개라 자연히 빠짐). 분모 = 드러난 단서 수(사용자 확정 N1 — #109, `judge` 검증 J1'·J2'로 드러난 단서마다 정확히 1개). ★ #116 → 사용자 확정 #117 |
| 지표 (나) `first_seen_accuracy` | 분모 세션 = 기간 안 위험 상황 종료 세션 중 `mode ≠ retry`이고, 같은 아이의 같은 `scenario_id` 세션(상태·`origin`·기간 무관) 가운데 `started_at`이 가장 이른 세션이며 `found`+`missed` ≥ 1(★). 값 = 그 세션들의 `found` 수 ÷ (`found`+`missed`) 수 | F-29 ⑤ (나) "같은 시나리오를 이전에 받은 적 없는 세션, 다시 도전 세션 제외" — "받음" = 세션 생성(중도 이탈·`stopped` 세션도 받은 것으로 셈 — 그 경우 가장 이른 세션이 종료 세션이 아니므로 그 시나리오는 (나)에 들지 않음). 분모 N1 — #109 |
| 지표 (다) `ahead_of_ai_ratio` | 분모 세션 = 기간 안 위험 상황 종료 세션(다시 도전 포함 — 정의에 제외 조건 없음, ★ 적용 안 함). 값 = 그중 `turn_index` 0에서 고른 선택지 `kind = correct`인 세션 수 ÷ 분모 세션 수. 원천은 `PracticeRepo.first_answer_judgments`(이름 권고 `FirstAnswerKind` 반환 — 엔티티 `practice_turns` 예외, ADR-0016, #93). 종료 세션인데 첫 답 `kind`가 없으면 domain 예외(500) — 임의로 세지 않음 | F-29 ⑤ (다), 해석 5 "분모는 위험 상황 세션만"(사용자 확정), #93·#115 |
| 비교 불가 | 지표마다 이번·직전 기간 각각의 분모 세션 수를 세어, 어느 한 기간이라도 `METRIC_MIN_SESSIONS` 미만이면 `insufficient`(`current`·`previous` null, `trend` []). 둘 다 이상이면 `ok`(두 값 + `trend` 2점) | F-29 ⑥, 해석 6 "지표별로 그 지표 분모에 들어가는 종료 세션 수"(사용자 확정). "한 기간이라도"는 글자 그대로의 해석 — [A-19] |
| 추이(`trend`) | `ok`일 때 `[{date: 직전 기간 마지막 날, value: previous}, {date: 오늘, value: current}]` 2점 | F-31 "2회 이상 기록된 지표 … 추이 그래프" — 2점이 최소. 더 긴 추이는 [A-20] |
| 지표 신호등 (`MetricView.level`) | 규칙 없음 — PRD OQ 63 ② 답 전까지 null | PRD OQ 63(지어내지 않음) |
| 배지 | 영역마다, 위험 상황 종료 세션 중 그 `area`이고 `missed` 0개·`found` 1개 이상인 세션(다시 도전 포함, `origin` 무관)이 `BADGE_REQUIRED_SESSIONS` 이상이면 "혼자 할 수 있어요" 배지 1개(`badge_id = "independent:{area}"`). 기간 제한 없음(누적). `stopped` 세션 제외 | F-28 ②, 해석 2(정상 상황 제외)·3(다시 도전 포함)(사용자 확정), 성공 세션 조건 = 사용자 확정 N1(#109 원문 "배지 성공 세션 = 놓침 0개 + 찾음 1개 이상"), #116 |
| 연속 기록 (`streak_days`) | 모든 종료 세션(위험·정상·다시 도전 — `status = ended`만, `stopped` 제외 #113)의 날짜 집합 D. 오늘 ∈ D면 시작 = 오늘, 아니고 어제 ∈ D면 시작 = 어제, 둘 다 아니면 0. 시작일부터 하루씩 거슬러 D에 있는 동안 센 일수 | F-28 ③, 해석 4(사용자 확정) |
| 저장 여부 | 배지·연속 기록·지표 모두 저장하지 않고 요청마다 계산(A13·A19·A11) | DECISIONS #28 유지·#90 |
| 오늘의 미션 | 이 절 범위 밖 — [OQ 13 중 미션 — 보류] | PRD OQ 13 남은 질문 |

### 콘텐츠 파일 규격 (2026-11-06 갱신 — 작성 담당 [OQ 3])

> **2026-11-11 메모 (사용자 확정 "AI 저장소 원본 (추천)" — DECISIONS #107 → #111)**: 아래 백엔드 `cues.json`·`scenarios.json`·`variants.json`은 만들지 않고(아래 표는 이력으로 남김 — `diagnosis.json` 행만 유효), ai 저장소 `content/clues.json`(`{version, areas[{id,name}], clues[{id, areas, keywords, choice_templates, name, description, found_when, safe_action, example_lines}]}`)·`content/scenarios/{area}.json`(`{version, area, ai_rules, scenarios[{id, title, platform, difficulty, ai_role, child_setup, opening_line, clues[{id, at_opening?, reveal_when, reveal_line}], safe_ending, variation_axes{platform, tone, context}, normal_situations[]}]}`)의 읽기 전용 사본 + 오버레이(`scenario_meta.json`·`platform_app_types.json`)로 바뀐다(구조는 커밋 331d2c6 기준, 인용 아님 — 직접 확인). `diagnosis.json`은 그대로. ~~답 전에는 아래 표를 유지한다.~~

backend 저장소 `app/content/data/`:

| 파일 | 규격 |
|---|---|
| `cues.json` | `[{id, area, label(쉬운 말 짧은 이름), explanation(쉬운 말 1문장)}]` |
| `scenarios.json` | `[{id, area, subtype\|null, is_normal, target_cue_ids:[], min_grade: Grade\|null, situation_seed(예시 데이터 — N-11), platform_ids:[]}]` |
| `variants.json` | `{tones:[{id,label}], personas:[{id,label}], platforms:[{id,label,app_type}], default_platform_ids:[]}` |
| `diagnosis.json` | `{questions:[{id, text, options:[{id, text, score}]}] (3개), difficulty_by_score:[...]}` |

**2026-11-11 추가(PRD OQ 64 사용자 답 "고정 문구+홈, 알림 없음 (추천)" — DECISIONS #118)**: 백엔드 소유 보충 파일 `safety_stop.json` = `{version, message}` — safe_reply 멈춤 안내 고정 문구(사람이 씀 — 믿는 어른·상담 전화 안내, 쉬운 말 N-03). 서버 시작 시 검증(`message` 공백만 아님, 길이 ≤ `SAFETY_STOP_MAX_CHARS = 300`), 실패면 시작하지 않음. 문구 내용·전화번호는 설계가 정하지 않음 — 콘텐츠 담당(PRD OQ 3)·사용자 확인. ai 사본(`app/content/data/ai/`)과 별개 파일.

ai 저장소 소유(권고 — [팀 요청 AI-1]): `fallbacks.json`(안전 필터 차단·생성 실패 시 대체 문구, 쉬운 말), `safety_rules.json`(입·출력 차단 규칙 — [OQ 25]).

서버 시작 시 Pydantic으로 전부 검증하고(참조 무결성: `target_cue_ids`가 `cues.json`에 존재 등), 실패하면 시작하지 않는다. 시나리오의 전화번호·URL·계좌번호는 실제 형식이 아닌 예시 표기만 쓴다(N-11) — AI 서비스 안전 필터 규칙과 충돌하지 않게.

### 계층 규칙 (2026-11-06 갱신)

기준은 `.agents/skills/clean-architecture/SKILL.md`.

| 항목 | 결정 |
|---|---|
| 의존성 방향 | Domain ← Use case(services) ← Adapter(api·repositories·ai_client) ← Framework(FastAPI·SQLAlchemy·httpx) (역방향 금지). `domain/`은 FastAPI·SQLAlchemy·Pydantic 외부 의존 없음(표준 라이브러리 dataclass) |
| Repository 포트 | `services/ports.py`에 `typing.Protocol`로 정의(GuardianRepo, ChildRepo, SessionRepo, PracticeRepo, NoticeRepo). 구현은 `repositories/`. services는 생성자 주입으로 받음(FastAPI `Depends`는 api 계층에서만) |
| AI 포트 | `ai_client/ports.py`의 `PracticeAI`(`opening`, `next_turn`, `judge`, `feedback`). services는 이 포트만 import — `ai_client/http_client.py`·`fake.py`를 직접 import 금지(선택은 `factory.py`) |
| DTO ↔ 도메인 변환 위치 | API DTO(Pydantic) ↔ 서비스 입출력은 `api/` 라우터의 매퍼에서. ORM 모델 ↔ 도메인 객체는 `repositories/`에서. 내부 API DTO ↔ 서비스 입출력은 `ai_client/`에서. ORM 모델을 API 응답으로 직접 반환 금지 |
| 순환 의존성 | 금지. 자동 검사: `tests/unit/test_import_boundaries.py` (DECISIONS #44) — ① 백엔드 어디에도 AI 제공사 SDK(`google.genai` 등) import 없음 ② `httpx` import는 `app/ai_client/http_client.py`만(테스트 제외) ③ `app/services`는 `app.ai_client.ports`만 import ④ `app.domain`이 `fastapi`·`sqlalchemy`를 import하지 않음 |

## 화면 메커니즘 (PRD "화면" 절 실현 — 2026-11-06 갱신: frontend 저장소 구현, 아래는 백엔드 계약과 맞물리는 합의안)

frontend 저장소는 프론트 담당 소유다(ADR-0012). 아래 경로·가드·상태 처리는 공개 API와 맞물리는 부분이라 설계로 정하되, 파일 배치는 프론트의 기존 규칙("화면은 피그마 프레임 1개당 파일 1개로 src/pages/", 첫 줄 주석에 프레임 번호 — 인용)을 따른다. 경로 이름은 프론트 담당과 합의 후 바꿀 수 있으나, 가드·상태 처리 규칙은 PRD 화면 상태를 충족해야 한다 [팀 요청 F-5].

### 라우팅과 화면별 상태 소유

| 화면 | 경로 (합의안) | 가드 | 데이터 (API) | 빈 값·로딩·에러·권한없음을 무엇이 처리하는가 |
|---|---|---|---|---|
| S0 | `/` | 없음 | 없음 (정적) | 서버 요청 없음 — PRD의 "없음 — 사유" 그대로. 보호자 → `/guardian/login`, 아이 → `/child/login` (F-45) |
| (분기) | `/guardian` | RequireGuardian | A8 | 아이 0명 → G2, 1명 이상 → 첫 아이의 G3. 여러 명이면 G3 상단에서 선택 |
| G1 | `/guardian/login` (로그인·가입 탭) | 없음 (이미 보호자 세션이면 `/guardian`) | A2, A3 | 클라이언트 필수값 검증 + 서버 422 필드 오류 / 제출 중 버튼 비활성·처리 중 표시 / `EMAIL_TAKEN`·`INVALID_CREDENTIALS` 문구 |
| G2 | `/guardian/children/new` | RequireGuardian | A7, A8 | 동의 미체크 시 등록 버튼 비활성(서버도 `CONSENT_REQUIRED`) / 아이 없음 안내 / 별명·학년·PIN(숫자 4자리) 입력 → 연결 완료 후 발급된 연결 코드를 표시(2026-11-07 변경 — 코드는 등록 전에 보이지 않음, PIN은 서버 응답에 없음). PIN 형식 오류는 422 `VALIDATION_ERROR` 필드 오류 |
| G3 | `/guardian/children/:childId/report` | RequireGuardian | A11 | 화면 상태 공용 컴포넌트: 로딩·에러(다시 시도) / 빈 값 3종(기록 없음·안전 알림 없음·그래프 데이터 부족) / `CHILD_NOT_FOUND` → 권한없음 안내 |
| G4 | `/guardian/children/:childId/credentials` | RequireGuardian | A9, A10 | PIN 재설정은 보호자가 새 PIN(숫자 4자리)을 입력(2026-11-07 변경), 성공 시 "새 PIN으로 바뀌었어요" 류 확인(평문 재표시 없음). 코드 재발급은 서버가 만든 새 코드를 표시 / 실패 시 "이전 값 유지" 안내 + 다시 시도 / 아이 없음 → G2 안내 / `CHILD_NOT_FOUND` → 권한없음 |
| Y1 | `/child/login` | 없음 | A4 | 코드·PIN 미입력 시 입장 버튼 비활성 / 확인 중 표시 / `INVALID_CODE_OR_PIN` → 쉬운 말 + "보호자에게 PIN 재설정을 부탁해요" 류 안내 |
| Y2 | `/child/setup` | RequireChild | A12 | 필수 단계 미완료 시 다음 비활성(자주 쓰는 앱은 선택) / 저장 중 / 실패 시 입력 유지 + 다시 시도 |
| Y3 | `/child/home` | RequireChild + 첫 설정 완료(미완료면 Y2) | A13, A14 | 화면 상태 공용 컴포넌트 / 배지 0 안내 / 연락 버튼 상시 |
| Y4 진입 | `/child/practice/start?mode=…&area=…` 또는 `?mode=retry&retryOf=…` | RequireChild | A15 (체크인 후) | 감정 온도계 단계(클라이언트 상태만) → 생성 중 표시 → `NO_SCENARIO_AVAILABLE` 빈 값 안내 + 홈으로 / `AI_UNAVAILABLE` 에러 + 다시 시도 |
| Y4 | `/child/practice/:sessionId` | RequireChild | A16, A17 | 대사 생성 중 표시 / `substituted`면 대체 대사 그대로 표시 / `AI_UNAVAILABLE` 다시 시도(같은 선택지로 A17 재요청 — 서버는 실패한 요청의 선택을 저장하지 않음) / A17·A16 응답 `status: "ended"`(`turn: null`) → 바로 Y5로 이동(마무리 대사 없음 — PRD OQ 62 ① 사용자 답 "바로 결과 화면", 2026-11-08 `is_terminal`에서 변경, DECISIONS #82). 종료하는 답의 A17도 판정(`judge`)을 기다리므로 로딩 표시는 같다 / `SESSION_ENDED`(409 — 다른 탭 등에서 이미 끝남) → Y5로 이동 / `SESSION_NOT_FOUND` → 홈 / **멈춤(2026-11-11 — DECISIONS #113·#118, PRD OQ 64 사용자 답 "고정 문구+홈, 알림 없음 (추천)")**: A17·A16 응답 `status: "stopped"` → `turn.ai_line`(백엔드 고정 문구)을 선택지 없이 보이고 "홈으로" 버튼 1개(→ Y3), Y5로 가지 않음, 새로고침해도 같은 상태 / `SESSION_STOPPED`(409) → A16을 다시 불러 같은 멈춤 상태 |
| Y5 | `/child/practice/:sessionId/result` | RequireChild | A18 | 결과 분석 중 / 놓친 0 "모두 찾았어요"·찾은 0 격려 문구 / 에러 다시 시도 / "다시 도전" → Y4 진입(retry) / 심화 연습 → Y5-1 (2026-11-07) |
| Y5-1 (2026-11-07 신규, 피그마 "Y6 심화학습 넘어가기") | `/child/practice/:sessionId/deep` | RequireChild | 1차 기본안: 없음 — Y5가 받은 A18 응답을 프론트 상태로 넘겨 씀(A18 재요청 금지 — 요청마다 AI `feedback` 호출). A20은 조건부(2026-11-07, DECISIONS #73) | 1차 기본안: 빈 값: OQ 50 ① 답 이후 확정 / 로딩·에러: 없음 — 서버 요청 없음. 프론트 상태가 없으면(새로고침·주소 직접 입력) Y5로 이동 — 404·409·에러는 Y5가 처리. A20을 되살리면: 로딩: 불러오는 중 / 에러: 다시 시도 + Y5로 돌아가기 / `SESSION_NOT_ENDED`·`SESSION_NOT_FOUND` → Y5 또는 홈 |
| Y5-2 (2026-11-07 신규, 피그마 "Y7-1") | `/child/practice/:sessionId/deep/text` | RequireChild | **1차 기본안: 없음 — 서버 요청 없음**(PRD OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #72·#76). [2차 — T-82] A21 | 1차: 빈 값: 미입력 시 제출 비활성(입력 상한 500자는 2차 A21 규격과 맞추는 권고 — 프론트 결정) / 로딩: 없음 — 서버 요청 없음(제출 = Y5-4로 화면 이동) / 에러: 없음 — 서버 요청 없음 / 위험 표현 안내: 탐지 없이 입력란 근처 고정 안내 문구(프론트 상수) 권고 — 둘지·문구는 PRD OQ 60(2026-11-08 OQ 59 ②에서 분리 — DECISIONS #74·#77). 입력 글은 프론트 메모리 상태로만 들고 있고 브라우저 저장소(localStorage·sessionStorage 등)·URL 쿼리에 남기지 않으며 어떤 API 요청에도 넣지 않음. **[2차 — T-82]** 로딩: 제출·피드백 생성 중 / 에러: `AI_UNAVAILABLE` → **입력 유지** + 다시 시도, 422 → 길이 안내 / `substituted` → 대체 안내를 Y5-4에 표시 |
| Y5-3 (2026-11-07 신규, 피그마 "Y7-2") | `/child/practice/:sessionId/deep/voice` | RequireChild | 1차 기본안: 없음 — 서버 요청 없음(Y5-2와 같은 처리). [2차 — T-82] A21 (Y5-2와 같은 요청) | 1차: 빈 값: 바뀐 글이 없으면 제출 비활성 / 로딩: 듣는 중·바꾸는 중(제출은 화면 이동) / 에러: 마이크 권한 거부·브라우저 미지원·인식 실패 → 쉬운 안내 + Y5-2로 이동. 바뀐 글은 Y5-2와 같은 프론트 상태로 넘김. 음성 데이터는 어떤 API 요청에도 넣지 않음(ADR-0014 — 브라우저 제조사 서버 전송 가능성은 D-9). **[2차 — T-82]** `AI_UNAVAILABLE` → 바뀐 글 유지 + 다시 시도 |
| Y5-4 (2026-11-07 신규, 피그마 "Y7-3") | `/child/practice/:sessionId/deep/result` | RequireChild | 1차 기본안: 없음 — OQ 50 ③ 후보에 따라 (a) 고정 문구 = 프론트 상수 / (b) Y5 단서 설명 다시 보기 = Y5가 받은 A18 응답(프론트 상태) / (c) 아이 답변 다시 보기 = 프론트 상태. [2차 — T-82] A21 응답(A-17 A안) 또는 A22(B안) | 1차: 빈 값: OQ 50 ③ 답 이후 확정 / 로딩·에러: 없음 — 서버 요청 없음. 새로고침으로 프론트 상태를 잃으면 (b)는 Y5로, (c)는 Y5-2로 안내((a)만이면 그대로 표시 가능). **[2차 — T-82]** A안에서 새로고침으로 응답을 잃으면 Y5-2로 안내 / 로딩·에러: B안일 때 A22 기준 |
| Y5-5 (2026-11-07 신규, 피그마 "Y7-4 선택 전/후") | `/child/practice/:sessionId/deep/next` | RequireChild | 선택지가 이동뿐이면 없음, 아니면 A23 | 빈 값: 선택 전 다음 버튼 비활성 / 로딩: 이동 중 / 에러: 이동 실패 시 다시 시도. 선택지는 OQ 50 ④ |
| Y8 | `/child/growth` | RequireChild | A19 | 기록 없음 안내 / 지표 `insufficient` → "비교 불가" / 에러 다시 시도 |

- 가드: A6(`GET /auth/me`)으로 역할을 확인한다. RequireGuardian은 `role ≠ guardian`이면 `/guardian/login`, RequireChild는 `role ≠ child`이면 `/child/login`으로 보낸다. API가 401을 주면 같은 규칙으로 이동한다.
- 서버 상태의 원본은 서버다. 연습 진행 중 새로고침은 A16으로 현재 턴을 복구한다.
- Y3 "지금 이거 수상해?" 진입(F-09 ②, 2차): 프론트 기능 플래그(값 `"hidden" | "coming_soon"`)로 처리 권고 — 어느 값으로 둘지 [OQ 44].

### 재사용 컴포넌트 경계 (권고 — 프론트 담당 결정)

| 컴포넌트 | 책임 | 사용 화면 |
|---|---|---|
| 화면 상태 공용 컴포넌트 | 요청 상태를 받아 로딩·에러(다시 시도 버튼)·빈 값(문구 인자)을 한 방식으로 표시. 서버 상태 관리 라이브러리(TanStack Query 등) 사용 여부는 프론트 결정 | G2·G3·G4·Y2·Y3·Y4·Y5·Y8 |
| SignalCard | `level`(red/yellow/green) + 문장 1개 → 색·아이콘·글자 라벨을 함께 표시, 카드 1장 = 문장 1개 (F-26). 색만으로 의미 전달 금지 | Y5, Y8 |
| TtsButton | `tts_enabled`이고 브라우저가 `speechSynthesis`를 지원할 때만 보임, 해당 문장 읽기 (F-27, ADR-0008) | Y4, Y5 |
| TrustedContactButton | 믿는 사람 `tel:`/`sms:` 링크 열기 + A14 기록 (F-23 ②③) | Y3 |
| EmotionCheckIn | 4개 선택지, '급해요'·'불안해요'면 진정 가이드 먼저 표시, 값은 컴포넌트 밖으로 나가지 않음 (F-25) — **어떤 API 요청에도 넣지 않는 것은 필수** | Y4 진입 |
| 표시 설정 적용 | A6의 `display`로 글자 크기·고대비를 모든 아이 화면에 적용 (F-05) | 아이 화면 전체 |
| 라우트 가드 | RequireGuardian / RequireChild | 라우터 |

시각적 완성도(타이포·색·모션)는 설계 대상이 아니다 — T-02 디자인과 구현 단계 몫.

## 보안·개인정보 (N-05 — 2026-11-06 갱신: CORS·내부 토큰 행 추가)

| 항목 | 결정 |
|---|---|
| 인가 — 보호자 | `{child_id}` 경로가 있는 모든 보호자 API는 services의 `get_owned_child(guardian_id, child_id)`(두 조건을 한 쿼리로)를 거친다. 없거나 남의 아이면 404 `CHILD_NOT_FOUND`. IDOR 통합 테스트 필수(F-02 ④, F-30 ④ — T-07·T-25) |
| 인가 — 아이 | 아이 API는 세션의 `subject_id`만 쓴다. 연습 세션 ID 접근은 `session.child_id == 세션 주체` 확인, 아니면 404 |
| 역할 분리 | 보호자 세션으로 아이 API, 아이 세션으로 보호자 API 호출 시 403 `FORBIDDEN_ROLE` |
| 비밀번호·PIN | Argon2id 해시. 비밀번호 8~128자. PIN은 보호자 입력(2026-11-07 변경) — 평문은 등록·재설정 요청 본문에만 존재하고 어떤 응답·DB·로그에도 없음 |
| 세션 토큰 | `secrets.token_urlsafe(32)`, DB에는 SHA-256 해시만. 만료: 보호자·아이 모두 7일(설정 상수). PIN 재설정·코드 재발급 시 그 아이의 세션 전부 폐기 |
| CORS | 켜지 않는다. 프론트는 같은 출처 프록시로만 호출(ADR-0013) — 교차 출처 호출이 실패하는 것은 의도된 동작 |
| CSRF | 같은 출처 + `SameSite=Lax` + 상태 변경 요청은 `Content-Type: application/json`만 허용 |
| 백엔드–AI 서비스 인증 | `X-Internal-Token` 공유 시크릿(`AI_SERVICE_TOKEN`). AI 서비스 URL은 공개 PaaS 주소이므로 토큰 없는 요청은 401. 토큰은 양쪽 환경 변수에만 |
| AI로 가는 데이터 | `ScenarioSpec`에 아이 식별 필드 없음(규격으로 차단). 연습 대화(Y4)의 아이 입력은 선택지 ID뿐(자유 입력 F-38은 2차). **2026-11-07 PRD OQ 55 해소 후(사용자 확인 대상)**: 1차에는 아이가 직접 쓴 글이 AI 서비스·Gemini로 가는 경로가 없다 — 심화 연습 AI 피드백은 2차이고, 1차 Y5-2·Y5-3 답변은 우리 서버로도 보내지 않는다(PRD OQ 59 기본안, DECISIONS #72). **[2차 — T-82]** 심화 연습(F-48)의 `answer_text`는 아이가 직접 쓴(또는 말을 바꾼) 글이 AI 서비스와 Gemini로 가는 첫 경로가 된다 — 피해 고백·개인정보가 섞일 수 있음(PRD R-8). 대응: AI 서비스 입력 필터가 개인정보 형식이면 LLM 호출 없이 대체 안내, 아이 ID·별명은 함께 보내지 않음, 무료 Gemini 키면 입력이 개선·인적 검토에 쓰일 수 있음(A-13, PRD OQ 46) |
| 보호자 비공개 범위 | 위 "보호자용 응답 금지 필드" + guardian_notices에 본문 열 없음 + 감정 값 저장·전송 경로 없음 |
| 로그 | 요청 본문·쿠키·비밀번호·PIN·연결 코드·이메일·내부 토큰·**아이 자유 답변(`answer_text`)과 심화 연습 피드백 문장**(2026-11-07 추가)을 로그에 남기지 않는다. 422 오류의 `details`에도 값은 넣지 않는다. 식별은 내부 UUID만 |
| 입력 검증 | 모든 요청 DTO에 타입·길이·허용값(enum) 검증. SQL은 ORM 매개변수 바인딩만(문자열 조립 금지). 프론트는 React 기본 이스케이프 사용, `dangerouslySetInnerHTML` 금지 권고 |
| 알려진 한계 | PIN 4자리 + 오류 횟수 제한 없음(F-44 보류) → 연결 코드를 아는 사람의 무차별 대입에 약하다. 2026-11-07부터 PIN을 보호자가 고르므로 1234 같은 쉬운 PIN이 가능해 더 약해진다(사용자 승인 추천안 원문 "보호자가 1234 같은 쉬운 PIN을 고를 수 있습니다. 지금은 오류 횟수 제한(F-44)도 보류된 상태라 보안이 더 약해집니다. 1차는 예시 데이터만 쓰니 받아들일 수 있는 수준"). 1차는 수용. **운영 전 과제**: F-44 오류 횟수 제한과 쉬운 PIN 거부 규칙을 함께 도입 |

### 시크릿과 환경 변수 (2026-11-06 갱신)

실제 `.env`는 에이전트가 읽기·수정·출력하지 않는다(AGENTS.md 시크릿 관리). `.env.example`에는 플레이스홀더만 두며, 아래 backend 변수는 T-01에서 implementer가 `.env.example`에 추가한다(architect 역할 원본은 Architecture·DECISIONS·adr 외 파일 수정을 금지).

backend 저장소:

| 변수 | 시크릿 | 용도 |
|---|---|---|
| `APP_ENV` | 아니오 | `local` / `test` / `production` |
| `PORT` | 아니오 | 로컬 기본 8080 (DECISIONS #39), 운영은 PaaS 제공 값 |
| `DATABASE_URL` | 예 | Postgres 접속 문자열 (로컬·테스트는 SQLite 경로) |
| `AI_CLIENT` | 아니오 | `http` / `fake` (테스트·로컬·E2E 기본 `fake`) |
| `AI_SERVICE_URL` | 아니오 | AI 서비스 기준 URL (로컬 권고 `http://localhost:8081`) |
| `AI_SERVICE_TOKEN` | 예 | 백엔드–AI 내부 인증 토큰 (AI 서비스와 같은 값) |
| `AI_SERVICE_TIMEOUT_SECONDS` | 아니오 | AI 서비스 호출 시간 초과 |
| `COOKIE_SECURE` | 아니오 | 운영 `true` |
| `LOG_LEVEL` | 아니오 | 운영 `INFO` |

ai 저장소(권고 — [팀 요청 AI-2]): `GEMINI_API_KEY`(시크릿 — AI 서비스에만), `GEMINI_MODEL`, `AI_PROVIDER=gemini|fake`, `AI_SERVICE_TOKEN`(시크릿), `PROVIDER_TIMEOUT_SECONDS`(백엔드 `AI_SERVICE_TIMEOUT_SECONDS`보다 짧게).

frontend 저장소(요청 — [팀 요청 F-3]): `VITE_API_URL`은 **비워 둔다**(설정하면 교차 출처가 되어 쿠키 세션이 동작하지 않음). 백엔드 공개 URL은 `vercel.json` 리라이트 대상에 리터럴로 적는다(시크릿 아님. `vercel.json`이 환경 변수를 치환하지 않는다고 보고 — 추정, T-27에서 확인).

## AI 제공사 정책 기록 (N-09 — 2026-11-06 갱신: 호출 위치가 AI 서비스로)

N-09 "그 밖의 제공사(TTS 등, OCR은 2차)는 미성년자 이용 조건 확인 기록을 설계 문서에 남긴 뒤 사용한다"에 따른 기록이다.

| 제공사·용도 | 정책 확인 기록 | 설계 대응 |
|---|---|---|
| Gemini API — 연습 대화 생성·검수·피드백 (1차 시연, N-09 확정). 호출 위치: ai 저장소 AI 서비스 | PRD 리스크 R-1 원문(메인 세션 2026-11-02 확인, (인용) — architect 재확인 안 함): Gemini API Additional Terms(https://ai.google.dev/gemini-api/terms, 2026-04-28 갱신): "You must be 18 years of age or older to use the APIs." / "You also will not use the Services as part of a website, application, or other service (collectively, "API Clients") that is directed towards or is likely to be accessed by individuals under the age of 18." — 보호자 동의 등 예외 조항 없음. Google Cloud Service Specific Terms 20(d): "Customer will not, and will not allow End Users to, use a Generative AI Service as part of a website, Customer Application, or other online service that is directed towards or is likely to be accessed by individuals under the age of 18." 20(f): 위반 의심만으로 즉시 정지·종료 가능. | 사용자가 위험을 인지하고 1차 시연 사용을 확정했고(PRD 머리글), 배포 URL 공개도 사용자 결정(N-07) — 설계는 이 결정을 바꾸지 않는다. 설계가 줄이는 것은 **교체 비용과 데이터 노출**뿐이며 약관 해당 위험 자체는 줄이지 않는다(법률 검토 아님): ① 제공사 교체는 ai 저장소 안의 일 — 백엔드 무변경(N-10, ADR-0011) ② AI로 가는 데이터에 아이 식별 정보 없음(규격으로 차단) ③ 시연·테스트는 예시 데이터만(N-11) ④ 키 정지 시 AI 서비스가 503 → 백엔드 `AI_UNAVAILABLE` → 연습 화면만 에러 상태, 나머지 화면(가입·리포트·성장)은 동작 |
| Gemini 무료/유료 등급의 데이터 활용 조건 (2026-11-06 메인 세션 확인) | 확인 출처(인용 — architect 재확인 안 함): 메인 세션이 2026-11-06 Browser pane으로 https://ai.google.dev/gemini-api/terms → https://aistudio.google.com/docs/terms 로 이동한 **한국어판** "Gemini API 추가 서비스 약관", 페이지 표기 "시행일: 2026년 3월 23일". 영문판 원문은 이번에 확인하지 않았다(한국어 번역판 인용). PRD R-1의 영문판 표기 "2026-04-28 갱신"과 날짜가 다르다 — 어느 쪽이 최신인지 판단하지 않았다. 원문 발췌: 무료 서비스 정의 "Google AI Studio와의 직접적인 상호작용이나 Gemini API의 무료 할당량과 같이 무료로 제공되는 모든 '서비스'입니다('무료 서비스')." / 무료 서비스 데이터 "Google은 귀하가 '서비스'에 제출한 콘텐츠와 생성된 대답을 사용하여 … Google 제품 및 서비스와 머신러닝 기술을 제공하고, 개선하고, 개발합니다." / "인적 검토자가 귀하의 API 입력 및 출력을 읽고, 주석을 달고, 처리할 수 있습니다." / "민감한 정보, 기밀 정보 또는 개인 정보를 '무료 서비스'에 제출하지 마세요." / 유료 전환 조건 "Cloud Billing 계정을 활성화하면 … 무료로 제공되는 서비스를 사용하는 경우에도 Google에서 귀하의 데이터를 사용하는 방식 측면에서 '유료 서비스'로 간주됩니다." / 유료 서비스 데이터 "Google은 귀하의 프롬프트 … 또는 대답을 Google 제품을 개선하는 데 사용하지 않으며" / "Google은 제한된 기간 동안 프롬프트와 대답을 기록하며, 이러한 기록은 금지된 사용 정책의 위반을 감지하고 방지하여 … 목적으로 제한됩니다." / 연령 요건(재확인, 변화 없음) "'API'를 사용하려면 만 18세 이상이어야 합니다. 또한 귀하는 '서비스'를 만 18세 미만인 개인을 대상으로 하거나 이러한 개인이 액세스할 가능성이 있는 … 일부로 사용하지 않습니다." | 해석(메인 세션 해석을 architect가 받아 적음 — 법률 검토 아님): ① 결제 계정 없는 무료 키로 쓰면 AI 서비스가 보내는 입력(시나리오 설명·단서 설명·대화 이력 — 이력에는 아이가 고른 선택지가 포함된다)과 AI 출력이 Google 제품 개선에 쓰이고 사람이 읽을 수 있다 → N-05(미성년자 개인정보)와 충돌 가능. 설계상 아이 식별 정보·아이가 직접 쓴 글은 가지 않지만(위 ②, 1차는 선택지 ID만), 미성년자의 선택 기록이 제공사로 간다는 점은 남는다 ② Cloud Billing 계정을 활성화하면 무료 할당량 안이라도 유료 서비스 데이터 조건(개선 미사용, 정책 위반 감지용 제한 기간 기록)이 적용된다 ③ 연령 조항 위험(PRD R-1)은 유료로 바꿔도 그대로다. **설계 권고: 운영(공개 URL) AI 서비스에는 Cloud Billing 계정이 활성화된 프로젝트의 키를 쓴다.** 활성화 여부는 비용·카드 등록이 걸린 팀 결정 [A-13] — 결정 전까지는 무료 키 사용 시 위 ①의 조건이 적용됨을 팀에 알린다. DECISIONS #49 |
| TTS — 브라우저 내장 Web Speech API (frontend 저장소) | 우리 서비스가 계약하는 외부 제공사 없음. 단, 일부 브라우저의 음성은 네트워크 음성(브라우저 제조사 서버로 문장 전송)일 수 있음(추정). 확인 방법: T-44에서 `speechSynthesis.getVoices()`의 `localService` 값을 대상 브라우저별로 기록 | `localService === true`인 한국어 음성을 우선 선택(권고). 읽는 문장은 연습 대사·단서 카드(예시 콘텐츠)뿐이라 개인정보 없음 — ADR-0008 |
| STT — 브라우저 내장 음성 인식 (frontend 저장소, 2026-11-07 신규 — F-48 ③ 말로 답하기) | 우리 서비스가 계약하는 외부 제공사 없음, 음성은 우리 서버·AI 서비스로 보내지 않음. **미확인(추정)**: 일부 브라우저의 음성 인식은 음성을 브라우저 제조사 서버로 보내 인식할 수 있고, 지원하지 않는 브라우저도 있을 수 있다(architect 기억 — 이번 세션에 문서 확인 안 함). 확인 방법: 대상 브라우저(Chrome Android·iOS Safari·데스크톱)의 음성 인식 API 문서와 실기기 동작 확인 — PRD OQ 53, T-81 | 음성 데이터는 어떤 API 요청에도 넣지 않음(E2E·네트워크 확인). 미지원·권한 거부면 Y5-2로 안내. 외부 전송이 확인되면 말로 답하기를 끌지 결정 필요 — ADR-0014, 설계 리스크 D-9 |
| OCR·이미지 이해 | 2차 (PRD OQ 2·30 잔여, 보류) | 1차 해당 없음 |
| 운영용 교체 AI | 보류 (PRD OQ 2·30 잔여) | ai 저장소의 제공자 구현 교체 지점(권고 구조 `app/providers/`) |

## 테스트 전략 (2026-11-06 갱신 — 저장소별)

케이스 도출·부실 테스트 방지 기준은 `.agents/skills/tdd-practitioner/SKILL.md`를 따른다 (정상 1 + 경계 2 + 예외 2 이상, 실제 값 단언, 비동기 대기, 외부 의존성 격리). 아래 표는 backend 저장소의 결정이고, 다른 저장소는 그 아래 "다른 저장소" 표의 권고다.

| 항목 | 결정 (backend 저장소) |
|---|---|
| 테스트 프레임워크 | pytest + FastAPI `TestClient` + httpx `MockTransport` (ADR-0006 갱신 메모) |
| 테스트 디렉토리 배치 | `tests/unit/`(domain 순수 규칙, import 경계) · `tests/integration/`(API + SQLite, IDOR·금지 필드) · `tests/contracts/ai/`(내부 API 요청·응답 샘플 JSON + `HttpPracticeAI` 계약 테스트) |
| 커버 범위 기준 | 수치 커버리지 목표는 두지 않는다(일정 N-08). 대신 **백엔드가 담당하는 각 F-xx 승인 기준마다 최소 1개 테스트**(Tasks 배정표 기준) + tdd 스킬 케이스 기준. 반드시 있어야 하는 회귀: IDOR(F-02 ④·F-30 ④), 보호자 응답 금지 키 0건(F-30 ②③·F-41 ③), 감정 값 필드가 어떤 요청 DTO에도 없음(F-25 ③ 서버 측), import 경계(N-10, DECISIONS #44), 학년 제한(F-14 ②), 변형 1개 이상 상이(F-12), 정상 비율 10회 중 3회(F-17 ①), 힌트 단조 감소(F-18 ②), 이전 PIN 실패·새 PIN 성공(F-04), AI 서비스 실패 5종(비2xx·연결 실패·시간 초과·스키마 위반·`cue_ids` 제약 위반) → `AI_UNAVAILABLE`. **2026-11-07 추가(F-48)**: 보호자 응답 금지 키 검사 대상에 `answer_text`·심화 연습 피드백 문장 추가(A11 응답에 0건 — 1차에도 유지, 키 목록 검사라 비용 작음). **[2차 — T-82, 2026-11-07 PRD OQ 55 해소]** A21 요청에 추가 필드(감정 값 등)가 있으면 422, A21 처리 중 로그 출력에 `answer_text` 0건(캡처한 로그 단언), 남의 세션 A21 → 404, 종료 전 세션 → 409, `deep_feedback` 실패 → 503·`substituted` 전달, 출력 숫자 검증 위반 → 503. A20을 1차에 되살리면(DECISIONS #73) 남의 세션 A20 → 404·종료 전 → 409를 1차에 둔다. **1차 기본안(PRD OQ 59)의 F-48 서버 회귀는 없다** — 아이 답변이 서버로 오지 않음은 프론트 E2E 네트워크 검사로 확인한다(아래 "다른 저장소" frontend 행). **2026-11-07 추가(AI 담당 답변 반영)**: 보호자 학습 요약 — 기록 기준 미만이면 `SummaryAI` 미호출 + `status:"insufficient"`, AI 실패·문장 3개 이상·입력에 없는 숫자·`unit`과 항목 불일치 → `status:"unavailable"`·`items: []`이고 나머지 리포트 필드는 정상, `LearningSummaryInput` 조립값(영역별 `found_count`·`missed_count`·`previous`)이 예시 기록에서 기대값과 같음, 입력에 금지 정보(별명·대화 문장·감정 값·`answer_text`) 0건. `feedback` 요청에 `history`·`normal_outcome`이 `judge`와 같은 값으로 실림(Fake 호출 인자 단언). **2026-11-08 추가(연습 종료 — DECISIONS #80~#83)**: domain 종료 함수 단위 테스트 — 위험 상황 `suspicious` × 답 수 1(첫 답 종료)·4(겹침) → 종료, `trusting`·`neutral` × 답 수 1·3 → 계속, × 답 수 4 → 종료, 정상 상황 입력 → 예외 / A17 통합(Fake) — 종료하는 답이면 Fake `next_turn` 미호출·`judge` 1회 호출·응답 `status:"ended"`·`turn: null`·세션 `ended`, 계속이면 `next_turn` 1회·`judge` 미호출·`status:"in_progress"`, 종료 뒤 A17 → 409 `SESSION_ENDED`, 종료 세션 A16 → `status:"ended"`·`turn: null`, `next_turn`·`judge` 실패 → 503이고 선택 기록·턴·cue_results 0건 저장(같은 `choice_id` 재요청 성공), 공개 응답에 `is_terminal` 키 0건 / F-11 ⑥ "AI 종료 신호 무시" — `tests/contracts/ai/`에서 `next-turn` 응답에 `is_terminal: true`·`false`를 각각 넣어도 `HttpPracticeAI`가 성공 파싱하고 `TurnResult`에 그 값이 남지 않음 + 종료 함수 입력에 AI 응답 값이 없음(시그니처) / 선택지 태그 제약(#83, 사용자 확정 #86) — 위험 상황에서 `suspicious` 0개 또는 전부 `suspicious` → 503. **2026-11-11 추가(PRD OQ 12·13·31·36 — DECISIONS #87~#92)**: ① **보호자 경로 `practice_turns` 예외 강제(ADR-0016)** — R1 `FirstAnswerJudgment` 필드 집합이 정확히 `{session_id, judgment}`(단위) / R2 `first_answer_judgments` 실행 SQL을 SQLAlchemy `before_cursor_execute` 이벤트로 수집해 `ai_line` 0건, `turn_index` 0 조건 포함(리포지토리 통합) / R3 예시 세션의 `turn_index` 0 `ai_line`·선택지 `text`에 고유 표지 문자열을 넣고 A11 응답 본문 전체와 Fake `SummaryAI`가 받은 `LearningSummaryInput` 직렬화 문자열에 표지 0건 + 보호자 응답 금지 키 검사에 `chosen_choice_id`·`choices`·`judgment` 추가(통합) / R4 `test_import_boundaries.py` ⑤ — `app/services/`의 리포트·성장 모듈이 호출하는 `PracticeRepo` 메서드 중 `practice_turns`를 읽는 것은 `first_answer_judgments`뿐(AST 허용 목록) ② **지표 domain 단위** — (가) 예시 "최근 7일 목표 단서 10개 중 3개 놓침 → 0.3"(F-29 ⑤), 정상 상황 세션은 (가)·(나)·(다) 분자·분모 불변 / (나) 다시 도전 세션·이전에 받은 시나리오 세션 제외 / (다) 첫 답 `suspicious` 2·`trusting` 1 → 2/3, 정상 상황 첫 답 `suspicious`는 분모·분자 모두 제외 / 분모 세션 2개 → `insufficient`·숫자 null·`trend` [], 3개(두 기간 모두) → `ok`·`trend` 2점 / 이번 3개·직전 2개 → `insufficient` / 종료 세션의 첫 답 `judgment` 없음 → 예외 ③ **한국 시간 경계** — `ended_at` 2026-11-10T15:00:00Z → 11-11, 2026-11-10T14:59:59Z → 11-10로 셈(기간 창·연속 기록 모두), 주입 `Clock`으로 오늘 고정 ④ **배지·연속 기록 domain 단위** — 한 영역 `missed` 0 세션 2개 → 배지 없음, 3개 → 배지 1개, 정상 상황 세션 3개 → 배지 없음, 다시 도전 세션 포함해 3개 → 배지 / 오늘·어제·그제 종료 → 3, 오늘 없음·어제·그제 → 2, 어제·오늘 없음 → 0, 하루 빈 날 → 끊김 ⑤ **`judge` 응답 검증** — J1 위험 상황에서 단서 누락·중복·목표 밖 단서·`normal_outcome` 값 있음 → 503, J2 정상 상황에서 `normal_outcome` null·`outcomes` 비어 있지 않음 → 503(계약 테스트 + A17 통합) ⑥ **안전 알림(F-41 ④⑤)** — `guardian_notices` CHECK: `safety`인데 `level` 또는 `area` null 삽입 → DB 오류, `trusted_contact`인데 `level` 값 → DB 오류 / A11 `notices[]` 각 항목의 키 집합이 `NoticeView` 6개와 정확히 같음. **2026-11-11 추가(사용자 확정 — DECISIONS #109~#116, 위 ②④⑤의 이름·조건을 대체)**: 이름은 `judgment`(`suspicious`) → `kind`(`correct`), R1 필드 집합 `{session_id, kind}`(#93). ② 지표 — `judge`가 `not_shown`을 준 단서는 `cue_results`에 0행(통합), (가)(나) 분모 = `found`+`missed`(예: 세션 3개 각 `found` 1·`not_shown` 3 → (가) 0, (나) 1.0), `found`+`missed` = 0 세션은 (가)(나) 분모 세션 수에서 빠짐(★ #116), `stopped` 세션은 (가)(나)(다)·배지·연속 기록 모두 불변 ④ 배지 — `missed` 0·`found` 1 세션 3개 → 배지, `missed` 0·`found` 0 세션 3개 → 배지 없음, `stopped` 세션은 세지 않음 ⑤ `judge` 검증 — J1 대신 J1'~J4' 위반 각각 → 503(계약 테스트 + A17 통합), 정상 상황 J2는 정상 상황을 켤 때(#110)까지 테스트하지 않음 ⑦ safe_reply(#113) — A17에서 Fake `turn`이 `safe_reply` → 응답 `status:"stopped"`·안내 턴(`choices` [])·`judge`·`feedback` 미호출·`cue_results` 0건, 이후 A17·A18 → 409 `SESSION_STOPPED`, A16 같은 응답. **2026-11-11 추가(#118 — PRD OQ 64)**: Fake `turn`의 `reply`에 고유 표지 문자열 → A17·A16 응답 `turn.ai_line` = 주입한 고정 문구, 응답 본문·`practice_turns` 행·캡처한 로그에 표지 0건, `substituted` false / `reply` 빈 문자열·`choices` 비어 있지 않음이어도 503이 아니라 `stopped` / `guardian_notices` 0행 / `safety_stop.json` `message` 공백·길이 초과 → 시작 시 검증 실패(단위) ⑧ 요약 단위(#114) — 기록 있는 영역 2개면 Fake `summary` 2회 호출·`unit:"area"`·`items` 2개, 한 영역이라도 `null`이면 `unavailable`·`items` [] ⑨ Area 값(#112) — 공개 API가 `identity_lending`·`friend_pressure`만 받고 옛 값 → 422 |
| Mock/Stub 대상 (외부 의존성) | AI 서비스 → `FakePracticeAI`(서비스·API 테스트) / httpx `MockTransport`(HTTP 어댑터 계약 테스트). DB → SQLite(테스트별 임시 파일 또는 메모리, OS 임시 디렉터리). 시계 → 주입 가능한 `Clock`(연속 기록·지표 — 2026-11-11: 한국 시간 날짜 경계 테스트용, DECISIONS #89). 난수 → 시드 주입 `Random`(변형·출제) |
| 실제 AI 서비스 테스트 | `@pytest.mark.live_ai` 마커 테스트만 실행 중인 AI 서비스(`AI_SERVICE_URL`)를 호출. 기본 실행에서 제외(`-m "not live_ai"` 기본 설정). 토큰은 사용자가 자기 셸 환경 변수로 제공 — 에이전트는 `.env`를 읽지 않는다 |
| E2E 실행 지원 (N-06) | E2E 러너는 frontend 저장소(권고 Playwright — [팀 요청 F-6]). 백엔드는 E2E용 기동 방법을 제공한다: `AI_CLIENT=fake`, OS 임시 디렉터리의 SQLite `DATABASE_URL`, 시작 시 마이그레이션, 포트 8080. 기동 명령 원문은 T-01에서 실제 성공한 것만 CodingRules에 등록하고 docs 저장소 로컬 실행 규칙에 공유 |
| 증거 보존 | 실행별 stdout·stderr·메타데이터를 `.artifacts/verification/T-xx/{실행ID}/`에 저장(AGENTS.md 검증 증거 보존 — 이 폴더는 `.gitignore`로 원격 제외) |

다른 저장소 (권고 — 각 담당 결정):

| 저장소 | 권고 |
|---|---|
| frontend | Vitest + React Testing Library + jsdom(컴포넌트·화면 상태). Playwright Test(E2E — 데스크톱 1280×800 + 모바일 360×800, `webServer`로 Vite dev + 로컬 백엔드(`AI_CLIENT=fake`) 기동). 시연 흐름 E2E `demo-flow.spec`: S0 → 보호자 가입 → 아이 등록(보호자가 PIN 입력)·연결 코드 발급 → 아이 로그인 → 첫 설정 → 사기 연습 → 결과 → 다시 도전(같은 단서·다른 변형) → Y8 → G3(예시 안전 알림). F-25 ③은 E2E에서 모든 요청 본문에 감정 값이 없음을 검사. 심화 연습(F-48, PRD OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76): Y5-2·Y5-3 제출 후 Y5-4까지 모든 요청 본문·URL에 입력한 예시 답변 문자열 0건, 음성 데이터 0건(F-48 ③④⑥), 브라우저 저장소에 답변 0건. 예시 성장 기록이 어떤 계정에 붙는지는 [A-1 — 보류, 추천안 고정 시연 계정] |
| ai | pytest. Fake 제공자로 단위 테스트, 백엔드와 같은 `contracts/ai` 샘플로 내부 API 응답 검증, N-04 안전 필터 세트(`{id, category(시나리오 이탈·사기 조장·민감정보 노출·정상 사례 과잉 경고), input, expected}`)를 Fake 경로·실제 Gemini 경로(마커로 분리)로 실행. 통과 기준 [OQ 25] |

### T-01 하네스 범위 (2026-11-06 갱신 — Tasks T-01 근거, DECISIONS #41. 2026-11-08 갱신 — Tasks 파트별 분리: 백엔드 T-01, 프론트 T-83, AI T-84)

| 실행 단위 | 저장소 | 러너 | 스모크 테스트 1개 | 담당 |
|---|---|---|---|---|
| 백엔드 (T-01) | backend (이 폴더) | pytest | `GET /api/v1/health` → 200 `{status:"ok", db:"ok"}` (SQLite — API 규격 A1 응답, 2026-11-08 맞춤) | 백엔드 |
| 백엔드 AI 경계 (T-01) | backend (이 폴더) | pytest | `FakePracticeAI.opening`이 `TurnResult` 스키마를 반환 + import 경계 테스트(DECISIONS #44) | 백엔드 |
| 백엔드 dev 서버 (T-01) | backend (이 폴더) | `.claude/launch.json` (로컬 전용) | uvicorn 포트 8080 기동 설정 | 백엔드 |
| 백엔드 CI (T-01) | backend (이 폴더) | GitHub Actions `.github/workflows/ci.yml` | `dev`·`main` 대상 PR에서 pytest (Fake AI, SQLite) | 백엔드 |
| 명령 등록 (T-01) | backend (이 폴더) | CodingRules.md "검증된 명령어" | T-01에서 **실제 성공한 원문만** 등록. 후보(미검증): `python -m pytest`, `python -m uvicorn app.main:app --reload --port 8080` | 백엔드 |
| 프론트 러너·E2E 러너·E2E 스모크·dev 서버 (T-83) | frontend | 권고 Vitest·Playwright | 앱 루트 렌더 / `/` 접속 + `/api/v1/health` 프록시 200 | 프론트 [팀 요청 F-6] |
| AI 러너·스모크 (T-84) | ai | 권고 pytest | `GET /internal/v1/health` 200 + Fake 제공자로 `/practice/opening` 응답 스키마 | AI [팀 요청 AI-3] |

AGENTS.md 고정 첫 작업(T-01 완료 전 T-02 이후 착수 금지)의 저장소 간 적용 — **2026-11-08 갱신**: Tasks 소유자(planner)가 실행 단위별 적용으로 정리했다(Tasks "파트별 하네스 분리" 절, 인용): 하네스는 백엔드 T-01·프론트 T-83·AI T-84, 원문 "각 코드 작업은 자기 실행 단위의 하네스(위 표) 완료 후 착수하고, 여러 실행 단위에 걸친 작업은 관련 하네스 전부를 선행으로 둔다.", T-83·T-84는 T-01과 동시 착수 가능(선행 없음). 이 해석과 AGENTS.md 문구(T-01 하나가 러너·스모크와 E2E 러너·E2E 스모크를 포함)의 충돌은 **해소 — 사용자 확정(2026-11-08 '받아들임')** [A-12, DECISIONS #78] — 설계는 위 표의 실행 단위별 범위만 정의한다. 하네스 확인용 최소 화면은 스모크 범위만 검증한다.

## 배포 (2026-11-06 갱신 — 배포 단위 3개)

PRD N-07 "공개 URL에서 시연 흐름이 동작하는 배포 가능한 mvp", 배포 형태 사용자 선택 원문 "Vercel + PaaS + 관리형 DB (Recommended)"의 실현 메커니즘이다. 구체 서비스는 ADR-0007 추천안으로 진행하고 T-27에서 확정 [A-2 — 보류].

| 항목 | 결정 |
|---|---|
| 호스팅 / 실행 대상 | 프론트: Vercel 정적 호스팅 + `vercel.json` 리라이트(`/api/:path*` → 백엔드 공개 URL, 그 외 → `index.html`) — frontend 저장소 [팀 요청 F-2]. 백엔드: Python PaaS 웹 서비스(추천 Render). AI: 같은 PaaS의 두 번째 웹 서비스(추천) — ai 저장소. DB: 관리형 Postgres(추천 Neon 또는 Supabase) |
| 빌드·릴리스 파이프라인 | 백엔드: `main` 병합(팀 컨벤션 "main(최종 데모)") 시 PaaS Git 연동으로 `pip install -r requirements.txt` 후 시작 명령 `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. 병합 전 CI(pytest) 통과가 조건(DECISIONS #42). 프론트·AI의 빌드는 각 저장소 담당. 배포 순서: 내부 API를 바꾸는 릴리스는 AI 서비스 먼저 → 백엔드 → 프론트 |
| 환경과 승격 | 로컬 → 운영(공개 URL) 2단계. 별도 스테이징 없음(일정 N-08). 팀의 `dev` 브랜치는 통합용이며 자동 배포 대상이 아니다(배포는 `main`) — 바꾸려면 팀 합의 |
| 환경별 설정 | 위 "시크릿과 환경 변수" 표. 로컬: 각자 `.env`(커밋 금지) / 운영: PaaS·Vercel 대시보드 환경 변수. 운영 백엔드는 `AI_CLIENT=http`, `COOKIE_SECURE=true`, `LOG_LEVEL=INFO`. 시크릿 값은 문서·코드·로그에 적지 않는다 |
| DB·상태 마이그레이션 | Alembic 마이그레이션을 백엔드 시작 명령에서 `upgrade head`로 적용(전진만). 콘텐츠(JSON)는 코드와 함께 배포되므로 마이그레이션 대상 아님. AI 서비스는 영속 상태 없음. 시연 데이터는 `python -m app.demo.seed`를 운영 DB에 수동 1회 실행(멱등 — 이미 있으면 건너뜀) |
| 롤백 절차 | 프론트: Vercel 이전 배포를 다시 운영으로 지정(대시보드, 수 분 — 추정). 백엔드·AI: PaaS에서 이전 커밋 재배포(수 분 — 추정). 마이그레이션이 포함된 릴리스는 `alembic downgrade -1` 후 재배포 — 1차 마이그레이션은 열 추가 위주로 써서 이전 코드와 호환되게 한다. 내부 API 변경 릴리스를 되돌릴 때는 백엔드 → AI 순서 |
| 헬스체크 / 스모크 테스트 | 백엔드 PaaS 헬스체크 `GET /api/v1/health`(DB 핑 포함), AI PaaS 헬스체크 `GET /internal/v1/health`. 릴리스 후 공개 URL에서 ① `/api/v1/health` 200(Vercel 프록시 경유) ② 로그인 후 쿠키 유지 확인(ADR-0013 — 설계 리스크 D-1) ③ 메인 세션 Browser pane으로 S0 표시 확인 ④ 시연 전 리허설(T-28). 무료 등급 PaaS의 유휴 절전(추정)에 대비해 시연 직전 두 헬스체크로 깨운다 |

## 에러 처리

| 항목 | 결정 |
|---|---|
| 예외를 잡는 위치 | services·domain은 `AppError`(code·HTTP 상태를 가진 예외 계층)를 던진다. `main.py`에 등록한 FastAPI 전역 예외 핸들러가 잡아 오류 응답 규격으로 바꾼다. 처리 안 된 예외는 같은 핸들러가 500 `INTERNAL`로 바꾸고 요청 ID와 함께 로그에 남긴다. 라우터에서 개별 try/except로 응답을 만들지 않는다 |
| 실패가 사용자에게 드러나는 방식 | 응답은 `{error:{code, message}}`. 프론트는 `code`로 쉬운 말 문구를 고르고(N-03, 비난 표현 없음 — 이를 위해 `client.js`가 `code`를 보존 [팀 요청 F-4]), 화면 상태 공용 컴포넌트가 에러 상태 + 다시 시도를 보인다. 폼 오류(422)는 필드 옆에 표시. 401은 역할별 로그인 화면으로 이동. 스택 트레이스·DB 오류 원문은 응답에 넣지 않는다 |
| 경계 간 전파 (2026-11-06 갱신) | AI 서비스 → 백엔드: HTTP 상태·오류 코드(내부 API 표). `HttpPracticeAI`는 비2xx·연결 실패·시간 초과·스키마 위반을 모두 `AIUnavailableError`로 바꾸고, 안전 필터 차단은 정상 응답(`substituted=true`)으로 받는다(F-11 ② — 차단은 정상 경로). services는 연습 API에서 `AIUnavailableError`를 `AppError(AI_UNAVAILABLE, 503)`로 바꾼다. 요약 문장(`SummaryAI`)의 실패·검증 실패는 오류로 올리지 않고 해당 필드를 비운다(2026-11-06 추가 — 2026-11-07부터 보호자 학습 요약은 `null` 대신 `summary.status = "unavailable"`). Repository → services: 유일 제약 위반(이메일·연결 코드)을 도메인 오류로 변환(이메일 → `EMAIL_TAKEN`, 연결 코드 충돌 → 재생성 최대 5회). 프론트 api 계층: HTTP 오류를 `{status, code}`를 가진 오류 객체로 던지도록 요청 [팀 요청 F-4] |

## 관측성

| 항목 | 결정 |
|---|---|
| 로깅 (2026-11-06 갱신) | 백엔드: Python `logging`으로 구조화 JSON 한 줄을 stdout에(PaaS 로그 수집). 필드: 시각, 레벨, 요청 ID, 경로, 상태 코드, 지연(ms), 주체 UUID, 오류 코드. 금지: 요청 본문·쿠키·비밀번호·PIN·연결 코드·이메일·내부 토큰·아이 자유 답변과 그 피드백 문장(2026-11-07 추가). AI 서비스 호출은 엔드포인트·소요 시간·상태 코드·`substituted` 여부만 기록하고, 요청 ID를 `X-Request-ID`로 AI 서비스에 전달해 두 서비스 로그를 잇는다. AI 서비스 로깅은 같은 규칙을 권고(운영에서 프롬프트·출력 본문 미기록) [팀 요청 AI-2] |
| 에러 추적 / 모니터링 | 없음 — MVP는 PaaS 로그와 헬스체크로 대체(일정 N-08, 외부 서비스 추가 계약 회피) |
| 메트릭 | MVP에서는 별도 수집 없음. PRD 성공 기준의 "시스템 지표" 수치 목표는 OQ 15 잔여(보류) — 정해지면 로그 기반 집계로 시작 |

## 2차 확장 지점 (만들지 않고 붙을 자리만 기록 — 2026-11-06 갱신)

| 2차 기능 | 붙을 자리 | 1차에서 미리 하지 않는 것 |
|---|---|---|
| 실생활 확인 Y6·Y7 (F-19·F-21·F-22) | backend: 새 라우터 `app/api/real_checks.py`(`POST /api/v1/real-checks` — 이미지 multipart 수신, 메모리에서만 처리), 새 서비스 `app/services/real_check_service.py`, 규칙 탐지 5범주(송금·사진·만남·개인정보·명의 요구)는 `app/domain/rule_detection.py`. ai: 새 내부 엔드포인트(예 `/internal/v1/real-check/analyze` — OCR·맥락 판단)와 백엔드 `ai_client` 포트 메서드 추가 | 엔드포인트·테이블·포트 메서드 선생성 금지 |
| 마스킹·이미지 미저장 (F-20, F-43) | 이미지가 AI 서비스로 가는지(서비스 쪽 OCR) 백엔드에서 마스킹 후 텍스트만 가는지는 2차 설계에서 결정 — 원칙: LLM 전달 전 마스킹, 이미지는 디스크·DB·로그에 쓰지 않음 | — |
| 실제 결과 → 안전 알림 (F-41 ②의 2차 경로, T-64) | `guardian_notices`에 `origin = "real_check"` 값 추가(Alembic enum 변경) + 알림 생성 서비스. 원문 열은 계속 없음 | 1차에서 enum 값 선추가 금지 |
| Y3 "지금 이거 수상해?" (F-09 ②) | 프론트 기능 플래그 → 실제 라우트 연결 | — |
| Y7 연락·도움 요청·거절 템플릿 (F-23·F-24·F-40) | 프론트 기존 컴포넌트 재사용, 거절 템플릿은 콘텐츠 파일 추가 | — |
| 운영용 교체 AI (N-09) | ai 저장소의 제공자 구현 교체 — backend 무변경 | — |
| PIN 잠금 F-44·접근성 설정 F-46 (보류) | F-44: `children`에 실패 횟수·잠금 열 추가 + A4 판정. F-46: `PUT /me/settings` + Y9 라우트 | — |
| 심화 연습 AI 피드백 (F-48 ② [2차]·⑤ [2차], T-78·T-82 — 2026-11-07 PRD OQ 55 해소) | 이미 정의된 규격을 그대로 쓴다: 공개 A21(`deep/answers`), `DeepFeedbackView`, 내부 `deep/feedback`, 심화 연습 안전 처리, `PracticeAI.deep_feedback` — 모두 [2차] 표시. 2차 착수 전 결정: A-17(답변 저장 여부 — 저장이면 A22·`deep_answers` 테이블), 1차 Y5-4 내용(OQ 50 ③)과 AI 피드백을 합치는 방식, AI 담당 합의(T-78) | 1차에 A21 라우터·`deep_feedback` 포트 메서드·Fake·AI 엔드포인트 선생성 금지 |

PRD OQ 45(팀 문서 A~E 대응)가 "실제 메시지 분석은 1차"로 바뀌면 위 첫 세 행이 1차로 돌아온다 — 구조는 그대로 붙일 수 있지만 일정(N-08) 영향이 크다.

## 팀 공유 규격 — docs 저장소 정본 대상 (2026-11-06 신규, DECISIONS #43)

팀 규칙(팀 docs 저장소 README 원문, 인용): "팀 공용 (기획·아키텍처·API) | docs", "백엔드 구현 상세 | backend/docs", "AI 구현 상세 | ai/docs". 아래 항목은 다른 파트가 의존하므로 팀 docs 저장소에 게시해야 한다. 게시는 architect 권한 밖이며 사용자(백엔드 담당)가 docs 저장소에 PR로 올린다 [A-10]. 게시 전까지는 이 문서가 설계 원본이고, 게시 후 변경은 docs 저장소 PR과 이 문서를 같은 날 함께 갱신한다.

| 공유 항목 | 이 문서의 원본 절 | 의존하는 파트 |
|---|---|---|
| 공개 API 규격 A1~A19, 응답 DTO, 오류 코드, 보호자 응답 금지 필드 | "API 규격", "응답 DTO", "오류 응답 규격" | 프론트 |
| 인증·쿠키·같은 출처 프록시 규칙(`VITE_API_URL` 비움, 204 없음) | ADR-0013, "API 규격" 머리말 | 프론트 |
| 백엔드–AI 내부 API 규격 + 계약 샘플 JSON(`tests/contracts/ai/`) | "백엔드–AI 내부 API" | AI |
| 로컬 실행 규칙: 포트(백엔드 8080, AI 8081), 프록시, E2E용 백엔드 기동(`AI_CLIENT=fake`) | "시크릿과 환경 변수", "테스트 전략" | 프론트·AI |
| 콘텐츠 파일 규격 | "콘텐츠 파일 규격" | 콘텐츠 담당(OQ 3)·AI |
| 화면 경로·가드·화면 상태 합의안 | "화면 메커니즘" | 프론트·디자인 |

## 팀원 요청 사항 (2026-11-06 신규 — 메인 세션·사용자가 전달)

"요청"은 백엔드 계약과 맞물려 필요한 것, "권고"는 선택이다.

| # | 대상 | 구분 | 내용 | 이유 |
|---|---|---|---|---|
| F-1 | 프론트 | 요청 | `vite.config.js`에 `server.proxy: { '/api': 'http://localhost:8080' }` 추가 | 로컬에서 같은 출처 — 쿠키 세션(ADR-0013) |
| F-2 | 프론트 | 요청 | `vercel.json` 리라이트: `/api/:path*` → 백엔드 공개 URL의 `/api/:path*`, 그 외 → `/index.html`(SPA 폴백) | 운영에서 같은 출처. 백엔드 URL은 T-27에서 전달 |
| F-3 | 프론트 | 요청 | README의 `VITE_API_URL=http://localhost:8080` 안내를 "비워 둔다(프록시 사용)"로 변경. API 경로는 `/api/v1/...` | 절대 주소면 교차 출처 → `fetch` 기본 `credentials: same-origin`이라 쿠키 미전송, 로그인 유지 불가 |
| F-4 | 프론트 | 요청 | `src/api/client.js`: 오류 시 응답 본문 `{error:{code,message}}`를 읽어 `status`·`code`를 담은 오류 객체를 던지기 (성공 응답은 항상 JSON — 백엔드가 204를 쓰지 않음) | 오류 코드별 쉬운 말 문구(N-03), 401 → 로그인 이동 |
| F-5 | 프론트 | 요청 | 화면 경로·가드·화면 상태 합의안("화면 메커니즘" 표) 검토·합의. 감정 온도계 값은 어떤 API 요청에도 넣지 않기(F-25 ③) | PRD 화면 상태·N-05 |
| F-6 | 프론트 | 권고 | 테스트 러너 Vitest + RTL, E2E Playwright 구축(데스크톱 + 모바일 프로젝트) + 시연 흐름 E2E. 설치는 허용됨(메인 세션 해석) | N-06 "E2E 테스트로 자동 검증", AGENTS.md 화면 흐름 회귀 |
| F-7 | 프론트 | 권고 | 서버 상태 관리(TanStack Query 등)와 화면 상태 공용 컴포넌트, TTS는 Web Speech API(`localService` 우선) | 11개 화면 상태 일관성, ADR-0008 |
| F-8 (2026-11-07 신규, 2026-11-07 PRD OQ 55·59 반영 — 사용자 확인 대상. 2026-11-08: 답변을 서버로 보내지 않는 부분은 PRD OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76 — A20 조건부(#73)는 확인 전) | 프론트 (프론트 B) | 요청 | 심화 연습(Y5-1~Y5-5, T-80·T-81). **1차 기본안**: Y5-1~Y5-4는 새 API를 부르지 않고 Y5가 받은 A18 응답을 프론트 상태로 넘겨 씀(A18 재요청 금지 — 요청마다 AI `feedback` 호출, 상태가 없으면 Y5로 이동. A20은 조건부). 글로 답하기·말로 답하기 모두 **서버로 보내지 않고** 제출 시 Y5-4로 화면 이동 — 입력 글은 프론트 메모리 상태로만(브라우저 저장소·URL에 남기지 않음, 어떤 API 요청에도 넣지 않음). 말로 답하기는 브라우저 음성 인식으로 글자로 바꾸고 음성은 어떤 요청에도 넣지 않음, 미지원·권한 거부면 Y5-2로 안내. 감정 온도계 값은 넣지 않음. Y5-4 내용은 PRD OQ 50 ③. E2E 네트워크 검사(테스트 전략 frontend 행). **[2차 — T-82]** A21 `{answer_text}` 하나로 제출, `AI_UNAVAILABLE`이면 입력 유지 후 다시 시도, Y5-4는 A21 응답을 표시(A-17 A안 기준) | F-48 ③④⑥, ADR-0014, DECISIONS #72 |
| F-9 (2026-11-08 신규 — PRD OQ 42 해소·OQ 62 ① 사용자 답) | 프론트 | 요청 | Y4 연습 대화(T-18): ① A17 응답이 `TurnView`에서 `PracticeSessionView`로 바뀐다 — `status: "in_progress"`면 `turn`(다음 턴)을 표시, `status: "ended"`(`turn: null`)면 바로 Y5로 이동(마무리 대사 없음) ② `TurnView.is_terminal` 필드는 없어졌다 — 종료 판단에 쓰지 않기 ③ A16(새로고침 복구)도 종료 세션이면 `status: "ended"`·`turn: null` → Y5 ④ A17 409 `SESSION_ENDED` → Y5 ⑤ `AI_UNAVAILABLE`이면 같은 선택지로 다시 시도. 화면에서 종료 시점을 계산하지 않는다(답 수·태그는 프론트에 없음 — 선택지 태그는 보내지 않음) | PRD F-11 ④⑤⑥, OQ 62 ① 사용자 답 "바로 결과 화면 (Recommended)", DECISIONS #82 |
| F-10 (2026-11-11 신규 — PRD OQ 64 사용자 답) | 프론트 | 요청 (알림 — 결정 사항, 이견 기한 없음) | Y4 멈춤 상태(T-18): ① A17·A16 응답 `status: "stopped"`면 `turn.ai_line`(서버가 넣은 사람이 쓴 고정 안내 문구)을 선택지 없이 보이고 "홈으로" 버튼 1개(→ Y3 `/child/home`) — Y5로 가지 않음, 더 답할 수 없음, 새로고침해도 같은 상태 ② A17 409 `SESSION_STOPPED` → A16으로 같은 멈춤 상태 표시 ③ 문구를 프론트에 따로 두지 않는다(서버 값만 표시) ④ 보호자 알림은 없음 | 사용자 답 원문 "고정 문구+홈, 알림 없음 (추천)", DECISIONS #113·#118 |
| AI-1 | AI | 요청 (2026-11-06 엔드포인트 목록 갱신, 2026-11-07 `deep/feedback` 추가). **2026-11-07 부분 합의** — 합의: ① 별도 HTTP 서버·포트 8081(답변 1 "동의합니다. AI 레포에서 별도 HTTP 서버(8081)를 운영하는 방식으로 진행하겠습니다.") ② 판단 분석 MVP = ①, `feedback`이 고른 선택지 설명(답변 2) ③ 성장 수준은 백엔드 계산·AI는 문장만(답변 3 "좋습니다.") ④ 보호자 학습 요약 = 백엔드 계산 데이터 → 1~2문장(답변 4). 미답변: `deep/feedback`·심화 연습 입력·출력 안전 필터(질문 다섯째 항목 — PRD OQ 55 → 2026-11-07 사용자 결정으로 2차, 1차 요청에서 뺌), 요약 단위(PRD OQ 56). 미확인(답변에 언급 없음): 아래 엔드포인트별 필드 규격·`X-Internal-Token`·오류 코드·계약 샘플 JSON 공유(A-16) | ai 저장소를 상태 없는 HTTP 서비스로 구성하고 "백엔드–AI 내부 API" 규격 구현. 필수: `GET /internal/v1/health`, `POST /internal/v1/practice/opening`(상황 생성 + 검수), `POST /internal/v1/practice/next-turn`(대사 + 힌트 문장), `POST /internal/v1/practice/judge`, `POST /internal/v1/practice/feedback`, `POST /internal/v1/summaries/guardian`(보호자 학습 요약 문장 — 2026-11-07 갱신: 입력에 찾은 단서·영역별 기록 수 추가, 응답 `items` 항목당 1~2문장, `unit` 기본 `overall`), **[2차 — 1차 필수 목록에서 뺌, 2026-11-07 PRD OQ 55 해소: 사용자 답변 원문 "AI 피드백만 2차로"]** `POST /internal/v1/deep/feedback`(심화 연습 자유 답변 피드백 문장 — F-48, T-78, 입력 필터에 걸리면 LLM 미호출, 아이 답변 원문 로그 금지 — 2차 착수 전 AI 담당 합의 필요, 1차 11/11 완료 대상 아님). 2026-11-07 갱신: `practice/feedback` 요청에 `history`·`normal_outcome` 추가(고른 선택지 설명 ①). 선택: `POST /internal/v1/summaries/child-growth`(PRD OQ 49 답 후에만), `POST /internal/v1/recommendations/reason`(요구사항 없음 — PRD F 미생성, 구현 금지). 힌트 문장은 T-74, 보호자 학습 요약은 F-47·T-75. 공통: `X-Internal-Token`, 오류 코드, `substituted`, 점수·등급을 새로 만들지 않음. 안전 필터·검수·판정·피드백·대체 문구·안전 규칙은 AI 서비스 소유, 계산·저장(약점 집계·지표·힌트 단계·다음 문제 선택)은 백엔드 | ADR-0011, 분담 원칙(사용자 "추천대로 반영") — 서비스 분리는 AI 담당 합의로 A-8 해소(2026-11-07, 대체안 pip 패키지 전환 불필요). 계약 고정 [A-16] |
| AI-2 | AI | 요청 | 환경 변수 `GEMINI_API_KEY`·`GEMINI_MODEL`·`AI_PROVIDER`·`AI_SERVICE_TOKEN`·`PROVIDER_TIMEOUT_SECONDS`, 로컬 포트 8081, 운영 로그에 프롬프트·출력 본문 미기록 | 시크릿 분리, N-05 |
| AI-3 | AI | 권고 | 제공사 SDK import를 한 파일(`providers/gemini.py`)로 한정 + Fake 제공자, pytest 스모크, 백엔드와 같은 계약 샘플로 응답 검증 | N-10, 계약 어긋남 방지 |
| AI-5 (2026-11-08 신규 — PRD OQ 42 해소) | AI | 요청 (알림 — 메인 세션·사용자가 AI 담당에게 전달) | **AI는 연습 종료를 판정하지 않는다.** ① `TurnResult`(`opening`·`next-turn` 응답)에서 `is_terminal` 필드를 뺀다(DECISIONS #81 — 사용자 확정 #84) — 보내도 백엔드가 무시하므로 급히 고치지 않아도 오류는 나지 않지만, 종료 판정 로직은 만들지 않는다 ② 종료는 백엔드가 아이가 고른 선택지의 `judgment`와 아이 답 수로만 정한다: 위험 상황에서 `suspicious`를 고르면 그 답에서 종료, 아니면 계속, 아이의 4번째 답에서 종료. `next-turn`은 종료가 아닐 때만 호출되며 종료 뒤 마무리 대사 요청은 없다(위험 상황 `next-turn`의 `turn_index`는 1~3) ③ 따라서 **`judgment` 태그가 종료를 좌우한다** — 거절·확인·믿는 사람에게 묻기 = `suspicious`, 돈·정보 주기 = `trusting`, 그 외 = `neutral`(PRD 질문 원문의 태그 설명 "의심(거절·확인·믿는 사람에게 묻기), 믿음(돈·정보 주기), 중립"). 태그가 내용과 맞는지 검증하는 방법(예: N-04 세트에 태그 정확성 케이스 추가)은 AI 담당 결정 ④ 위험 상황 턴마다 `suspicious` 1개 이상 + 그 외 1개 이상(DECISIONS #83 — 사용자 확정 #86, 위반 시 백엔드가 503 처리) ⑤ T-84 스모크의 `/practice/opening` 응답 스키마에서도 `is_terminal` 제외. 참고(승인 기준 아님): 사용자 선택지 설명 원문 "믿는 답을 고르면 상대가 더 조르면서 계속되어 다시 알아챌 기회가 생깁니다" — 생성 지침에 넣을지는 AI 담당 | PRD F-11 ⑥·N-12, 사용자 답 "백엔드 규칙만 (Recommended)"의 선택지 설명 원문 "대신 설계 문서를 architect가 고쳐야 하고 AI 담당에게 알려야 합니다.", DECISIONS #80·#81·#83, ADR-0015 |
| AI-6 (2026-11-11 신규 — PRD OQ 31 해소) | AI | 요청 (알림 — 메인 세션·사용자가 AI 담당에게 전달) | `POST /internal/v1/practice/judge`의 판정 규칙이 정해졌다(응답 형태는 그대로): ① 위험 상황 — 목표 단서마다, 그 단서가 `cue_ids`에 있는 `suspicious` 선택지를 대화 중 한 번이라도 골랐으면 `found`, 끝까지 안 골랐으면 `missed`. `trusting`·`neutral` 선택지에 단서가 붙어 있어도 `found`로 세지 않는다 ② 정상 상황 — `suspicious`를 한 번도 안 골랐으면 `trusted_correctly`, 한 번이라도 골랐으면 `over_warned`, `outcomes`는 [] ③ 백엔드가 응답을 검증한다(위반 → 503): 위험 상황은 목표 단서마다 정확히 1개·목표 밖 단서 없음·`normal_outcome` null, 정상 상황은 `outcomes` []·`normal_outcome` 값 있음 ④ 같은 입력이면 항상 같은 결과(결정적 — LLM 미사용 권고 유지) | PRD F-13 ④⑤, 사용자 답 원문 "한 번이라도 의심 (추천)", DECISIONS #91 |
| AI-7 (2026-11-11 신규 — AI 계약 채택) | AI | 요청 (알림·합의 — 메인 세션·사용자가 AI 담당에게 전달) | 백엔드는 ai 저장소 커밋 331d2c6의 `contracts/` 계약을 그대로 쓰기로 했다(경로·필드·상태 전달 방식 — "1차 내부 API v1" 하위 절). 합의 요청은 "AI 담당 합의 필요" G1~G10. 그 밖에 알릴 것: ① 백엔드가 `variant` 요청에 `platform`·`tone`·`context`를 항상 채워 보낸다 ② 백엔드 검증(선택지 3종 각 1개, `revealed_clue_ids` 단조 증가, `judge` J1'~J4', `feedback` V1'~V3')을 어기면 백엔드가 503으로 처리한다 ③ `safe_reply`면 백엔드가 세션을 멈추고 `judge`를 부르지 않는다 — 2026-11-11(#118): 백엔드는 `status`만 읽고 `reply` 문장은 쓰지 않는다(저장·표시 안 함, 백엔드 고정 문구로 대체). AI 변경 요청 없음 ④ 요약 입력에 지표·직전 기간은 1차에 넣지 않는다(G5 요청 안 함 — #119). AI-5·AI-6의 옛 필드명(`judgment`·`cue_ids`·`opening`)은 이 행으로 대체 | DECISIONS #96~#108, ADR-0017·ADR-0018 |
| AI-4 | AI | 메인 세션 확인 완료(2026-11-06) | Gemini 무료/유료 데이터 활용 조항 원문 확인 — 결과는 "AI 제공사 정책 기록" 표(한국어판 인용). AI 담당에게는 확인 결과 공유만 필요. 운영 키를 결제 계정 활성 프로젝트로 만들지는 [A-13] | N-09 기록 |

## 설계가 의존하는 미결 질문

제품·콘텐츠 결정은 추측으로 채우지 않았다. 아래는 설계가 그 답에 의존하는 지점만 표시한다.

| PRD OQ | 설계가 의존하는 지점 | 답 전까지의 설계 상태 |
|---|---|---|
| 3 콘텐츠 제작 담당 | `app/content/data/*.json`, 동의 문구(`consent_version`), AI 서비스의 대체 문구 | 파일 규격만 확정. 내용 없이는 T-12 이후 연습 기능이 동작하지 않음 |
| 6 프론트 스택 | ADR-0012 | 2026-11-06 frontend 저장소 실제 코드로 답이 났다고 봄(인용) — PRD 기록 갱신은 planner |
| 12 성장 지표 정의 | `domain/metrics.py` 계산식, MetricView 값, `SUMMARY_PERIOD_DAYS` | **해소(2026-11-11 — 사용자 답 "추천 정의 묶음 (추천)", planner 해석 9건 사용자 확정)**: "성장 계산 규칙" 절, `METRIC_PERIOD_DAYS = 7`·`METRIC_MIN_SESSIONS = 3`, 요약 기간 = 지표 기간, 지표 (다) 원천 = `practice_turns` 예외(DECISIONS #87·#88, ADR-0016). **2026-11-11**: 분모 = 드러난 단서(`found`+`missed`) — 사용자 확정 N1(#109), 최종 규격 #116. 남은 것: 지표 색 [OQ 63], [A-19]·[A-20] |
| 13 배지·연속 기록 | `domain/badges.py`, 저장 여부(계산 vs 테이블) | **배지·연속 기록 해소(2026-11-11 — 사용자 답 "3회 성공 + 하루 단위 (추천)")**: "성장 계산 규칙" 절, 계산 방식(#28) 유지(DECISIONS #90). **2026-11-11**: 배지 성공 세션 = `missed` 0 + `found` ≥ 1 — 사용자 확정 N1(#109), 최종 규격 #116. 오늘의 미션 구성은 보류 그대로("연습 출제 규칙" 오늘의 미션 행) |
| 14 난이도·적응형·힌트 수치 | 약점 임계값, `HINT_MAX`, 난이도 단계 수 | 구조와 설정 상수 자리만 |
| 24 노랑 문구 | 프론트 문구, Y5 카드 색 값(OQ 63과 함께) | **해소(2026-11-12 — 사용자 답 "믿는 사람에게 물어봐요 (추천)")**: 화면 표기 "믿는 사람에게 물어봐요", 내부 등급 이름 `yellow`('확인 필요') 그대로 — 문구는 프론트 표시, API 값 변경 없음(DECISIONS #121). 카드 색 값은 OQ 63 행 |
| 25 안전 필터·자동 검수 기준 | AI 서비스 `safety_rules.json`·검수 통과 조건, N-04 세트 통과 기준 | 내부 API의 `review`·`substituted` 구조만 |
| 26 연령 하한 | Grade 목록에 `E5` 포함 여부 | `E6`~`H3`로 시작 |
| 31 찾음/놓침 판정 | AI 서비스 `judge` 규칙, Y5 카드 `level` 매핑 | **해소(2026-11-11 — 사용자 답 "한 번이라도 의심 (추천)")**: `judge` 규칙과 백엔드 응답 검증 J1·J2, 정상 상황 `normal_outcome = null` 불허(DECISIONS #91, AI-6). **2026-11-11 AI 계약 채택 후**: J1 → J1'~J4'(#100, 사용자 확정 #115), `not_shown` 저장 안 함(#109), J2·null 불허는 정상 상황을 켤 때의 검증으로 보류(#110). Y5 카드 `level` 값은 이 답 범위 밖 → OQ 63 행 |
| 36 최소 알림 항목 | NoticeView 필드, guardian_notices 열 | **해소(2026-11-11 — 사용자 답 "시각·위험도·영역 (추천)")**: 열·필드 추가 없음, `guardian_notices` CHECK 제약(`safety`면 `level`·`area` 필수), 상세 API 없음(DECISIONS #92). 남은 것: [A-21] |
| 63 신호등 색 매핑 (2026-11-11 추가 — PRD OQ 12·31 해소에서 나옴) | ① Y5 카드 `CARD_LEVEL_BY_KEY`(K1~K5) ② `MetricView.level` | ① **해소(2026-11-12 — 사용자 답 "판단 결과 기준 (추천)")**: `CARD_LEVEL_BY_KEY` = K1 `green` / K2 `yellow` / K3 `green` / K4 `green` / K5 `yellow`(DECISIONS #120, 매핑 행 ③). T-16 리뷰 권고 #1 대응: 매핑 확인을 `feedback` 호출 전에 한다(값이 있어도 방어 유지) — 구현 T-89 ② 미결 — 규칙 없음, 응답 `level`은 항상 null(DECISIONS #88). 노랑 문구는 OQ 24(해소) |
| 42 연습 종료 조건 | `MAX_TURNS`, `is_terminal` 규칙 | **해소(2026-11-08 — 사용자 답 "4번"·"의심 답이면 바로 종료"·"백엔드 규칙만", 세부 3가지 "그대로")**: 위험 상황은 백엔드 domain이 `judgment`와 아이 답 수로만 판정, `MAX_CHILD_ANSWERS = 4`, `is_terminal`은 내부·공개 규격에서 삭제(DECISIONS #80~#82, ADR-0015) |
| 61 정상 상황 종료 규칙 (2026-11-08 추가) | domain 종료 함수의 정상 상황 분기, 정상 상황 선택지 태그 제약 | 규칙·제약 없음 — 정상 상황 입력은 예외(500). 정상 상황 출제(T-34·T-35)는 답 후. 값은 설계에서 정하지 않음. **2026-11-11**: 답이 나와도 AI 계약에 정상 상황 실행 경로·`normal_outcome`이 없어 출제를 켤 수 없다 — **사용자 확정 M1(2026-11-11 "끄고 AI에 요청 (추천)", DECISIONS #110)**: 정상 상황 출제는 OQ 61 답 + AI G2·G3 반영 전까지 끈다, ADR-0018 갈래 2 |
| 62 종료 화면 처리 (2026-11-08 추가) | A17 종료 응답, Y4 이동 | ① **해소(2026-11-08 사용자 답 "바로 결과 화면")**: 종료 시 `next_turn` 미호출, A17 `status:"ended"`·`turn: null` → Y5(DECISIONS #82) / ② 종료 사유 표시 — 보류: 응답에 사유 필드 없음, 요구되면 `PracticeSessionView`에 하위 호환 추가(domain 함수가 사유를 이미 구분하므로 비용 작음) |
| 64 안전 안내 멈춤 뒤 처리 (2026-11-11 추가 — PRD F-11 ⑧) | safe_reply 안내 턴 `ai_line` 출처, Y4 멈춤 상태 이동, 보호자 알림 | **해소(2026-11-11 — 사용자 답 "고정 문구+홈, 알림 없음 (추천)", DECISIONS #118)**: ① "홈으로" 버튼(→ Y3) ② 보호자 알림 1차 미생성 ③ 안내 = 백엔드 고정 문구 `safety_stop.json`, AI `reply`는 저장·표시·로그 안 함. 문구 내용은 콘텐츠 담당(OQ 3)·사용자. PRD OQ 64 해소 기록은 planner |
| 43 보호자 알림 간소화 내용 | 예시 알림 적재만으로 충분한지, 연습 결과로 알림을 만드는 경로가 필요한지 | 예시 데이터 적재(`origin=demo_seed`)만 설계 |
| 44 Y3 진입 처리 | 프론트 기능 플래그 값 | 플래그만 |
| 45 팀 문서 대응 | 2차 확장 지점이 1차로 돌아오는지 | 1차 범위 기준 설계 |
| 55 F-48 심화 연습 유지/2차 (2026-11-07 추가) | 내부 API `deep/feedback`·심화 연습 안전 처리, 공개 API A20~A23, AI-1의 `deep/feedback` 요청 | **해소(2026-11-07 — 사용자 확인 대상)**: 사용자 답변 원문 "AI 피드백만 2차로" → (나), 화면 유지는 메인 세션 해석(추정). 차수 변경: `deep/feedback`·심화 연습 안전 처리·`PracticeAI.deep_feedback`·A21·`DeepFeedbackView`·AI-1의 `deep/feedback` 요청 → [2차](규격은 삭제하지 않고 유지 — T-82). A20 → 조건부(1차 기본안: 만들지 않음), A22 → 1차 없음, A23 → 조건 그대로. DECISIONS #71·#73 |
| 59 1차 심화 연습 아이 입력 처리 (2026-11-07 추가 — PRD OQ 59, architect 판단 후 사용자 확인) | A20·A21 1차 존치, A22·A-17, Y5-1~Y5-4 화면 상태, 위험 표현 안내, N-04 1차 케이스 | **① 사용자 확정(2026-11-07 '기본안대로' — 메인 세션 질문 원문 "1차에 아이 답변을 서버로 보내지 않는 기본안으로 갈까요?", DECISIONS #76) / ② 2026-11-08 PRD OQ 60으로 분리 — architect 권고, 사용자 확인 대상(DECISIONS #74·#77) / ③ ①의 귀결 — planner 반영 대상**: ① 1차에는 아이 답변을 서버로 보내지 않는다 — 브라우저 화면에서만 다룬다(A21 1차 없음). 근거: OQ 50 ③의 후보 (a)(b)(c)와 조합 모두 답변을 서버로 보낼 필요가 없고(데이터 흐름 4-1번), 1차 인수 기준에 서버가 답변으로 할 일이 없으며, 받기만 하면 PRD R-8의 민감 정보 노출면(전송·로그·저장 유혹)만 늘어난다. ② 위험 표현 탐지(서버·브라우저)는 두지 않는다 — 탐지 규칙은 OQ 25 미정이고 1차에는 탐지 결과로 할 일(차단·전달)이 없다. 대신 입력란 근처 **고정 안내 문구**(프론트 상수, 예 방향: 이름·전화번호 같은 개인정보는 쓰지 않아도 된다는 안내 — 문구는 N-03·OQ 23 기준으로 planner·사용자)를 권고 — 남는 위험(아이가 민감한 내용을 입력, 말로 답하기의 브라우저 외부 전송 D-9)을 줄이는 비용이 가장 작은 수단. 둘지 여부는 사용자 확인. ③ A-17은 1차에 저장할 대상이 없다 → 2차(T-82) 착수 전으로 넘긴다(planner 판단과 같음). N-04 1차 테스트 케이스 필요 없음(AI 입·출력이 없음). 예외: OQ 50 ⑤가 1차 "저장"으로 정해지면 ①을 뒤집어 A21을 AI 없는 제출 엔드포인트로 1차에 두고 A-17 B안을 새 결정으로 정한다. DECISIONS #72·#74 |
| 56 보호자 학습 요약 단위 (2026-11-07 추가) | ~~`summaries/guardian`의 `unit`~~ AI `summary` 호출 수, `GuardianSummaryView.unit`·`items` 개수 | **해소(2026-11-11 — 사용자 답 "영역별 요약 (추천)", DECISIONS #114)**: `unit = "area"`, 기록 있는 영역마다 항목 1개·AI 호출 1회(최대 3). ~~기본값 `overall`(항목 1개)~~. PRD OQ 56 기록 갱신은 planner |
| 57 고른 선택지 설명 ①과 F-13 (2026-11-07 추가) | `practice/feedback` 요청 필드, 카드 문장 내용 | architect 판단: 같은 카드 문장에서 처리(별도 설명 영역 없음), 요청에 `history`·`normal_outcome` 추가. 검증 가능한 승인 기준이 필요하면 planner가 F-13에 추가(사용자 확인) |

### 설계가 올린 질문 (PRD에 없음 — 2026-11-06 상태 갱신)

| # | 질문 | 상태 | 설계의 현재 처리 |
|---|---|---|---|
| A-1 | 시연 흐름에서 Y8 예시 성장 기록·G3 예시 안전 알림을 어느 계정에 보이는가 — ① 고정 시연 계정 ② 시연 중 새로 가입·등록한 아이에 덧붙임 | 보류 (메인 세션 분류) | 추천안 ① 고정 시연 계정으로 진행. `app/demo/seed`는 두 방식 모두 지원(`origin=demo_seed`). T-67에서 확정 |
| A-2 | 배포 서비스 확정 — PaaS(추천 Render, 이제 웹 서비스 2개)·관리형 Postgres(추천 Neon·Supabase)와 계정·요금제 | 보류 | ADR-0007 추천안으로 진행, T-27에서 확정 |
| A-3 | 패키지 설치 허용 범위 | **해소** — 사용자 원문 "필요한 건 추가 해"(메인 세션 해석: 설치 허용) | 기술 스택 확정 |
| A-4 | 프론트 스택 팀 확인(PRD OQ 6) | **해소** — frontend 저장소 실제 코드(인용) | ADR-0012 |
| A-5 | 연결 코드 6자·PIN 숫자 4자리 형식과 PIN 잠금 없음의 보안 한계 수용 | **부분 해소(2026-11-07)** — PIN은 보호자가 입력하는 숫자 4자리로 확정, 쉬운 PIN·잠금 없음의 위험은 1차 수용(사용자 "보호자 입력으로 반영", DECISIONS #59). 연결 코드 6자 형식은 보류 유지 | 연결 코드는 기본값으로 진행(설정 상수). 운영 전 과제: F-44 + 쉬운 PIN 거부 |
| A-6 | 저장소 초기화·원격 호스팅 | **부분 해소** — GitHub 조직 line1thon-15의 backend 저장소(비어 있음)가 대상(인용). 이 폴더의 git 초기화·원격 연결·push는 사용자가 아직 하지 않음 | "저장소와 브랜치" 절 |
| A-7 | 팀원 6명의 Python·Node 버전 | 보류 | Python 3.12+ 기준으로 진행 |
| A-8 (신규) | AI 담당이 ADR-0011(별도 HTTP 서비스 + 내부 API 규격)에 합의하는가 — 아니면 대체안(ai를 pip 패키지로 백엔드가 설치) | **해소(2026-11-07 — 사용자 확인 대상)** — AI 담당 답변 원문 "동의합니다. AI 레포에서 별도 HTTP 서버(8081)를 운영하는 방식으로 진행하겠습니다." 대체안(pip 패키지)은 쓰지 않음. 엔드포인트별 필드 규격·토큰·계약 샘플 합의는 답변에 없음 → A-16에 남김 | ADR-0011 결정 A 유지(상태는 Architecture 승인과 함께 사용자가 정함). 백엔드는 계속 `FakePracticeAI`로 진행 |
| A-9 (신규) | 이 저장소의 docs/GitWorkflow.md(main + feature, dev 없음)와 팀 컨벤션(main/dev/feature/*, PR base dev, main·dev 직접 push 금지)이 다르다 — 어느 쪽을 따르는가 | 미확인 — GitWorkflow.md는 사용자 소유 | 이 문서의 CI·배포는 팀 컨벤션 기준으로 적음 |
| A-10 (신규) | 팀 docs 저장소에 공유 규격("팀 공유 규격" 표)을 누가 언제 게시하는가 | 미확인 | 사용자(백엔드 담당)가 게시하는 것으로 가정 |
| A-11 (신규) | 프론트 담당이 요청 F-1~F-5에 합의하는가, 테스트·E2E 하네스(F-6)를 구축하는가 | 미확인 — 확인 방법: 사용자가 프론트 담당에게 전달 후 답변 원문 수집 | F-1~F-4가 안 되면 ADR-0013 대안 C(Bearer 토큰)로 새 ADR. F-6이 안 되면 N-06 E2E 미충족 — AGENTS.md에 따라 사유를 이 문서에 기록해야 함 |
| A-13 (신규 2026-11-06) | 운영(공개 URL) AI 서비스의 Gemini 키를 Cloud Billing 계정이 활성화된 프로젝트로 만들 것인가 — 활성화하면 무료 할당량 안이라도 유료 서비스 데이터 조건이 적용되어 입력·출력이 제품 개선에 쓰이지 않고, 기록은 제한된 기간·정책 위반 감지 목적으로 한정된다(한국어판 약관 인용). 유료 조건에서 사람 검토가 있는지는 인용된 발췌에 없어 미확인. 비용 사실(메인 세션 2026-11-06 Browser pane 확인, https://ai.google.dev/gemini-api/docs/billing 영문판, 인용): "Upgrading from the Free Tier to the Paid Tier means linking a billing account and prepaying to add a minimum of $5 (or equivalent in other currencies) of credits to your account." / "the Gemini API will only serve requests if you have a positive Prepay credit balance." / "You can unlink a project from its billing account to return to the free tier." — 해석(메인 세션, 법률·회계 검토 아님): 최소 $5 선불 후 사용량 차감, 잔액이 0이면 요청이 중단되므로 시연 직전 잔액 확인 필요(중단 시 백엔드는 `AI_UNAVAILABLE`). 약관의 "무료 할당량 … 유료 서비스로 간주"는 데이터 처리 기준이지 비용 기준이 아니다. 모델별 토큰 단가는 미확인 | 미확인 — 팀 결정(사용자가 팀원과 논의) | 설계 권고는 활성화(DECISIONS #49). 연령 조항 위험(PRD R-1)은 어느 쪽이든 그대로 |
| A-14 (신규 2026-11-06, = PRD OQ 48) | AI 파트 3 "사용자의 선택과 판단 이유 분석"의 1차 범위 — 1차 입력은 선택지(ID)뿐이고 자유 답변·판단 이유 입력(F-38)은 2차다. AI 담당이 1차 "판단 분석"을 선택지 태그 기반 찾음/놓침 판정(`judge`)으로 이해하는가 | **해소(2026-11-07 — 사용자 확인 대상)** — AI 담당 답변 원문 "이번 MVP에서는 ①을 구현하고, ②는 향후 발전 방향으로 가져가면 좋겠습니다." (① = 메인 세션 질문 원문 "아이가 고른 선택지가 왜 맞았는지/틀렸는지 AI가 설명해 주는 것") | 1차 입력은 선택지만, 점수 없음 유지. ①은 `practice/feedback` 카드 문장으로(요청에 `history`·`normal_outcome` 추가 — PRD OQ 57 판단). ②와 F-48의 관계는 PRD OQ 55 |
| A-15 (신규 2026-11-06, = PRD OQ 49) | AI 파트 8 "영역별 성장 수준 분석"의 "수준" — 1차는 백엔드가 계산한 지표(OQ 12)만 쓰고 수준 등급·점수는 만들지 않는다(F-29 ③ "검증되지 않은 능력 점수·자립 보증 수치는 표시하지 않는다"). AI 담당이 "수준 분석"을 백엔드 지표의 문장화로 이해하는가 | **해소(2026-11-07 — 사용자 확인 대상)** — 메인 세션 질문(점수(단계)는 백엔드가 계산, AI는 문장만)에 AI 담당 답변 원문 "좋습니다." 질문의 "점수(단계)"는 메인 세션 표현이며 새 등급 체계로 반영하지 않음(PRD OQ 49 반영과 같음). Y8 아이용 AI 요약 여부는 PRD OQ 49 잔여 | 영역별 성장 수준 = `LearningSummaryInput.areas`의 영역별 기록 수(이번·직전 기간), 비율·등급 없음. 요약 문장 공통 제약(숫자는 입력 값만) 유지. `child-growth`는 계속 선택·구현 금지 |
| A-18 (신규 2026-11-07) | 보호자 학습 요약의 "기록이 부족하면"(PRD F-47 ⑥) 기준 — PRD에 수치가 없다 | 미확인 — planner가 PRD에 기준을 두거나 사용자 확인 | **[가정]** 기간(`SUMMARY_PERIOD_DAYS`) 안에 종료된 연습 세션이 설정 상수 `SUMMARY_MIN_ENDED_SESSIONS`(가정 기본값 1) 미만이면 `insufficient`. 값은 상수 1곳 — 답에 따라 교체. 2026-11-11 메모: 기간(`SUMMARY_PERIOD_DAYS`)은 지표 기간 7일(한국 시간)로 정해졌다(DECISIONS #88). 이 기준 값(가정 1)은 PRD OQ 58 미결이라 바꾸지 않았다 |
| A-19 (신규 2026-11-11) | 지표의 "비교 불가"(PRD F-29 ⑥ "한 기간(7일)의 완료 세션이 3개 미만 … 그 지표는 숫자 대신 '비교 불가'")에서, 이번 기간은 3개 이상이고 직전 기간만 3개 미만일 때 이번 기간 값은 보이는가 | 미확인 — planner·사용자 확인 | **[가정 — 글자 그대로]** 어느 한 기간이라도 3개 미만이면 `insufficient`, 숫자 0개(`current`·`previous` null). 이번 값을 보이기로 정해지면 `insufficient`일 때 `current`만 채우는 하위 호환 변경(필드 그대로). 영향: 첫 사용 후 약 2주간 모든 지표가 "비교 불가" — 시연 계정은 예시 데이터(T-67)가 두 기간 모두 3세션 이상이어야 숫자가 보인다 |
| A-20 (신규 2026-11-11) | 보호자 G3 추이 그래프(F-31 "시간 순 추이 그래프")에 몇 개 기간을 보이는가 — 답(OQ 12)은 "최근 7일 vs 직전 7일" 두 기간만 정했다 | 미확인 — planner·사용자 확인 | **[가정]** `trend` = 두 기간 2점(F-31 "2회 이상 기록"의 최소). 더 많은 기간(예: 최근 4주)이 필요하면 `trend` 점 수만 늘리는 하위 호환 변경 + 기간 수 설정 상수 추가 |
| A-21 (신규 2026-11-11) | `NoticeView`의 `notice_id`·`kind`(그리고 `trusted_contact`의 `channel`)가 PRD F-41 ⑤ "보호자용 안전 알림 응답에도 위 세 항목 외의 알림 내용 필드가 없다"(planner 해석 9, 사용자 확정)에 어긋나는가 | 미확인 — planner·사용자 확인 | **[가정]** 어긋나지 않는다고 본다 — `notice_id`는 목록 키용 식별자(상세 API 없음), `kind`·`channel`은 기존 연락 알림(F-23 ③)과 안전 알림을 구분하는 값이며 알림 내용(무엇이 위험했는지)을 담지 않는다. 어긋난다고 정해지면 `kind = "safety"` 항목에서 해당 키를 빼는 응답 변경(프론트 T-65 영향) |
| A-22 (신규 2026-11-11) | AI `judge`의 `not_shown`을 어떻게 다루는가 — 지표 (가)(나) 분모·배지 "모두 찾음"의 뜻(PRD F-13 ④·F-28 ②·F-29 ⑤ 문구와 충돌) | **해소(2026-11-11 — 사용자 답 "드러난 단서만 판정 (추천)", DECISIONS #109)** | N1: 드러난 단서만 판정 대상, `not_shown`은 저장·집계하지 않음. 계산 규격 #116("성장 계산 규칙" 절). PRD F-13 ④·F-28 ②·F-29 ⑤ 문구 갱신은 planner |
| A-23 (신규 2026-11-11) | `safe_reply` 즉시 중단(세션 `stopped`, Y4 안내 상태, 409 `SESSION_STOPPED`)을 1차에 두는가 — PRD F-11에 없는 종료 조건과 화면 상태 | **해소(2026-11-11 — 사용자 답 "이대로 (추천)", DECISIONS #113)** | #99대로 1차에 둔다. PRD F-11 종료 조건·Y4 안내 상태 추가는 planner. 1차 선택지 입력에서는 거의 나지 않음(추정 — 확인 방법은 #99 근거 열) |
| A-24 (신규 2026-11-11) | 콘텐츠 원천(ai `content/` vs 백엔드)과 Area ID(AI `identity_lending`·`friend_pressure`) | **해소(2026-11-11 — 사용자 답 "AI 저장소 원본 (추천)"·"AI ID로 맞춤 (추천)", DECISIONS #111·#112)** | AI 원천 + 백엔드 읽기 전용 사본(커밋 고정)·오버레이, Area는 AI ID(공통 값 타입 Area 행 갱신). 프론트 알림은 메인 세션·사용자 |
| A-16 (신규 2026-11-06) | 내부 API v1·공개 API v1 계약 고정일을 2026-11-07로 할 수 있는가(팀 타임라인 "11/11 - 각 파트 개발 완료 / 11/12 - 연동") | 미확인 — 팀 합의 | "계약 고정과 연동 일정" 표 |
| A-17 (신규 2026-11-07, = PRD OQ 50 ⑤) | 심화 연습에서 아이가 쓴 글(말을 바꾼 글 포함)과 AI 피드백을 서버에 저장하는가 | 미확인 — PRD OQ 50(프론트 B·디자인·팀). Tasks T-79는 2026-11-08부터 이 답 때문에 보류된 것이 아니다 — 답변 제출 처리를 빼고 조건부 API(A20·A23)만 남아, 보류 사유가 "DECISIONS #73 사용자 확인 대기, PRD OQ 50 ①②④"로 바뀌었다(Tasks T-79 상태 열, 인용). **2026-11-07 갱신(PRD OQ 59 ① — 2026-11-08 기록: 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76)**: 1차에는 답변이 서버로 오지 않아(DECISIONS #72) 1차에 저장할 대상이 없다 → 이 질문은 2차(T-82) 착수 전에 정하면 된다. 아래 A안·B안 비교는 2차 기준으로 유지. 1차에서 이 질문이 다시 열리는 경우: OQ 50 ⑤가 1차 "저장"으로 정해질 때뿐 | **A안 저장 안 함 (기본 권고)**: 새 테이블·마이그레이션 없음, A22 불필요, Y5-4는 A21 응답을 표시(새로고침 시 결과를 잃음 → Y5-2 안내), 보관 기간(OQ 32)·삭제 절차가 필요 없음, 민감한 고백이 DB에 남지 않음(PRD R-8). 성장 지표·보호자 요약에 답변을 쓸 수 없음. **B안 저장하되 보호자 비노출**: `deep_answers` 테이블(세션·아이 FK, 답변, 피드백, 시각) + Alembic 마이그레이션 + A22 + 보관 기간·삭제 정책(OQ 32) 결정 필요, 보호자 응답 금지 키 테스트는 같음, 저장된 고백을 누가 볼 수 있는지 운영 정책 필요. 권고 이유: F-48 인수 기준에 저장된 답변을 쓰는 기능이 없고, 보관 정책이 미정이며, 개발 마감(2026-11-11)이 가깝다. 어느 안이든 A21 요청·응답 형태는 같다 — T-79는 A안으로 먼저 진행 가능(이 판단은 planner 몫) |
| A-12 (신규) | T-01을 저장소별로 나눌지 — 이 폴더(backend)의 T-01 완료로 백엔드 코드 작업(T-06 등) 착수를 허용하는가 | **해소 — 사용자 확정(2026-11-08 '받아들임')** — Tasks 쪽 분리: T-01 백엔드·T-83 프론트·T-84 AI 하네스, 실행 단위별 적용(Tasks "파트별 하네스 분리" 절, 인용). AGENTS.md 문구 해석: 메인 세션 질문 원문 "하네스 규칙을 파트별로 적용하는 해석을 받아들일까요?", 사용자 답변 원문 "받아들임"(DECISIONS #78) | 설계는 실행 단위별 하네스 범위만 정의("T-01 하네스 범위" 표 — 2026-11-08 T-01·T-83·T-84 표기) |

## 설계 리스크 (2026-11-06 갱신)

| # | 리스크 | 대응 |
|---|---|---|
| D-1 | Vercel 외부 리라이트(프록시)로 쿠키가 정상 전달되는지 미검증(추정으로 설계). 프론트가 프록시·`VITE_API_URL` 변경을 하지 않으면 로그인 유지 불가 | 프론트 요청 F-1~F-3 [A-11]. T-27에서 공개 URL로 로그인 → 쿠키 → 인증 API 확인. 실패 시 ADR-0013 대안 C(Bearer 토큰)로 새 ADR |
| D-2 | 테스트는 SQLite, 운영은 Postgres — 방언 차이 | ORM 공통 타입(`Uuid`·`JSON`·`DateTime(timezone=True)`)만 사용, Postgres 전용 기능 금지. T-27·T-28에서 운영 DB로 시연 흐름 확인 |
| D-3 | 무료 등급 PaaS 유휴 절전으로 시연 첫 요청 지연(추정) — 이제 백엔드·AI 두 서비스 | 시연 직전 두 헬스체크 호출, 필요 시 유료 등급 — [A-2] |
| D-4 | 콘텐츠(OQ 3) 미정으로 AI 연습 기능 착수 불가 | `FakePracticeAI` + 테스트용 최소 예시 콘텐츠로 백엔드·프론트는 먼저 진행 가능. 실제 콘텐츠는 OQ 3 답 후 |
| D-5 | Gemini 키 정지(약관 20(f), PRD R-1) | 연습 화면만 `AI_UNAVAILABLE`, 그 외 화면은 동작. 제공사 교체는 ai 저장소 안에서(N-10) |
| D-6 (신규) | 저장소 3개 사이 계약 어긋남(공개 API·내부 API) — 프론트는 JavaScript라 컴파일 시점 검출 없음 | docs 저장소 정본 + 계약 샘플 JSON 공유 + 팀 컨벤션의 "다른 파트 담당 리뷰어 지정" + 프론트 E2E(F-6) |
| D-7 (신규) | AI 서비스 지연이 연습 응답 시간에 더해짐(백엔드 → AI → Gemini 2홉) | 시간 초과를 백엔드 > AI 서비스 > 제공사 순으로 설정, 로딩 표시(Y4 상태). 지연 수치는 측정 안 함 — T-12·T-15에서 실측 |
| D-8 (신규 2026-11-06) | G3 조회마다 보호자 학습 요약 생성 호출(캐시 없음) → G3 응답 지연·Gemini 사용량 증가(유료 선불 잔액 소진 — A-13) | 요약 호출에 짧은 별도 시간 초과(설정 상수), 실패 시 `summary.status = "unavailable"`로 G3는 정상(2026-11-07 갱신 — 기록 부족이면 AI 미호출). 요약 단위가 영역별로 정해져도(PRD OQ 56) 호출은 G3 조회당 1회 — 출력 문장 수·토큰은 늘 수 있음(수치 미측정, 추정). 지연·사용량이 문제로 측정되면 요약 저장(캐시) 테이블을 새 결정으로 추가. **상태(2026-11-06)**: 사용자가 비저장을 확정하며 이 트레이드오프를 수용함(사용자 "추천안대로" — 추천안 원문 "G3를 볼 때마다 AI를 호출하므로 조금 느리고 선불 크레딧이 줄어듭니다. 시연 계정은 예시 데이터라 영향이 작습니다."). 지연·사용량 수치는 미측정 |
| D-9 (신규 2026-11-07) | 말로 답하기(F-48 ③)의 브라우저 음성 인식이 음성을 브라우저 제조사 서버로 보낼 수 있고(추정 — 미확인), 일부 브라우저는 지원하지 않을 수 있다(추정). 우리 서버로 음성이 오지 않아도 아이의 목소리가 제3자에게 갈 수 있음(PRD R-8, OQ 53) | 음성은 우리 API로 보내지 않음(ADR-0014), 미지원·권한 거부 시 Y5-2로 안내. T-81 착수 전 대상 브라우저 문서·실기기 확인. 외부 전송이 확인되면 말로 답하기를 끌지(글로 답하기만 둘지) 사용자 결정 |
| D-10 (신규 2026-11-07, 2026-11-07 갱신 — 사용자 확인 대상) | **[2차 — T-82]** 아이가 직접 쓴 글이 처음으로 AI 서비스·Gemini로 간다 — 피해 고백·개인정보 포함 가능(PRD R-8). **1차(PRD OQ 55 해소 + OQ 59 ① 사용자 확정(2026-11-07 '기본안대로'), DECISIONS #76)**: 아이 글이 우리 서버·AI·Gemini로 가지 않는다. 남는 1차 위험: ① 아이가 민감한 내용(피해 고백 등)을 입력해도 아무도 읽지 않는다 — 도움 연결 여부는 제품 결정(설계로 정하지 않음) ② 말로 답하기의 브라우저 음성 인식 외부 전송(D-9) | 1차: 서버 요청 없음(DECISIONS #72), 프론트 메모리 상태만·브라우저 저장소 금지, 고정 안내 문구 권고(DECISIONS #74), E2E 네트워크 검사. [2차]: 입력 필터(개인정보 형식이면 LLM 미호출), 로그 금지, 보호자 비노출, 저장 안 함 권고(A-17), 결제 계정 활성 키 권고(DECISIONS #49) |
| D-11 (신규 2026-11-08) | 연습 종료가 AI가 붙인 선택지 `judgment` 태그에 달려 있다(DECISIONS #80). 태그가 내용과 어긋나면(예: 돈을 보내는 선택지에 `suspicious`) 아이가 믿는 답을 골라도 바로 끝나거나 그 반대가 된다 — 종료 시점과 판정(`judge`, 태그 기반)이 함께 틀어진다. 백엔드는 태그 개수 구성(#83)만 검증할 수 있고 의미는 검증할 수 없다 | AI 서비스 몫으로 명시(AI-5 ③) — AI 담당이 태그 정확성 검증 방법을 정함(예: N-04 세트에 케이스 추가, 추정). 백엔드는 #83 구성 제약 + Fake 결정적 태그로 종료 로직만 검증. 시연 전 리허설(T-28)에서 실제 AI로 의심·믿음 선택 흐름을 각 1회 이상 확인 권고 |

| D-12 (신규 2026-11-11) | 배지·연속 기록·지표를 저장하지 않고 매 요청 계산하므로(DECISIONS #28·#90), 보존 기간(PRD OQ 32)이 옛 연습 세션을 지우게 정해지면 이미 보인 배지가 사라지고 지표 원천도 줄어든다. 또 지표 (다)는 보호자 경로에서 `practice_turns`를 읽는 예외(ADR-0016)에 기대므로, 그 예외의 보장은 구조가 아니라 테스트(R1~R4)다 | OQ 32 답에서 삭제가 정해지면 배지 테이블(획득 시점 고정)을 새 결정으로 추가. 예외 회귀는 테스트 전략 2026-11-11 ①의 R1~R4를 반드시 둔다 — 하나라도 빠지면 ADR-0016 방법 2(세션 열 저장)로 바꾸는 새 ADR 검토 |
| D-13 (신규 2026-11-11) | AI 계약 채택 후: ① AI가 Gemini 실패·한도 초과를 오류 대신 고정 문장으로 대체해(`source = "fallback"`) 장애가 화면에 드러나지 않고 대화 품질만 떨어진다(AI 담당 원문 "Gemini 무료 키 하루 제한을 다 써서") ② `variant` fallback(원본 시나리오)이 직전 세션과 같으면 F-12 검사로 503 — 한도 소진 중에는 같은 시나리오 재출제·다시 도전이 실패할 수 있다 ③ 보호자 요약 호출이 G3당 최대 3회로 늘어난다(D-8) | ① 시연 전 리허설(T-28)에서 AI `source` 값을 백엔드 로그(값만, 본문 없음)로 확인 ② 다시 도전 실패는 "다시 시도"로 처리(#85와 같은 화면), 운영 키 결제 계정(A-13) ③ 요약 호출에 짧은 시간 초과 유지(D-8) |

## 주요 결정

결정 기록은 [DECISIONS.md](DECISIONS.md)와 [adr/](adr/)에 있다. 이 문서에는 결과만 반영한다.

| ADR | 제목 | 상태 |
|---|---|---|
| [ADR-0001](adr/0001-service-composition.md) | 단일 Python 백엔드 + 같은 프로세스의 AI 포트 모듈 | 폐기(→ ADR-0011) |
| [ADR-0002](adr/0002-backend-framework.md) | 백엔드 프레임워크 FastAPI | 제안 |
| [ADR-0003](adr/0003-frontend-stack.md) | 프론트엔드 React + Vite SPA + TypeScript + Tailwind ([가정]) | 폐기(→ ADR-0012) |
| [ADR-0004](adr/0004-auth-session.md) | 인증·세션: DB 불투명 토큰 + httpOnly 쿠키 + 같은 출처 프록시 | 폐기(→ ADR-0013) |
| [ADR-0005](adr/0005-data-store.md) | 저장소: PostgreSQL + SQLAlchemy/Alembic, 테스트 SQLite | 제안 |
| [ADR-0006](adr/0006-test-runners.md) | 테스트 러너 (2026-11-06 범위 갱신 — backend는 pytest만) | 제안 |
| [ADR-0007](adr/0007-deployment.md) | 배포: Vercel + Python PaaS + 관리형 Postgres (2026-11-06 갱신 — 배포 단위 3개) | 제안 |
| [ADR-0008](adr/0008-tts.md) | TTS: 브라우저 Web Speech API (프론트 구현) | 제안 |
| [ADR-0009](adr/0009-practice-selection.md) | 연습 출제: 정상 상황 슬롯 방식 30%, 변형은 백엔드가 결정 | 제안 |
| [ADR-0010](adr/0010-content-storage.md) | 콘텐츠: JSON 파일 읽기 전용 적재 (2026-11-06 갱신 — 대체 문구·안전 규칙은 ai 저장소) | 제안 |
| [ADR-0011](adr/0011-ai-separate-service.md) | 백엔드–AI: ai 저장소 별도 HTTP 서비스 + 백엔드 포트·HTTP 어댑터 | 제안 — AI 담당 합의(2026-11-07, A-8 해소), 사용자 승인 전 |
| [ADR-0012](adr/0012-frontend-actual-stack.md) | 프론트엔드: 실제 스택(React 19·Vite 7·JavaScript·Tailwind v4·React Router 7) 수용 | 제안 |
| [ADR-0013](adr/0013-auth-same-origin-proxy.md) | 인증 쿠키 유지 + 프론트 쪽 같은 출처 프록시(`VITE_API_URL` 비움) | 제안 |
| [ADR-0014](adr/0014-deep-practice-voice-input.md) | 심화 연습 말로 답하기: 브라우저 음성 인식으로 글자 변환, 서버는 글만 받음 (2026-11-07 덧붙임 — 1차는 글도 서버로 보내지 않음, 결정 A 유지) | 제안 |
| [ADR-0015](adr/0015-practice-end-backend-rule.md) | 연습 종료: 백엔드 규칙만 — `is_terminal` 삭제(내부·공개), A17은 `PracticeSessionView`로 종료 알림 (2026-11-08) | 제안 — 결정 1·2 사용자 확정(2026-11-08, DECISIONS #84·#85), 사용자 승인 전 |
| [ADR-0016](adr/0016-guardian-path-first-answer-read.md) | 성장 지표 "AI보다 먼저"의 원천 — 보호자 경로의 `practice_turns` 읽기에 좁은 예외 (2026-11-11) | 제안 — 방향(방법 1)·경계·강제 수단 모두 2026-11-11 사용자 확정("그렇게 해", DECISIONS #93 — 덧붙임), 태그 이름은 `kind`로 읽음. 사용자 승인 전 |
| [ADR-0017](adr/0017-ai-contract-alignment.md) | 백엔드–AI 내부 API v1을 AI 저장소 1차 구현 계약(`contracts/`)으로 재정렬 (2026-11-11) | 제안 — 방향은 사용자 결정("그렇게 해"), 세부도 2026-11-11 사용자 확정(DECISIONS #111~#115 — 덧붙임). 사용자 승인 전 |
| [ADR-0018](adr/0018-not-shown-and-normal-judgment.md) | AI 계약의 `not_shown`과 정상 상황 판정 — 지표·배지의 "목표 단서" 해석 (2026-11-11) | 제안 — N1·M1 2026-11-11 사용자 확정(DECISIONS #109·#110 — 덧붙임). 사용자 승인 전 |
