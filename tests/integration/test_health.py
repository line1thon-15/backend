"""A1 `GET /api/v1/health` 스모크 (Architecture API 규격 A1, Tasks T-01)."""


def test_health_returns_ok_with_sqlite_file(make_client, sqlite_url):
    client = make_client(sqlite_url)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_returns_ok_with_in_memory_sqlite(make_client):
    client = make_client("sqlite://")

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_is_only_served_under_api_v1_prefix(make_client, sqlite_url):
    client = make_client(sqlite_url)

    response = client.get("/health")

    assert response.status_code == 404


def test_health_returns_503_db_unavailable_when_database_cannot_open(make_client, tmp_path):
    unreachable = tmp_path / "missing-dir" / "nested" / "db.sqlite"
    client = make_client(f"sqlite:///{unreachable.as_posix()}")

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "DB_UNAVAILABLE"
    assert isinstance(body["error"]["message"], str) and body["error"]["message"]
    assert set(body) == {"error"}
    assert "unable to open" not in response.text.lower()
    assert "operationalerror" not in response.text.lower()


def test_health_rejects_post(make_client, sqlite_url):
    client = make_client(sqlite_url)

    response = client.post("/api/v1/health")

    assert response.status_code == 405
