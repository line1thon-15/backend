from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def make_client() -> Iterator[Callable[[str], TestClient]]:
    from app.core.config import Settings
    from app.main import create_app

    clients: list[TestClient] = []

    def _make(database_url: str) -> TestClient:
        settings = Settings(_env_file=None, database_url=database_url, ai_client="fake")
        client = TestClient(create_app(settings))
        clients.append(client)
        return client

    yield _make

    for client in clients:
        client.close()
        client.app.state.engine.dispose()


@pytest.fixture
def sqlite_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
