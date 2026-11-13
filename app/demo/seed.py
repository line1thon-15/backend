"""시연 예시 데이터 적재 실행 진입점 (T-67 — DECISIONS #30·#132, N-11).

두 방식(DECISIONS #30):
  fixed   고정 시연 계정(보호자·아이 — app/demo/data/demo_account.json)을 만들거나 다시 쓰고 예시 기록을 넣는다.
          시연 기본 방식(DECISIONS #132, 2026-11-13 사용자 답 "고정 시연 계정 (추천)").
  attach  이미 있는 아이(--child-id)에 예시 기록을 덧붙인다.

재실행 안전: 같은 명령을 다시 실행하면 그 아이의 `demo_seed` 행을 새 계획으로 바꾼다(중복 없음, `live` 행 유지).
날짜는 실행 시각 기준 상대값 — 시연 당일 다시 실행하면 7일 창이 시연일에 맞춰진다.
스키마는 미리 마이그레이션돼 있어야 한다(`alembic upgrade head`). 비밀번호·PIN은 출력하지 않는다.
fixed는 환경 변수 DEMO_GUARDIAN_PASSWORD(8~128자)·DEMO_CHILD_PIN(숫자 4자리)이 필요하다 — 없거나 틀리면 종료 코드 2.

사용: python -m app.demo.seed fixed [--database-url URL]
      python -m app.demo.seed attach --child-id UUID [--database-url URL]
"""

import argparse
import json
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.content.loader import ContentBundle, load_content
from app.core.config import Settings
from app.core.security import hash_password
from app.db.session import make_engine, make_session_factory
from app.demo.plan import build_demo_plan
from app.repositories.demo_seed import FixedAccountSpec, LinkCodeTakenError, SqlAlchemyDemoSeedRepository

DEFAULT_ACCOUNT_FILE = Path(__file__).resolve().parent / "data" / "demo_account.json"
# 시연 계정 비밀번호·PIN 환경 변수 — fixed 방식만 쓴다(attach는 계정을 만들지 않아 필요 없음).
# 프로세스 환경 변수만 읽는다(dotenv 파일은 읽지 않음).
PASSWORD_ENV = "DEMO_GUARDIAN_PASSWORD"
PIN_ENV = "DEMO_CHILD_PIN"
# 보호자 로그인 API의 비밀번호 길이 규칙과 같게 — 다르면 만든 계정으로 로그인할 수 없다 (app/api/auth.py PasswordValue)
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class DemoSeedError(Exception):
    pass


class DemoSeedConfigError(Exception):
    """시연 계정 비밀번호·PIN 환경 변수가 없거나 형식이 틀림 — 메시지에 값을 넣지 않는다."""


@dataclass(frozen=True)
class DemoAccount:
    guardian_email: str
    guardian_password: str
    child_nickname: str
    child_grade: str
    pin: str
    link_code: str
    consent_version: str


@dataclass(frozen=True)
class SeedResult:
    child_id: UUID
    sessions: int
    notices: int


def _secret(environ: Mapping[str, str], name: str, valid: Callable[[str], bool], rule: str) -> str:
    value = environ.get(name)
    if not value:
        raise DemoSeedConfigError(f"environment variable {name} is not set")
    if not valid(value):
        raise DemoSeedConfigError(f"environment variable {name} is invalid ({rule})")  # 값은 넣지 않는다
    return value


def load_demo_account(path: Path = DEFAULT_ACCOUNT_FILE, environ: Mapping[str, str] | None = None) -> DemoAccount:
    """계정 프로필은 저장소 파일, 비밀번호·PIN은 환경 변수(2026-11-13 사용자 답 "환경 변수로 받기 (추천)")."""
    environ = os.environ if environ is None else environ
    password = _secret(
        environ,
        PASSWORD_ENV,
        lambda v: PASSWORD_MIN_LENGTH <= len(v) <= PASSWORD_MAX_LENGTH,
        f"{PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters",
    )
    pin = _secret(environ, PIN_ENV, lambda v: re.fullmatch(r"[0-9]{4}", v) is not None, "4 ASCII digits")
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return DemoAccount(
        guardian_email=raw["guardian_email"].strip().casefold(),
        guardian_password=password,
        child_nickname=raw["child_nickname"],
        child_grade=raw["child_grade"],
        pin=pin,
        link_code=raw["child_link_code"].strip().upper(),
        consent_version=raw["consent_version"],
    )


def seed_into_child(
    repository: SqlAlchemyDemoSeedRepository,
    content: ContentBundle,
    child_id: UUID,
    now: datetime,
) -> SeedResult:
    plan = build_demo_plan(now, content)
    if not repository.replace_demo_records(child_id, plan):
        raise DemoSeedError(f"child not found: {child_id}")
    return SeedResult(child_id=child_id, sessions=len(plan.sessions), notices=len(plan.notices))


def seed_fixed_account(
    repository: SqlAlchemyDemoSeedRepository,
    content: ContentBundle,
    account: DemoAccount,
    now: datetime,
) -> SeedResult:
    build_demo_plan(now, content)  # 콘텐츠가 맞지 않으면 계정을 만들기 전에 실패
    spec = FixedAccountSpec(
        guardian_email=account.guardian_email,
        child_nickname=account.child_nickname,
        child_grade=account.child_grade,
        child_link_code=account.link_code,
        consent_version=account.consent_version,
    )
    try:
        child_id = repository.ensure_fixed_account(
            spec,
            password_hash=lambda: hash_password(account.guardian_password),
            pin_hash=lambda: hash_password(account.pin),
        )
    except LinkCodeTakenError as exc:
        raise DemoSeedError(f"demo link code is used by another guardian's child: {exc}") from exc
    return seed_into_child(repository, content, child_id, now)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.demo.seed", description="시연 예시 데이터 적재 (T-67)")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name, help_text in (("fixed", "고정 시연 계정에 적재"), ("attach", "지정 아이에 덧붙임")):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--database-url", default=None, help="생략하면 앱 설정(DATABASE_URL)")
        if name == "attach":
            command.add_argument("--child-id", type=UUID, required=True)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    settings: Settings | None = None,
    clock: Callable[[], datetime] = _utcnow,
) -> int:
    args = _parser().parse_args(argv)
    account = None
    if args.mode == "fixed":
        # DB 연결 전에 확인 — 비밀번호·PIN이 없거나 틀리면 아무것도 쓰지 않고 종료 코드 2
        try:
            account = load_demo_account()
        except DemoSeedConfigError as exc:
            print(f"demo seed config error: {exc}", file=sys.stderr)
            return 2
    if args.database_url:
        settings = Settings(_env_file=None, database_url=args.database_url)
    settings = settings or Settings()

    engine = make_engine(settings.database_url)
    try:
        repository = SqlAlchemyDemoSeedRepository(make_session_factory(engine))
        content = load_content()
        if args.mode == "fixed":
            result = seed_fixed_account(repository, content, account, clock())
        else:
            result = seed_into_child(repository, content, args.child_id, clock())
    except DemoSeedError as exc:
        print(f"demo seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print(f"demo seed ok: mode={args.mode} child_id={result.child_id} sessions={result.sessions} notices={result.notices}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
