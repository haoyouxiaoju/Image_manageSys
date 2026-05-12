from __future__ import annotations

import logging
from time import perf_counter

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.repositories import asset_repository, vision_repository
from app.services.agent_service import agent_service

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class AgentSearchResultItem(BaseModel):
    asset: dict
    score: float
    match_reasons: list[str]
    llm_relevance: float | None = None


class AgentSearchResponse(BaseModel):
    items: list[AgentSearchResultItem]
    reasoning: str
    total: int
    page: int
    page_size: int


@router.post("/search", response_model=AgentSearchResponse)
async def agent_search(payload: AgentSearchRequest) -> AgentSearchResponse:
    t_total = perf_counter()

    t_agent = perf_counter()
    agent_result = agent_service.search(
        query=payload.query,
        page=payload.page,
        page_size=payload.page_size,
    )
    t_agent_elapsed = (perf_counter() - t_agent) * 1000
    logger.info("[agent-endpoint] agent_service.search elapsed=%.0fms", t_agent_elapsed)

    # Build lookup of asset_id -> (match_reason, score) from agent result
    result_map: dict[int, dict] = {}
    for item in agent_result.get("items", []):
        aid = item.get("asset_id")
        if aid is not None:
            result_map[int(aid)] = {
                "match_reason": item.get("match_reason", ""),
                "score": item.get("score", 0.0),
                "llm_relevance": item.get("llm_relevance"),
            }

    # Fetch asset details for matched asset_ids
    asset_ids = list(result_map.keys())
    items: list[AgentSearchResultItem] = []

    if asset_ids:
        t_db = perf_counter()
        rows = vision_repository.list_ready_embeddings_assets()
        t_db_elapsed = (perf_counter() - t_db) * 1000
        logger.info("[agent-endpoint] vision_repository.list_ready_embeddings_assets elapsed=%.0fms rows=%d",
                     t_db_elapsed, len(rows))
        rows_by_id: dict[int, dict] = {int(r["id"]): r for r in rows}

        t_detail = perf_counter()
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
            info = result_map.get(aid, {})
            items.append(AgentSearchResultItem(
                asset=asset_payload,
                score=info.get("score", 0.0),
                match_reasons=[info.get("match_reason", "")] if info.get("match_reason") else [],
                llm_relevance=info.get("llm_relevance"),
            ))
        # 按向量相似度降序排列
        items.sort(key=lambda it: it.score, reverse=True)
        logger.info("[agent-endpoint] build_asset_details count=%d elapsed=%.0fms",
                     len(items), (perf_counter() - t_detail) * 1000)

    t_total_elapsed = (perf_counter() - t_total) * 1000
    logger.info("[agent-endpoint] DONE query=%r item_count=%d total=%.0fms",
                 payload.query, len(items), t_total_elapsed)

    return AgentSearchResponse(
        items=items,
        reasoning=agent_result.get("reasoning", ""),
        total=len(items),
        page=payload.page,
        page_size=payload.page_size,
    )
