from app.core.database import get_connection


def list_collections() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.name, c.description, c.creator, c.created_at, COUNT(ca.asset_id) AS asset_count
            FROM collections c
            LEFT JOIN collection_assets ca ON ca.collection_id = c.id
            GROUP BY c.id
            ORDER BY c.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_collection(name: str, description: str, creator: str) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO collections (name, description, creator) VALUES (?, ?, ?)",
            (name, description, creator),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT id, name, description, creator, created_at
            FROM collections
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    result = dict(row)
    result["asset_count"] = 0
    return result


def get_collection_by_id(collection_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT c.id, c.name, c.description, c.creator, c.created_at, COUNT(ca.asset_id) AS asset_count
            FROM collections c
            LEFT JOIN collection_assets ca ON ca.collection_id = c.id
            WHERE c.id = ?
            GROUP BY c.id
            """,
            (collection_id,),
        ).fetchone()
    return dict(row) if row else None


def update_collection(collection_id: int, name: str, description: str) -> dict | None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE collections SET name = ?, description = ? WHERE id = ?",
            (name, description, collection_id),
        )
        conn.commit()
    return get_collection_by_id(collection_id)


def delete_collection(collection_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        conn.commit()
        return cursor.rowcount > 0


def add_asset_to_collection(collection_id: int, asset_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO collection_assets (collection_id, asset_id) VALUES (?, ?)",
            (collection_id, asset_id),
        )
        conn.commit()


def remove_asset_from_collection(collection_id: int, asset_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM collection_assets WHERE collection_id = ? AND asset_id = ?",
            (collection_id, asset_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_collection_assets(collection_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name, a.description, a.source, a.file_name, a.file_path, a.file_size, a.mime_type,
                   a.uploaded_by, a.created_at, a.updated_at
            FROM collection_assets ca
            JOIN assets a ON a.id = ca.asset_id
            WHERE ca.collection_id = ?
            ORDER BY a.id DESC
            """,
            (collection_id,),
        ).fetchall()
    return [dict(row) for row in rows]
