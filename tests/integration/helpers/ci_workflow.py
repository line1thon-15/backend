"""CI 워크플로 텍스트에서 job 수준 `env`를 읽는다 (T-101 reviewer 권고 2).

yaml 라이브러리를 의존성에 두지 않으므로 이 저장소 ci.yml이 쓰는 블록 형식(`KEY: value` 한 줄씩)만 읽는다.
흐름 매핑(`env: {A: b}`)처럼 읽지 못하는 형식은 조용히 빈 값으로 넘기지 않고 문제로 보고한다.
"""

import re

from tests.integration.helpers.postgres_guard import REQUIRE_ENV, TRUTHY, URL_ENV

POSTGRES_JOB = "pytest-postgres"
_KEY_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


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
    return {key: _scalar(value) for key, value, _ in _child_keys(_block(job_block, env_entry[1]))}


def ci_postgres_env_problems(ci_text: str) -> list[str]:
    """PostgreSQL job이 가드를 켜는지: `REQUIRE_TEST_POSTGRES`가 TRUTHY, `TEST_POSTGRES_URL`이 비어 있지 않음."""
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
    return problems
