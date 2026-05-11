from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import logging
from pathlib import Path
from typing import Any
from urllib import request as urllib_request

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant

from app.core.config import settings
from app.core.exceptions import ApiError

logger = logging.getLogger(__name__)


@dataclass
class VectorHit:
    asset_id: int
    score: float


class VectorSearchService:
    def __init__(self) -> None:
        self._enabled = settings.vector_enabled
        self._provider = settings.vector_provider.strip().lower()
        self._initialized = False
        self._ready = False
        self._last_error: str | None = None
        self._client: QdrantClient | None = None
        self._vector_size: int | None = None

    def initialize(self) -> None:
        self._initialized = True
        self._ready = False
        self._last_error = None
        self._vector_size = None
        self._client = None

        if not self._enabled:
            logger.info("Vector search disabled by VECTOR_ENABLED.")
            return
        if self._provider != "qdrant":
            self._last_error = f"Unsupported VECTOR_PROVIDER: {self._provider}"
            logger.error(self._last_error)
            return

        vector_dir = Path(settings.vector_db_path)
        vector_dir.mkdir(parents=True, exist_ok=True)
        self._client = QdrantClient(path=str(vector_dir))
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
        vector = self._embed_text(normalized_query)
        self._ensure_collection(len(vector))
        query_filter = None
        if asset_ids is not None:
            if not asset_ids:
                return [], 0
            query_filter = qdrant.Filter(must=[qdrant.HasIdCondition(has_id=asset_ids)])
        hits = self._client.search(
            collection_name=settings.vector_collection_name,
            query_vector=vector,
            limit=limit,
            offset=offset,
            query_filter=query_filter,
            with_payload=False,
            with_vectors=False,
        )
        total = self._client.count(
            collection_name=settings.vector_collection_name,
            count_filter=query_filter,
            exact=True,
        ).count
        return [VectorHit(asset_id=int(hit.id), score=float(hit.score)) for hit in hits], int(total)

    def delete_asset(self, asset_id: int) -> None:
        if not self._ready or not self._client:
            return
        self._client.delete(
            collection_name=settings.vector_collection_name,
            points_selector=qdrant.PointIdsList(points=[asset_id]),
            wait=True,
        )

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
        if settings.clip_provider == "mock":
            return _deterministic_embedding(text)
        if not settings.dashscope_api_key:
            raise ApiError(
                status_code=503,
                code="EMBEDDING_KEY_MISSING",
                message="DASHSCOPE_API_KEY is missing, embedding service unavailable.",
            )

        payload = {
            "model": settings.text_embedding_model,
            "input": text,
        }
        url = settings.qwen_base_url.rstrip("/") + "/embeddings"
        req = urllib_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.dashscope_api_key}",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(req, timeout=60) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ApiError(
                status_code=502,
                code="EMBEDDING_REQUEST_FAILED",
                message=f"Embedding API request failed: {exc}",
            ) from exc

        try:
            vector = raw["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ApiError(
                status_code=500,
                code="EMBEDDING_INVALID_RESPONSE",
                message="Embedding response format is invalid.",
            ) from exc
        if not isinstance(vector, list) or not vector:
            raise ApiError(status_code=500, code="EMBEDDING_EMPTY", message="Embedding result is empty.")
        return [float(item) for item in vector]


def _deterministic_embedding(text: str, dim: int = 256) -> list[float]:
    values = [0.0] * dim
    digest = sha256(text.strip().lower().encode("utf-8")).digest()
    if not digest:
        return values
    for idx, byte in enumerate(digest * ((dim // len(digest)) + 1)):
        if idx >= dim:
            break
        values[idx] = (byte / 255.0) * 2.0 - 1.0
    norm = sum(item * item for item in values) ** 0.5
    if norm == 0:
        return values
    return [item / norm for item in values]


vector_search_service = VectorSearchService()
