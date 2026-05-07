from app.core.database import get_connection


def list_share_links(created_by: str | None = None) -> list[dict]:
    where_clause = ""
    params: list = []
    if created_by:
        where_clause = "WHERE s.created_by = ?"
        params.append(created_by)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT s.id, s.asset_id, s.token, s.created_by, s.created_at, s.expires_at, s.is_active,
                   a.name AS asset_name
            FROM share_links s
            JOIN assets a ON a.id = s.asset_id
            {where_clause}
            ORDER BY s.id DESC
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def create_share_link(asset_id: int, token: str, created_by: str, expires_at: str) -> dict:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO share_links (asset_id, token, created_by, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (asset_id, token, created_by, expires_at),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT s.id, s.asset_id, s.token, s.created_by, s.created_at, s.expires_at, s.is_active,
                   a.name AS asset_name
            FROM share_links s
            JOIN assets a ON a.id = s.asset_id
            WHERE s.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def get_share_link_by_id(share_link_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT s.id, s.asset_id, s.token, s.created_by, s.created_at, s.expires_at, s.is_active,
                   a.name AS asset_name
            FROM share_links s
            JOIN assets a ON a.id = s.asset_id
            WHERE s.id = ?
            """,
            (share_link_id,),
        ).fetchone()
    return dict(row) if row else None


def revoke_share_link(share_link_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE share_links SET is_active = 0 WHERE id = ?",
            (share_link_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
