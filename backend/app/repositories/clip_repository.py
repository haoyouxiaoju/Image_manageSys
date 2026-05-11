import json
from typing import Any

from app.core.database import get_connection


def upsert_clip_analysis(
    asset_id: int,
    status: str,
    provider: str,
    model_name: str | None,
    model_version: str | None,
    embedding: list[float] | None,
    features: dict[str, Any] | None,
    suggested_description: str | None,
    suggested_tags: list[str] | None,
    error_message: str | None,
) -> None:
    embedding_json = json.dumps(embedding, ensure_ascii=False) if embedding is not None else None
    features_json = json.dumps(features, ensure_ascii=False) if features is not None else None
    suggested_tags_json = json.dumps(suggested_tags, ensure_ascii=False) if suggested_tags is not None else None
    embedding_dim = len(embedding) if embedding is not None else None

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO asset_clip_analysis (
                asset_id, status, provider, model_name, model_version, embedding_json, embedding_dim, features_json,
                suggested_description, suggested_tags_json, error_message, analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(asset_id) DO UPDATE SET
                status = excluded.status,
                provider = excluded.provider,
                model_name = excluded.model_name,
                model_version = excluded.model_version,
                embedding_json = excluded.embedding_json,
                embedding_dim = excluded.embedding_dim,
                features_json = excluded.features_json,
                suggested_description = excluded.suggested_description,
                suggested_tags_json = excluded.suggested_tags_json,
                error_message = excluded.error_message,
                analyzed_at = datetime('now')
            """,
            (
                asset_id,
                status,
                provider,
                model_name,
                model_version,
                embedding_json,
                embedding_dim,
                features_json,
                suggested_description,
                suggested_tags_json,
                error_message,
            ),
        )
        conn.commit()


def get_clip_analysis(asset_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT asset_id, status, provider, model_name, model_version, embedding_json, embedding_dim, features_json,
                   suggested_description, suggested_tags_json, error_message, analyzed_at
            FROM asset_clip_analysis
            WHERE asset_id = ?
            """,
            (asset_id,),
        ).fetchone()
    if not row:
        return None

    payload = dict(row)
    payload["embedding"] = json.loads(payload.pop("embedding_json")) if payload["embedding_json"] else None
    payload["features"] = json.loads(payload.pop("features_json")) if payload["features_json"] else None
    payload["suggested_tags"] = (
        json.loads(payload.pop("suggested_tags_json")) if payload["suggested_tags_json"] else None
    )
    return payload


def list_ready_embeddings_assets() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id, a.name, a.description, a.source, a.file_name, a.file_path, a.file_size, a.mime_type,
                a.uploaded_by, a.created_at, a.updated_at,
                c.status, c.provider, c.model_name, c.model_version, c.embedding_json, c.embedding_dim,
                c.features_json, c.suggested_description, c.suggested_tags_json, c.error_message, c.analyzed_at
            FROM asset_clip_analysis c
            JOIN assets a ON a.id = c.asset_id
            WHERE c.status = 'ready'
            ORDER BY a.id DESC
            """
        ).fetchall()

    result: list[dict] = []
    for row in rows:
        item = dict(row)
        item["embedding"] = json.loads(item.pop("embedding_json")) if item["embedding_json"] else None
        item["features"] = json.loads(item.pop("features_json")) if item["features_json"] else None
        item["suggested_tags"] = json.loads(item.pop("suggested_tags_json")) if item["suggested_tags_json"] else None
        result.append(item)
    return result
