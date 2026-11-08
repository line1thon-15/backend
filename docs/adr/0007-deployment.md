# ADR-0007: 배포 — Vercel(프론트) + Python PaaS(백엔드) + 관리형 Postgres

> 상태: 제안 — 형태는 사용자 선택으로 정해졌고, **구체 서비스(PaaS·DB)와 계정·요금제는 사용자 확인 필요**(Architecture.md [A-2]). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-06
> 2026-11-06 갱신(승인 전 제안 상태라 같은 ADR에서 범위만 고침): ADR-0011로 AI가 별도 HTTP 서비스가 되어 **배포 단위가 3개**(프론트 Vercel / 백엔드 PaaS 웹 서비스 / AI PaaS 웹 서비스) + 관리형 Postgres가 된다. AI 서비스는 같은 PaaS에 두 번째 웹 서비스로 두는 것을 추천한다(후보·추정 내용은 아래 백엔드 행과 같음). Gemini 키는 AI 서비스 환경 변수에만 둔다. 두 번째 서비스의 비용·계정은 [A-2]에 포함. Vercel 리라이트는 frontend 저장소의 `vercel.json`이므로 프론트 담당 작업이다(ADR-0013).

## 맥락

- N-07: "공개 URL에서 시연 흐름이 동작하는 배포 가능한 mvp … 배포 형태 사용자 선택 원문: "Vercel + PaaS + 관리형 DB (Recommended)"(라운드 8) — 구체 서비스는 architect가 확정". 배포 URL 공개(2026-11-03 사용자 답변 "3. 배포 url 공개").
- 세션에 Vercel·Supabase MCP 연결이 있으나 사용 여부 미정(인용). 계정·요금제 미확인. Docker 없음.
- 백엔드는 Python FastAPI 단일 서비스(ADR-0001·0002), DB는 Postgres(ADR-0005).

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| 프론트: Vercel (고정 — 사용자 선택) | 정적 SPA 배포·리라이트로 `/api` 같은 출처(ADR-0004) | 외부 리라이트의 쿠키 동작 미검증(추정) |
| 백엔드 A. Render 웹 서비스 | Docker 없이 Python 네이티브 빌드·시작 명령 지정, 헬스체크 경로 설정 가능(추정 — architect 기억, 이번 세션 미확인) | 무료 등급 유휴 절전으로 첫 요청 지연 가능(추정) |
| 백엔드 B. Railway | Python 자동 감지, Postgres 부속 | 무료 범위·크레딧 조건 미확인(추정) |
| 백엔드 C. Fly.io | 성능·리전 선택 | 사실상 컨테이너 이미지 기반 — Docker 없는 로컬과 거리 |
| 백엔드 D. Vercel Python Functions | 플랫폼 1개 | 사용자 선택 "PaaS"와 다름, 서버리스 시간 제한·콜드 스타트가 AI 호출과 충돌 가능(추정) |
| DB A. Neon | 관리형 Postgres, 무료 등급 존재(추정) | 유휴 시 일시 정지·재개 지연 가능(추정) |
| DB B. Supabase Postgres | 관리형 Postgres, 세션에 MCP 연결 존재(인용) | 무료 프로젝트 비활성 시 일시 정지 정책 가능(추정). 인증·스토리지 등 부가 기능은 쓰지 않음 |
| DB C. PaaS 부속 Postgres(Render·Railway) | 백엔드와 한 대시보드 | 무료 DB 보존 기간 제한 가능(추정) |

## 결정

형태는 "Vercel + Python PaaS + 관리형 Postgres"로 확정(사용자 선택). 구체 서비스는 **추천만** 하고 사용자 확인 후 확정한다:

- 추천: 프론트 Vercel / 백엔드 Render 웹 서비스 / DB Neon 또는 Supabase Postgres.
- 결정적 이유: Docker 없이 Python 네이티브 빌드가 가능한 PaaS가 이 팀 환경에 맞고, 설계는 "Postgres 접속 문자열 + ASGI 시작 명령 + 정적 호스팅"에만 의존하므로 어느 후보로 확정해도 코드 변경이 없다.
- 위 서비스별 장단점의 요금·정책 항목은 전부 architect 기억 기반 추정이다. 확인 방법: 사용자가 각 서비스의 현재 요금제 페이지를 확인하거나 메인 세션이 Browser pane으로 확인.

## 결과 (트레이드오프 포함)

- 얻는 것: 서비스 교체 시 환경 변수·리라이트 대상만 바뀜.
- 감수하는 것: 무료 등급 절전·일시 정지로 시연 지연 위험(Architecture.md D-3), 외부 리라이트 쿠키 미검증(D-1). 둘 다 T-27에서 실측.
- 배포 메커니즘(빌드·마이그레이션·롤백·헬스체크)은 Architecture.md "배포" 절.
