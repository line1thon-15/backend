# ADR-0003: 프론트엔드 React + Vite SPA + TypeScript + Tailwind CSS ([가정])

> 상태: 폐기(→ ADR-0012로 대체, 2026-11-06 — frontend 저장소 실제 코드가 JavaScript(.jsx)·React 19·Vite 7·Tailwind v4임을 확인. 승인 전 제안 상태에서 폐기).
> 날짜: 2026-11-06

## 맥락

- PRD OQ 6 원문: "react랑 Tailwind CSS 사용하는 거 같은데 확인해봐"(라운드 7). 저장소에 앱 코드가 없어 확인 불가, 팀 확인 미완(PRD.md:319). TypeScript 여부는 원문에 없다.
- 백엔드는 Python FastAPI로 분리(ADR-0002) — 프론트는 JSON API를 호출하는 화면만 담당.
- 화면 11개, 반응형(N-01), WCAG 2.1 AA(N-02), 배포는 Vercel(N-07 사용자 선택).

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. React + Vite SPA + TypeScript + Tailwind + React Router | OQ 6 원문(React·Tailwind)과 일치. Vite dev 서버 프록시로 로컬에서도 `/api` 같은 출처(ADR-0004). Vitest와 설정 공유. 정적 빌드라 Vercel 배포 단순. TS 타입으로 API DTO를 고정해 프론트 2명 간 어긋남 감소 | TS 미경험 팀원이 있으면 초기 속도 저하 |
| B. Next.js(App Router) + Tailwind | Vercel과 궁합, 파일 기반 라우팅 | 서버 컴포넌트·SSR이 이 구성(별도 Python API)에서 이득이 적고, 인증 쿠키·데이터 패칭 모델이 복잡해짐 |
| C. React + Vite + JavaScript + Tailwind | 진입 장벽 낮음 | DTO 규격 위반을 실행 전에 못 잡음 |

## 결정

A를 **가정**으로 선택한다. 결정적 이유: 원문이 언급한 React·Tailwind와 일치하면서, 별도 Python API 구성에 가장 단순한 정적 SPA다. TypeScript는 architect 제안이며 팀이 JS를 원하면 C로 바꿔도 Architecture.md의 나머지 설계(라우팅·상태·컴포넌트 경계)는 그대로 유효하다.

## 결과 (트레이드오프 포함)

- 얻는 것: 단순 배포, 로컬·운영 동일 출처 구조, 타입 기반 계약.
- 감수하는 것: SSR·SEO 없음(로그인 후 화면 위주라 영향 작음). 확정 전 착수 시 팀 결정과 어긋나면 재작업.
- 확정 조건: 팀 확인(Architecture.md [A-4]) + 설치 허용(Architecture.md [A-3]).
