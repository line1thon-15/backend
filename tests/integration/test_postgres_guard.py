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
