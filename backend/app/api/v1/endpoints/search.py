from math import sqrt
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories import asset_repository, clip_repository
from app.services.clip_service import clip_service

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


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for left, right in zip(vec1, vec2):
        dot += left * right
        norm1 += left * left
        norm2 += right * right
    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0
    return dot / (sqrt(norm1) * sqrt(norm2))


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
        "download_url": f"/api/v1/assets/{asset_id}/download",
        "clip_analysis": {
            "status": row["status"],
            "model_name": row["model_name"],
            "model_version": row["model_version"],
            "embedding_dim": row["embedding_dim"],
            "features": row["features"],
            "suggested_description": row["suggested_description"],
            "suggested_tags": row["suggested_tags"],
            "error_message": row["error_message"],
            "analyzed_at": row["analyzed_at"],
        },
    }


@router.post("/text", response_model=SearchTextResponse)
async def search_text(payload: SearchTextRequest) -> SearchTextResponse:
    text_embedding = clip_service.encode_text(payload.query)
    rows = clip_repository.list_ready_embeddings_assets()

    scored: list[tuple[dict, float]] = []
    for row in rows:
        image_embedding = row["embedding"]
        if not isinstance(image_embedding, list):
            continue
        if len(image_embedding) != len(text_embedding):
            continue
        score = _cosine_similarity(text_embedding, image_embedding)
        scored.append((row, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    total = len(scored)
    start = (payload.page - 1) * payload.page_size
    end = start + payload.page_size
    paged = scored[start:end]

    items = [
        SearchResultItem(
            asset=_build_asset_payload(row),
            score=round(score, 6),
        )
        for row, score in paged
    ]
    return SearchTextResponse(items=items, total=total, page=payload.page, page_size=payload.page_size)
