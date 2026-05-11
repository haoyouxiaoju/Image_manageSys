from difflib import SequenceMatcher
import re
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories import asset_repository, clip_repository

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


def _tokenize(text: str) -> list[str]:
    cleaned = text.strip().lower()
    if not cleaned:
        return []
    parts = [part for part in re.split(r"[\s,，。;；!！?？/\\]+", cleaned) if part]
    if parts:
        return parts
    return [cleaned]


def _keyword_score(query: str, keywords: list[str], summary: str) -> float:
    query_lower = query.strip().lower()
    terms = _tokenize(query_lower)

    score = 0.0
    normalized_keywords = [keyword.lower() for keyword in keywords]
    summary_lower = summary.lower()

    for keyword in normalized_keywords:
        if query_lower and query_lower in keyword:
            score += 2.0
    for term in terms:
        for keyword in normalized_keywords:
            if term in keyword:
                score += 1.5
        if term and term in summary_lower:
            score += 0.8

    if query_lower and query_lower in summary_lower:
        score += 1.5

    if score == 0.0:
        candidates = normalized_keywords + ([summary_lower] if summary_lower else [])
        best_ratio = 0.0
        for candidate in candidates:
            best_ratio = max(best_ratio, SequenceMatcher(None, query_lower, candidate).ratio())
        score = best_ratio
    return score


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
            "provider": row["provider"],
            "status": row["status"],
            "model_name": row["model_name"],
            "model_version": row["model_version"],
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
    rows = clip_repository.list_ready_embeddings_assets()

    scored: list[tuple[dict, float]] = []
    for row in rows:
        keywords = row.get("suggested_tags") or []
        summary = row.get("suggested_description") or ""
        if not isinstance(keywords, list):
            keywords = []
        if not isinstance(summary, str):
            summary = ""
        score = _keyword_score(payload.query, [str(item) for item in keywords], summary)
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
