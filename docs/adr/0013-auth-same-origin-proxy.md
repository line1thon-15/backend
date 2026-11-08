# ADR-0013: 인증 쿠키 유지 + 프론트 쪽 같은 출처 프록시(`VITE_API_URL` 비움)

> 상태: 제안 (docs/Architecture.md 초안과 함께 사용자 승인 대기). ADR-0004를 대체한다(쿠키·토큰 방식은 그대로 이어받고, 같은 출처를 만드는 책임과 프론트 요청 사항을 실제 frontend 코드에 맞춰 다시 정한다). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-06

## 맥락

- ADR-0004(제안): DB 저장 불투명 토큰 + httpOnly 쿠키 + 프론트와 같은 출처(`/api` 프록시).
- frontend 저장소 실제 코드(메인 세션 2026-11-06 확인, 인용): README 원문 "백엔드 서버 주소는 루트에 .env 파일을 만들어 넣습니다." 예시 "VITE_API_URL=http://localhost:8080". `vite.config.js`에 proxy 설정 없음. `src/api/client.js` 원문:

```
const BASE_URL = import.meta.env.VITE_API_URL ?? ''
export async function api(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}
```

- 관찰: `VITE_API_URL`을 절대 주소로 두면 요청이 교차 출처가 된다. `fetch`의 기본 `credentials`는 `same-origin`이므로(웹 표준) 교차 출처 요청에는 쿠키가 실리지 않는다 → 이 상태로는 쿠키 세션이 동작하지 않는다. 반대로 `VITE_API_URL`이 없거나 빈 문자열이면 `?? ''`(빈 문자열은 그대로 유지)로 상대 경로가 되어, 프록시만 있으면 같은 출처가 된다.
- `client.js`는 성공 시 항상 `res.json()`을 호출한다 → 본문 없는 204 응답에서 실패한다. 오류 시 응답 본문을 버린다 → 백엔드 오류 코드(Architecture.md 오류 응답 규격)를 화면 문구 선택에 쓸 수 없다.
- 지원 브라우저에 Safari가 포함된다(N-01, Architecture.md).

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. 쿠키 유지 + 같은 출처: 로컬은 Vite `server.proxy`로 `/api` → `http://localhost:8080`, 운영은 Vercel 리라이트 `/api/:path*` → 백엔드 공개 URL. `VITE_API_URL`은 비움 | `client.js` 경로 결합 코드는 그대로 동작(상대 경로), `credentials` 옵션 불필요, CORS 설정 불필요, 토큰이 JS에 노출되지 않음, Safari 서드파티 쿠키 문제 없음 | 프론트에 설정 2개(vite.config.js·vercel.json)와 README 변경 요청 필요. Vercel 외부 리라이트의 쿠키 전달은 미검증(추정 — T-27) |
| B. 쿠키 + 교차 출처: 백엔드 CORS `allow_origins=[프론트 출처]`·`allow_credentials=true`, 쿠키 `SameSite=None; Secure`, 프론트 `fetch(..., {credentials: 'include'})` | 프록시 불필요 | 운영에서 프론트(vercel.app)와 백엔드(PaaS 도메인)가 서로 다른 사이트 → Safari 등 서드파티 쿠키 차단 정책에 막힐 수 있음(추정 — 브라우저 정책 기억, 이번 세션 미확인). CSRF 방어 별도 필요 |
| C. 쿠키 대신 Bearer 토큰: 로그인 응답의 토큰을 `sessionStorage`에 두고 `Authorization` 헤더, 백엔드 CORS(자격 증명 없음) | 교차 출처·Safari 문제 없음, 프록시 불필요 | XSS 시 토큰 탈취 가능, `client.js`에 헤더 주입 변경 필요, 탭 닫으면 재로그인 |
| D. 현재 README대로 `VITE_API_URL=http://localhost:8080` 유지 + 쿠키 | 프론트 변경 없음 | 위 관찰대로 쿠키가 실리지 않아 로그인 유지 불가 — 탈락 |

## 결정

A를 선택한다. 결정적 이유: 프론트의 기존 `client.js`가 상대 경로를 이미 지원하므로 설정 변경만으로 같은 출처가 되고, 쿠키 세션의 장점(즉시 폐기·스크립트 비노출)과 Safari 호환을 함께 지킨다.

백엔드 쪽 확정 사항: CORS 미들웨어를 켜지 않는다(교차 출처 호출은 브라우저가 막는 것이 의도된 동작). 쿠키 `sid`·`HttpOnly`·`SameSite=Lax`·`Path=/api`·운영 `Secure`, 토큰 해시 저장·7일 만료·재설정 시 폐기는 ADR-0004 그대로. 모든 성공 응답은 JSON 본문을 가진다(204 금지 — `client.js`의 `res.json()` 호환). 백엔드 로컬 포트는 8080(프론트 README 예시와 동일).

프론트 요청(Architecture.md "팀원 요청 사항" F-1~F-4): Vite 프록시, Vercel 리라이트, `VITE_API_URL` 비우기(README 수정), `client.js` 오류 처리에서 상태 코드와 `error.code`를 담은 오류 객체를 던지기.

A가 T-27에서 실패하면(Vercel 리라이트가 쿠키를 전달하지 않음) B가 아니라 C로 가는 새 ADR을 쓴다 — B는 Safari 위험 때문.

## 결과 (트레이드오프 포함)

- 얻는 것: 쿠키 세션 유지, CORS 없음, 프론트 코드 변경 최소(설정 + 오류 처리).
- 감수하는 것: 프론트 담당의 변경 합의가 선행 조건([A-11]). 팀원이 `.env`에 절대 주소를 남겨 두면 로그인이 유지되지 않는 증상이 생김 — README·docs 저장소 로컬 실행 규칙에 명시 요청.
