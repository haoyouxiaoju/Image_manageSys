import os
import shutil
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

TEST_DB_PATH = Path(os.getenv("TEMP", ".")) / "vision_backend_tests.db"
TEST_UPLOADS_DIR = Path(os.getenv("TEMP", ".")) / "vision_backend_uploads"
TEST_VECTOR_DB_DIR = Path(os.getenv("TEMP", ".")) / "vision_backend_vector"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
if TEST_UPLOADS_DIR.exists():
    shutil.rmtree(TEST_UPLOADS_DIR)
if TEST_VECTOR_DB_DIR.exists():
    shutil.rmtree(TEST_VECTOR_DB_DIR)
os.environ["DATABASE_PATH"] = str(TEST_DB_PATH)
os.environ["UPLOADS_DIR"] = str(TEST_UPLOADS_DIR)
os.environ["VECTOR_DB_PATH"] = str(TEST_VECTOR_DB_DIR)
os.environ["VISION_ENABLED"] = "false"
os.environ["VISION_REQUIRED_ON_UPLOAD"] = "false"

from app.main import app
from app.services.vector_search_service import vector_search_service

client = TestClient(app)


def _reset_users_table() -> None:
    with sqlite3.connect(TEST_DB_PATH) as conn:
        conn.execute("DELETE FROM asset_vision_analysis")
        conn.execute("DELETE FROM share_links")
        conn.execute("DELETE FROM collection_assets")
        conn.execute("DELETE FROM collections")
        conn.execute("DELETE FROM asset_tags")
        conn.execute("DELETE FROM tags")
        conn.execute("DELETE FROM asset_versions")
        conn.execute("DELETE FROM audit_logs")
        conn.execute("DELETE FROM assets")
        conn.execute("DELETE FROM users")
        conn.commit()
    if TEST_UPLOADS_DIR.exists():
        shutil.rmtree(TEST_UPLOADS_DIR)
    vector_search_service.clear_index()


def _register_and_login(username: str, password: str = "Passw0rd!") -> str:
    client.post("/api/v1/auth/register", json={"username": username, "password": password})
    login_response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return login_response.json()["access_token"]


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


def test_assets_upload_and_pagination() -> None:
    _reset_users_table()
    token = _register_and_login(f"admin_{uuid4().hex[:8]}")

    upload_response = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("demo.png", b"PNGDATA", "image/png")},
        data={"description": "demo asset", "source": "test"},
    )
    assert upload_response.status_code == 200
    asset = upload_response.json()
    assert asset["name"] == "demo"
    assert asset["mime_type"] == "image/png"
    assert asset["vision_analysis"] is None

    list_response = client.get("/api/v1/assets?page=1&page_size=10")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1
    assert list_data["page_size"] == 10
    assert len(list_data["items"]) == 1

    detail_response = client.get(f"/api/v1/assets/{asset['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == asset["id"]
    assert detail_response.json()["vision_analysis"] is None


def test_assets_permission_update_delete() -> None:
    _reset_users_table()
    admin_token = _register_and_login(f"admin_{uuid4().hex[:8]}")
    editor1_token = _register_and_login(f"editor1_{uuid4().hex[:8]}")
    editor2_token = _register_and_login(f"editor2_{uuid4().hex[:8]}")

    upload_response = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {editor1_token}"},
        files={"file": ("asset.jpg", b"JPEGDATA", "image/jpeg")},
        data={"name": "asset-a", "description": "v1", "source": "editor1"},
    )
    assert upload_response.status_code == 200
    asset_id = upload_response.json()["id"]

    forbidden_delete = client.delete(
        f"/api/v1/assets/{asset_id}",
        headers={"Authorization": f"Bearer {editor2_token}"},
    )
    assert forbidden_delete.status_code == 403
    assert forbidden_delete.json()["error"]["code"] == "FORBIDDEN"

    update_response = client.put(
        f"/api/v1/assets/{asset_id}",
        headers={"Authorization": f"Bearer {editor1_token}"},
        json={"description": "updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "updated"

    admin_delete = client.delete(
        f"/api/v1/assets/{asset_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_delete.status_code == 200


def test_assets_upload_validation_and_download_auth() -> None:
    _reset_users_table()
    token = _register_and_login(f"admin_{uuid4().hex[:8]}")

    unsupported = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("bad.txt", b"not-image", "text/plain")},
    )
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

    oversize = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("big.png", b"a" * (20 * 1024 * 1024 + 1), "image/png")},
    )
    assert oversize.status_code == 400
    assert oversize.json()["error"]["code"] == "FILE_TOO_LARGE"

    uploaded = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("ok.webp", b"WEBPDATA", "image/webp")},
    )
    assert uploaded.status_code == 200
    asset_id = uploaded.json()["id"]

    download_without_auth = client.get(f"/api/v1/assets/{asset_id}/download")
    assert download_without_auth.status_code == 401
    assert download_without_auth.json()["error"]["code"] == "MISSING_TOKEN"


def test_assets_versions_and_tags() -> None:
    _reset_users_table()
    token = _register_and_login(f"admin_{uuid4().hex[:8]}")

    uploaded = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("base.png", b"BASEPNG", "image/png")},
        data={"tags": '["海报","科技感"]'},
    )
    assert uploaded.status_code == 200
    asset_id = uploaded.json()["id"]
    assert set(uploaded.json()["tags"]) == {"海报", "科技感"}

    version_resp = client.post(
        f"/api/v1/assets/{asset_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("v2.png", b"V2PNG", "image/png")},
        data={"version": "v1.1", "note": "颜色优化"},
    )
    assert version_resp.status_code == 200
    assert version_resp.json()["version"] == "v1.1"

    versions = client.get(f"/api/v1/assets/{asset_id}/versions")
    assert versions.status_code == 200
    assert len(versions.json()) == 1

    update = client.put(
        f"/api/v1/assets/{asset_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"tags": ["产品图", "科技感"]},
    )
    assert update.status_code == 200
    assert set(update.json()["tags"]) == {"产品图", "科技感"}

    tags_resp = client.get("/api/v1/tags")
    assert tags_resp.status_code == 200
    assert any(item["name"] == "产品图" for item in tags_resp.json())


def test_collections_share_links_and_audit_logs() -> None:
    _reset_users_table()
    admin_token = _register_and_login(f"admin_{uuid4().hex[:8]}")
    editor_token = _register_and_login(f"editor_{uuid4().hex[:8]}")

    uploaded = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {editor_token}"},
        files={"file": ("asset.webp", b"ASSET", "image/webp")},
        data={"name": "shared-asset"},
    )
    assert uploaded.status_code == 200
    asset_id = uploaded.json()["id"]

    create_col = client.post(
        "/api/v1/collections",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={"name": "我的分组", "description": "测试"},
    )
    assert create_col.status_code == 201
    collection_id = create_col.json()["id"]

    add_rel = client.post(
        f"/api/v1/collections/{collection_id}/assets",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={"asset_id": asset_id},
    )
    assert add_rel.status_code == 200

    detail = client.get(f"/api/v1/collections/{collection_id}")
    assert detail.status_code == 200
    assert detail.json()["asset_count"] == 1
    assert len(detail.json()["assets"]) == 1

    create_share = client.post(
        "/api/v1/share-links",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={"asset_id": asset_id, "expires_in_hours": 24},
    )
    assert create_share.status_code == 201
    share_id = create_share.json()["id"]
    assert create_share.json()["is_active"] is True

    revoke = client.delete(
        f"/api/v1/share-links/{share_id}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert revoke.status_code == 200

    logs_forbidden = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {editor_token}"})
    assert logs_forbidden.status_code == 403

    logs_ok = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert logs_ok.status_code == 200
    assert len(logs_ok.json()) >= 1


def test_vision_status() -> None:
    _reset_users_table()

    status_resp = client.get("/api/v1/vision/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["enabled"] is False


def test_search_text_semantic_pagination() -> None:
    _reset_users_table()
    token = _register_and_login(f"admin_{uuid4().hex[:8]}")

    first_upload = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("search_a.png", b"SEARCH_A", "image/png")},
        data={"name": "search-a"},
    )
    assert first_upload.status_code == 200

    second_upload = client.post(
        "/api/v1/assets/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("search_b.png", b"SEARCH_B", "image/png")},
        data={"name": "search-b"},
    )
    assert second_upload.status_code == 200

    search_response = client.post(
        "/api/v1/search/text",
        json={"query": "企业宣传海报", "page": 1, "page_size": 2},
    )
    assert search_response.status_code == 200
    payload = search_response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert len(payload["items"]) == 2
    assert payload["items"][0]["score"] >= payload["items"][1]["score"]
    assert payload["items"][0]["asset"]["vision_analysis"] is None

    second_page = client.post(
        "/api/v1/search/text",
        json={"query": "企业宣传海报", "page": 2, "page_size": 1},
    )
    assert second_page.status_code == 200
    second_page_payload = second_page.json()
    assert second_page_payload["total"] == 2
    assert second_page_payload["page"] == 2
    assert second_page_payload["page_size"] == 1
    assert len(second_page_payload["items"]) == 1

