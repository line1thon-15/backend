"""PostgreSQL 통합 테스트 접속 URL 결정·스키마 초기화 안전장치 (T-99 ⑧ → T-101 ①②).

`test_postgres_constraints.py`의 fixture가 쓴다. 실제 PostgreSQL 없이 단위 검증한다(`test_postgres_guard.py`).

이 가드는 실수 방지용이지 완전 차단이 아니다 (팀 리뷰 P3). SSH 터널 등으로 `localhost`에 붙은 운영 DB가 허용 접미사
(`_ci`·`_test`)로 끝나는 이름이고 `CI=true`까지 맞으면 통과한다. 그래서 운용 규칙을 함께 지킨다:
- 스키마 삭제(`DROP SCHEMA public CASCADE`) 테스트는 일회용 CI PostgreSQL 컨테이너 — `.github/workflows/ci.yml`
  job `pytest-postgres`의 `postgres` 서비스(전용 계정 `ci`, DB `line1thon_ci`) — 에서만 실행한다.
- 운영·공유 DB URL을 `TEST_POSTGRES_URL`에 넣지 않는다.
- libpq 서비스 환경 변수 `PGSERVICE`·`PGSERVICEFILE`이 비어 있지 않게 설정된 실행은 URL 확정·스키마 삭제 전에 중단한다.
"""

from collections.abc import Callable, Mapping

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

URL_ENV = "TEST_POSTGRES_URL"
REQUIRE_ENV = "REQUIRE_TEST_POSTGRES"
ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
# 일회용 DB 이름 접미사 — CI 서비스 컨테이너 DB는 `line1thon_ci`(.github/workflows/ci.yml)
DISPOSABLE_DB_SUFFIXES = ("_ci", "_test")
TRUTHY = {"1", "true", "yes"}
# URL 쿼리로 넘어가면 libpq 접속 대상을 바꾸는 키 (T-101 reviewer 권고 1). SQLAlchemy psycopg 방언은 쿼리 `host`로
# URL 호스트를 덮어쓰고 나머지는 그대로 접속 인자로 넘긴다 — 호스트·DB 이름 검사를 우회하므로 값과 무관하게 거부한다.
# service·servicefile: 서비스 파일 항목이 host·dbname을 정한다. dbname: URL 경로의 DB 이름 대신 쓰인다.
# port·user·passfile·options(T-101 재리뷰 권고 2): 같은 localhost의 다른 터널 포트·다른 계정·비밀번호 파일·
# 서버 설정(search_path 등)으로 향하게 한다.
QUERY_TARGET_KEYS = {"host", "hostaddr", "service", "servicefile", "dbname", "port", "user", "passfile", "options"}
# URL 밖(환경 변수)에서 서비스 파일 항목으로 libpq 접속 인자를 채우는 변수 — 사용자 지시 원문 "PGSERVICE도 T-101에서 막아"
SERVICE_ENV_VARS = ("PGSERVICE", "PGSERVICEFILE")


def _flag(environ: Mapping[str, str], name: str) -> bool:
    return environ.get(name, "").strip().lower() in TRUTHY


def checked_postgres_url(raw: str) -> str:
    """로컬 PostgreSQL URL만 통과. 아니면 pytest 실패(운영·외부 DB 보호)."""
    url = make_url(raw)
    if not url.drivername.startswith("postgresql"):
        pytest.fail(f"{URL_ENV}는 postgresql URL이어야 한다", pytrace=False)
    if url.host not in ALLOWED_HOSTS:
        pytest.fail(f"{URL_ENV} 호스트는 localhost·127.0.0.1만 허용 (운영·외부 DB 보호)", pytrace=False)
    target_keys = sorted(key for key in url.query if key.lower() in QUERY_TARGET_KEYS)
    if target_keys:
        pytest.fail(
            f"{URL_ENV} 쿼리에 접속 대상·계정을 바꾸는 키({', '.join(target_keys)})를 쓸 수 없다 (호스트·DB 이름 검사 우회 방지)",
            pytrace=False,
        )
    return raw


def check_no_service_env(environ: Mapping[str, str]) -> None:
    """`PGSERVICE`·`PGSERVICEFILE`이 비어 있지 않게 설정돼 있으면 pytest 실패(엔진 생성 전).

    빈 문자열("")만 미설정으로 본다 — 공백만 있어도 libpq는 그 이름으로 서비스를 찾으므로 막는다.
    """
    present = [name for name in SERVICE_ENV_VARS if environ.get(name, "") != ""]
    if present:
        pytest.fail(
            f"libpq 서비스 환경 변수({', '.join(present)})가 설정된 실행에서는 PostgreSQL 테스트를 하지 않는다 "
            "(URL 밖에서 접속 인자를 채우는 경로 차단)",
            pytrace=False,
        )


def resolve_postgres_url(environ: Mapping[str, str]) -> str:
    """접속 URL. 없으면 로컬은 skip, `REQUIRE_TEST_POSTGRES`가 켜진 실행(CI job pytest-postgres)은 실패.

    `CI`만으로 실패시키지 않는 이유: 같은 CI의 SQLite job(`python -m pytest`)도 `CI=true`이고 postgres 테스트를
    수집해 skip해야 한다 — 그 job까지 깨지 않도록 PostgreSQL job에만 전용 변수를 둔다.
    """
    raw = environ.get(URL_ENV, "").strip()
    if not raw:
        if _flag(environ, REQUIRE_ENV):
            pytest.fail(f"{URL_ENV} 미설정 — {REQUIRE_ENV}가 켜진 실행에서는 skip하지 않는다", pytrace=False)
        pytest.skip(f"{URL_ENV} 미설정")
    check_no_service_env(environ)
    return checked_postgres_url(raw)


def check_schema_reset_allowed(raw: str, environ: Mapping[str, str]) -> None:
    """`DROP SCHEMA public CASCADE` 전 확인: 로컬 호스트(쿼리 접속 대상 키 없음) + 일회용 DB 이름 + CI 환경
    + `PGSERVICE`·`PGSERVICEFILE` 미설정. 어긋나면 pytest 실패.

    호스트 검사만으로는 SSH 터널 등으로 localhost에 붙은 운영 DB를 막지 못한다(T-99 리뷰 권고 B) — DB 이름·CI 확인을
    더했지만 이것도 실수 방지용이지 완전 차단이 아니다(팀 리뷰 P3): 터널 너머 운영 DB 이름이 `_ci`·`_test`로 끝나고
    `CI=true`면 통과한다. 이 확인을 거치는 테스트는 일회용 CI PostgreSQL 컨테이너(ci.yml `pytest-postgres`의
    `postgres` 서비스, 전용 계정 `ci`)에서만 실행하고, 운영·공유 DB URL을 `TEST_POSTGRES_URL`에 넣지 않는다.
    """
    check_no_service_env(environ)
    url = make_url(checked_postgres_url(raw))
    if not (url.database or "").endswith(DISPOSABLE_DB_SUFFIXES):
        pytest.fail(
            f"{URL_ENV}의 DB 이름은 {'·'.join(DISPOSABLE_DB_SUFFIXES)}로 끝나야 한다 (일회용 DB만 스키마 삭제)",
            pytrace=False,
        )
    if not _flag(environ, "CI"):
        pytest.fail("CI 환경(CI=true)이 아니면 public 스키마를 삭제하지 않는다", pytrace=False)


def reset_public_schema(raw: str, environ: Mapping[str, str], engine_factory: Callable = create_engine):
    """확인을 통과한 경우에만 엔진을 만들고 public 스키마를 비운다. 확인 실패 시 연결도 하지 않는다.

    확인은 실수 방지용이다(`check_schema_reset_allowed` 참조) — 일회용 CI PostgreSQL 컨테이너(ci.yml `pytest-postgres`의
    `postgres` 서비스, 전용 계정 `ci`)에서만 호출되게 하고, 운영·공유 DB URL을 `TEST_POSTGRES_URL`에 넣지 않는다.
    """
    check_schema_reset_allowed(raw, environ)
    engine = engine_factory(raw)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    return engine
