"""import 경계 테스트 (DECISIONS #44, Architecture "계층 규칙").

① 백엔드 어디에도 AI 제공사 SDK import 없음
② httpx import는 app/ai_client/http_client.py만
③ app/services는 app.ai_client 중 app.ai_client.ports만 import
④ app/domain은 fastapi·sqlalchemy를 import하지 않음
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

PROVIDER_SDK_PREFIXES = (
    "google.genai",
    "google.generativeai",
    "vertexai",
    "openai",
    "anthropic",
)
HTTPX_ALLOWED_FILE = "app/ai_client/http_client.py"
DOMAIN_FORBIDDEN_PREFIXES = ("fastapi", "sqlalchemy")


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def imported_refs(source: str, rel_path: str) -> list[str]:
    """파일의 import 대상 절대 이름 목록.

    `import X` → X, `from B import n` → B.n (상대 import는 파일 위치로 B를 풀어 쓴다).
    """
    package = rel_path[: -len(".py")].split("/")[:-1]
    refs: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            refs.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = package[: len(package) - (node.level - 1)]
                base = ".".join(base_parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            for alias in node.names:
                refs.append(base if alias.name == "*" else f"{base}.{alias.name}")
    return refs


def find_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted((root / "app").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        for ref in imported_refs(path.read_text(encoding="utf-8"), rel):
            if any(_matches(ref, prefix) for prefix in PROVIDER_SDK_PREFIXES):
                violations.append(f"① {rel}: AI 제공사 SDK import {ref}")
            if _matches(ref, "httpx") and rel != HTTPX_ALLOWED_FILE:
                violations.append(f"② {rel}: httpx import는 {HTTPX_ALLOWED_FILE}만 허용 ({ref})")
            if (
                rel.startswith("app/services/")
                and _matches(ref, "app.ai_client")
                and not _matches(ref, "app.ai_client.ports")
            ):
                violations.append(f"③ {rel}: services는 app.ai_client.ports만 import ({ref})")
            if rel.startswith("app/domain/") and any(
                _matches(ref, prefix) for prefix in DOMAIN_FORBIDDEN_PREFIXES
            ):
                violations.append(f"④ {rel}: domain이 {ref} import")
    return violations


def _write(root: Path, rel: str, source: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_real_backend_tree_has_no_import_boundary_violations():
    scanned = {p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "app").rglob("*.py")}

    assert "app/main.py" in scanned
    assert "app/ai_client/ports.py" in scanned
    assert "app/ai_client/fake.py" in scanned
    assert "app/ai_client/factory.py" in scanned
    assert find_violations(REPO_ROOT) == []


def test_clean_synthetic_tree_has_no_violations(tmp_path):
    _write(tmp_path, "app/ai_client/http_client.py", "import httpx\n")
    _write(tmp_path, "app/services/practice.py", "from app.ai_client.ports import PracticeAI\n")
    _write(tmp_path, "app/services/other.py", "from ..ai_client import ports\n")
    _write(tmp_path, "app/domain/rules.py", "import dataclasses\n")

    assert find_violations(tmp_path) == []


@pytest.mark.parametrize(
    "rel, source, rule",
    [
        ("app/ai_client/fake.py", "from google import genai\n", "①"),
        ("app/api/x.py", "import google.genai as genai\n", "①"),
        ("app/core/x.py", "import openai\n", "①"),
        ("app/services/a.py", "import httpx\n", "②"),
        ("app/ai_client/fake.py", "from httpx import Client\n", "②"),
        ("app/services/a.py", "from app.ai_client.fake import FakePracticeAI\n", "③"),
        ("app/services/a.py", "from ..ai_client import factory\n", "③"),
        ("app/services/sub/a.py", "from ...ai_client.http_client import HttpPracticeAI\n", "③"),
        ("app/services/a.py", "import app.ai_client\n", "③"),
        ("app/domain/rules.py", "from sqlalchemy import select\n", "④"),
        ("app/domain/rules.py", "import fastapi\n", "④"),
    ],
)
def test_synthetic_violation_is_detected(tmp_path, rel, source, rule):
    _write(tmp_path, rel, source)

    violations = find_violations(tmp_path)

    assert any(v.startswith(rule) and rel in v for v in violations), violations


def test_import_inside_function_is_detected(tmp_path):
    _write(tmp_path, "app/domain/rules.py", "def f():\n    import sqlalchemy\n    return sqlalchemy\n")

    assert any(v.startswith("④") for v in find_violations(tmp_path))
