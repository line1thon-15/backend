# ADR-0005: 저장소 — PostgreSQL + SQLAlchemy/Alembic, 테스트 SQLite

> 상태: 제안 (docs/Architecture.md 초안과 함께 사용자 승인 대기, 패키지 설치 허용 확인 필요). 승인된 ADR은 수정하지 않는다 — 뒤집으려면 새 ADR로 대체.
> 날짜: 2026-11-06

## 맥락

- N-07 배포 형태 사용자 선택 원문 "Vercel + PaaS + 관리형 DB (Recommended)" — 관리형 DB 사용.
- 데이터: 보호자·아이·세션·연습 세션·턴·단서 결과·보호자 알림(Architecture.md 엔티티 표). 관계형(보호자 1 : 아이 N : 연습 N)이며 인가 쿼리가 "보호자 ID + 아이 ID" 조인 중심.
- Docker 없음 → 로컬 Postgres 컨테이너·testcontainers 불가(실행환경 확인, 인용). 로컬 Postgres 설치 여부 미확인.

## 검토한 대안

| 대안 | 장점 | 단점 |
|---|---|---|
| A. 운영 관리형 PostgreSQL + SQLAlchemy 2.x + Alembic, 테스트·로컬은 SQLite | 관계형 인가 쿼리에 적합. ORM 공통 타입으로 두 DB 지원. SQLite는 Python 내장이라 설치 없이 테스트 가능 | 방언 차이로 운영에서만 드러나는 오류 가능(Architecture.md D-2) |
| B. 모든 환경 PostgreSQL | 방언 차이 없음 | 팀원 6명 각자 로컬 Postgres 설치 필요(Docker 없음), 테스트 격리 복잡 |
| C. 운영도 SQLite(PaaS 영구 디스크) | 가장 단순 | 사용자 선택 "관리형 DB"와 어긋남, PaaS 재배포·인스턴스 교체 시 데이터 유실 위험 |
| D. 문서형 DB(예: Firestore·MongoDB) | 스키마 유연 | 소유 관계 인가 쿼리·집계(성장 지표)가 번거로움, 사용자 선택과 거리 |

## 결정

A를 선택한다. 결정적 이유: 사용자 선택(관리형 DB)을 지키면서 Docker 없는 환경에서도 설치 없이 테스트를 돌릴 수 있다.

규칙: ORM 공통 타입(`Uuid`, `JSON`, `DateTime(timezone=True)`, `Enum`)만 쓰고 Postgres 전용 기능(배열 타입, `JSONB` 연산자, 부분 인덱스 등)은 1차에서 쓰지 않는다. 드라이버는 Postgres `psycopg`(v3), SQLite 내장. 스키마 변경은 Alembic 마이그레이션으로만.

## 결과 (트레이드오프 포함)

- 얻는 것: 설치 없는 테스트 DB, 운영의 관리형 백업·가용성(서비스별 — [A-2]).
- 감수하는 것: 방언 차이 위험 — T-27·T-28에서 운영 DB로 시연 흐름을 확인해 보완. 구체 관리형 Postgres 서비스는 ADR-0007에서 사용자 확인.
