from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel

from app.core.auth_context import get_current_user, require_editor_or_admin
from app.core.config import settings
from app.core.exceptions import ApiError
from app.services.clip_service import clip_service

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ClipAnalyzeResponse(BaseModel):
    provider: str
    model: str
    model_version: str
    summary: str
    keywords: list[str]


@router.get("/status")
async def clip_status() -> dict:
    return clip_service.status()


@router.post("/analyze", response_model=ClipAnalyzeResponse)
async def clip_analyze(request: Request, file: UploadFile = File(...)) -> ClipAnalyzeResponse:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ApiError(status_code=400, code="UNSUPPORTED_FILE_TYPE", message="Only JPG/PNG/WebP are supported.")

    uploads_tmp_dir = Path(settings.uploads_dir) / "clip-tmp"
    uploads_tmp_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    temp_path = uploads_tmp_dir / f"{uuid4().hex}{suffix}"

    content = await file.read()
    temp_path.write_bytes(content)
    try:
        result = clip_service.analyze_file(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return ClipAnalyzeResponse(
        provider=result.provider,
        model=result.model_name,
        model_version=result.model_version,
        summary=result.suggested_description,
        keywords=result.suggested_tags,
    )
