from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories import asset_repository, vision_repository
from app.services.agent_service import agent_service

router = APIRouter()


class AgentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class AgentSearchResultItem(BaseModel):
    asset: dict
    score: float
    match_reasons: list[str]


class AgentSearchResponse(BaseModel):
    items: list[AgentSearchResultItem]
    reasoning: str
    total: int
    page: int
    page_size: int


@router.post("/search", response_model=AgentSearchResponse)
async def agent_search(payload: AgentSearchRequest) -> AgentSearchResponse:
    agent_result = agent_service.search(
        query=payload.query,
        page=payload.page,
        page_size=payload.page_size,
    )

    # Build a lookup of asset_id -> match_reason from agent result
    match_reason_map: dict[int, str] = {}
    for item in agent_result.get("items", []):
        aid = item.get("asset_id")
        if aid is not None:
            match_reason_map[int(aid)] = item.get("match_reason", "")

    # Fetch asset details for matched asset_ids
    asset_ids = list(match_reason_map.keys())
    items: list[AgentSearchResultItem] = []

    if asset_ids:
        rows = vision_repository.list_ready_embeddings_assets()
        rows_by_id: dict[int, dict] = {int(r["id"]): r for r in rows}

        for aid in asset_ids:
            row = rows_by_id.get(aid)
            if row is None:
                continue
            tags = asset_repository.list_asset_tag_names(aid)
            versions = asset_repository.list_asset_versions(aid)
            from pathlib import Path

            asset_payload = {
                "id": aid,
                "name": row["name"],
                "description": row["description"],
                "source": row["source"],
                "file_name": row["file_name"],
                "file_size": row["file_size"],
                "mime_type": row["mime_type"],
                "uploaded_by": row["uploaded_by"],
                "tags": tags,
                "versions": versions,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "file_url": f"/files/{Path(row['file_path']).name}" if row.get("file_path") else "",
                "download_url": f"/api/v1/assets/{aid}/download",
                "vision_analysis": {
                    "provider": row.get("provider"),
                    "status": row.get("status"),
                    "model_name": row.get("model_name"),
                    "model_version": row.get("model_version"),
                    "prompt": row.get("generated_prompt"),
                    "summary": row.get("suggested_description"),
                    "keywords": row.get("suggested_tags"),
                    "suggested_description": row.get("suggested_description"),
                    "suggested_tags": row.get("suggested_tags"),
                    "error_message": row.get("error_message"),
                    "analyzed_at": row.get("analyzed_at"),
                },
            }
            items.append(AgentSearchResultItem(
                asset=asset_payload,
                score=1.0,  # Agent-determined relevance, not cosine distance
                match_reasons=[match_reason_map.get(aid, "")],
            ))

    return AgentSearchResponse(
        items=items,
        reasoning=agent_result.get("reasoning", ""),
        total=len(items),
        page=payload.page,
        page_size=payload.page_size,
    )
