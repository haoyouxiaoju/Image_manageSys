from app.core.database import get_connection


def create_asset(
    name: str,
    description: str,
    source: str,
    file_name: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    uploaded_by: str,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO assets (
                name, description, source, file_name, file_path, file_size, mime_type, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, description, source, file_name, file_path, file_size, mime_type, uploaded_by),
        )
        conn.commit()
        asset_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT id, name, description, source, file_name, file_path, file_size, mime_type,
                   uploaded_by, created_at, updated_at
            FROM assets
            WHERE id = ?
            """,
            (asset_id,),
        ).fetchone()
    return dict(row)


def get_asset_by_id(asset_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, description, source, file_name, file_path, file_size, mime_type,
                   uploaded_by, created_at, updated_at
            FROM assets
            WHERE id = ?
            """,
            (asset_id,),
        ).fetchone()
    return dict(row) if row else None


def list_assets(page: int, page_size: int, query: str | None = None) -> dict:
    where_clause = ""
    params: list = []
    if query:
        where_clause = "WHERE name LIKE ? OR description LIKE ? OR source LIKE ?"
        like = f"%{query}%"
        params.extend([like, like, like])

    with get_connection() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) AS total FROM assets {where_clause}",
            params,
        ).fetchone()
        total = int(total_row["total"])

        offset = (page - 1) * page_size
        rows = conn.execute(
            f"""
            SELECT id, name, description, source, file_name, file_path, file_size, mime_type,
                   uploaded_by, created_at, updated_at
            FROM assets
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()

    return {"total": total, "items": [dict(row) for row in rows]}


def update_asset(asset_id: int, name: str, description: str, source: str) -> dict | None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE assets
            SET name = ?, description = ?, source = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (name, description, source, asset_id),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT id, name, description, source, file_name, file_path, file_size, mime_type,
                   uploaded_by, created_at, updated_at
            FROM assets
            WHERE id = ?
            """,
            (asset_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_asset(asset_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()
        return cursor.rowcount > 0

