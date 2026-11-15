# 2026_line1thon (backend)

> 이 리포는 [start_coding](https://github.com/) 템플릿에서 생성되었다. 초기화 전이라면 아래 "새 프로젝트 시작"을 먼저 실행할 것.

## 새 프로젝트 시작 (템플릿 사용법)

1. GitHub에서 **Use this template** → 새 리포 생성 → clone
2. 초기화 스크립트 실행 (Windows):

```bash
powershell -ExecutionPolicy Bypass -File scripts/init.ps1 -ProjectName "프로젝트명"
```

   macOS/Linux:

```bash
bash scripts/init.sh "프로젝트명"
```

3. **Codex를 쓸 계획이면 먼저 `/hooks`로 훅 정의를 신뢰 승인한다** — 승인 전에는 main 직접 커밋·`.env` 접근 차단이 조용히 무동작한다. 안티그래비티 훅은 루트와 `.agents` cwd용 진입점을 사용한다. 실제 앱 연결은 `git status` 같은 읽기 명령으로 재확인한다. 실제 `.env` 파일을 열어 시험하지 않는다.
4. 아이디어를 **Claude Code 메인 세션**에 말한다 → 메인 세션이 **대화형 인터뷰**로 명세를 완성한 뒤 `docs/PRD.md`가 작성된다 (파이프라인 0~1단계). Codex·안티그래비티는 인터뷰를 시작하지 않는다 ([AGENTS.md "메인 오케스트레이터" 문단](AGENTS.md#개발-파이프라인) 참조)
5. Claude Code / Codex / 안티그래비티 어느 도구로 열어도 같은 규칙(AGENTS.md)이 적용된다. **메인 오케스트레이터는 Claude Code 세션**이고, Codex·안티그래비티는 같은 폴더에서 작업 하나를 맡는 실행자다 — Claude가 CLI로 위임하거나, 사용자가 같은 폴더를 해당 도구로 열어 직접 지시한다. 절차는 [AGENTS.md의 핸드오프 절](AGENTS.md#다른-도구-세션과의-핸드오프)과 `.claude/skills/cli-delegate/SKILL.md`.

| 도구 | 규칙 읽는 방식 | 강제 계층 활성 조건 |
|---|---|---|
| Claude Code (메인 오케스트레이터) | CLAUDE.md의 `@AGENTS.md` import, `.claude/agents/`는 `.agents/roles/` 원본을 가리키는 연결 파일 | 자동 |
| Codex (같은 폴더의 작업 실행자) | 루트 AGENTS.md 직접 읽음, `.codex/agents/`의 연결 파일이 `.agents/roles/` 원본을 가리킴 | **최초 1회 `/hooks` 신뢰 승인 필요 — 안 하면 무동작** |
| 안티그래비티 (같은 폴더의 작업 실행자) | 루트 AGENTS.md 직접 읽음, `.agents/roles/` 원본을 직접 읽음 | 루트·`.agents` cwd 진입점 제공 — 첫 사용 시 `git status` 같은 읽기 명령으로 도구 호출이 막히지 않는지 확인 |

## 프로젝트 개요

느린학습자(경계선 지능) 청소년이 위험하거나 어려운 상황을 AI와 안전하게 반복 연습하도록 돕는 반응형 웹 서비스의 **백엔드 저장소**다 (서비스명 미정, 근거: [docs/PRD.md](docs/PRD.md) 머리글·한 줄 정의). Python + FastAPI 백엔드이며 프론트·AI 서비스는 별도 저장소다([Architecture](docs/Architecture.md) 참조).

### 현재 상태 (2026-11-15, `dev` 7cbae24 기준)

아래는 모두 `dev`에 병합된 상태다. 기능 PR: #23(T-67)·#25(T-94)·#26(T-36)·#27(T-97)·#29(T-76)·#30(T-95·T-96)·#31(T-98)·#32(T-40)·#33(T-49)·#35(T-30, 병합 커밋 fce3b33)·#36(Neon 기존 DB용 호환 리비전·`/auth/me`·진단 문구, 병합 커밋 5008829), 문서 PR #28·#37(DECISIONS #137~#142·ADR-0022·0023, 병합 커밋 7cbae24). #35~#37은 githeobu가 2026-11-15 00:32~00:33Z에 병합했다. 병합 후 `dev` 7cbae24에서 메인 세션이 전체 테스트를 실행해 1028 passed·종료 코드 0이었다(`.artifacts/verification/ADHOC/dev-7cbae24-20261115T101547/`의 `stdout.txt` 끝줄 "1028 passed, 31 warnings in 584.91s"·`exit_code.txt` 0을 이번에 직접 열어 확인했고, 테스트는 다시 실행하지 않음). PR #38(T-100)은 열려 있고 `dev`에 병합되지 않았다. 그 밖의 통과 수는 각 작업의 QA·리뷰 보고(`docs/Tasks.md`)에서 가져온 인용값이다. 변경 이력은 [docs/CHANGELOG.md](docs/CHANGELOG.md)다.

**제공 API** (모두 `/api/v1` 아래, 라우터 `app/api/*.py` 기준)

| 영역 | 엔드포인트 | 세션 | 비고 |
|---|---|---|---|
| 헬스 | `GET /health` | 없음 | 해당 없음 |
| 인증·아이 관리 | `POST /guardians`, `POST /auth/guardian/login`, `POST /auth/child/login`, `GET /auth/me`(A6, 아래 표 아래 설명), `POST·GET /children`, `POST /children/{child_id}/pin-reset`, `POST /children/{child_id}/link-code` | 보호자 | 보호자 전용 API는 아이 세션에 401(T-25 A11만 403). `GET /auth/me`는 보호자·아이 세션 모두 허용 |
| 온보딩(A12) | `PUT /me/onboarding` | 아이 | 보호자 세션은 403 `FORBIDDEN_ROLE`, 세션이 없거나 무효·만료는 401 |
| 믿는 사람 연락 기록(A14) | `POST /me/trusted-contact-events` | 아이 | 보호자 세션은 403 `FORBIDDEN_ROLE`, 세션이 없으면 401 `UNAUTHENTICATED` |
| 홈·성장(A13·A19) | `GET /me/home`, `GET /me/growth` | 아이 | 보호자 세션은 403 `FORBIDDEN_ROLE` |
| 연습(A15~A18) | `POST /practice/sessions`, `GET /practice/sessions/{session_id}`, `POST /practice/sessions/{session_id}/turns`, `GET /practice/sessions/{session_id}/result` | 아이 | 보호자 세션은 403 `FORBIDDEN_ROLE` |
| 보호자 리포트(A11) | `GET /children/{child_id}/report` | 보호자 | 아이 세션은 403 `FORBIDDEN_ROLE` |

**연습 API (A15~A18)**
- A15 `POST /practice/sessions`는 세 모드(`area`·`retry`·`mission`)를 받는다. `mode:"area"`+`area`는 영역별 출제(영역 값 `scam`·`identity_lending`·`friend_pressure`)이고, `mode:"retry"`+`retry_of`는 끝난 세션의 다시 도전(영역은 원 세션 값)이며, `mode:"mission"`은 아래 오늘의 미션(T-49)이다. 영역별 출제는 T-30 병합(PR #35)으로 세 영역 모두 가능하다(아래 T-30 항목).
- **오늘의 미션 `mode:"mission"` (T-49) — PR #33, dev에 병합됨(병합 커밋 377b573)** — 구현 커밋 0715f41. `{"mode":"mission"}`이 영역 없이 기존 출제 규칙으로 새로 출제하고(`area`·`retry_of`를 함께 보내면 422, `draw_index`는 area 모드와 순번 공유), 누를 때마다 새로 출제한다(하루 1개 고정·영역 선택·완료 표시는 PRD OQ 13 미결). 당시에는 사기 영역(고1 이상)뿐이라 중학생 이하는 409였으나 T-30 병합(PR #35)으로 해소됐다(아래 T-30 항목). QA 989 passed(`.artifacts/verification/T-49/qa-20261115-1/`, 인용 — 이번에 다시 실행하지 않음). 병합 후 `dev` 전체는 1003 passed(위 "현재 상태" 인용).
- **영역 출제 활성화 (T-30) — PR #35, dev에 병합됨(병합 커밋 fce3b33, githeobu, 2026-11-15)**(https://github.com/line1thon-15/backend/pull/35; 브랜치 `feat/T-30-areas`, 구현 커밋 1527c00) — AI 콘텐츠 사본이 ai dev 8d900d1(12개 시나리오: `scam`·`identity_lending`·`friend_pressure` 각 4)로 바뀌어 area 모드에서 두 영역이 출제되고 mission 후보에 세 영역이 포함되며, 중학생 이하도 사기 영역 시나리오를 받아 위 T-49의 409 한계와 "고등학생만 출제" 서술은 해소됐다. 앱 코드 변경 없음(콘텐츠·보충 파일·테스트). QA 1022 passed·종료 코드 0(`.artifacts/verification/T-30/qa-20261115-1/`, 인용 — 이번에 다시 실행하지 않음). 병합 후 `dev` 전체는 1028 passed(위 "현재 상태"). 학년 값·사기 subtype은 잠정값(PRD OQ 3), AI 계약 샘플은 331d2c6 고정 유지, `opening_choices`는 백엔드가 무시한다(PR #38 병합 시 해소).
- **AI 시작 선택지 전달 (T-100) — PR #38, dev 미병합**(https://github.com/line1thon-15/backend/pull/38, base dev, 열림; 브랜치 `feat/T-100-opening-choices`, 커밋 006066b·437b880·760cf73) — 위 서술은 모두 `dev` 기준이며 PR #38은 아직 반영되지 않았다. 병합되면 AI 변형의 `opening_choices`(선택, 각 1~60자)가 버려지지 않고 start·turn·judge·feedback 요청에 전달된다(없으면 null, 위반 시 503). AI 계약 샘플은 ai dev 8d900d1로 재고정된다. 기능이 동작하려면 AI가 ai 8d900d1 이후여야 한다(옛 AI도 null 키는 거부하지 않음). 리뷰 치명 0·권고 2, QA 1053 passed·종료 코드 0(`.artifacts/verification/T-100/qa-20261115-1/`, 인용 — 이번에 다시 실행하지 않음). 설계 근거 DECISIONS #137~#139·ADR-0022(이 브랜치).
- A17 요청은 `{choice_id, turn_index}`이고 둘 다 필수다. 현재 턴이 아닌 `turn_index`는 409 `TURN_ALREADY_ANSWERED`, 동시 충돌은 `TURN_ALREADY_ANSWERED`·`SESSION_ENDED`·`SESSION_STOPPED`, `turn_index` 누락·음수·비정수는 422 `VALIDATION_ERROR`다(T-91).
- A18 결과는 찾은/놓친 단서 카드와 `can_retry`를 준다. 카드 색은 K1 green / K2 yellow / K3 green / K4 green / K5 yellow다(DECISIONS #120). 정상 상황 출제가 1차에서 꺼져 있어 정상 상황 결과 조회는 범위 밖이다.
- 출제는 약점 단서(놓침 2회 이상 + 최근 놓침, 최대 3개)를 가진 시나리오를 우선하고(T-36), 세션 `hint_level`은 저장만 한다 — 화면의 `hint`는 항상 null이다. `HINT_MAX=2`는 잠정값(PRD OQ 14)이다.
- 다시 도전에서 AI 변형 응답이 대체 응답(fallback)이고 직전과 같은 조합이면 다른 조합으로 1회 다시 요청하고, 재요청도 fallback이면 같은 모습으로 진행한다(T-95, ADR-0019). AI 오류는 503이다. 연습 시작의 종료 기록 조회는 1회다(T-96).
- DB: 마이그레이션 `20261112_04`(`practice_sessions`·`practice_turns`·`cue_results`)와 `20261112_05`(`guardian_notices`). PR #36(githeobu)이 `20261111_05`(동작 없는 호환 리비전, `alembic/versions/20261111_05_legacy_compat.py`)를 추가했다 — 옛 분할 마이그레이션 체인에서 `20261111_05`가 이미 기록된 기존 Neon DB를 위한 것이고 `20261112_04`의 `down_revision`이 이것을 가리킨다. PostgreSQL에서의 마이그레이션 검증은 이 저장소의 확인 범위 밖이다(미검증).
- **`GET /auth/me`(A6, PR #36)** — 세션 쿠키 `sid`로 현재 사용자를 돌려준다(`app/api/auth.py`, `origin/dev` 기준 확인). 보호자는 `{role:"guardian", guardian_id, email}`, 아이는 `{role:"child", nickname, grade, onboarding_completed, display:{font_scale, high_contrast, tts_enabled}}`이고, 세션이 없거나 무효이면 401 `UNAUTHENTICATED`다. 역할 제한은 없다(두 역할 모두 허용). 같은 PR에서 진단 3문항 문구가 `app/content/data/diagnosis.json`에서 "모르는 사람이 말을 걸면 대답해요"·"친구 부탁은 거절하기 어려워요"·"돈이나 물건 이야기는 헷갈려요"(선택지 "그래요"·"가끔"·"아니에요")로 바뀌었다.

**보호자 리포트 A11과 요약 (T-25·T-76·T-98)**
- 영역별 진행·약점 단서·`metrics`·알림 목록을 준다(원문 비공개). 성장 지표·배지·연속 기록은 T-45·T-46 계산 계층을 쓴다.
- `summary`는 조회 시마다 AI 요약을 호출해 채운다(저장·캐시 없음). 이번 기간에 종료 세션이 있는 영역마다 `/internal/v1/summary`를 병렬로 호출한다. 종료 세션 기록이 없으면 `insufficient`(AI 미호출), 전체 상한 `SUMMARY_DEADLINE_SECONDS`=25초 초과나 AI·검증(S1~S3) 실패가 하나라도 있으면 `unavailable`(리포트는 200, 부분 결과 없음), 그 외 `ok`다(ADR-0020). 상한을 넘어도 이미 보낸 AI 호출은 AI 클라이언트 시간 초과까지 백그라운드에서 끝난다. 기록 부족 기준(종료 세션 1개)은 Architecture A-18 가정값이다(PRD OQ 58 미결).

**믿는 사람 연락 기록 A14 (T-40) — PR #32, dev에 병합됨(병합 커밋 909e758)** — 구현 커밋 774a9ab. 아이 세션의 `POST /me/trusted-contact-events`(`{channel:"call"|"sms"}` → `{ok:true}`)가 `guardian_notices`에 `trusted_contact` 알림을 남기고 A11 `notices`에 보인다. 연락처 이름·번호·원문은 저장·노출하지 않고, 외부 전달은 PRD OQ 9 보류다. QA 989 passed(`.artifacts/verification/T-40/qa-20261115-1/`, 인용 — 이번 정리에서 다시 실행하지 않음). 한계: A14 호출 횟수 제한 없음(연타 시 알림 증가, 사용자 판단 대기), PostgreSQL `guardian_notices` CHECK 제약 동작 미검증(SQLite에서만 실행). 상세는 [docs/CHANGELOG.md](docs/CHANGELOG.md).

**AI 연결** — `AI_CLIENT=http`이면 `HttpPracticeAI`가 AI 서버를 호출한다(T-94). 방법·확인 범위·한계는 아래 "실제 AI 서버 연결".

**콘텐츠** — T-87: `create_app()`이 시작 시 콘텐츠를 검증하며 잘못되면 서버가 뜨지 않는다. 사본은 `app/content/data/ai/`(출처·고정 커밋·해시: `SOURCE.txt`), 보충 파일 `scenario_meta.json`·`platform_app_types.json`·`diagnosis.json`·`safety_stop.json`은 `app/content/data/`에 있다. 보충 파일은 **예시 데이터**이고 `safety_stop.json` 문구는 OQ 66 답을 받은 뒤 교체한다.

**시연 데이터** — T-67·T-97: `python -m app.demo.seed`로 시연 계정에 예시 기록을 넣는다. 아래 "시연 예시 데이터 적재".

**테스트·CI** — T-01 하네스: pytest 러너, `FakePracticeAI`·`FakeSummaryAI`(AI 계약 v1 포트 `PracticeAI`·`SummaryAI`), import 경계 테스트. CI(`.github/workflows/ci.yml`, 워크플로 `backend-ci`)는 `dev`·`main` 대상 PR에서 pytest를 Fake AI로 돌린다. GitHub Actions 실행은 2026-11-14에 `gh run list --repo line1thon-15/backend --limit 5`로 최근 5건 success를 확인했다(이후 실행은 미확인).

- **AI 콘텐츠 사본 갱신 절차(T-87 완료 조건 ⑤, DECISIONS #107)** — AI 콘텐츠가 바뀌는 PR 때 백엔드 담당이 같이 갱신한다. 사본은 직접 수정하지 않고 통째로 다시 복사한다.
  1. 복사 대상(원본 저장소 `line1thon-15/ai`, 브랜치 `feature/ai`): `content/clues.json` → `app/content/data/ai/clues.json`, `content/scenarios/*.json` → `app/content/data/ai/scenarios/`. `content/safety_cases.json`·`safety_messages.json`은 복사 대상이 아니다.
  2. 새 원본 커밋으로 고정 커밋을 갱신하고 `app/content/data/ai/SOURCE.txt`의 고정 커밋·복사일을 고친다.
  3. `SOURCE.txt`의 SHA-256을 새 값으로 갱신한다(LF 기준 = git blob 내용, `git show <커밋>:<원본 경로> | sha256sum`).
  4. 검증: `.venv/Scripts/python.exe -m pytest` — `tests/unit/test_content_loader.py`의 사본 무결성 테스트(`test_ai_copy_matches_pinned_source_hashes`)가 CRLF→LF 정규화 후 SOURCE.txt 해시와 대조하고, 로더 검증 테스트가 새 콘텐츠의 구조를 확인한다.

## 구조

```
2026_line1thon/
├── app/               # 백엔드 소스 (api·services·repositories·db·core·ai_client)
├── tests/             # pytest (unit·integration)
│   └── contracts/ai/  # AI 계약 샘플 12개 사본 (ai 저장소 feature/ai 331d2c6 고정, 직접 수정 금지, 출처 SOURCE.txt)
├── requirements.txt·requirements-dev.txt·pyproject.toml
├── .env.example       # 환경 변수 플레이스홀더 (실제 값은 .env에만)
├── .github/workflows/ci.yml # 백엔드 CI (dev·main 대상 PR에서 pytest)
├── AGENTS.md          # 마스터 규칙 (단일 원본)
├── CLAUDE.md          # Claude Code 어댑터
├── docs/              # 프로젝트 문서 + ToolPacks.md(스킬·MCP 팩) + KitFeedback.md(템플릿 개선 대기열)
├── scripts/           # 초기화 스크립트 init.ps1·init.sh(1회 실행) + agy-guard.js(안티그래비티 가드, 상주)
├── .agents/roles/     # 역할 단일 원본 (*.role.md — 3개 도구 공용)
├── .agents/skills/    # 공용 스킬 원본 (안티그래비티·Codex 직접 사용)
├── .agents/scripts/   # .agents cwd에서 기존 안티그래비티 가드를 호출하는 진입점
├── .claude/agents/    # 6-에이전트 연결 파일 (도구 권한·모델만 정의, 본문은 .agents/roles/)
├── .claude/skills/    # Claude Code의 공용 스킬 연결 파일 + 전용 스킬 cli-delegate(Codex·안티그래비티 위임)
├── .claude/hooks/     # 강제 가드 3종 + 안티그래비티 위임 확인 훅(confirm-agy-delegate.js, Claude Code 전용) + 정합성 검사 (가드는 Claude Code·Codex 공유)
├── .codex/agents/     # 6-에이전트 연결 파일 (Codex 전용, 본문은 .agents/roles/)
├── .codex/EXECUTION.md # Codex 실행 출력·세션 수집 안내
├── .codex/DEVELOPMENT.md·FRONTEND.md # Codex 개발 보조·UI 구현 지침
├── .codex/tests/      # Codex 연결 파일·훅 배선 검사
├── .codex/hooks.json  # Codex 배선 (최초 1회 /hooks 신뢰 승인 필요)
├── .agents/hooks.json # 안티그래비티 배선 → cwd별 scripts/agy-guard.js 진입점
└── .artifacts/        # 로컬 증거 (Git 제외): verification/ 검증 로그, handoff/ 다른 도구 세션과의 prompt.md·report.md
```

## 개발 파이프라인

아이디어 인터뷰 → 기획 → 설계 → 구현 → 리뷰/검증 → 문서화. 단계별 산출물과 게이트는 [AGENTS.md](AGENTS.md) 참조. 각 단계를 메인 세션과 서브에이전트 중 누가 수행하는지는 [AGENTS.md의 "메인 세션과 서브에이전트 구분" 절](AGENTS.md#메인-세션과-서브에이전트-구분)을 따른다. 별도 세션이 필요한 작업은 앱 서브 세션(생성·보고·검증·제공·정리, 정리는 보관이 기본)으로 맡기며 규칙은 같은 절의 "앱 서브 세션" 하위 절에 있다.

인터뷰는 아이디어를 받아 적는 단계가 아니라 **같이 설계하는 대화**다: 개인/팀·언어·배포·기능 범위 등 빈칸을 질문으로 채우고, 선택지마다 추천 방향과 반대 방향을 함께 제시하며, 사용자가 "완성"을 선언할 때까지 계속된다. 절차는 [.agents/skills/idea-interview/SKILL.md](.agents/skills/idea-interview/SKILL.md).

기술 스택을 정하기 전에 런타임·버전, 설치 허용 범위, 테스트 실행 수단, 실제 화면 확인 도구를 읽기 전용으로 확인한다. 확인한 환경 제약은 [Architecture의 사전 확인 표](docs/Architecture.md#실행환경-사전-확인-기술-선택-전)에 기록한다. 기획에서는 승인 기준과 화면 상태를 담당 작업에 배정해 후속 기능 때문에 선행 작업의 완료가 막히지 않도록 한다.

구현·검증에서는 Red·Green·회귀 실행의 전체 출력과 종료 코드를 작업별 `.artifacts/verification/`에 보존한다. 이 경로는 Git 추적에서 제외된다. 실제 화면 확인은 현재 도구의 가용성과 실패 결과에 따라 담당·미검증 범위를 기록한다. 화면 확인은 사용자가 보는 Browser pane에서 하고 마지막 화면을 남기며, 리뷰·QA 통과 뒤 메인 세션이 사용자 확인을 받아야 완료로 전환한다(웹 UI 프로젝트의 T-01에는 `.claude/launch.json` dev 서버 설정 포함, [AGENTS.md "사용자 화면 확인"](AGENTS.md#검증-루프-테스트-우선)). 웹 UI의 PRD 핵심 사용자 흐름은 E2E 회귀 테스트를 Red-First로 두며(T-01에 E2E 러너 설정과 스모크 1개 포함) 실물 확인과 서로 대신하지 않는다([AGENTS.md "화면 흐름 회귀"](AGENTS.md#검증-루프-테스트-우선)). 공통 판정은 [AGENTS.md](AGENTS.md#검증-증거-보존)와 [DefinitionOfDone.md](docs/DefinitionOfDone.md)를 따르고, Codex의 세션 출력 수집 방법은 [.codex/EXECUTION.md](.codex/EXECUTION.md)를 참조한다. 자동 로그 수집 프로그램은 제공하지 않는다. 이전의 `scripts/pipeline.ps1`·`scripts/orchestrator.ps1`·`.agents/role-map.yaml` 자동 오케스트레이션은 제거되었다.

## 이 킷 자체의 문제를 발견하면

규칙 때문에 막히거나 우회했다면 **여기서 규칙을 고치지 말고** [docs/KitFeedback.md](docs/KitFeedback.md)에 행을 추가한다. 나중에 템플릿 리포에서 그 표를 읽고 원본을 고치면 다음 프로젝트부터 반영된다.

## 실행/빌드/테스트

원문은 [docs/CodingRules.md "검증된 명령어"](docs/CodingRules.md#검증된-명령어)다. 아래 명령은 Git Bash에서 저장소 루트 기준이며 시스템 Python 3.13으로 검증됐다. 환경 변수는 [.env.example](.env.example)을 참조한다.

```bash
# 가상환경 생성
python -m venv .venv
# 의존성 설치
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
# 테스트 (live_ai 마커 기본 제외)
.venv/Scripts/python.exe -m pytest
# dev 서버 (포트 8080)
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8080
# 헬스 확인 (dev 서버 기동 중)
curl -sS -i http://localhost:8080/api/v1/health
```

## 실제 AI 서버 연결

기본값은 `AI_CLIENT=fake`(Fake AI)다. 실제 AI 서버를 쓰려면 환경 변수를 아래처럼 설정한다(실제 `.env` 파일은 커밋하지 않는다). 값은 [.env.example](.env.example)의 플레이스홀더를 참고하고, 토큰은 AI 서버의 내부 토큰과 같은 값을 쓴다.

```bash
AI_CLIENT=http
AI_SERVICE_URL=http://localhost:8081        # AI 서버 기준 URL (기본값)
AI_SERVICE_TOKEN=<your-internal-token>      # 필수 — http인데 없으면 서버 시작 실패
AI_SERVICE_TIMEOUT_SECONDS=30               # 기본 30, 0보다 큰 유한한 수
```

- 호출 실패(시간 초과·연결 실패·비2xx·응답 형식 불일치)는 `AIUnavailableError`로 처리된다.
- 확인된 것(실제 AI 서버 = ai 저장소 dev e82ea66를 로컬에서 실행):
  - `AI_PROVIDER=fake`: 연습 흐름(시작 201 → 답 4회 200 → 결과 200)과 잘못된 토큰 503(2026-11-14, `.artifacts/verification/T-94/main-20261114-live-ai-2/`·`main-20261114-live-ai-wrong-token/`), 다시 도전 201(2026-11-15, `T-95/main-20261115-live-ai-retry/`).
  - 실제 Gemini(`GEMINI_MODEL=gemini-3.8-flash`, 2026-11-15, 메인 세션 로컬 실행, 종료 코드 모두 0): 연습 흐름과 다시 도전(`T-95/main-20261115-live-gemini-3/` — Gemini 호출 7회 모두 200, 다시 도전 201)과 보호자 요약(`T-98/main-20261115-live-gemini/` — 리포트 200, `summary.status=ok`, 18.6초·12.4초; 수정 전 영역 1개 16.6초는 `T-76/main-20261115-live-gemini-summary-2` 인용).
- 한계:
  - 위 확인은 모두 로컬 AI 서버 기준이다. 배포 환경의 AI 서버는 아직 배포되지 않았다(배포 방식은 ADR-0021 제안 상태, 미승인).
  - `gemini-2.5-flash`는 새 키에서 404("no longer available to new users")여서 쓸 수 없었다(`T-95/main-20261115-live-gemini-3/meta.md`). `gemini-3.8-flash`는 사용자가 AI 쪽 설정에서 바꾼 모델이다.
  - 실제 Gemini 확인은 시나리오 `scam` 흐름뿐이다. 다른 영역·모델에서의 품질·지연은 미검증이다.
  - 요약 호출은 오래 걸린다(측정 12~19초). 25초 상한을 넘으면 `unavailable`이다.
  - AI 쪽 정상 상황 응답 형태가 백엔드 포트와 달라 1차에서는 정상 상황 출제가 꺼져 있다.
  - 프론트 `FirstSetup.jsx`의 진단 문구는 아직 옛 문구다(메인 세션 확인, 프론트 dev fedf631 기준, 인용 — 이번에 직접 확인하지 않음). 백엔드 진단 문구(PR #36)와 어긋난다.

## 시연 예시 데이터 적재 (T-67)

시연 계정에 예시 성장 기록(8세션)과 예시 안전 알림(2건)을 넣는다(`origin=demo_seed`, DECISIONS #132 — 고정 시연 계정이 기본). 명령 원문은 [docs/CodingRules.md "검증된 명령어"](docs/CodingRules.md#검증된-명령어)의 T-67 행이다. Git Bash, 저장소 루트 기준이며 `$URL`은 대상 DB URL(Windows SQLite는 `sqlite:///C:/...` 형식)이다.

```bash
# 1) 마이그레이션 (대상 DB)
DATABASE_URL="$URL" .venv/Scripts/alembic.exe upgrade head
# 2) 시연 계정 비밀번호(8~128자)·아이 PIN(숫자 4자리)을 환경 변수로 설정 — 값은 직접 정해 넣는다
export DEMO_GUARDIAN_PASSWORD=<비밀번호>
export DEMO_CHILD_PIN=<PIN>
# 3) 고정 시연 계정에 적재 (재실행 안전)
.venv/Scripts/python.exe -m app.demo.seed fixed --database-url "$URL"
# (선택) 이미 있는 아이에 덧붙이기 — 환경 변수 불필요
.venv/Scripts/python.exe -m app.demo.seed attach --child-id <child UUID> --database-url "$URL"
```

- 시연 당일 다시 실행하는 것을 권장한다 — 날짜가 실행 시점 기준 상대값이라 7일 창이 시연일에 맞춰진다. 다시 실행해도 그 아이의 `demo_seed` 행만 새로 바뀌고 중복이 생기지 않는다(`live` 행 유지). 예시 세션은 항상 계획 수(8개)로 모두 새로 만들어지며, 실제(`live`) 다시 도전이 가리키던 예시 세션은 같은 순번·시나리오·목표 단서의 새 예시 세션으로 연결이 옮겨진다. 대응하는 새 예시 세션이 없으면 연결은 비워지며(다른 시나리오로 잇지 않음) 다시 도전 세션 자체는 유지된다.
- 시연 계정이 이미 있으면 비밀번호·PIN을 갱신하지 않는다(환경 변수 값은 새 계정을 만들 때만 쓰인다).
- 값을 명령줄 앞에 직접 쓰면(`DEMO_GUARDIAN_PASSWORD=... 명령`) 셸 히스토리에 남으니 위처럼 `export`를 권장한다. 환경 변수가 없거나 형식이 틀리면 종료 코드 2로 끝난다. 실제 값은 저장소·문서에 적지 않는다([.env.example](.env.example)은 플레이스홀더만).
- 제한: 시연 계정에서 "처음 본 상황에서 찾은 신호"는 콘텐츠 시나리오가 2개라 "비교 불가"로 보이고, 시연 아이는 첫 설정이 미완료 상태다(사용자 결정). 자세한 내용은 [docs/CHANGELOG.md](docs/CHANGELOG.md) 참조.
