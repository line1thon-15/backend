# ADR-0023: 새 출제 순번(`draw_index`) 중복 방지 — 아이·출처별 고유 인덱스 + 저장 트랜잭션 안 번호 계산 + 충돌 시 1회 재시도

> 상태: 승인 (2026-11-15 사용자 승인 — 메인 세션 질문 원문 "설계 결정 5건을 추천안대로 확정할까요?", 사용자 답 원문 "추천안대로 확정"(대안 A — 계산 기준 `live` 최댓값 변경 동의 포함, DECISIONS #140), 메인 세션 지시로 architect가 기입). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-15
> 관련: DECISIONS #140. Tasks T-99 완료 조건 ①. ADR-0009(제안)의 순번 정의 "아이별 새 출제 순번 `draw_index`(1부터, 다시 도전 제외)"를 뒤집지 않고, **무엇을 세는가**(실제 출제 `live` 행만)와 **언제 정하는가**(저장 트랜잭션 안)를 정한다. ADR-0009 본문은 수정하지 않았다.

## 맥락

- 리뷰 원문(PR #33 사후 리뷰 후속 권고 2, Tasks T-99 근거 셀 인용): "P2: 동시 출제 요청 시 `count_new_draws() + 1`에 따른 `draw_index` 중복 가능성 검토 및 회귀 테스트 추가."
- 코드 관찰(architect 직접 확인, 작업 트리 = 브랜치 `docs/t100-opening-choices`):
  - `app/services/practice.py:216` — 새 출제 순번 = `count_new_draws(child_id) + 1`. 이 값은 `_begin_session`(:359~) **안의 AI `variant`·`start` 호출보다 먼저** 계산되고, 저장(`create_session`, :399)은 AI 호출이 끝난 뒤다 → 경쟁 구간이 AI 응답 시간(수 초)만큼 길다.
  - `app/repositories/practice.py:86-95` `count_new_draws` — `child_id` 일치 + `mode != "retry"`인 행 수. **`origin` 조건이 없다** — 예시(`demo_seed`) 행도 센다.
  - `app/db/models.py:177-197` `practice_sessions` 제약에 `draw_index` 고유 제약 없음, `:221` `nullable=True`. 다시 도전은 `draw_index = None`(`app/services/practice.py:263`).
  - `app/repositories/practice.py:123-127` `create_session`은 자체 트랜잭션, `IntegrityError` 처리 없음(→ 지금은 500).
  - 예시 데이터: `app/demo/plan.py:125,142` 예시 세션 8개(`_SESSION_SCHEDULE` :21-30)가 `draw_index` **0~7**(0부터 — ADR-0009 "1부터"와 다름), `mode = "area"`, `origin = demo_seed`. `app/repositories/demo_seed.py:68-138` 재적재는 그 아이의 `demo_seed` 행을 지우고 같은 순번으로 다시 넣으며, `live` 다시 도전의 `retry_of`를 `(draw_index, scenario_id, target_cue_ids)` 키로 **새 예시 행끼리만** 다시 잇는다(:112-138, :162-167).
  - `app/demo/seed.py:100-111` — 지정 아이에 덧붙이는 적재 경로가 있다(DECISIONS #30 두 방식, 인용).
- 따라서 같은 아이 안에서 `demo_seed` 행과 `live` 행의 `draw_index`가 **겹칠 수 있다** — 이미 실제 출제가 있는 아이(순번 1, 2, …)에 예시를 덧붙이면 예시 0~7과 겹친다. 반대로 예시를 먼저 넣은 고정 시연 계정은 실제 출제가 9부터 시작한다(예시 8행을 세므로).
- 동시성 외 중복 경로(architect 발견): 예시 계획 행 수가 줄어든 채 재적재되면 `count_new_draws`가 줄어 다음 실제 순번이 이미 있는 `live` 순번과 같아진다(예: 예시 8 + 실제 9·10 → 예시 6으로 재적재 → 다음 = 6+2+1 = 9). 고유 제약만 추가하고 계산을 그대로 두면 이 아이는 **매번** 충돌한다(재계산해도 같은 값) — 계산 기준을 같이 바꿔야 한다.
- 현재 `draw_index`를 읽는 곳(architect grep): `latest_variant_axes`의 같은 시각 순서(:78), `first_session_ids`의 같은 시각 순서(:348-352), 예시 재연결 키(`demo_seed.py`). 정상 상황 슬롯(ADR-0009 `mod 10`)은 정상 상황 출제가 꺼져 있어(#110) 아직 읽지 않는다.
- DB: 운영 PostgreSQL, 테스트 SQLite(ADR-0005). 두 DB 모두 고유 인덱스에서 NULL끼리는 같지 않은 것으로 본다(PostgreSQL 기본 `NULLS DISTINCT`, SQLite 고유 인덱스의 NULL 처리) — 다시 도전의 NULL은 부분 인덱스 없이도 제외된다. SQLite는 `ALTER TABLE … ADD CONSTRAINT`가 없지만 `CREATE UNIQUE INDEX`는 된다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. 고유 인덱스 `(child_id, origin, draw_index)` + 순번을 **저장 트랜잭션 안에서** `live` 행 최댓값 + 1로 계산 + 고유 위반 시 1회 재계산·재시도 (**추천**) | DB가 중복을 막는다(코드 경로와 무관). `origin`을 키에 넣어 예시·실제가 겹쳐도 충돌하지 않는다. 최댓값 기준이라 예시 재적재·행 수 변화와 무관하게 실제 순번이 단조 증가하고 기존 실제 행과 겹치지 않는다. 두 DB에서 같은 DDL(일반 고유 인덱스). AI 호출을 다시 하지 않는다 | 마이그레이션 1개(기존 중복 처리 포함). 저장소 포트 변경(순번을 서비스가 아니라 저장 시점에 정함). 계산 기준이 "예시 포함 행 수" → "실제 행 최댓값"으로 바뀐다 — 예시만 있는 아이의 첫 실제 순번이 9 → 1로 바뀜(지금은 순번을 읽는 동작 차이 없음). 정상 상황 슬롯을 켤 때 "출제 전에 순번으로 정상/위험을 정함"과 "저장 때 순번 확정"을 맞추는 규칙이 필요(T-34·T-35 몫) |
| A'. A와 같되 고유 인덱스를 `live` 행에만 거는 부분 인덱스 `(child_id, draw_index) WHERE origin = 'live'` | 예시 행에는 제약이 없다 | 방언별 `postgresql_where`·`sqlite_where`를 둘 다 써야 한다. 예시 행은 계획상 이미 0~7로 유일해 제약해도 손해가 없다 — 이득 없이 복잡 |
| A''. 고유 인덱스 `(child_id, draw_index)` (출처 구분 없음) | 가장 단순 | 실제 출제가 있는 아이에 예시를 덧붙이면 예시 적재가 고유 위반으로 실패한다(위 겹침) — 기존 적재 경로가 깨진다 |
| B. 아이 행 잠금(`SELECT … FROM children WHERE id = … FOR UPDATE`) 후 계산·저장 | 스키마 변경 없음 | SQLite에서 `FOR UPDATE`는 무시된다 — 테스트 DB에서는 SQLite 쓰기 잠금 동작(동시 쓰기 시 "database is locked" 오류)에 기대게 된다. DB 제약이 없어 잠금을 안 거치는 다른 쓰기 경로(예시 적재 등)는 막지 못한다. 예시 행 수 감소 경로는 그대로 남음 |
| C. 아이별 카운터 열(`children.next_draw_index`)을 원자적 `UPDATE … SET n = n + 1`로 증가 | 두 DB에서 원자적, 순번에 빈칸 없음 | `children` 테이블 변경 + 기존 값 채우기 마이그레이션. 고유 인덱스 없이는 다른 경로의 중복을 여전히 못 막는다 — 결국 A의 인덱스도 필요 |
| D. 문서에 한계로만 기록 | 변경 없음 | 리뷰 권고(P2) 미해결. 정상 상황 슬롯을 켜면 중복 순번이 정상 비율을 깨뜨린다. 예시 행 수 감소 경로도 남음 |

## 결정

A. 결정적 이유: 중복을 코드 규칙이 아니라 DB가 막고(두 DB 공통 DDL), 예시 행과의 겹침·예시 재적재로 인한 순번 후퇴를 같은 변경으로 함께 없앤다.

규칙(T-99 ①):

1. **인덱스**: `practice_sessions`에 고유 인덱스 `uq_practice_sessions_child_origin_draw` = `(child_id, origin, draw_index)`. 모델(`__table_args__`)과 Alembic 마이그레이션 양쪽에 둔다(`op.create_index(..., unique=True)` — 제약 추가가 아니라 인덱스라 SQLite 배치 모드 불필요). 다시 도전(`draw_index` NULL)은 NULL 처리로 자동 제외.
2. **계산 기준**: 새 실제 출제의 `draw_index` = 그 아이의 `origin = 'live'`이고 `draw_index`가 NULL이 아닌 행의 최댓값 + 1(없으면 1). 예시 행은 세지 않는다. `count_new_draws`는 이 용도로 쓰지 않는다(다른 호출처가 없으면 제거 여부는 implementer).
3. **계산 시점**: 순번은 `practice_sessions` 행을 넣는 **같은 트랜잭션 안에서** 계산한다(AI 호출 전이 아니라 저장 직전). 서비스가 AI 호출 전에 정해 넘기는 현재 흐름(`NewPracticeSession.draw_index`, `app/services/ports.py:190`)은 바꾼다 — 저장소가 "새 출제면 순번을 정해 넣는다"를 맡는다(포트 모양은 implementer, 계층 규칙 그대로).
4. **충돌 시**: 이 인덱스 위반(`IntegrityError`)이면 같은 입력으로 순번만 다시 계산해 **1회** 재시도한다. AI를 다시 부르지 않는다. 재시도도 위반이면 예외를 그대로 올려 500 `INTERNAL`(아이는 다시 시도). 이 인덱스가 아닌 고유 위반은 재시도하지 않는다.
5. **기존 데이터(마이그레이션)**: 인덱스를 만들기 전에 `(child_id, origin, draw_index)`가 같은 비NULL 행 묶음을 찾는다. 묶음마다 `started_at`, 같으면 `id` 순으로 첫 행은 그대로 두고, 나머지는 그 아이·그 출처의 현재 최댓값 + 1부터 차례로 다시 매긴다. 다시 매긴 행 수만 마이그레이션 출력에 남긴다(아이 ID 등 식별값 금지). SQLite·PostgreSQL 공통이 되도록 방언 전용 SQL(창 함수 갱신 등) 대신 행을 읽어 개별 `UPDATE`로 처리해도 된다. 되돌리기(downgrade)는 인덱스만 지우고 번호는 되돌리지 않는다.
6. **예시 데이터**: 예시 계획의 0부터 시작하는 순번(`app/demo/plan.py:125`)과 재연결 키는 바꾸지 않는다 — `origin`이 키에 있어 실제 행과 충돌하지 않는다. 예시 순번을 1부터로 맞출지는 이번 범위가 아니다(DECISIONS #140 메모).
7. **테스트(T-99 ①)**: Red-First — (a) 같은 아이의 동시 새 출제 2건이 서로 다른 `draw_index`(현재 코드에서 중복 재현 시도, 출력 보존) (b) 예시 8행이 있는 아이의 첫 실제 출제 = 1, 실제 출제가 있는 아이에 예시를 덧붙여도 적재 성공 (c) 예시 계획 행 수가 줄어든 재적재 뒤에도 다음 실제 순번이 기존 실제 최댓값 + 1 (d) 다시 도전은 NULL로 여러 건 저장 가능 (e) 충돌 1회 → 재시도 성공, AI 호출 수 증가 없음 / 2회 → 500 (f) 마이그레이션: 중복이 있는 SQLite DB에서 upgrade 성공·재번호 규칙대로. PostgreSQL 실행은 T-99 ④와 같은 실행 수단 문제 — 수단이 없으면 `미검증 — 사유`.

## 결과 (트레이드오프 포함)

- 얻는 것: 동시 요청·예시 재적재 어느 쪽으로도 같은 아이·같은 출처의 순번이 겹치지 않는다(DB 보장). 경쟁 구간이 AI 응답 시간에서 저장 트랜잭션 길이로 줄어 충돌 자체가 드물어진다.
- 감수하는 것: ① 마이그레이션 1개와 기존 중복 행 재번호(현재 순번을 결과로 읽는 기능이 없어 화면 영향 없음 — 같은 시각 정렬 순서만 영향). ② 예시만 있는 아이의 첫 실제 순번이 9 → 1로 바뀜. ③ 저장소 포트 변경. ④ 정상 상황 슬롯을 켤 때(T-34·T-35) 출제 전 슬롯 판단과 저장 때 순번 확정 사이의 불일치 처리 규칙을 그때 정해야 한다 — 이 ADR은 정하지 않는다(설계 리스크로 기록).
- 바뀌지 않는 것: ADR-0009의 슬롯 식(`draw_index mod 10 ∈ {4,7,0}`), 다시 도전 NULL, 예시 적재·재연결 규칙(T-97), 공개 API·오류 코드.
