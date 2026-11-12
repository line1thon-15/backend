# CHANGELOG — 2026_line1thon

> 소유자: docs | 형식: [Keep a Changelog](https://keepachangelog.com/ko/) 축약. 최신이 위.

## [Unreleased]

### Added
- 2026-11-12 T-89 결과 카드 색 확정(구현 커밋 d52dbcf, 문서 결정 ee047af) — `CARD_LEVEL_BY_KEY`를 K1 green / K2 yellow / K3 green / K4 green / K5 yellow로 채움(DECISIONS #120). 노랑 화면 문구는 "믿는 사람에게 물어봐요"(#121), API 값은 그대로 `yellow`. 카드 매핑 확인을 `feedback` 호출 전으로 옮겨, 매핑이 없으면 AI 호출 없이 500. 위 T-16 제한 ①(카드 색 미정이라 기본 설정에서 A18 항상 500)은 이 항목으로 해소됨. 테스트 485 passed(인용)
- 2026-11-12 T-16 연습 결과 API와 다시 도전(브랜치 `claude/feat-t-16-practice-result-ccc228`, 구현 커밋 47ff287, T-15 6bdde6a 위) — A18 `GET /api/v1/practice/sessions/{session_id}/result`(`app/api/practice.py`): AI `feedback` 응답을 `found`·`missed` 단서 카드와 `cards`(K 단계 매핑)·`can_retry`로 바꿔 돌려주고, 검증 V1'~V3' 위반이나 `feedback` 실패는 전체 503 `AI_UNAVAILABLE`. A15 `mode:"retry"`(요청 `retry_of`, 영역은 원 세션 값 사용)로 다시 도전 출제. 결과 매핑·다시 도전 판정 domain `app/domain/practice_result.py`, `create_app()`에 `card_level_by_key` 주입 인자 추가. 리뷰 치명 0, QA 480 passed·치명 0(Tasks.md T-16 행 인용; T-15 기준 408 passed)
- 2026-11-12 T-16 알려진 제한(근거: docs/Tasks.md T-16 행) — ① [T-89로 해소됨 — 위 T-89 항목 참조] 카드 색 값(PRD OQ 63·24)이 아직 정해지지 않아 기본 설정(`CARD_LEVEL_BY_KEY` 빈 값)에서는 A18이 항상 500이다. 시연 전 결정 필요(테스트는 값을 주입). ② `can_retry` 규칙이 문서화되지 않았다. ③ A15 retry의 409 오류 코드(`SESSION_NOT_ENDED`·`SESSION_STOPPED`·`NO_SCENARIO_AVAILABLE` 재사용)가 Architecture A15에 없다(404만 있음). ④ 정상 상황 결과 조회는 1차 범위 밖이다(정상 상황 출제가 꺼져 있음, 도메인 함수만 테스트). ⑤ 미검증: 정상 상황 K4·K5 끝단, 실제 `HttpPracticeAI`(미구현)
- 2026-11-12 T-15 연습 세션 API(브랜치 `feat/T-15-practice-session`, 구현 커밋 d1c2222, 리뷰 수정 eb25efc) — A15 `POST /api/v1/practice/sessions`(영역별 출제, 201)·A16 `GET /api/v1/practice/sessions/{session_id}`·A17 `POST /api/v1/practice/sessions/{session_id}/turns`(`app/api/practice.py`, 서비스 `app/services/practice.py`, 출제·종료 판정 domain `app/domain/practice_selection.py`·`practice_end.py`, 저장소 `app/repositories/practice.py`). 마이그레이션 `20261112_04`(`practice_sessions`·`practice_turns`·`cue_results`, `cue_results`는 세션·단서 쌍 유일 제약). 동시에 같은 세션에 답이 겹치면 조건부 갱신으로 하나만 반영하고 나머지는 409 `SESSION_ENDED`(리뷰 치명 1건 수정). `FakePracticeAI`·`build_practice_ai`에 선택 인자 `scenario_clue_ids`(시나리오별 단서 ID) 추가. 리뷰 치명 0(재검토), QA 408 passed·치명 0(QA 확인, 인용; dev 기준 165 passed)
- 2026-11-12 T-15 알려진 제한(근거: docs/Tasks.md T-15 행) — ① 미검증 3건: `HttpPracticeAI`의 `is_terminal` 파싱(클래스 없음), 보호자 알림 0행(`guardian_notices` 테이블 없음), 진짜 병렬 요청 레이스(순차 재현으로 대체). ② A15는 `mode:"area"`만 받는다(`mission`·`retry`는 후속). ③ 지금 콘텐츠로는 고등학생만 출제된다(사기 시나리오 2개가 `min_grade H1`). ④ 같은 선택지를 더블탭하는 동시 요청도 409 `SESSION_ENDED`가 나간다(후속 미정). ⑤ 공개 API 영역 값이 `scam`·`identity_lending`·`friend_pressure`라 프론트에 알려야 한다(DECISIONS #108)
- 2026-11-11 T-87 AI 콘텐츠 읽기 전용 사본과 서버 시작 시 검증(브랜치 `claude/angry-lewin-8ac42e`, 구현 커밋 53144c9) — `app/content/data/ai/`(clues.json·scenarios/scam.json, ai 저장소 `feature/ai` 331d2c6 고정, 출처·SHA-256 `SOURCE.txt`), 보충 예시 데이터 `scenario_meta`·`platform_app_types`·`diagnosis`·`safety_stop`(.json; safety_stop 문구는 OQ 66 답 후 교체), `app/content/loader.py`·`schemas.py`, `create_app()`이 시작 시 콘텐츠를 로드·검증(잘못되면 기동 거부), `tests/unit/test_content_loader.py`(사본 해시 무결성 포함). 리뷰 치명 0, QA 6/6, pytest 142 passed(QA 확인, 인용). 사본 갱신 절차는 README 참조(DECISIONS #107)
- 2026-11-11 T-86 `tests/contracts/ai/` — AI 계약 샘플 12개(ai 저장소 `feature/ai` 331d2c6 고정 사본)와 `SOURCE.txt`(출처·SHA-256), 신규 `tests/unit/test_ai_ports.py`(샘플이 포트 모델로 파싱되는지 검증)
- 2026-11-08 T-01 백엔드 테스트 하네스(커밋 43a6acd, 브랜치 `feat/T-01-backend-harness`) — pytest 설정, `GET /api/v1/health` 헬스 엔드포인트(`app/api/health.py`), `FakePracticeAI`와 `PracticeAI` 포트(`app/ai_client/`), import 경계·헬스·AI 클라이언트 팩토리 테스트(`tests/`), `.env.example`, `requirements*.txt`
- 2026-11-08 `.github/workflows/ci.yml` — `dev`·`main` 대상 PR에서 pytest 실행(Fake AI). 작성만 됨, GitHub 실제 실행은 원격 미연결로 미검증
- 2026-11-08 docs/CodingRules.md "검증된 명령어"에 backend 가상환경·설치·테스트·dev 서버·헬스 확인 5행 추가(T-01 실측)
- 2026-11-08 기획·설계 문서와 저장소 기본 설정 추가(커밋 5070035) — docs/PRD.md, Architecture.md, DECISIONS.md, Tasks.md, adr/0001~0014, `.editorconfig`, `.gitattributes`, `.gitignore`
- 2026-10-27 Claude 전용 스킬 `.claude/skills/cli-delegate/SKILL.md` — Codex·안티그래비티에 작업을 넘기는 CLI 위임 절차(프롬프트는 파일·stdin으로 전달)
- 2026-10-27 AGENTS.md "다른 도구 세션과의 핸드오프" 절 — `.artifacts/handoff/{작업ID}/{실행ID}/`의 prompt.md·report.md 규칙, 메인 오케스트레이터는 Claude Code 세션임을 명시
- 2026-10-27 `.codex/DEVELOPMENT.md`, `.codex/FRONTEND.md`(Codex 개발 보조·UI 지침), `.codex/tests/adapters.test.cjs`(연결 파일·훅 배선 검사)
- 2026-10-27 `.claude/hooks/test-contract-check.js` — contract-check C5 워크트리 제외 회귀 검사
- 2026-10-27 docs/CodingRules.md "검증된 명령어"에 회귀 검사 2행과 위임 CLI 명령 2행 추가
- 2026-10-27 `.gitignore`에 `.artifacts/handoff/` 추가
- 2026-10-27 AGENTS.md "메인 세션과 서브에이전트 구분" 절 — 수행 주체 판정표(7행)와 단계별 적용 결과(인터뷰·기획/설계·구현·리뷰/QA/문서화)
- 2026-10-27 `.claude/hooks/test-contract-check.js`에 C5의 `.artifacts/` 제외 회귀 검사 추가
- 2026-10-27 docs/HarnessAudit.md "구성요소 유지·삭제 판정표"
- 2026-10-27 docs/CodingRules.md "검증된 명령어"에 Codex stdin 위임 명령(`-m`·`-o` 포함, 종료 코드 0 실측) 1행 추가
- 2026-10-27 AGENTS.md "사용자 화면 확인" 규칙 — 화면 확인은 사용자가 보는 Browser pane에서 하고 마지막 화면을 닫지 않고 남김, 리뷰·QA 통과 뒤 메인 세션이 `사용자 확인: 통과/보류/미요청 — 사유`를 기록
- 2026-10-27 AGENTS.md "앱 서브 세션 (Claude 데스크톱 앱)" 절 — 생성·보고·검증·제공·정리 5단계(정리는 보관이 기본, 영구 삭제는 명시 지시 시만)
- 2026-10-27 docs/DefinitionOfDone.md에 사용자 확인 기록 항목 추가(planner "완료" 전환 조건, 검증중 전환 조건 아님)
- 2026-10-27 implementer·QA 보고 템플릿에 "남긴 화면" 행 추가
- 2026-10-27 AGENTS.md 검증 루프에 "화면 흐름 회귀" 행 — 웹 UI의 PRD 핵심 사용자 흐름은 E2E 회귀 테스트를 Red-First로 두고, 세션 중 실물 확인과 서로 대신하지 않음(러너를 쓰지 않으면 사유를 Architecture에 기록)
- 2026-10-27 docs/DefinitionOfDone.md에 웹 UI E2E 회귀 항목 추가
- 2026-11-08 프로젝트 초기화 (start_coding 템플릿) — 날짜는 최초 커밋 5070035 기준

### Changed
- 2026-11-11 T-86 AI 포트·Fake를 AI 계약 v1로 재정의(브랜치 `feature/T-86-ai-contract-v1-port`, 미커밋) — `app/ai_client/ports.py`는 `PracticeAI`(`variant`·`start`·`turn`·`judge`·`feedback`)와 `SummaryAI`(`summary`)로, `fake.py`는 `FakePracticeAI`·`FakeSummaryAI`로 바뀌고 `opening`·`ScenarioSpec`·`TurnResult`·`OpeningResult`는 삭제됨(DECISIONS #96·#97·#98·#104·#108, ADR-0017). 영역 ID는 `scam`·`identity_lending`·`friend_pressure`로 변경(옛 `name_lending`·`friend_request` 삭제). T-85가 추가한 `TurnResult` 테스트 3개는 모델 삭제로 함께 제거. pytest 55 → 113 passed(QA 직접 재실행 확인)
- 2026-11-09 T-85 `TurnResult.is_terminal` 삭제(브랜치 `feature/T-85-remove-is-terminal`, 미커밋) — `app/ai_client/ports.py`·`fake.py`에서 필드·인자 제거. 연습 종료 판정은 백엔드 규칙만 한다(DECISIONS #81, ADR-0015). AI가 `is_terminal`을 아직 보내도 오류 없이 파싱하고 값은 남기지 않음(전환 허용). `tests/unit/test_fake_practice_ai.py`에 "필드 없음"·"AI 값 무시(True/False)" 테스트 추가로 pytest 35 → 38 passed(QA 재실행 확인)
- 2026-10-27 역할 단일 원본을 `.agents/roles/*.role.md`로 통합 — `.claude/agents/*.md`와 `.codex/agents/*.toml`은 원본을 가리키는 연결 파일로 축소
- 2026-10-27 `.codex/EXECUTION.md`·`.agents/skills/vibe-mode/SKILL.md`·`docs/ToolPacks.md`·`docs/KitFeedback.md` 갱신, AGENTS.md 문서 소유권 표에 새 경로 반영
- 2026-10-27 `.claude/hooks/contract-check.js` C5 플레이스홀더 검사가 `.claude/worktrees/`를 제외
- 2026-10-27 `.claude/hooks/contract-check.js` C5 플레이스홀더 검사가 `.artifacts/`도 제외(Git 제외 증거·핸드오프 보관소)
- 2026-10-27 `.claude/hooks/README.md`·`test-guards.js` 헤더·AGENTS.md "강제 장치" 표에 `confirm-agy-delegate.js` 확인 훅 반영
- 2026-10-27 `.agents/skills/vibe-mode/SKILL.md` 완료 판정 상태값 `done` → `완료`(Tasks.md 상태값과 일치)
- 2026-10-27 `docs/UpdateRequests.md` 규칙 문장에서 AGENTS.md 문서 소유권 표와 모순되던 implementer 비교 구절 제거
- 2026-10-27 `.agents/skills/idea-interview/SKILL.md` 인터뷰 수행 주체를 Claude Code 메인 세션으로 명시
- 2026-10-27 AGENTS.md 핸드오프 "상태 전환" 행에 "받은 역할이 planner여도 같다" 보완
- 2026-10-27 `.claude/skills/cli-delegate/SKILL.md` Codex stdin·`-o` 조합 검증 상태를 실측됨으로 갱신
- 2026-10-27 README: 인터뷰 시작 주체를 Claude Code 메인 세션으로 정정, hooks 구조 설명에 확인 훅 반영, 수행 주체 절 참조 추가
- 2026-10-27 안티그래비티 가드(`scripts/agy-guard.js`, `.agents/hooks.json`): `read_file`/`write_file`/`edit_file` 도구와 `Path` 인자의 환경 파일 접근 차단, `-nm`·`-mn` 같은 `-n` 단축 플래그 묶음(커밋 명령 대상) 우회 차단. `scripts/test-agy-hook-cwd.js` 확장
- 2026-10-27 AGENTS.md 핸드오프 표 "리뷰·QA 통과" 행: planner(완료 전환) → docs 앞에 메인 세션의 사용자 확인 단계 추가
- 2026-10-27 AGENTS.md "고정 첫 작업"(T-01): 웹 UI 프로젝트면 dev 서버 실행 설정(Claude Code는 `.claude/launch.json`) 포함
- 2026-10-27 implementer·QA 역할 원본 화면 확인 단계: 사용자가 보는 브라우저 패널에서 확인하고 마지막 화면을 남김. `.claude/agents/implementer.md`·`quality-assurance.md`에 `.claude/launch.json` 이름으로 `preview_start` 안내 추가
- 2026-10-27 AGENTS.md "고정 첫 작업"(T-01): 웹 UI 프로젝트면 Architecture가 정한 E2E 러너 설정과 E2E 스모크 테스트 1개 포함
- 2026-10-27 implementer·QA 역할 원본 4단계와 보고 표에 E2E 회귀 확인 추가

### Removed
- 2026-10-27 `scripts/pipeline.ps1`, `scripts/orchestrator.ps1`, `.agents/role-map.yaml` 삭제(자동 오케스트레이션 폐기, Claude 중심 + CLI 위임 방식으로 전환). 위임 CLI 명령은 docs/CodingRules.md로 이전
