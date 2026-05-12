from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import logging
from pathlib import Path
from time import perf_counter
from typing import Any

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant

from app.core.config import settings
from app.core.exceptions import ApiError

logger = logging.getLogger(__name__)


@dataclass
class VectorHit:
    asset_id: int
    score: float
    prompt: str = ""
    summary: str = ""
    keywords: list[str] | None = None


class VectorSearchService:
    def __init__(self) -> None:
        self._enabled = settings.vector_enabled
        self._provider = settings.vector_provider.strip().lower()
        self._initialized = False
        self._ready = False
        self._last_error: str | None = None
        self._client: QdrantClient | None = None
        self._embedding_client: OpenAI | None = None
        self._vector_size: int | None = None

    def initialize(self) -> None:
        self._initialized = True
        self._ready = False
        self._last_error = None
        self._vector_size = None
        self._client = None
        self._embedding_client = None

        if not self._enabled:
            logger.info("Vector search disabled by VECTOR_ENABLED.")
            return
        if self._provider != "qdrant":
            self._last_error = f"Unsupported VECTOR_PROVIDER: {self._provider}"
            logger.error(self._last_error)
            return

        vector_dir = Path(settings.vector_db_path)
        vector_dir.mkdir(parents=True, exist_ok=True)

        # 进程被强制终止时 Qdrant 锁文件可能残留，启动时清理
        lock_file = vector_dir / ".lock"
        if lock_file.exists():
            try:
                lock_file.unlink()
                logger.info("Removed stale Qdrant lock file: %s", lock_file)
            except OSError:
                logger.warning("Cannot remove Qdrant lock file (maybe another instance is running): %s", lock_file)

        self._client = QdrantClient(path=str(vector_dir))
        if settings.dashscope_api_key:
            self._embedding_client = OpenAI(
                base_url=settings.qwen_base_url,
                api_key=settings.dashscope_api_key,
                timeout=30.0,
                max_retries=1,
            )
        self._ready = True
        logger.info("Vector search initialized. provider=qdrant path=%s", vector_dir)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "provider": self._provider,
            "initialized": self._initialized,
            "ready": self._ready,
            "last_error": self._last_error,
            "collection_name": settings.vector_collection_name,
        }

    def index_asset_prompt(
        self,
        *,
        asset_id: int,
        prompt: str,
        summary: str | None,
        keywords: list[str] | None,
    ) -> None:
        self._ensure_ready()
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise ApiError(status_code=400, code="EMPTY_PROMPT", message="Prompt for vector indexing cannot be empty.")

        vector = self._embed_text(normalized_prompt)
        self._ensure_collection(len(vector))

        payload = {
            "asset_id": asset_id,
            "prompt": normalized_prompt,
            "summary": (summary or "").strip(),
            "keywords": [item for item in (keywords or []) if isinstance(item, str) and item.strip()],
        }
        self._client.upsert(
            collection_name=settings.vector_collection_name,
            points=[qdrant.PointStruct(id=asset_id, vector=vector, payload=payload)],
            wait=True,
        )

    def search_assets(
        self,
        *,
        query: str,
        limit: int,
        offset: int,
        asset_ids: list[int] | None = None,
    ) -> tuple[list[VectorHit], int]:
        self._ensure_ready()
        normalized_query = query.strip()
        if not normalized_query:
            raise ApiError(status_code=400, code="EMPTY_QUERY", message="Search query cannot be empty.")
        t_embed = perf_counter()
        vector = self._embed_text(normalized_query)
        t_embed_elapsed = (perf_counter() - t_embed) * 1000
        self._ensure_collection(len(vector))
        query_filter = None
        if asset_ids is not None:
            if not asset_ids:
                return [], 0
            query_filter = qdrant.Filter(must=[qdrant.HasIdCondition(has_id=asset_ids)])
        t_qdrant = perf_counter()
        hits = self._client.search(
            collection_name=settings.vector_collection_name,
            query_vector=vector,
            limit=limit,
            offset=offset,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False,
        )
        t_qdrant_elapsed = (perf_counter() - t_qdrant) * 1000
        total = self._client.count(
            collection_name=settings.vector_collection_name,
            count_filter=query_filter,
            exact=True,
        ).count
        logger.info(
            "[vector-search] query=%r embed=%.0fms qdrant_search=%.0fms hits=%d total=%d",
            normalized_query, t_embed_elapsed, t_qdrant_elapsed, len(hits), total,
        )
        return [
            VectorHit(
                asset_id=int(hit.id),
                score=float(hit.score),
                prompt=(hit.payload or {}).get("prompt", ""),
                summary=(hit.payload or {}).get("summary", ""),
                keywords=(hit.payload or {}).get("keywords", []),
            )
            for hit in hits
        ], int(total)

    def delete_asset(self, asset_id: int) -> None:
        if not self._ready or not self._client:
            return
        self._client.delete(
            collection_name=settings.vector_collection_name,
            points_selector=qdrant.PointIdsList(points=[asset_id]),
            wait=True,
        )

    def count_indexed(self) -> int:
        if not self._ready or not self._client or not self._collection_exists():
            return 0
        return self._client.count(
            collection_name=settings.vector_collection_name,
            exact=True,
        ).count

    def clear_index(self) -> None:
        if not self._ready or not self._client:
            return
        if self._collection_exists():
            self._client.delete_collection(settings.vector_collection_name)
        self._vector_size = None

    def _ensure_collection(self, vector_size: int) -> None:
        if self._vector_size is not None:
            if self._vector_size != vector_size:
                raise ApiError(
                    status_code=500,
                    code="VECTOR_DIMENSION_MISMATCH",
                    message=f"Vector dimension mismatch: expected {self._vector_size}, got {vector_size}.",
                )
            return
        if self._collection_exists():
            collection = self._client.get_collection(settings.vector_collection_name)
            existing_size = int(collection.config.params.vectors.size)
            if existing_size != vector_size:
                raise ApiError(
                    status_code=500,
                    code="VECTOR_DIMENSION_MISMATCH",
                    message=f"Collection vector size is {existing_size}, embedding size is {vector_size}.",
                )
            self._vector_size = existing_size
            return

        self._client.create_collection(
            collection_name=settings.vector_collection_name,
            vectors_config=qdrant.VectorParams(size=vector_size, distance=qdrant.Distance.COSINE),
        )
        self._vector_size = vector_size

    def _collection_exists(self) -> bool:
        collections = self._client.get_collections().collections
        target = settings.vector_collection_name
        return any(item.name == target for item in collections)

    def _ensure_ready(self) -> None:
        if not self._enabled:
            raise ApiError(status_code=503, code="VECTOR_DISABLED", message="Vector search is disabled.")
        if not self._initialized:
            raise ApiError(status_code=503, code="VECTOR_NOT_INITIALIZED", message="Vector search is not initialized.")
        if not self._ready or not self._client:
            reason = self._last_error or "Vector service is not ready."
            raise ApiError(status_code=503, code="VECTOR_UNAVAILABLE", message=reason)

    def _embed_text(self, text: str) -> list[float]:
        if not settings.dashscope_api_key:
            raise ApiError(
                status_code=503,
                code="EMBEDDING_KEY_MISSING",
                message="DASHSCOPE_API_KEY is missing, embedding service unavailable.",
            )

        cache_key = _embedding_cache_key(settings.text_embedding_model, text)
        cached = _embedding_cache().get(cache_key)
        if cached is not None:
            logger.info("[embedding] cache_hit model=%s len=%d", settings.text_embedding_model, len(text))
            return cached

        try:
            resp = self._embedding_client.embeddings.create(
                model=settings.text_embedding_model,
                input=text,
            )
            vector = resp.data[0].embedding
        except Exception as exc:
            raise ApiError(
                status_code=502,
                code="EMBEDDING_REQUEST_FAILED",
                message=f"Embedding API request failed: {exc}",
            ) from exc

        result = [float(item) for item in vector]
        _embedding_cache()[cache_key] = result
        logger.info("[embedding] cached model=%s len=%d dim=%d", settings.text_embedding_model, len(text), len(result))
        return result


# 进程级 LRU 缓存：相同 query + model → 相同向量，避免重复 API 调用
_EMBEDDING_CACHE: dict[str, list[float]] = {}
_EMBEDDING_CACHE_MAX = 512


def _embedding_cache_key(model: str, text: str) -> str:
    return f"{model}::{text.strip()}"


def _embedding_cache() -> dict[str, list[float]]:
    return _EMBEDDING_CACHE


def clear_embedding_cache() -> None:
    _EMBEDDING_CACHE.clear()
    logger.info("Embedding cache cleared.")


vector_search_service = VectorSearchService()
