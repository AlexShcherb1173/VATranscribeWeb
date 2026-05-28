from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_root_returns_api_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["app"] == "VATranscribe"
    assert data["version"] == "0.1.0"
    assert "api_prefix" in data
    assert "endpoints" in data


def test_health_live_returns_ok() -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["app"] == "VATranscribe"


def test_health_ready_returns_json() -> None:
    response = client.get("/api/v1/health/ready")

    # В зависимости от доступности Postgres/Redis это может быть 200 или 503.
    assert response.status_code in (200, 503)

    data = response.json()
    assert "status" in data
    assert "app" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "storage" in data["checks"]