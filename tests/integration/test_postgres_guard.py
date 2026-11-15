"""PostgreSQL 통합 테스트 안전장치 (T-101 ①② — T-99 리뷰 권고 A·B).

실제 PostgreSQL 없이 검증한다 — 이 파일은 `postgres` 마커가 없어 기본(SQLite) 실행에서 돈다.
- ① URL 결정: `TEST_POSTGRES_URL`이 없을 때 로컬은 skip, CI 전용 변수 `REQUIRE_TEST_POSTGRES`가 켜져 있으면 실패.
- ② 스키마 초기화: `DROP SCHEMA public CASCADE` 전에 호스트·DB 이름·CI 환경을 모두 확인하고, 하나라도
  어긋나면 엔진을 만들지도 않고(=연결·삭제 없이) 중단한다.
"""

import re
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from tests.integration.helpers.postgres_guard import (
    REQUIRE_ENV,
    URL_ENV,
    reset_public_schema,
    resolve_postgres_url,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_CI_URL = "postgresql+psycopg://ci:pw@localhost:5432/line1thon_ci"


# ---- ① URL 결정 ---------------------------------------------------------------------------
# skip을 pytest.raises로 받으면 회귀 시 skip이 그대로 새어 나가 "통과 아닌 skip"이 된다 — 결과를 값으로 바꿔 단언한다.


def _outcome(environ: dict[str, str]) -> tuple[str, str]:
    try:
        return "url", resolve_postgres_url(environ)
    except pytest.skip.Exception as exc:
        return "skip", str(exc)
    except pytest.fail.Exception as exc:
        return "fail", str(exc)


def test_url_present_is_returned():
    assert _outcome({URL_ENV: f"  {LOCAL_CI_URL} "}) == ("url", LOCAL_CI_URL)


def test_url_missing_locally_skips():
    assert _outcome({}) == ("skip", f"{URL_ENV} 미설정")


@pytest.mark.parametrize("flag", ["0", "false", "", "no"])
def test_url_missing_with_require_flag_off_still_skips(flag):
    assert _outcome({REQUIRE_ENV: flag, "CI": "true"})[0] == "skip"


@pytest.mark.parametrize("flag", ["1", "true", "TRUE", " yes "])
def test_url_missing_with_require_flag_fails(flag):
    kind, message = _outcome({REQUIRE_ENV: flag})
    assert kind == "fail"
    assert URL_ENV in message and REQUIRE_ENV in message


def test_url_blank_with_require_flag_fails():
    assert _outcome({URL_ENV: "   ", REQUIRE_ENV: "1"})[0] == "fail"


def test_url_non_local_with_require_flag_fails():
    remote = "postgresql+psycopg://u:p@db.example.com:5432/line1thon_ci"
    assert _outcome({URL_ENV: remote, REQUIRE_ENV: "1"})[0] == "fail"


# ---- ① 실제 pytest 프로세스 종료 코드 ---------------------------------------------------------


def _run_postgres_suite(tmp_path, extra_env: dict[str, str]) -> subprocess.CompletedProcess:
    import os

    env = {k: v for k, v in os.environ.items() if k not in (URL_ENV, REQUIRE_ENV)}
    env.update(extra_env)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "postgres",
            "-q",
            "-p",
            "no:cacheprovider",
            f"--basetemp={tmp_path / 'inner'}",
            "tests/integration/test_postgres_constraints.py",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _summary_line(stdout: str) -> str:
    lines = [line for line in stdout.splitlines() if re.search(r"\d+ (passed|failed|skipped|errors?)", line)]
    return lines[-1] if lines else ""


def test_ci_run_without_url_exits_nonzero(tmp_path):
    result = _run_postgres_suite(tmp_path, {"CI": "true", REQUIRE_ENV: "1"})

    summary = _summary_line(result.stdout)
    assert result.returncode not in (0, 5), result.stdout[-2000:]
    assert "error" in summary and "skipped" not in summary and "passed" not in summary, summary


def test_local_run_without_url_still_skips_with_exit_zero(tmp_path):
    result = _run_postgres_suite(tmp_path, {})

    summary = _summary_line(result.stdout)
    assert result.returncode == 0, result.stdout[-2000:]
    assert "skipped" in summary and "passed" not in summary and "error" not in summary, summary


# ---- ② DROP SCHEMA 전 보호 --------------------------------------------------------------------


class RecordingEngine:
    def __init__(self) -> None:
        self.statements: list[str] = []

    @contextmanager
    def begin(self):
        engine = self

        class Conn:
            def execute(self, statement):
                engine.statements.append(str(statement))

        yield Conn()


class RecordingFactory:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.engine = RecordingEngine()

    def __call__(self, url: str) -> RecordingEngine:
        self.calls.append(url)
        return self.engine


def test_reset_drops_and_recreates_public_schema_when_all_conditions_hold():
    factory = RecordingFactory()

    engine = reset_public_schema(LOCAL_CI_URL, {"CI": "true"}, engine_factory=factory)

    assert engine is factory.engine
    assert factory.calls == [LOCAL_CI_URL]
    assert factory.engine.statements == ["DROP SCHEMA IF EXISTS public CASCADE", "CREATE SCHEMA public"]


@pytest.mark.parametrize("db_name", ["app_test", "line1thon_ci"])
def test_reset_accepts_disposable_db_name_suffixes(db_name):
    factory = RecordingFactory()

    reset_public_schema(f"postgresql+psycopg://u:p@127.0.0.1:5432/{db_name}", {"CI": "1"}, engine_factory=factory)

    assert len(factory.calls) == 1


@pytest.mark.parametrize("ci_value", [None, "", "false", "0"])
def test_reset_outside_ci_is_refused_without_connecting(ci_value):
    factory = RecordingFactory()
    environ = {} if ci_value is None else {"CI": ci_value}

    with pytest.raises(pytest.fail.Exception, match="CI"):
        reset_public_schema(LOCAL_CI_URL, environ, engine_factory=factory)

    assert factory.calls == []
    assert factory.engine.statements == []


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://u:p@localhost:5432/neondb",  # 운영형 이름
        "postgresql+psycopg://u:p@localhost:5432/postgres",
        "postgresql+psycopg://u:p@localhost:5432/line1thon_ci_backup",  # 접미사가 끝이 아님
        "postgresql+psycopg://u:p@localhost:5432",  # DB 이름 없음
    ],
)
def test_reset_with_non_disposable_db_name_is_refused_without_connecting(url):
    factory = RecordingFactory()

    with pytest.raises(pytest.fail.Exception, match="DB 이름"):
        reset_public_schema(url, {"CI": "true"}, engine_factory=factory)

    assert factory.calls == []
    assert factory.engine.statements == []


def test_reset_with_non_local_host_is_refused_without_connecting():
    # SSH 터널이 아닌 원격 호스트 — 기존 호스트 검사도 그대로 먼저 막는다
    factory = RecordingFactory()

    with pytest.raises(pytest.fail.Exception):
        reset_public_schema("postgresql+psycopg://u:p@db.example.com:5432/line1thon_ci", {"CI": "true"}, factory)

    assert factory.calls == []


# ---- 쿼리 문자열의 접속 대상 키 (T-101 reviewer 권고 1) ---------------------------------------
# `url.host`가 localhost여도 SQLAlchemy psycopg 방언은 쿼리 `host`로 덮어쓰고, `hostaddr`·`service`·`dbname`은
# 그대로 libpq 접속 인자로 넘긴다 — 호스트·DB 이름 검사를 우회해 다른 DB에 닿을 수 있으므로 거부한다.

QUERY_TARGET_BYPASS_URLS = [
    f"{LOCAL_CI_URL}?host=prod.example.com",
    f"{LOCAL_CI_URL}?hostaddr=203.0.113.5",
    f"{LOCAL_CI_URL}?service=prod",
    f"{LOCAL_CI_URL}?servicefile=/tmp/pg_service.conf",
    f"{LOCAL_CI_URL}?dbname=neondb",
    f"{LOCAL_CI_URL}?sslmode=disable&HOST=prod.example.com",  # 대소문자 무관
    f"{LOCAL_CI_URL}?host=localhost",  # 값이 로컬이어도 쿼리 접속 대상 키 자체를 거부
    # 재리뷰 권고 2: 같은 localhost의 다른 터널 포트·다른 계정·접속 설정으로 향할 수 있는 키
    f"{LOCAL_CI_URL}?port=6543",
    f"{LOCAL_CI_URL}?user=admin",
    f"{LOCAL_CI_URL}?passfile=/tmp/pgpass",
    f"{LOCAL_CI_URL}?options=-csearch_path%3Dprod",
    f"{LOCAL_CI_URL}?sslmode=disable&Port=6543",  # 대소문자 무관
]


@pytest.mark.parametrize("url", QUERY_TARGET_BYPASS_URLS)
def test_url_with_query_connection_target_fails(url):
    kind, message = _outcome({URL_ENV: url, REQUIRE_ENV: "1"})

    assert kind == "fail"
    assert "쿼리" in message


@pytest.mark.parametrize("url", QUERY_TARGET_BYPASS_URLS)
def test_reset_with_query_connection_target_is_refused_without_connecting(url):
    factory = RecordingFactory()

    with pytest.raises(pytest.fail.Exception, match="쿼리"):
        reset_public_schema(url, {"CI": "true"}, engine_factory=factory)

    assert factory.calls == []
    assert factory.engine.statements == []


def test_url_with_unrelated_query_options_is_accepted():
    # 접속 대상과 무관한 옵션까지 막지는 않는다 (과잉 차단 방지)
    url = f"{LOCAL_CI_URL}?sslmode=disable&connect_timeout=5"
    factory = RecordingFactory()

    assert _outcome({URL_ENV: url}) == ("url", url)
    reset_public_schema(url, {"CI": "true"}, engine_factory=factory)
    assert factory.calls == [url]


# ---- libpq 서비스 환경 변수 PGSERVICE·PGSERVICEFILE (T-101 — 사용자 지시 원문 "PGSERVICE도 T-101에서 막아") ----
# 서비스 파일 항목은 URL 밖에서 libpq 접속 인자(호스트·DB·계정·sslmode 등)를 채운다 — 값이 비어 있지 않으면 엔진 생성 전에
# 중단한다. URL이 없고 REQUIRE도 꺼진 로컬 실행은 연결 자체를 하지 않으므로 기존대로 skip한다.
# 차단 범위는 사용자 지시대로 PGSERVICE·PGSERVICEFILE 두 개뿐이다 — PGHOST 등 다른 PG* 변수는 막지 않는다.

SERVICE_ENV_CASES = [
    {"PGSERVICE": "prod"},
    {"PGSERVICEFILE": "/tmp/pg_service.conf"},
    {"PGSERVICE": "prod", "PGSERVICEFILE": "/tmp/pg_service.conf"},
    {"PGSERVICE": " "},  # 공백만 있어도 비어 있지 않다 — libpq는 그 이름으로 서비스를 찾는다
]


@pytest.mark.parametrize("service_env", SERVICE_ENV_CASES)
def test_url_with_libpq_service_env_fails(service_env):
    kind, message = _outcome({URL_ENV: LOCAL_CI_URL, REQUIRE_ENV: "1", **service_env})

    assert kind == "fail"
    assert all(name in message for name in service_env), message


@pytest.mark.parametrize("service_env", SERVICE_ENV_CASES)
def test_reset_with_libpq_service_env_is_refused_without_connecting(service_env):
    factory = RecordingFactory()

    with pytest.raises(pytest.fail.Exception, match="PGSERVICE"):
        reset_public_schema(LOCAL_CI_URL, {"CI": "true", **service_env}, engine_factory=factory)

    assert factory.calls == []
    assert factory.engine.statements == []


def test_url_missing_locally_still_skips_with_service_env():
    # 로컬 skip 경로는 연결하지 않으므로 서비스 변수가 있어도 결과를 바꾸지 않는다
    assert _outcome({"PGSERVICE": "prod", "PGSERVICEFILE": "/tmp/pg_service.conf"}) == ("skip", f"{URL_ENV} 미설정")


def test_empty_service_env_is_not_refused():
    environ = {"CI": "true", "PGSERVICE": "", "PGSERVICEFILE": ""}
    factory = RecordingFactory()

    assert _outcome({URL_ENV: LOCAL_CI_URL, **environ}) == ("url", LOCAL_CI_URL)
    reset_public_schema(LOCAL_CI_URL, environ, engine_factory=factory)
    assert factory.calls == [LOCAL_CI_URL]


def test_other_libpq_env_is_not_refused():
    # 사용자 지시 범위 밖 — PGHOST 등은 막지 않는다 (URL에 명시한 값이 우선하는지는 보고서에 따로 기록)
    environ = {"CI": "true", "PGHOST": "prod.example.com", "PGDATABASE": "neondb", "PGPORT": "6543"}
    factory = RecordingFactory()

    assert _outcome({URL_ENV: LOCAL_CI_URL, **environ}) == ("url", LOCAL_CI_URL)
    reset_public_schema(LOCAL_CI_URL, environ, engine_factory=factory)
    assert factory.calls == [LOCAL_CI_URL]
