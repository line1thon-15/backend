# ADR-0022: AI 변형의 시작 선택지(`opening_choices`)를 백엔드 `Variant` 규격에 넣어 그대로 전달

> 상태: 승인 (2026-11-15 사용자 승인 — 메인 세션 질문 원문 "설계 결정 5건을 추천안대로 확정할까요?", 사용자 답 원문 "추천안대로 확정"(1A·2A·3A, DECISIONS #137~#139), 메인 세션 지시로 architect가 기입). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-15
> 관련: DECISIONS #137·#138·#139. Tasks T-100 완료 조건 ①. 바꾸는 범위는 Architecture "1차 내부 API v1"의 `Variant` 행·`start` 행·계약 샘플 행과 엔티티 `practice_sessions.variant` 필드 목록뿐이다. ADR-0017(제안)·ADR-0019(승인) 본문은 수정하지 않았다 — #98 "받은 그대로 저장하고 그대로 보낸다" 원칙은 그대로이고, 이번 결정은 그 원칙이 새 필드에서 지켜지게 한다.

## 맥락

- 팀 리뷰 원문(PR #35, Tasks T-100 행 인용): "1. [P2] `opening_choices` 전달 누락: AI 서버의 `Variant`에는 `opening_choices`가 있지만, 백엔드 `app/ai_client/ports.py`의 `Variant` 모델에는 해당 필드가 없습니다. 이로 인해 AI가 생성한 상황별 시작 선택지가 파싱 과정에서 사라지고 공통 템플릿으로 대체될 수 있습니다. 필드 추가 및 `variant → start` 전달 테스트를 권장합니다."
- 사용자 지시 원문(2026-11-15, 메인 세션 전달): "35 실제 ai 확인하고, opening_choices 전달해, 그리고 99 사후 리뷰 권고 정리하자"
- AI 쪽 사실(메인 세션 확인 — architect는 ai 저장소를 재확인하지 않음, 인용): ai dev `8d900d1` `app/schemas.py` `OpeningChoices{correct, doubtful, other}`(각 1~60자), `Variant.opening_choices: OpeningChoices | None = None`. `app/practice.py:57-58` `start`는 variant에 `opening_choices`가 있으면 그것으로, 없으면 첫 단서의 선택지 예시로 시작 선택지를 만든다. `app/scenarios.py:213-248`이 `opening_choices`를 검증한다. ai `8d900d1`의 `contracts/practice.variant.response.json`에 `opening_choices`가 있다.
- 백엔드 사실(architect 직접 확인, 작업 트리 = 브랜치 `docs/t100-opening-choices`):
  - `app/ai_client/ports.py:34-36` `_InboundModel` — 모르는 필드는 버린다. `:69-79` `Variant`에 `opening_choices` 없음. `Variant`의 다른 필드는 이미 AI 스키마와 같은 길이 제약을 Pydantic `Field`로 건다(`:71-79`) — 응답 검증 실패는 `AIUnavailableError` → 503(Architecture "백엔드 쪽 처리" 행).
  - `app/services/practice.py:398` 저장은 `variant.model_dump(mode="json")`, `:464`·`:616` 이후 요청은 `Variant.model_validate(record.variant)`. `app/ai_client/http_client.py:112` 요청 본문은 `request.model_dump(mode="json")` — `exclude_none` 없음. 즉 선택 필드를 `None` 기본값으로 추가하면 **추가 코드 없이** 저장 JSON과 요청 본문에 `"opening_choices": null`이 실린다.
  - `tests/contracts/ai/SOURCE.txt:4-5` 계약 샘플은 ai `feature/ai` `331d2c6` 고정. 같은 작업 트리의 `app/content/data/ai/SOURCE.txt:4-5`도 `331d2c6`이다 — 이 브랜치에는 PR #35(T-30, 콘텐츠 사본 `8d900d1` 재고정)가 아직 들어 있지 않다. T-30 완료 근거(Tasks T-30 행, 인용)에 따르면 PR #35 병합 뒤 콘텐츠 사본은 `8d900d1`, 계약 샘플은 `331d2c6`으로 커밋이 갈린다 — T-87 고정 근거 원문 "고정 커밋 = T-86 계약 샘플과 같은 커밋"(`app/content/data/ai/SOURCE.txt:11`)과 어긋나는 상태.

## 검토한 대안

결정 1 — 필드 규격과 백엔드 검증 (DECISIONS #137)

| 대안 | 장점 | 단점 |
|---|---|---|
| 1A. 명시 필드 + AI 스키마와 같은 형태·길이 검증 (**추천**): `OpeningChoices{correct, doubtful, other}` 각 문자열 1~60자, `Variant.opening_choices: OpeningChoices \| None = None`. 위반 = 응답 스키마 위반 → `AIUnavailableError` → 503 | 기존 `Variant` 필드 관례(AI 스키마 길이 그대로 `Field` 제약)와 같다. 받은 값이 무엇인지 백엔드 규격에 드러난다. 추가 처리 코드 없음 | AI가 길이 상한을 바꾸면 백엔드도 바꿔야 한다(다른 `Variant` 필드와 같은 부담). 형태가 틀린 `opening_choices` 하나로 연습 시작이 503이 된다 — AI가 자기 검증(`scenarios.py:213-248`, 인용)을 거쳐 보내므로 드물다(추정) |
| 1B. 명시 필드 + 관대한 처리: 형태·길이가 틀리면 그 필드만 버리고(`null`) 진행 → AI가 첫 단서 선택지 예시로 시작 | 선택 필드 하나 때문에 연습이 막히지 않는다 | 다른 `Variant` 필드(위반 503)와 처리가 갈린다. 필드 단위 예외 처리 코드가 필요. AI 계약 위반을 조용히 삼켜 발견이 늦어진다 |
| 1C. 필드를 정의하지 않고 `Variant`가 모르는 필드를 통째로 보존(`extra="allow"`) | 앞으로 AI가 `Variant`에 필드를 더해도 다시 사라지지 않는다 | 백엔드가 검증하지 않은 값을 AI에 되돌려 보낸다 — 나가는 값은 규격 필드만 싣는 원칙(`_OutboundModel` `extra="forbid"`, N-05)과 성격이 다르다. 규격 문서에 무엇이 오가는지 드러나지 않는다 |
| 1D. 백엔드가 `start` 응답 선택지 문장이 `opening_choices`와 같은지도 검증 | 전달 누락을 운영 중에도 잡는다 | 시작 선택지를 어떻게 만들지는 AI 몫(D-11과 같은 경계). AI가 문장을 다듬거나 섞으면 정상 응답이 503이 된다 |

결정 2 — 필드가 없을 때 저장·요청 표현 (DECISIONS #138)

| 대안 | 장점 | 단점 |
|---|---|---|
| 2A. `null`로 싣는다 (**추천**) — Pydantic 기본 직렬화 그대로. 이 필드가 없는 기존 저장 variant도 읽을 때 `None` → 요청에 `null` | 코드 변경 없음(`model_dump` 그대로). AI `8d900d1` 스키마가 `OpeningChoices \| None = None`이라 `null`은 계약상 유효한 값(인용). 새 세션·옛 세션의 요청 모양이 같다 | ~~AI가 `8d900d1`보다 옛 버전이고 `Variant`가 모르는 필드를 거부하면 모든 `start`·`turn`이 AI 422 → 503이 된다(옛 AI의 거부 여부는 미확인)~~ **2026-11-15 해소**: ai `331d2c6`·`e82ea66`의 `app/schemas.py`에는 `model_config`·`extra` 설정이 없다(메인 세션 `git show`로 grep 0건 — 인용). Pydantic 기본은 모르는 필드 무시이므로 옛 AI도 `null` 키를 거부하지 않는다. 남는 단점: 옛 AI에서는 `opening_choices`가 오지 않아 기능이 동작하지 않는다 — 배포 시 `AI_REPO_REF`(DECISIONS #136)가 `8d900d1` 이후여야 한다 |
| 2B. 키를 생략한다 — `Variant`에 한해 `None`인 `opening_choices`를 직렬화에서 뺀다(요청 전체 `exclude_none`은 금지 — `Message.choice_kind`·`clue_id` null 전송이 바뀐다) | 옛 AI 버전과도 호환. 옛 저장 variant와 같은 모양 | `Variant` 직렬화 맞춤 코드가 필요. 저장 JSON에도 같은 규칙을 걸어야 일관된다 |

결정 3 — 계약 샘플 재고정 (DECISIONS #139)

| 대안 | 장점 | 단점 |
|---|---|---|
| 3A. `tests/contracts/ai/` 12개 전부를 ai dev `8d900d1`로 통째로 다시 복사 (**추천**) — `SOURCE.txt`의 브랜치(`dev`)·커밋·복사일·고정 근거·SHA-256 갱신, 콘텐츠 사본과 같은 커밋 | 계약 샘플과 콘텐츠 사본의 고정 커밋이 다시 같아진다(T-87 원칙). 한 커밋 기준이라 샘플끼리 모순이 없다 | `opening_choices` 외 다른 계약 변경도 함께 들어온다 — 테스트가 깨지면 범위가 커질 수 있다(T-100 ③이 "임의로 맞추지 말고 보고"로 막음) |
| 3B. `practice.variant.response.json` 1개만 `8d900d1` 것으로 교체 | 변경 범위 최소 | 샘플 묶음이 두 커밋에 걸친다 — "커밋 고정으로 복사" 원칙(Architecture 계약 샘플 행)이 깨지고, 콘텐츠 사본과도 여전히 어긋난다 |
| 3C. 재고정하지 않고 백엔드 테스트에 손으로 만든 `opening_choices` 예시만 추가 | AI 쪽 변경 영향 없음 | 손으로 만든 예시는 AI 계약이 아니다 — 계약 테스트의 의미가 없다 |

## 결정

1A + 2A + 3A. 결정적 이유: 셋 다 기존 관례(Variant 필드 = AI 스키마와 같은 제약·위반 503, Pydantic 기본 직렬화, 계약 샘플은 한 커밋 통째 복사)를 그대로 따라 새 처리 규칙을 만들지 않는다.

규칙(T-100):

1. `app/ai_client/ports.py`에 `OpeningChoices`(받는 모델 — `_InboundModel`)를 두고 `correct`·`doubtful`·`other` 각각 `str`, 1~60자. `Variant.opening_choices: OpeningChoices | None = None`.
2. 형태·길이 위반은 다른 `Variant` 필드 위반과 같다 — `variant` 응답 스키마 위반 → `AIUnavailableError` → 503 `AI_UNAVAILABLE`, 저장 없음. ADR-0019(#133)의 "스키마 위반은 재요청하지 않고 503"이 그대로 적용된다.
3. 저장·전달: 받은 `Variant` 전체(이 필드 포함)를 지금처럼 `practice_sessions.variant`에 저장하고 같은 세션의 `start`·`turn`·`judge`·`feedback` 요청에 그대로 보낸다(#98). 필드가 없으면 `null`(2A). 기존 저장 variant는 데이터 이전 없이 읽을 때 `None`.
4. 백엔드는 `start`의 선택지가 `opening_choices`로 만들어졌는지 검증하지 않는다(1D 기각) — 기존 ST1~ST5만. 실제 일치는 T-100 ⑤의 실서버 확인으로 관찰한다.
5. `FakePracticeAI`는 테스트에서 `opening_choices`가 있는 변형과 없는 변형을 모두 돌려줄 수 있어야 한다(T-100 ②(a)~(d)).
6. 계약 샘플: 3A. 다른 계약 파일 변경으로 테스트가 깨지면 T-100 ③대로 보고.
7. 배포 조건: T-100이 배포될 때 `AI_REPO_REF`(DECISIONS #136)는 ai `8d900d1` 또는 그 뒤 커밋이어야 한다 — 그 전 커밋이면 `opening_choices`가 오지 않는다(기능 없음). 옛 AI가 `null` 키를 거부할 가능성은 2026-11-15 해소 — ai `331d2c6`·`e82ea66` `app/schemas.py`에 `model_config`·`extra` 설정 없음(메인 세션 확인, 인용), Pydantic 기본은 모르는 필드 무시.

## 결과 (트레이드오프 포함)

- 얻는 것: AI가 만든 상황별 시작 선택지가 버려지지 않고 `start`에 도달한다. 공개 API(`TurnView`)·DB 스키마·마이그레이션 변경 없음(`variant`는 JSON 열).
- 감수하는 것: ① 1A — `opening_choices` 형태 오류 하나로 연습 시작이 503(다른 Variant 필드와 같은 수준). ② 2A — AI 버전 결합: 백엔드 배포 전에 AI `8d900d1` 이후가 떠 있어야 시작 선택지 기능이 동작한다(옛 AI도 `null` 키는 무시하므로 오류는 나지 않음 — 2026-11-15 메인 세션 확인, 인용). ③ 3A — 재고정으로 `opening_choices` 외 계약 차이가 드러날 수 있음.
- 바뀌지 않는 것: #98(받은 그대로 저장·전달), #102·#133(변형 결정·fallback 재요청), ST1~ST5, `TurnView` 형태.
- 남는 위험: `_InboundModel`이 모르는 필드를 버리는 구조는 그대로라, AI가 `Variant`에 다른 필드를 더하면 같은 누락이 다시 생긴다(1C를 고르지 않은 대가). 대응은 계약 샘플 재고정 때 `Variant` 필드 목록 비교(설계 리스크로 기록).
