from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

from app.repositories import asset_repository, vision_repository
from app.services.vector_search_service import vector_search_service

router = APIRouter()


class SearchTextRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class SearchResultItem(BaseModel):
    asset: dict[str, Any]
    score: float


class SearchTextResponse(BaseModel):
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int


def _build_asset_payload(row: dict) -> dict[str, Any]:
    asset_id = row["id"]
    return {
        "id": asset_id,
        "name": row["name"],
        "description": row["description"],
        "source": row["source"],
        "file_name": row["file_name"],
        "file_size": row["file_size"],
        "mime_type": row["mime_type"],
        "uploaded_by": row["uploaded_by"],
        "tags": asset_repository.list_asset_tag_names(asset_id),
        "versions": asset_repository.list_asset_versions(asset_id),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "file_url": f"{settings.asset_base_url}/files/{Path(row['file_path']).name}" if row.get("file_path") else "",
        "download_url": f"{settings.asset_base_url}/api/v1/assets/{asset_id}/download",
        "vision_analysis": {
            "provider": row["provider"],
            "status": row["status"],
            "model_name": row["model_name"],
            "model_version": row["model_version"],
            "prompt": row["generated_prompt"],
            "summary": row["suggested_description"],
            "keywords": row["suggested_tags"],
            "suggested_description": row["suggested_description"],
            "suggested_tags": row["suggested_tags"],
            "error_message": row["error_message"],
            "analyzed_at": row["analyzed_at"],
        },
    }


@router.post("/text", response_model=SearchTextResponse)
async def search_text(payload: SearchTextRequest) -> SearchTextResponse:
    rows = vision_repository.list_ready_embeddings_assets()
    rows_by_asset_id = {int(row["id"]): row for row in rows}
    start = (payload.page - 1) * payload.page_size
    hits, total = vector_search_service.search_assets(
        query=payload.query,
        limit=payload.page_size,
        offset=start,
        asset_ids=list(rows_by_asset_id.keys()),
    )
    items = [
        SearchResultItem(
            asset=_build_asset_payload(rows_by_asset_id[hit.asset_id]),
            score=round(hit.score, 6),
        )
        for hit in hits
        if hit.asset_id in rows_by_asset_id
    ]
    return SearchTextResponse(items=items, total=total, page=payload.page, page_size=payload.page_size)
