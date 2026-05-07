from app.core.database import get_connection


def create_audit_log(user: str, action: str, target: str, ip_address: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_logs (user, action, target, ip_address) VALUES (?, ?, ?, ?)",
            (user, action, target, ip_address),
        )
        conn.commit()


def list_audit_logs(
    user: str | None = None,
    action: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    where_parts: list[str] = []
    params: list = []
    if user:
        where_parts.append("user = ?")
        params.append(user)
    if action:
        where_parts.append("action = ?")
        params.append(action)
    if start_date:
        where_parts.append("created_at >= ?")
        params.append(start_date)
    if end_date:
        where_parts.append("created_at <= ?")
        params.append(end_date)

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, user, action, target, ip_address, created_at
            FROM audit_logs
            {where_clause}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]
