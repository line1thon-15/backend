"""앱 종료 시 create_app이 만든 AI 클라이언트를 닫는다 (T-94 리뷰 권고 #3 — httpx 커넥션 풀 정리)."""

import pytest
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


# ---- 보호자 학습 요약 AI 배선 (T-76) -----------------------------------------------


class ClosableBothAI(ClosableAI):
    """HttpPracticeAI처럼 PracticeAI·SummaryAI를 함께 구현하는 대역."""

    def summary(self, request):  # pragma: no cover - 배선 확인용
        raise NotImplementedError


def test_practice_ai_that_also_summarizes_is_shared_and_closed_once(monkeypatch, sqlite_url):
    built = ClosableBothAI()
    monkeypatch.setattr(main_module, "build_practice_ai", lambda *args, **kwargs: built)
    monkeypatch.setattr(
        main_module, "build_summary_ai", lambda *args, **kwargs: pytest.fail("summary AI must be shared")
    )
    app = main_module.create_app(_settings(sqlite_url))

    with TestClient(app):
        assert app.state.guardian_report_service._summary_ai is built

    assert built.close_calls == 1
    app.state.engine.dispose()


def test_summary_ai_built_separately_is_closed_on_shutdown(monkeypatch, sqlite_url):
    # 주입한 practice_ai에 summary가 없으면 설정대로 따로 만든다 — 만든 것은 앱이 닫는다
    class ClosableSummary:
        close_calls = 0

        def summary(self, request):  # pragma: no cover
            raise NotImplementedError

        def close(self) -> None:
            self.close_calls += 1

    built_summary = ClosableSummary()
    monkeypatch.setattr(main_module, "build_summary_ai", lambda *args, **kwargs: built_summary)
    app = main_module.create_app(_settings(sqlite_url), practice_ai=ClosableAI())

    with TestClient(app):
        assert app.state.guardian_report_service._summary_ai is built_summary

    assert built_summary.close_calls == 1
    app.state.engine.dispose()


def test_injected_summary_ai_is_used_and_not_closed(sqlite_url):
    injected = ClosableBothAI()
    app = main_module.create_app(_settings(sqlite_url), summary_ai=injected)

    with TestClient(app):
        assert app.state.guardian_report_service._summary_ai is injected

    assert injected.close_calls == 0
    app.state.engine.dispose()
