from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_v1_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["api_version"] == "v1"


def test_request_id_and_process_time_headers() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-MS" in response.headers


def test_invalid_auth_header_format() -> None:
    response = client.get("/api/v1/health", headers={"Authorization": "Token abc"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_AUTH_HEADER"

