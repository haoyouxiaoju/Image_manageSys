from app.core.database import get_connection


def list_tags() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.id, t.name, t.created_at, COUNT(at.asset_id) AS asset_count
            FROM tags t
            LEFT JOIN asset_tags at ON at.tag_id = t.id
            GROUP BY t.id
            ORDER BY t.name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_tag(name: str) -> dict:
    with get_connection() as conn:
        existed = conn.execute("SELECT id, name, created_at FROM tags WHERE name = ?", (name,)).fetchone()
        if existed:
            return dict(existed)
        cursor = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        conn.commit()
        row = conn.execute(
            "SELECT id, name, created_at FROM tags WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def delete_tag(tag_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
        return cursor.rowcount > 0
