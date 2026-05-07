from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.auth_context import get_current_user
from app.core.config import settings
from app.core.exceptions import ApiError
from app.repositories import asset_repository

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
WRITABLE_ROLES = {"admin", "editor"}


class AssetResponse(BaseModel):
    id: int
    name: str
    description: str
    source: str
    file_name: str
    file_size: int
    mime_type: str
    uploaded_by: str
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


def _to_asset_response(asset: dict) -> AssetResponse:
    return AssetResponse(
        id=asset["id"],
        name=asset["name"],
        description=asset["description"],
        source=asset["source"],
        file_name=asset["file_name"],
        file_size=asset["file_size"],
        mime_type=asset["mime_type"],
        uploaded_by=asset["uploaded_by"],
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


@router.post("/upload", response_model=AssetResponse)
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    description: str | None = Form(default=""),
    source: str | None = Form(default=""),
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
    return _to_asset_response(created_asset)


@router.get("", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    query: str | None = Query(default=None),
) -> AssetListResponse:
    result = asset_repository.list_assets(page=page, page_size=page_size, query=query)
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

    return {"message": "Asset deleted successfully."}


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

    return FileResponse(
        path=str(file_path),
        media_type=asset["mime_type"],
        filename=asset["file_name"],
    )

