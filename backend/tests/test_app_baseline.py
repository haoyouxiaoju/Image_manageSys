import os
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

TEST_DB_PATH = Path(os.getenv("TEMP", ".")) / "clip_image_backend_tests.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ["DATABASE_PATH"] = str(TEST_DB_PATH)

from app.main import app

client = TestClient(app)


def _reset_users_table() -> None:
    with sqlite3.connect(TEST_DB_PATH) as conn:
        conn.execute("DELETE FROM users")
        conn.commit()


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


def test_register_login_and_me() -> None:
    _reset_users_table()
    username = f"user_{uuid4().hex[:8]}"
    password = "Passw0rd!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert register_response.status_code == 201
    register_data = register_response.json()
    assert register_data["token_type"] == "bearer"
    assert "access_token" in register_data
    assert register_data["role"] == "admin"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["username"] == username
    assert me_data["role"] == "admin"


def test_register_conflict() -> None:
    _reset_users_table()
    username = f"user_{uuid4().hex[:8]}"
    payload = {"username": username, "password": "Passw0rd!"}

    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "USER_EXISTS"


def test_login_invalid_credentials() -> None:
    _reset_users_table()
    username = f"user_{uuid4().hex[:8]}"
    password = "Passw0rd!"
    client.post("/api/v1/auth/register", json={"username": username, "password": password})

    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "WrongPass1!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_token() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"


def test_admin_users_endpoint_forbidden_for_editor() -> None:
    _reset_users_table()

    admin_username = f"admin_{uuid4().hex[:6]}"
    editor_username = f"editor_{uuid4().hex[:6]}"
    password = "Passw0rd!"

    admin_register = client.post(
        "/api/v1/auth/register",
        json={"username": admin_username, "password": password},
    )
    assert admin_register.status_code == 201
    assert admin_register.json()["role"] == "admin"

    editor_register = client.post(
        "/api/v1/auth/register",
        json={"username": editor_username, "password": password},
    )
    assert editor_register.status_code == 201
    assert editor_register.json()["role"] == "editor"

    editor_token = client.post(
        "/api/v1/auth/login",
        json={"username": editor_username, "password": password},
    ).json()["access_token"]
    editor_users = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {editor_token}"})
    assert editor_users.status_code == 403
    assert editor_users.json()["error"]["code"] == "FORBIDDEN"

    admin_token = client.post(
        "/api/v1/auth/login",
        json={"username": admin_username, "password": password},
    ).json()["access_token"]
    admin_users = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_users.status_code == 200
    users = admin_users.json()
    assert len(users) == 2
    assert users[0]["role"] == "admin"
    assert users[1]["role"] == "editor"

