# ADR-0006: 테스트 러너 — pytest / Vitest / Playwright, 자동 테스트의 AI는 Fake 제공자

> 상태: 제안 (docs/Architecture.md 초안과 함께 사용자 승인 대기, 패키지 설치·Playwright 브라우저 다운로드 허용 확인 필요). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-06
> 2026-11-06 갱신(승인 전 제안 상태라 같은 ADR에서 범위만 고침): 저장소가 파트별로 나뉨(ADR-0011·0012). 이 ADR의 결정 중 **backend 저장소에 적용되는 것은 pytest와 `AI_CLIENT=fake`(백엔드 안의 FakePracticeAI)** 뿐이다. Vitest + RTL과 Playwright는 frontend 저장소에 대한 **권고**이며 설치·구축은 프론트 담당이 정한다. "실제 Gemini 호출 테스트"는 백엔드에서 Gemini를 직접 부르지 않으므로, 백엔드 쪽은 실행 중인 AI 서비스를 부르는 `@pytest.mark.live_ai` 테스트로 바뀐다(기본 실행 제외). N-04 안전 필터 세트의 실행은 ai 저장소(AI 담당) 몫이다. 상세는 Architecture.md "테스트 전략".

## 맥락

- AGENTS.md 검증 루프: T-01은 러너 + 스모크 + 명령 등록, 웹 UI면 E2E 러너 + E2E 스모크. PRD N-06 "핵심 흐름 E2E … 러너는 설계에서 확정".
- 실행 단위: Python 백엔드(AI 모듈 포함 — ADR-0001), React 프론트(ADR-0003).
- 외부 의존성: Gemini API — 키 보유 여부 미확인, 비용·약관(PRD R-1)·비결정성 때문에 자동 테스트에서 호출하면 안 됨(tdd 스킬 "외부 의존성 격리"). 에이전트는 `.env`를 읽지 않는다.
- 테스트 러너 설치 여부 미확인(실행환경 표).

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| 백엔드 A. pytest | 픽스처·마커(`live_ai` 분리)·파라미터화(N-04 데이터 주도 세트)에 강함, FastAPI `TestClient`와 표준 조합 | 설치 필요 |
| 백엔드 B. unittest(내장) | 설치 불필요 | 마커·파라미터화 불편 — 설치 불허 시 대안으로만 |
| 프론트 A. Vitest + React Testing Library + jsdom | Vite 설정 공유, 빠름 | 설치 필요 |
| 프론트 B. Jest + RTL | 자료 많음 | Vite·ESM 설정 추가 부담 |
| E2E A. Playwright Test | `webServer`로 백엔드·프론트 동시 기동, 모바일 에뮬레이션(N-01), 네트워크 요청 검사(F-25 ③ 감정 값 미전송), 트레이스 증거 | 브라우저 바이너리 다운로드 필요 |
| E2E B. Cypress | 대화형 디버깅 | 다중 서버 기동·모바일 에뮬레이션·멀티 탭 제약, 무거움 |

## 결정

pytest / Vitest + RTL / Playwright Test를 선택한다. 결정적 이유: N-06 E2E와 N-04 안전 필터 세트, F-25 ③ 네트워크 검증을 각 러너의 기본 기능으로 할 수 있다.

AI 격리: `AI_PROVIDER=fake`(결정적 `FakeProvider`)가 모든 단위·통합·E2E의 기본이다. 실제 Gemini 호출은 `@pytest.mark.live_ai` 테스트만 하며 기본 실행에서 제외한다. 키는 사용자가 자기 셸 환경 변수로 제공한다.

## 결과 (트레이드오프 포함)

- 얻는 것: 키 없이 전체 테스트 실행, 결정적 E2E, 증거(트레이스·리포트) 보존.
- 감수하는 것: Fake로 통과한 것이 실제 Gemini 출력 품질을 보장하지 않음 — N-04 live 실행(T-12·T-51)으로 보완. 설치 불허 시 Architecture.md "설치 불허 시 대안" 표로 돌아가며 E2E 자동화는 불가.
- 배치·T-01 범위는 Architecture.md "테스트 전략" 절.
