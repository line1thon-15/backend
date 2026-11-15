"""CI 워크플로 텍스트에서 job 수준 `env`를 읽는다 (T-101 reviewer 권고 2).

yaml 라이브러리를 의존성에 두지 않으므로 이 저장소 ci.yml이 쓰는 블록 형식(`KEY: value` 한 줄씩)만 읽는다.
흐름 매핑(`env: {A: b}`)·블록 스칼라(`>`·`|` 계열)·앵커(`&`)·별칭(`*`)·태그(`!`)처럼 값을 확정할 수 없는 형식은
조용히 빈 값이나 표시자 문자로 넘기지 않고 문제로 보고한다 (T-101 재리뷰 권고 1).
"""

import re

from tests.integration.helpers.postgres_guard import LIBPQ_TARGET_ENV_VARS, REQUIRE_ENV, TRUTHY, URL_ENV

POSTGRES_JOB = "pytest-postgres"
_KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
# 따옴표 없는 값이 이 문자로 시작하면 블록 스칼라(> |)·앵커(&)·별칭(*)·태그(!) — 값이 다른 줄·다른 곳에 있다
_UNRESOLVABLE_PREFIXES = (">", "|", "&", "*", "!")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _block(lines: list[str], start: int) -> list[str]:
    """`lines[start]` 키의 하위 줄(들여쓰기가 더 깊은 줄). 빈 줄·주석 줄은 건너뛴다."""
    parent = _indent(lines[start])
    children = []
    for line in lines[start + 1 :]:
        if not _is_content(line):
            continue
        if _indent(line) <= parent:
            break
        children.append(line)
    return children


def _child_keys(block: list[str]) -> list[tuple[str, str, int]]:
    """블록의 바로 아래 단계 키 목록 (키, 값 원문, 블록 안 위치)."""
    if not block:
        return []
    level = _indent(block[0])
    result = []
    for index, line in enumerate(block):
        if _indent(line) != level:
            continue
        match = _KEY_LINE.match(line.strip())
        if match:
            result.append((match.group(1), match.group(2), index))
    return result


def _scalar(raw: str) -> str:
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        end = raw.find(raw[0], 1)
        return raw[1:end] if end != -1 else raw[1:]
    return raw.split(" #", 1)[0].strip()


class UnsupportedFormat(ValueError):
    pass


def job_env(ci_text: str, job: str) -> dict[str, str] | None:
    """`jobs.<job>.env` (job 수준 — 서비스 컨테이너 env 아님). job이 없으면 None."""
    lines = ci_text.splitlines()
    top = [(i, line) for i, line in enumerate(lines) if _is_content(line) and _indent(line) == 0]
    jobs_index = next((i for i, line in top if line.strip().split("#", 1)[0].strip() == "jobs:"), None)
    if jobs_index is None:
        return None
    jobs_block = _block(lines, jobs_index)
    job_entry = next(((v, i) for k, v, i in _child_keys(jobs_block) if k == job), None)
    if job_entry is None:
        return None
    job_block = _block(jobs_block, job_entry[1])
    env_entry = next(((v, i) for k, v, i in _child_keys(job_block) if k == "env"), None)
    if env_entry is None:
        return {}
    if _scalar(env_entry[0]):
        raise UnsupportedFormat(f"jobs.{job}.env 형식 미지원(블록 매핑만 읽음): {env_entry[0]!r}")
    env = {}
    for key, value, _ in _child_keys(_block(job_block, env_entry[1])):
        if value.strip().startswith(_UNRESOLVABLE_PREFIXES):
            raise UnsupportedFormat(
                f"jobs.{job}.env.{key} 형식 미지원(블록 스칼라·앵커·별칭·태그는 값을 확정할 수 없음): {value!r}"
            )
        env[key] = _scalar(value)
    return env


def ci_postgres_env_problems(ci_text: str) -> list[str]:
    """PostgreSQL job이 가드를 켜는지: `REQUIRE_TEST_POSTGRES`가 TRUTHY, `TEST_POSTGRES_URL`이 비어 있지 않음,
    가드가 차단하는 libpq 변수(`LIBPQ_TARGET_ENV_VARS`)가 job env에 없음 (T-101 리뷰 권고 3 — 런타임 실패 전에 정적으로).
    libpq 변수는 값과 무관하게 키가 있으면 보고한다 — 이 job env에 둘 이유가 없다.
    """
    try:
        env = job_env(ci_text, POSTGRES_JOB)
    except UnsupportedFormat as exc:
        return [str(exc)]
    if env is None:
        return [f"jobs.{POSTGRES_JOB} job이 없다"]
    problems = []
    flag = env.get(REQUIRE_ENV)
    if flag is None or flag.strip().lower() not in TRUTHY:
        problems.append(
            f"jobs.{POSTGRES_JOB}.env.{REQUIRE_ENV}가 {sorted(TRUTHY)} 중 하나여야 한다 (현재: {flag!r}) — "
            "아니면 URL 누락 시 실패 대신 skip된다"
        )
    if not env.get(URL_ENV, "").strip():
        problems.append(f"jobs.{POSTGRES_JOB}.env.{URL_ENV}가 설정돼 있어야 한다")
    for name in LIBPQ_TARGET_ENV_VARS:
        if name in env:
            problems.append(
                f"jobs.{POSTGRES_JOB}.env.{name}가 있으면 안 된다 — 값이 비어 있지 않으면 가드가 PostgreSQL 테스트를 실패시킨다"
                "(URL 밖 접속 인자 차단). 빈 값도 둘 이유가 없어 보수적으로 보고한다"
            )
    return problems
