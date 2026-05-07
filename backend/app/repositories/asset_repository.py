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


def list_assets(
    page: int,
    page_size: int,
    query: str | None = None,
    tags: list[str] | None = None,
    sort: str = "date_desc",
) -> dict:
    where_parts: list[str] = []
    params: list = []
    if query:
        where_parts.append("(name LIKE ? OR description LIKE ? OR source LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like, like])
    if tags:
        for tag in tags:
            where_parts.append(
                """
                EXISTS (
                    SELECT 1
                    FROM asset_tags at
                    JOIN tags t ON at.tag_id = t.id
                    WHERE at.asset_id = assets.id AND t.name = ?
                )
                """
            )
            params.append(tag)

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    order_by = {
        "date_desc": "created_at DESC, id DESC",
        "date_asc": "created_at ASC, id ASC",
        "name": "name ASC, id DESC",
    }.get(sort, "created_at DESC, id DESC")

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
            ORDER BY {order_by}
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


def list_asset_versions(asset_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, asset_id, version, note, file_name, file_path, file_size, mime_type, created_by, created_at
            FROM asset_versions
            WHERE asset_id = ?
            ORDER BY id DESC
            """,
            (asset_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_asset_version(
    asset_id: int,
    version: str,
    note: str,
    file_name: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    created_by: str,
) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO asset_versions (
                asset_id, version, note, file_name, file_path, file_size, mime_type, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_id, version, note, file_name, file_path, file_size, mime_type, created_by),
        )
        conn.commit()
        version_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT id, asset_id, version, note, file_name, file_path, file_size, mime_type, created_by, created_at
            FROM asset_versions
            WHERE id = ?
            """,
            (version_id,),
        ).fetchone()
    return dict(row)


def list_asset_tag_names(asset_id: int) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.name
            FROM asset_tags at
            JOIN tags t ON at.tag_id = t.id
            WHERE at.asset_id = ?
            ORDER BY t.name ASC
            """,
            (asset_id,),
        ).fetchall()
    return [row["name"] for row in rows]


def replace_asset_tags(asset_id: int, tag_names: list[str]) -> list[str]:
    normalized = sorted({name.strip() for name in tag_names if name and name.strip()})
    with get_connection() as conn:
        conn.execute("DELETE FROM asset_tags WHERE asset_id = ?", (asset_id,))
        for tag_name in normalized:
            tag_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if tag_row is None:
                cursor = conn.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid
            else:
                tag_id = tag_row["id"]
            conn.execute(
                "INSERT INTO asset_tags (asset_id, tag_id) VALUES (?, ?)",
                (asset_id, tag_id),
            )
        conn.commit()
    return normalized

