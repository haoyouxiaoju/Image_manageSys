import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.auth_context import get_current_user
from app.core.config import settings
from app.core.exceptions import ApiError
from app.repositories import asset_repository, audit_repository

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
WRITABLE_ROLES = {"admin", "editor"}


class AssetVersionResponse(BaseModel):
    id: int
    asset_id: int
    version: str
    note: str
    file_name: str
    file_size: int
    mime_type: str
    created_by: str
    created_at: str


class AssetResponse(BaseModel):
    id: int
    name: str
    description: str
    source: str
    file_name: str
    file_size: int
    mime_type: str
    uploaded_by: str
    tags: list[str] = []
    versions: list[AssetVersionResponse] = []
    created_at: str
    updated_at: str
    download_url: str


class AssetListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AssetResponse]


class AssetUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    source: str | None = Field(default=None, max_length=200)
    tags: list[str] | None = None


def _to_asset_response(asset: dict) -> AssetResponse:
    tags = asset_repository.list_asset_tag_names(asset["id"])
    versions = [
        AssetVersionResponse(
            id=item["id"],
            asset_id=item["asset_id"],
            version=item["version"],
            note=item["note"],
            file_name=item["file_name"],
            file_size=item["file_size"],
            mime_type=item["mime_type"],
            created_by=item["created_by"],
            created_at=item["created_at"],
        )
        for item in asset_repository.list_asset_versions(asset["id"])
    ]
    return AssetResponse(
        id=asset["id"],
        name=asset["name"],
        description=asset["description"],
        source=asset["source"],
        file_name=asset["file_name"],
        file_size=asset["file_size"],
        mime_type=asset["mime_type"],
        uploaded_by=asset["uploaded_by"],
        tags=tags,
        versions=versions,
        created_at=asset["created_at"],
        updated_at=asset["updated_at"],
        download_url=f"/api/v1/assets/{asset['id']}/download",
    )


def _ensure_editor_or_admin(user: dict) -> None:
    if user["role"] not in WRITABLE_ROLES:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Editor or admin role is required.")


def _ensure_asset_manage_permission(user: dict, asset: dict) -> None:
    if user["role"] == "admin":
        return
    if user["role"] == "editor" and asset["uploaded_by"] == user["username"]:
        return
    raise ApiError(status_code=403, code="FORBIDDEN", message="No permission to modify this asset.")


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _parse_tags(tags_raw: str | None) -> list[str]:
    if not tags_raw:
        return []
    tags_raw = tags_raw.strip()
    if not tags_raw:
        return []
    try:
        parsed = json.loads(tags_raw)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in tags_raw.split(",") if item.strip()]


@router.post("/upload", response_model=AssetResponse)
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    description: str | None = Form(default=""),
    source: str | None = Form(default=""),
    tags: str | None = Form(default=None),
) -> AssetResponse:
    user = get_current_user(request, required=True)
    _ensure_editor_or_admin(user)

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ApiError(status_code=400, code="UNSUPPORTED_FILE_TYPE", message="Only JPG/PNG/WebP are supported.")

    content = await file.read()
    file_size = len(content)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ApiError(status_code=400, code="FILE_TOO_LARGE", message="File size exceeds 20MB.")

    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    original_suffix = Path(file.filename or "").suffix.lower()
    if original_suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
        original_suffix = suffix_map[file.content_type]

    stored_file_name = f"{uuid4().hex}{original_suffix}"
    stored_file_path = uploads_dir / stored_file_name
    stored_file_path.write_bytes(content)

    asset_name = name.strip() if name else Path(file.filename or stored_file_name).stem
    created_asset = asset_repository.create_asset(
        name=asset_name,
        description=(description or "").strip(),
        source=(source or "").strip(),
        file_name=file.filename or stored_file_name,
        file_path=str(stored_file_path),
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=user["username"],
    )
    parsed_tags = _parse_tags(tags)
    if parsed_tags:
        asset_repository.replace_asset_tags(created_asset["id"], parsed_tags)

    audit_repository.create_audit_log(
        user=user["username"],
        action="上传",
        target=created_asset["name"],
        ip_address=_client_ip(request),
    )
    return _to_asset_response(created_asset)


@router.get("", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    query: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    sort: str = Query(default="date_desc"),
) -> AssetListResponse:
    search_query = q if q is not None else query
    parsed_tags = [item.strip() for item in tags.split(",") if item.strip()] if tags else None
    result = asset_repository.list_assets(
        page=page,
        page_size=page_size,
        query=search_query,
        tags=parsed_tags,
        sort=sort,
    )
    return AssetListResponse(
        total=result["total"],
        page=page,
        page_size=page_size,
        items=[_to_asset_response(item) for item in result["items"]],
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int) -> AssetResponse:
    asset = asset_repository.get_asset_by_id(asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")
    return _to_asset_response(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: int, payload: AssetUpdateRequest, request: Request) -> AssetResponse:
    user = get_current_user(request, required=True)
    _ensure_editor_or_admin(user)

    asset = asset_repository.get_asset_by_id(asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")
    _ensure_asset_manage_permission(user, asset)

    updated_asset = asset_repository.update_asset(
        asset_id=asset_id,
        name=(payload.name or asset["name"]).strip(),
        description=(payload.description if payload.description is not None else asset["description"]).strip(),
        source=(payload.source if payload.source is not None else asset["source"]).strip(),
    )
    if payload.tags is not None:
        asset_repository.replace_asset_tags(asset_id, payload.tags)

    audit_repository.create_audit_log(
        user=user["username"],
        action="编辑",
        target=updated_asset["name"],
        ip_address=_client_ip(request),
    )
    return _to_asset_response(updated_asset)


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int, request: Request) -> dict[str, str]:
    user = get_current_user(request, required=True)
    _ensure_editor_or_admin(user)

    asset = asset_repository.get_asset_by_id(asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")
    _ensure_asset_manage_permission(user, asset)

    if not asset_repository.delete_asset(asset_id):
        raise ApiError(status_code=500, code="DELETE_FAILED", message="Failed to delete asset.")

    file_path = Path(asset["file_path"])
    if file_path.exists():
        file_path.unlink()

    audit_repository.create_audit_log(
        user=user["username"],
        action="删除",
        target=asset["name"],
        ip_address=_client_ip(request),
    )
    return {"message": "Asset deleted successfully."}


@router.post("/{asset_id}/versions", response_model=AssetVersionResponse)
async def upload_asset_version(
    asset_id: int,
    request: Request,
    file: UploadFile = File(...),
    version: str | None = Form(default=None),
    note: str | None = Form(default=""),
) -> AssetVersionResponse:
    user = get_current_user(request, required=True)
    _ensure_editor_or_admin(user)

    asset = asset_repository.get_asset_by_id(asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")
    _ensure_asset_manage_permission(user, asset)

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ApiError(status_code=400, code="UNSUPPORTED_FILE_TYPE", message="Only JPG/PNG/WebP are supported.")

    content = await file.read()
    file_size = len(content)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ApiError(status_code=400, code="FILE_TOO_LARGE", message="File size exceeds 20MB.")

    uploads_dir = Path(settings.uploads_dir) / "versions"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]

    stored_file_name = f"{uuid4().hex}{suffix}"
    stored_file_path = uploads_dir / stored_file_name
    stored_file_path.write_bytes(content)

    if not version:
        existing = asset_repository.list_asset_versions(asset_id)
        version = f"v{len(existing) + 1}.0"

    created = asset_repository.create_asset_version(
        asset_id=asset_id,
        version=version.strip(),
        note=(note or "").strip(),
        file_name=file.filename or stored_file_name,
        file_path=str(stored_file_path),
        file_size=file_size,
        mime_type=file.content_type,
        created_by=user["username"],
    )
    audit_repository.create_audit_log(
        user=user["username"],
        action="上传版本",
        target=asset["name"],
        ip_address=_client_ip(request),
    )
    return AssetVersionResponse(**created)


@router.get("/{asset_id}/versions", response_model=list[AssetVersionResponse])
async def list_versions(asset_id: int) -> list[AssetVersionResponse]:
    asset = asset_repository.get_asset_by_id(asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")
    return [AssetVersionResponse(**item) for item in asset_repository.list_asset_versions(asset_id)]


@router.get("/{asset_id}/download")
async def download_asset(asset_id: int, request: Request):
    user = get_current_user(request, required=True)
    _ensure_editor_or_admin(user)

    asset = asset_repository.get_asset_by_id(asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")

    file_path = Path(asset["file_path"])
    if not file_path.exists():
        raise ApiError(status_code=404, code="FILE_NOT_FOUND", message="Asset file does not exist.")

    audit_repository.create_audit_log(
        user=user["username"],
        action="下载",
        target=asset["name"],
        ip_address=_client_ip(request),
    )
    return FileResponse(
        path=str(file_path),
        media_type=asset["mime_type"],
        filename=asset["file_name"],
    )
