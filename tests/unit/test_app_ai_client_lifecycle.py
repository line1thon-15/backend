"""앱 종료 시 create_app이 만든 AI 클라이언트를 닫는다 (T-94 리뷰 권고 #3 — httpx 커넥션 풀 정리)."""

from fastapi.testclient import TestClient

import app.main as main_module
from app.ai_client.fake import FakePracticeAI
from app.core.config import Settings


class ClosableAI(FakePracticeAI):
    def __init__(self) -> None:
        super().__init__()
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


def _settings(sqlite_url: str) -> Settings:
    return Settings(_env_file=None, database_url=sqlite_url, ai_client="fake")


def test_ai_client_built_by_create_app_is_closed_on_shutdown(monkeypatch, sqlite_url):
    built = ClosableAI()
    monkeypatch.setattr(main_module, "build_practice_ai", lambda *args, **kwargs: built)
    app = main_module.create_app(_settings(sqlite_url))

    with TestClient(app):
        assert built.close_calls == 0

    assert built.close_calls == 1
    app.state.engine.dispose()


def test_injected_ai_client_is_not_closed_by_app(sqlite_url):
    # 주입한 쪽(테스트 등)이 수명을 관리한다
    injected = ClosableAI()
    app = main_module.create_app(_settings(sqlite_url), practice_ai=injected)

    with TestClient(app):
        pass

    assert injected.close_calls == 0
    app.state.engine.dispose()


def test_ai_client_without_close_is_fine_on_shutdown(sqlite_url):
    # FakePracticeAI에는 close가 없다 — 종료가 깨지지 않는다
    app = main_module.create_app(_settings(sqlite_url))

    with TestClient(app):
        pass

    app.state.engine.dispose()
