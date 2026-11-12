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

### 현재 상태 (2026-11-11)

- T-01(백엔드 테스트 하네스)이 구현돼 있다: pytest 러너, 헬스 엔드포인트(`/api/v1/health`), `FakePracticeAI`·`FakeSummaryAI`(AI 계약 v1 포트 `PracticeAI`·`SummaryAI` 기준, T-86 재정의), import 경계 테스트, CI 워크플로. **기능 API 중 연습 세션·결과 API(T-15·T-16, 아래)만 있다.**
- T-15(연습 세션 API)가 구현돼 있다(리뷰 치명 0, QA 408 passed — `docs/Tasks.md` T-15 행 인용): `POST /api/v1/practice/sessions`(A15, 영역별 출제), `GET /api/v1/practice/sessions/{session_id}`(A16), `POST /api/v1/practice/sessions/{session_id}/turns`(A17, 답 제출·종료 판정). DB 마이그레이션 `20261112_04`(`practice_sessions`·`practice_turns`·`cue_results`). 제한: A15는 `mode:"area"`만 받고, 지금 콘텐츠로는 고등학생만 출제되며, 공개 영역 값은 `scam`·`identity_lending`·`friend_pressure`다. 자세한 내용과 미검증 항목은 [docs/CHANGELOG.md](docs/CHANGELOG.md) 참조.
- T-16(연습 결과 API·다시 도전)이 구현돼 있다(리뷰 치명 0, QA 480 passed — `docs/Tasks.md` T-16 행 인용): `GET /api/v1/practice/sessions/{session_id}/result`(A18, 찾은/놓친 단서 카드와 `can_retry`), `POST /api/v1/practice/sessions`에 `mode:"retry"`+`retry_of`(A15 다시 도전). 카드 색 값은 T-89에서 확정돼(K1 green / K2 yellow / K3 green / K4 green / K5 yellow, DECISIONS #120) A18이 기본 설정에서 동작한다(485 passed, 인용). 제한: 정상 상황 결과 조회는 1차 범위 밖이다. 자세한 내용은 [docs/CHANGELOG.md](docs/CHANGELOG.md) 참조.
- T-90(아이용 성장·홈 API)이 구현돼 있다(656 passed — 인용): `GET /api/v1/me/growth`(A19), `GET /api/v1/me/home`(A13), 보호자 세션은 403. 보호자 리포트 A11 `metrics`도 채워진다. 제한: 기존 아이 API는 보호자 세션에 401(신규 A13·A19만 403), A19 오류 코드 규격이 Architecture에 없다. 자세한 내용은 [docs/CHANGELOG.md](docs/CHANGELOG.md) 참조.
- T-45(배지·연속 기록)·T-46(성장 지표 3개·더 연습이 필요한 단서) 계산 계층이 구현돼 있고(공개 API 없음), T-25 보호자 리포트 `GET /api/v1/children/{child_id}/report`(A11)와 `guardian_notices` 테이블(마이그레이션 `20261112_05`)이 있다(통합 638 passed — 인용). 제한: A11 `summary`는 임시값(T-76), PostgreSQL 마이그레이션 미검증. 자세한 내용은 [docs/CHANGELOG.md](docs/CHANGELOG.md) 참조.
- T-87(AI 콘텐츠 읽기 전용 사본 + 보충 파일 + 서버 시작 시 검증)이 구현돼 있다(리뷰 치명 0, QA 6/6, 142 passed). `create_app()`이 시작 시 콘텐츠를 검증하며, 잘못되면 서버가 뜨지 않는다. 사본은 `app/content/data/ai/`(출처·고정 커밋·해시: `SOURCE.txt`), 보충 파일 `scenario_meta.json`·`platform_app_types.json`·`diagnosis.json`·`safety_stop.json`은 `app/content/data/`에 있다. 보충 파일은 **예시 데이터**이고 `safety_stop.json` 문구는 OQ 66 답을 받은 뒤 교체한다.
- **AI 콘텐츠 사본 갱신 절차(T-87 완료 조건 ⑤, DECISIONS #107)** — AI 콘텐츠가 바뀌는 PR 때 백엔드 담당이 같이 갱신한다. 사본은 직접 수정하지 않고 통째로 다시 복사한다.
  1. 복사 대상(원본 저장소 `line1thon-15/ai`, 브랜치 `feature/ai`): `content/clues.json` → `app/content/data/ai/clues.json`, `content/scenarios/*.json` → `app/content/data/ai/scenarios/`. `content/safety_cases.json`·`safety_messages.json`은 복사 대상이 아니다.
  2. 새 원본 커밋으로 고정 커밋을 갱신하고 `app/content/data/ai/SOURCE.txt`의 고정 커밋·복사일을 고친다.
  3. `SOURCE.txt`의 SHA-256을 새 값으로 갱신한다(LF 기준 = git blob 내용, `git show <커밋>:<원본 경로> | sha256sum`).
  4. 검증: `.venv/Scripts/python.exe -m pytest` — `tests/unit/test_content_loader.py`의 사본 무결성 테스트(`test_ai_copy_matches_pinned_source_hashes`)가 CRLF→LF 정규화 후 SOURCE.txt 해시와 대조하고, 로더 검증 테스트가 새 콘텐츠의 구조를 확인한다.
- CI(`.github/workflows/ci.yml`)는 `dev`·`main` 대상 PR에서 pytest를 Fake AI로 돌리도록 작성돼 있다. **GitHub에서 실제로 실행되는지는 아직 확인하지 못했다**(원격 저장소 미연결, 미검증).
- T-01은 docs/Tasks.md 기준 "완료"다(리뷰·QA 통과, 치명 결함 0건). CI의 GitHub 실제 실행은 원격 저장소 연결 뒤 확인한다.

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
