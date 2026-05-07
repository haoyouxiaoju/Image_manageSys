from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from app.core.auth_context import get_current_user, require_editor_or_admin
from app.core.exceptions import ApiError
from app.repositories import asset_repository, audit_repository, share_link_repository

router = APIRouter()


class ShareLinkResponse(BaseModel):
    id: int
    asset_id: int
    asset_name: str
    token: str
    url: str
    created_by: str
    created_at: str
    expires_at: str
    is_active: bool


class ShareLinkCreateRequest(BaseModel):
    asset_id: int
    expires_in_hours: int = Field(default=24, ge=1, le=720)


def _to_share_link_response(row: dict) -> ShareLinkResponse:
    return ShareLinkResponse(
        id=row["id"],
        asset_id=row["asset_id"],
        asset_name=row["asset_name"],
        token=row["token"],
        url=f"/share/{row['token']}",
        created_by=row["created_by"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        is_active=bool(row["is_active"]),
    )


def _ensure_share_manage_permission(user: dict, row: dict) -> None:
    if user["role"] == "admin":
        return
    if row["created_by"] == user["username"]:
        return
    raise ApiError(status_code=403, code="FORBIDDEN", message="No permission to manage this share link.")


@router.get("", response_model=list[ShareLinkResponse])
async def list_share_links(request: Request) -> list[ShareLinkResponse]:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    rows = share_link_repository.list_share_links()
    if user["role"] != "admin":
        rows = [row for row in rows if row["created_by"] == user["username"]]
    return [_to_share_link_response(row) for row in rows]


@router.post("", response_model=ShareLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_share_link(payload: ShareLinkCreateRequest, request: Request) -> ShareLinkResponse:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)

    asset = asset_repository.get_asset_by_id(payload.asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")

    token = uuid4().hex
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)).isoformat()
    row = share_link_repository.create_share_link(
        asset_id=payload.asset_id,
        token=token,
        created_by=user["username"],
        expires_at=expires_at,
    )
    audit_repository.create_audit_log(
        user=user["username"],
        action="分享",
        target=asset["name"],
        ip_address=request.client.host if request.client else "unknown",
    )
    return _to_share_link_response(row)


@router.delete("/{share_link_id}")
async def revoke_share_link(share_link_id: int, request: Request) -> dict[str, str]:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    row = share_link_repository.get_share_link_by_id(share_link_id)
    if row is None:
        raise ApiError(status_code=404, code="SHARE_LINK_NOT_FOUND", message="Share link does not exist.")
    _ensure_share_manage_permission(user, row)

    share_link_repository.revoke_share_link(share_link_id)
    audit_repository.create_audit_log(
        user=user["username"],
        action="撤销分享",
        target=row["asset_name"],
        ip_address=request.client.host if request.client else "unknown",
    )
    return {"message": "Share link revoked."}

