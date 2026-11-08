# ADR-0012: 프론트엔드 — 팀 frontend 저장소의 실제 스택(React 19 + Vite 7 + JavaScript + Tailwind v4 + React Router 7) 수용

> 상태: 제안 (docs/Architecture.md 초안과 함께 사용자 승인 대기). ADR-0003을 대체한다. 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-06

## 맥락

- ADR-0003(제안)은 PRD OQ 6 원문 "react랑 Tailwind CSS 사용하는 거 같은데 확인해봐"에 기대 React + Vite + **TypeScript** + Tailwind를 가정했다.
- 메인 세션이 2026-11-06 gh CLI로 확인한 frontend 저장소 실제 코드(인용): 설명 "프론트엔드 레포지토리 (React + Tailwind)", 최근 커밋 2026-11-04. package.json — react ^19.1.0, react-dom ^19.1.0, react-router-dom ^7.6.0, vite ^7.0.0, @vitejs/plugin-react ^4.6.0, tailwindcss ^4.1.0, @tailwindcss/vite ^4.1.0. TypeScript 없음, 테스트 러너 없음. 파일은 `.jsx`(src/App.jsx, src/api/client.js, src/components/Layout.jsx, src/pages/Home.jsx 등). README 원문 "화면은 피그마 프레임 1개당 파일 1개로 src/pages/", 첫 줄 주석에 프레임 번호(예 "// Y8 성장 기록").
- frontend 저장소는 프론트 담당(2명) 소유다. 사용자·에이전트의 작업 범위는 backend 저장소다(사용자 원문 "내가 접근할 곳은 backend 부분 쪽이야").

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. 실제 스택을 그대로 수용하고, 백엔드 설계는 이 스택에 맞춘다. 프론트 내부 구조·라이브러리는 권고로만 전달 | 이미 진행 중인 프론트 작업과 충돌 없음, 소유권 존중 | API DTO를 타입으로 강제할 수 없음 — 계약은 문서·샘플·E2E로 지킴 |
| B. 프론트에 TypeScript 전환을 요청 | 타입 기반 계약 | 일정(N-08) 중 전환 비용, 다른 파트 저장소에 대한 설계 강요 |

## 결정

A를 선택한다. 결정적 이유: 프론트 스택은 이미 코드로 존재하는 사실이고 소유자가 다르다 — 설계는 그 위에 맞춘다. PRD OQ 6은 이 저장소 사실로 답이 났다고 본다(PRD 기록 갱신은 planner 몫).

프론트에 대한 **요청**(필수 — 백엔드 계약과 맞물림)과 **권고**(선택)는 Architecture.md "팀원 요청 사항" 표에 둔다. 요약:
- 요청: `/api` 같은 출처 프록시(Vite `server.proxy`, Vercel 리라이트), `VITE_API_URL` 비움, `client.js`가 오류 본문 `{error:{code}}`를 보존해 던지기 (ADR-0013).
- 권고: 서버 상태 관리(TanStack Query 등)·공용 화면 상태 컴포넌트, 테스트 러너 Vitest + React Testing Library, E2E Playwright(N-06) — 설치 결정은 프론트 담당.

## 결과 (트레이드오프 포함)

- 얻는 것: 기존 프론트 작업과 정합, 다른 파트 저장소에 대한 강요 없음.
- 감수하는 것: DTO 오타·필드 누락을 컴파일 시점에 못 잡음 → 팀 docs 저장소의 API 정의서 + 응답 예시 JSON + N-06 E2E로 보완. 프론트 테스트·E2E 하네스의 실제 구축 여부는 프론트 담당 결정에 달림(AGENTS.md 화면 흐름 회귀 요구 — [A-11]).
