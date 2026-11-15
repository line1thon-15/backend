"""PostgreSQL 통합 테스트 접속 URL 결정·스키마 초기화 안전장치 (T-99 ⑧ → T-101 ①②).

`test_postgres_constraints.py`의 fixture가 쓴다. 실제 PostgreSQL 없이 단위 검증한다(`test_postgres_guard.py`).
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


def _flag(environ: Mapping[str, str], name: str) -> bool:
    return environ.get(name, "").strip().lower() in TRUTHY


def checked_postgres_url(raw: str) -> str:
    """로컬 PostgreSQL URL만 통과. 아니면 pytest 실패(운영·외부 DB 보호)."""
    url = make_url(raw)
    if not url.drivername.startswith("postgresql"):
        pytest.fail(f"{URL_ENV}는 postgresql URL이어야 한다", pytrace=False)
    if url.host not in ALLOWED_HOSTS:
        pytest.fail(f"{URL_ENV} 호스트는 localhost·127.0.0.1만 허용 (운영·외부 DB 보호)", pytrace=False)
    return raw


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
    return checked_postgres_url(raw)


def check_schema_reset_allowed(raw: str, environ: Mapping[str, str]) -> None:
    """`DROP SCHEMA public CASCADE` 전 확인: 로컬 호스트 + 일회용 DB 이름 + CI 환경. 어긋나면 pytest 실패.

    호스트 검사만으로는 SSH 터널 등으로 localhost에 붙은 운영 DB를 막지 못한다(T-99 리뷰 권고 B).
    """
    url = make_url(checked_postgres_url(raw))
    if not (url.database or "").endswith(DISPOSABLE_DB_SUFFIXES):
        pytest.fail(
            f"{URL_ENV}의 DB 이름은 {'·'.join(DISPOSABLE_DB_SUFFIXES)}로 끝나야 한다 (일회용 DB만 스키마 삭제)",
            pytrace=False,
        )
    if not _flag(environ, "CI"):
        pytest.fail("CI 환경(CI=true)이 아니면 public 스키마를 삭제하지 않는다", pytrace=False)


def reset_public_schema(raw: str, environ: Mapping[str, str], engine_factory: Callable = create_engine):
    """확인을 통과한 경우에만 엔진을 만들고 public 스키마를 비운다. 확인 실패 시 연결도 하지 않는다."""
    check_schema_reset_allowed(raw, environ)
    engine = engine_factory(raw)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    return engine
