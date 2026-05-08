import json
from typing import Any

from app.core.database import get_connection


def upsert_clip_analysis(
    asset_id: int,
    status: str,
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
                asset_id, status, model_name, model_version, embedding_json, embedding_dim, features_json,
                suggested_description, suggested_tags_json, error_message, analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(asset_id) DO UPDATE SET
                status = excluded.status,
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
            SELECT asset_id, status, model_name, model_version, embedding_json, embedding_dim, features_json,
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
