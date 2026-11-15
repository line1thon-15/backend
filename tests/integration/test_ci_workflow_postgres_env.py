"""CI 워크플로의 PostgreSQL job 환경 변수 확인 (T-101 reviewer 권고 2).

`REQUIRE_TEST_POSTGRES` 이름·값이 ci.yml에서 틀리면 가드가 조용히 꺼진다(URL 누락 시 실패 대신 skip).
`postgres` 마커가 없어 기본(SQLite) 실행에서도 돈다. yaml 라이브러리를 의존성에 두지 않으므로 텍스트로 읽는다.
"""

from pathlib import Path

import pytest

from tests.integration.helpers.ci_workflow import ci_postgres_env_problems, job_env
from tests.integration.helpers.postgres_guard import (
    LIBPQ_TARGET_ENV_VARS,
    REQUIRE_ENV,
    URL_ENV,
    check_schema_reset_allowed,
)

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


# ---- 가짜 ci 텍스트: 텍스트 파서가 값을 확정할 수 없는 형식 (T-101 재리뷰 권고 1) ---------------
# 블록 스칼라(`>`·`|` 계열)는 값이 다음 줄에 있고, 앵커·별칭·태그는 값이 다른 곳에 있거나 형이 바뀐다.
# 이 파서는 그 값을 읽지 못하므로 표시자 문자를 값으로 오인해 "비어 있지 않음"으로 통과시키지 말고 문제로 보고한다.

UNRESOLVABLE_VALUE_FORMS = [">", "|", ">-", "|-", "|+", ">2", "&url postgresql+psycopg://x", "*url", "!!str value"]


@pytest.mark.parametrize("form", UNRESOLVABLE_VALUE_FORMS)
def test_fake_ci_url_in_unresolvable_form_is_reported(form):
    text = _fake(
        "      TEST_POSTGRES_URL: postgresql+psycopg://ci:pw@localhost:5432/line1thon_ci\n",
        f"      TEST_POSTGRES_URL: {form}\n        postgresql+psycopg://ci:pw@localhost:5432/line1thon_ci\n",
    )

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and URL_ENV in problems[0], problems


def test_fake_ci_empty_block_scalar_url_is_reported():
    # 재현(재리뷰 원문): "TEST_POSTGRES_URL: > 변형으로 ci_postgres_env_problems 실행 시 [] 반환" — 내용이 비어도 통과하던 미탐
    text = _fake("TEST_POSTGRES_URL: postgresql+psycopg://ci:pw@localhost:5432/line1thon_ci", "TEST_POSTGRES_URL: >")

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and URL_ENV in problems[0], problems


@pytest.mark.parametrize("form", ["|-", "*flag"])
def test_fake_ci_require_flag_in_unresolvable_form_is_reported(form):
    text = _fake('      REQUIRE_TEST_POSTGRES: "1"\n', f'      REQUIRE_TEST_POSTGRES: {form}\n        "1"\n')

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and REQUIRE_ENV in problems[0], problems


@pytest.mark.parametrize("value", ["'>'", '"|"', "'*url'"])
def test_fake_ci_quoted_indicator_characters_are_plain_values(value):
    # 따옴표 안의 표시자 문자는 일반 문자열이다 — 형식 오류로 보고하지 않는다 (과잉 보고 방지)
    text = _fake('AI_CLIENT: fake\n      TEST_POSTGRES_URL', f"AI_CLIENT: {value}\n      TEST_POSTGRES_URL")

    assert ci_postgres_env_problems(text) == []


# ---- 가짜 ci 텍스트: pytest-postgres job env의 libpq 접속 대상 변수 (T-101 리뷰 권고 3) ---------------------
# 가드는 이 변수들이 비어 있지 않은 값으로 설정된 실행을 런타임에 실패시킨다 — CI 설정 단계에서 정적으로 먼저 잡는다
# (빈 값 키도 보수적으로 보고).
# 목록은 가드 상수(LIBPQ_TARGET_ENV_VARS)와 같아야 한다 — 아래 상수 대조 테스트가 드리프트를 잡는다.
CI_BLOCKED_LIBPQ_ENV = ["PGSERVICE", "PGSERVICEFILE", "PGHOSTADDR", "PGPORT", "PGOPTIONS", "PGPASSFILE"]
POSTGRES_JOB_ENV_LINE = "      AI_CLIENT: fake\n      TEST_POSTGRES_URL"


def test_ci_blocked_list_matches_guard_constant():
    assert sorted(CI_BLOCKED_LIBPQ_ENV) == sorted(LIBPQ_TARGET_ENV_VARS)


@pytest.mark.parametrize("name", CI_BLOCKED_LIBPQ_ENV)
@pytest.mark.parametrize("value", ["x", '""'])  # 빈 값도 키가 있으면 보고 — job env에 둘 이유가 없다
def test_fake_ci_libpq_target_env_in_postgres_job_is_reported(name, value):
    text = _fake(POSTGRES_JOB_ENV_LINE, f"      AI_CLIENT: fake\n      {name}: {value}\n      TEST_POSTGRES_URL")

    problems = ci_postgres_env_problems(text)

    assert len(problems) == 1 and name in problems[0], problems


def test_fake_ci_libpq_target_env_outside_postgres_job_env_is_not_reported():
    # 다른 job(SQLite pytest)의 env, 서비스 컨테이너 env는 pytest-postgres 프로세스에 전달되지 않는다
    text = _fake(
        "      AI_CLIENT: fake\n    steps:\n      - run: python -m pytest\n",
        '      AI_CLIENT: fake\n      PGPORT: "6543"\n    steps:\n      - run: python -m pytest\n',
    ).replace("          POSTGRES_DB: line1thon_ci\n", '          POSTGRES_DB: line1thon_ci\n          PGPORT: "5432"\n')
    assert 'PGPORT: "6543"' in text and 'PGPORT: "5432"' in text  # 치환이 실제로 일어났는지

    assert ci_postgres_env_problems(text) == []


def test_fake_ci_unblocked_libpq_env_in_postgres_job_is_not_reported():
    # 가드가 막지 않는 변수(URL 명시값이 우선)는 보고하지 않는다
    text = _fake(POSTGRES_JOB_ENV_LINE, "      AI_CLIENT: fake\n      PGHOST: db\n      PGUSER: ci\n      TEST_POSTGRES_URL")

    assert ci_postgres_env_problems(text) == []
