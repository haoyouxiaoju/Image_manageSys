from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.core.auth_context import get_current_user, require_admin
from app.repositories import audit_repository

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    user: str
    action: str
    target: str
    ip_address: str
    created_at: str


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    request: Request,
    user_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> list[AuditLogResponse]:
    current_user = get_current_user(request, required=True)
    require_admin(current_user)
    rows = audit_repository.list_audit_logs(
        user=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
    )
    return [AuditLogResponse(**row) for row in rows]

