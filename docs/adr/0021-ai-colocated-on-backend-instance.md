# ADR-0021: AI 서버를 백엔드 Render 웹 서비스 인스턴스 안에서 함께 실행 (같은 인스턴스, 별도 프로세스)

> 상태: 제안 (2026-11-15 — 방향은 사용자 답 "그렇게 진행", 세부 규격은 사용자 확인 대상). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-15
> 관련: DECISIONS #135·#136. **부분 대체**: ADR-0007(제안)의 "AI: 같은 PaaS의 두 번째 웹 서비스(추천)"와 그에 딸린 배포 단위 3개 서술만 대체한다 — 프론트 Vercel·백엔드 Render 웹 서비스·관리형 Postgres는 그대로다. ADR-0011(제안)의 결정 A(ai 저장소 = 상태 없는 별도 HTTP 서비스, 백엔드는 `PracticeAI` 포트 + `HttpPracticeAI`)는 **그대로** — 바뀌는 것은 AI 프로세스가 어디서 도는가(배포 위치)뿐이고, 내부 API 계약·토큰·시간 초과·`AIUnavailableError` 처리는 변경 없음. ADR-0007·ADR-0011 본문은 수정하지 않았다.

## 맥락

- AI 담당 원문(사용자 전달, 인용): "render 가 오류가 잘나고 제가 또 배포하면 배포 위에 배포가 씌워져서" / "깃허브에 있는 코드 그대로 백엔드 서버에서 python -m app으로 띄우시고 http://localhost:8081로 호출 하면 될 것 같아요" / "이번엔 docs같은 파일 안써서 fastapi로는 안바꾸고"
- 사용자 답 원문: "그렇게 진행"(2026-11-15) — 메인 세션 제안(진행 순서: 답장 → ADR·시작 스크립트 → Render 설정 → 배포 확인)에 대한 답(메인 세션 전달).
- 메인 세션 확인 사실(전부 인용 — architect는 이번 세션에 원격 저장소·Render를 직접 확인하지 않았다):
  - AI 저장소 `line1thon-15/ai`는 PUBLIC. 기본 브랜치 `main`에는 "chore: 저장소 시작" 커밋뿐이고 코드는 `dev`(e82ea66).
  - AI 의존성 `requirements.txt` = `pydantic>=2`, `pytest>=8`, `google-genai>=1.0`.
  - AI 실행: `python -m app`. 환경 변수 `AI_INTERNAL_TOKEN`(필수), `AI_PROVIDER`(`fake`|`gemini`), `AI_PORT`(기본 8081), `AI_HOST`(기본 127.0.0.1), `GEMINI_API_KEY`, `GEMINI_MODEL`. 새 키는 `gemini-2.5-flash`가 404 "no longer available to new users" → `gemini-3.8-flash`로 동작 확인. AI 서버는 `.env`를 자체 로드하지만 환경 변수가 우선.
  - 로컬에서 이 구성(백엔드 → localhost:8081, 실제 Gemini)으로 연습·다시 도전·보호자 요약 동작 확인 — `.artifacts/verification/T-95/main-20261115-live-gemini-3/`, `.artifacts/verification/T-76/main-20261115-live-gemini-summary-2/`.
  - 백엔드 저장소에 `render.yaml`·`Procfile` 없음(Render 대시보드 설정으로 추정). 백엔드 배포 URL health 200.
- architect 직접 확인(이번 세션, 작업 트리 — 최신 dev와 다를 수 있음):
  - `app/core/config.py:32` — `AI_SERVICE_URL` 기본 `http://localhost:8081`, `:33` `AI_SERVICE_TOKEN` 필수(`min_length=1`), `:35` `AI_SERVICE_TIMEOUT_SECONDS` 기본 30.0.
  - `requirements.txt` — 백엔드는 `httpx==0.28.1`·`fastapi==0.162.2` 등 직접 의존성만 고정(전이 의존성 `pydantic` 등은 고정 안 함).
  - `pyproject.toml:2` — pytest `testpaths = ["tests"]`.
  - `.gitignore` — `.venv/`·`.env` 등은 제외 중, AI 코드를 받을 디렉터리는 제외 목록에 없음.
  - **패키지 이름 충돌**: 백엔드 패키지가 `app`이고 AI도 `python -m app`(패키지 `app`)이다 — 같은 프로세스에서 둘을 함께 import할 수 없다(대안 C 판단 근거).

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. 별도 Render 웹 서비스 (기존 — ADR-0007 갱신 메모) | 장애 격리(AI가 죽어도 백엔드 무관), AI 담당이 독립 배포, 메모리·로그 분리 | AI 담당이 운영을 맡지 않겠다고 함(원문 "render 가 오류가 잘나고 … 배포 위에 배포가 씌워져서"). 서비스 2개의 유휴 절전·비용(D-3), 공개 URL에 내부 API 노출(토큰만으로 방어) |
| **B. 같은 인스턴스에서 별도 프로세스로 동시 실행 (선택)** — 빌드 때 AI 코드를 받아 두고, 시작 스크립트가 AI를 감시 루프로 백그라운드 실행한 뒤 기존 시작 명령(`alembic upgrade head` → `uvicorn`) | AI 담당 제안과 같음. AI 코드 변경 없음(`python -m app` 그대로, FastAPI 전환 불필요 — 원문 "fastapi로는 안바꾸고"). 내부 API·`HttpPracticeAI` 무변경(URL만 루프백). AI 포트가 외부에 열리지 않음(127.0.0.1 바인딩). Render 서비스 1개 — 절전·비용·대시보드 1곳. AI와 백엔드가 한 배포로 함께 바뀌어 "AI 먼저 → 백엔드" 순서 문제 없음 | 장애 격리 상실(인스턴스 재시작·메모리 초과가 둘 다에 영향), AI 프로세스 감시를 우리가 해야 함, AI 갱신 = 백엔드 재배포, 메모리 합산, 로그가 한 스트림에 섞임, AI 코드 버전(브랜치·커밋)을 백엔드 쪽에서 고정해야 함 |
| C. AI 코드를 백엔드 프로세스에 직접 import (지난 해커톤 방식에 가까움, ADR-0001·ADR-0011 대안 B 계열) | 프로세스 1개, 네트워크 홉 없음 | 두 저장소 모두 최상위 패키지가 `app`이라 그대로는 import 불가 — AI 쪽 패키지 이름 변경 또는 백엔드 쪽 사본(vendoring)이 필요. 백엔드 포트에 HTTP 대신 함수 호출 어댑터를 새로 만들어야 함(ADR-0011·#47 경계 재작성), AI 의존성(google-genai)이 백엔드 의존성·CI에 섞임(N-10 "백엔드에 제공사 SDK 없음" 약화). AI 담당 원문 "깃허브에 있는 코드 그대로 … python -m app으로 띄우시고"와 다름 |
| D. AI만 다른 호스트(다른 PaaS)로 이전 | 장애 격리 유지 | 운영 주체 문제(누가 배포·감시하나)가 그대로, 새 계정·설정 필요. 사용자 답은 B 방향 |

## 결정

B. 결정적 이유: AI 담당이 별도 서비스를 운영하지 않기로 했고(원문 인용), AI 코드·내부 API·백엔드 코드를 하나도 바꾸지 않고 배포 위치만 옮길 수 있는 유일한 대안이다. C는 `app` 패키지 충돌 때문에 코드 변경 없이 불가능하다.

규격(구현 대상 — 새 T-xx, planner 배정):

1. **AI 코드 위치**: 백엔드 저장소 루트의 `.ai_runtime/`(빌드 산출물 — 커밋 금지). 점으로 시작하는 이름을 쓰는 이유: pytest 기본 `norecursedirs`가 점 디렉터리를 건너뛰고(`testpaths = ["tests"]`와 이중 방어), 백엔드 `app`과 같은 단계에 두 번째 `app` 패키지가 눈에 띄게 놓이는 것을 피한다. `.gitignore`에 `.ai_runtime/` 추가가 필요하다 — `.gitignore`는 사용자 소유라 **사용자 요청 사항**이다(그 전까지 implementer는 이 디렉터리를 커밋하지 않도록 `git status`로 확인).
2. **AI 코드 버전 고정**: 환경 변수 `AI_REPO_REF`(브랜치 이름 또는 **커밋 SHA 권고**)로 받는다. 기본값 없음 — 비어 있으면 빌드 실패(어느 코드가 배포되는지 모르는 상태를 만들지 않는다). 저장소 주소 `AI_REPO_URL` 기본 `https://github.com/line1thon-15/ai.git`(PUBLIC — 인용, 토큰 불필요). 빌드 로그에 받은 커밋 SHA를 한 줄 출력한다. 어느 브랜치·커밋을 쓸지는 Open Question(아래).
3. **AI 의존성 격리**: AI 의존성은 `.ai_runtime/.venv`(별도 가상환경)에 설치한다 — 백엔드 가상환경에 섞지 않는다. 이유: 백엔드는 직접 의존성만 고정하므로 `google-genai` 설치가 전이 의존성(`pydantic`·`anyio` 등)을 CI와 다른 버전으로 바꿀 수 있다(추정 — 확인 방법: 같은 가상환경에 설치 후 `pip freeze` 비교). 별도 가상환경이 Render 빌드에서 만들어지지 않으면(미확인) 같은 가상환경 설치 + `pip check`로 바꾸는 것은 사용자 확인 후(조용한 우회 금지).
4. **빌드 스크립트** `deploy/render-build.sh`(bash, 소스 코드 — implementer): ① `pip install -r requirements.txt`(기존 빌드 명령 그대로) ② `AI_REPO_REF` 비었으면 오류 종료 ③ `.ai_runtime/` 삭제 후 `git init` → `git fetch --depth 1 origin "$AI_REPO_REF"` → `git checkout FETCH_HEAD`(브랜치·SHA 모두 처리) ④ 받은 SHA 출력 ⑤ `python -m venv .ai_runtime/.venv` → `.ai_runtime/.venv/bin/python -m pip install -r .ai_runtime/requirements.txt`. 하나라도 실패하면 빌드 실패(`set -euo pipefail`).
5. **시작 스크립트** `deploy/render-start.sh`(bash, 소스 코드 — implementer): ① `PORT`가 `AI_PORT`(기본 8081)와 같으면 오류 종료 ② `AI_INTERNAL_TOKEN`이 비어 있으면 `AI_SERVICE_TOKEN` 값을 쓴다(같은 값이어야 하므로 한 곳에서만 설정 — 값은 출력하지 않음) ③ **AI 감시 루프를 백그라운드로 시작**: `.ai_runtime/`을 작업 디렉터리로, `AI_HOST=127.0.0.1` 강제, `.ai_runtime/.venv/bin/python -m app` 실행, 출력에 `[ai] ` 접두어를 붙여 stdout으로, 프로세스가 끝나면 종료 코드를 한 줄 로그로 남기고 5초 뒤 재시작(무한 반복) ④ `alembic upgrade head` ⑤ `exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"` — ④⑤는 기존 시작 명령과 같은 동작(`&&` 대신 `set -e` + `exec`). AI 준비를 기다리지 않는다(AI가 늦게 뜨면 그동안의 연습 요청은 기존 규칙대로 503 `AI_UNAVAILABLE` — 아이가 다시 시도).
6. **백엔드 연결**: `AI_CLIENT=http`, `AI_SERVICE_URL=http://127.0.0.1:8081`. AI 담당 원문은 `localhost`지만 AI가 `127.0.0.1`에만 바인딩하므로 `localhost`의 IPv6(`::1`) 해석 시도를 피하려고 숫자 주소를 쓴다(동작은 같음 — 로컬 확인은 `localhost`로 됨, 인용). 토큰 헤더·시간 초과는 그대로.
7. **헬스체크**: Render 헬스체크는 백엔드 `GET /api/v1/health` 그대로 — AI 상태를 넣지 않는다(AI 장애로 인스턴스 전체가 재시작되는 것을 막고, AI 장애는 연습 화면 503으로만 드러난다는 기존 원칙 유지). AI 생존은 감시 루프가 맡는다.
8. **기존 AI Render 서비스**: 새 구성이 공개 URL에서 확인된 뒤 AI 담당이 정지(삭제는 그 뒤 AI 담당 판단). 확인 전에는 그대로 둔다 — 롤백 수단.

## 결과 (트레이드오프 포함)

- 얻는 것: Render 서비스 1개(유휴 절전·대시보드·비용 1곳), AI 포트가 공개되지 않음, AI·백엔드 코드 무변경, 한 배포에서 AI·백엔드 버전이 함께 고정됨(배포 순서 문제 소멸).
- 감수하는 것:
  - **장애 격리 상실** — 인스턴스 재시작·메모리 초과(OOM)·배포 실패가 백엔드와 AI를 함께 멈춘다.
  - **AI 프로세스 감시** — 감시 루프는 "프로세스 종료"만 감지한다. 살아 있지만 응답하지 않는 AI(멈춤)는 재시작하지 않는다 — 그동안 연습 API는 시간 초과로 503. 측정되면 헬스 폴링 추가를 새 결정으로.
  - **AI 갱신 = 백엔드 재배포** — AI 담당이 코드를 고쳐도 `AI_REPO_REF` 변경(또는 브랜치 지정 시 재배포)이 필요하다. 재배포 권한은 Render 서비스 소유자(사용자)에게 있다.
  - **메모리 합산** — Python 프로세스 2개(+ 별도 가상환경). Render 인스턴스 메모리 한도(무료 등급 512MB — architect 기억, 추정)에 대한 실측 없음 — 배포 후 Render 메트릭으로 확인.
  - **로그 섞임** — 한 로그 스트림. `[ai] ` 접두어로 구분. AI 로그도 프롬프트·출력 본문을 남기지 않는 규칙(AI-2) 그대로 적용.
  - **AI 브랜치 선택** — 기본 브랜치 `main`에 코드가 없어(인용) `dev` 또는 특정 SHA를 써야 한다. 브랜치를 지정하면 배포 시점마다 다른 코드가 들어갈 수 있다.
  - **롤백** — Render에서 백엔드 커밋만 되돌리면 AI는 빌드 시점 `AI_REPO_REF`로 다시 받는다. AI를 되돌리려면 `AI_REPO_REF`를 이전 SHA로 바꿔 재배포. (Render "이전 배포로 롤백"이 빌드 산출물을 재사용하는지는 미확인 — 재사용하면 AI도 함께 되돌아간다, 추정.)
  - **콜드 스타트** — 유휴 절전 후 깨어날 때 AI가 백엔드보다 늦게 뜨면 첫 연습 요청이 503일 수 있다(추정). 시연 직전 리허설(T-28)에서 연습 1회로 워밍업.
- 바뀌지 않는 것: 내부 API v1 규격, `X-Internal-Token`, `AI_SERVICE_TIMEOUT_SECONDS`, `AIUnavailableError` → 503, 백엔드 테스트·CI(Fake AI), 프론트 Vercel 리라이트, DB·마이그레이션.
- 미확인(추정)으로 남은 Render 동작 — 첫 배포에서 확인: 빌드 환경에 `git` 존재, 빌드 시점 환경 변수 사용 가능, `python -m venv` 동작, 빌드 디렉터리(`.ai_runtime/` 포함)가 실행 시점까지 유지, 127.0.0.1 바인딩 포트를 Render 포트 감지가 무시함, `PORT` 기본값이 8081이 아님.
