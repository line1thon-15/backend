"""CI 워크플로의 PostgreSQL job 환경 변수 확인 (T-101 reviewer 권고 2).

`REQUIRE_TEST_POSTGRES` 이름·값이 ci.yml에서 틀리면 가드가 조용히 꺼진다(URL 누락 시 실패 대신 skip).
`postgres` 마커가 없어 기본(SQLite) 실행에서도 돈다. yaml 라이브러리를 의존성에 두지 않으므로 텍스트로 읽는다.
"""

from pathlib import Path

import pytest

from tests.integration.helpers.ci_workflow import ci_postgres_env_problems, job_env
from tests.integration.helpers.postgres_guard import REQUIRE_ENV, URL_ENV, check_schema_reset_allowed

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"

FAKE_CI = """\
name: backend-ci

jobs:
  pytest:
    runs-on: ubuntu-latest
    env:
      AI_CLIENT: fake
    steps:
      - run: python -m pytest

  pytest-postgres:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_DB: line1thon_ci
    env:
      AI_CLIENT: fake
      TEST_POSTGRES_URL: postgresql+psycopg://ci:pw@localhost:5432/line1thon_ci
      # 설명 주석
      REQUIRE_TEST_POSTGRES: "1"
    steps:
      - run: python -m pytest -m postgres
"""


def _fake(old: str, new: str) -> str:
    assert old in FAKE_CI
    return FAKE_CI.replace(old, new)


# ---- 실제 ci.yml ---------------------------------------------------------------------------


def test_real_ci_postgres_job_env_turns_guard_on():
    text = CI_PATH.read_text(encoding="utf-8")

    assert ci_postgres_env_problems(text) == []


def test_real_ci_postgres_url_passes_schema_reset_guard():
    env = job_env(CI_PATH.read_text(encoding="utf-8"), "pytest-postgres")

    # 이 URL로 실제 CI가 스키마를 초기화한다 — 가드가 CI 자체를 막지 않는지 확인
    check_schema_reset_allowed(env[URL_ENV], {"CI": "true"})


# ---- 가짜 ci 텍스트: 정상·경계 -------------------------------------------------------------


def test_fake_ci_job_env_is_parsed_from_job_level_only():
    assert job_env(FAKE_CI, "pytest-postgres") == {
        "AI_CLIENT": "fake",
        URL_ENV: "postgresql+psycopg://ci:pw@localhost:5432/line1thon_ci",
        REQUIRE_ENV: "1",
    }
    assert job_env(FAKE_CI, "pytest") == {"AI_CLIENT": "fake"}
    assert ci_postgres_env_problems(FAKE_CI) == []


@pytest.mark.parametrize("value", ["true", "'yes'", '"TRUE"', "1  # 켜기"])
def test_fake_ci_truthy_value_forms_are_accepted(value):
    text = _fake('REQUIRE_TEST_POSTGRES: "1"', f"REQUIRE_TEST_POSTGRES: {value}")

    assert ci_postgres_env_problems(text) == []


# ---- 가짜 ci 텍스트: 가드가 꺼지는 실수 ------------------------------------------------------


@pytest.mark.parametrize("value", ['"on"', "on", '"0"', "false", '""'])
def test_fake_ci_require_flag_outside_truthy_is_reported(value):
    text = _fake('REQUIRE_TEST_POSTGRES: "1"', f"REQUIRE_TEST_POSTGRES: {value}")

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and REQUIRE_ENV in problems[0]


def test_fake_ci_require_flag_name_typo_is_reported():
    text = _fake('REQUIRE_TEST_POSTGRES: "1"', 'REQUIRE_TEST_POSTGRESS: "1"')

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and REQUIRE_ENV in problems[0]


def test_fake_ci_require_flag_only_in_service_env_is_reported():
    # 서비스 컨테이너 env에 넣으면 pytest 프로세스에는 전달되지 않는다
    text = _fake('      REQUIRE_TEST_POSTGRES: "1"\n', "").replace(
        "          POSTGRES_DB: line1thon_ci\n",
        '          POSTGRES_DB: line1thon_ci\n          REQUIRE_TEST_POSTGRES: "1"\n',
    )

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and REQUIRE_ENV in problems[0]


def test_fake_ci_url_name_typo_is_reported():
    text = _fake("TEST_POSTGRES_URL:", "TEST_POSTGRESQL_URL:")

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and URL_ENV in problems[0]


def test_fake_ci_missing_postgres_job_is_reported():
    text = _fake("  pytest-postgres:", "  pytest-pg:")

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and "pytest-postgres" in problems[0]
