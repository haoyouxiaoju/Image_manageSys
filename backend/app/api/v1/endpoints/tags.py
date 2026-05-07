from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from app.core.auth_context import get_current_user, require_editor_or_admin
from app.core.exceptions import ApiError
from app.repositories import tag_repository

router = APIRouter()


class TagResponse(BaseModel):
    id: int
    name: str
    asset_count: int = 0
    created_at: str


class TagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


@router.get("", response_model=list[TagResponse])
async def list_tags() -> list[TagResponse]:
    rows = tag_repository.list_tags()
    return [TagResponse(**row) for row in rows]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreateRequest, request: Request) -> TagResponse:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    row = tag_repository.create_tag(payload.name.strip())
    return TagResponse(id=row["id"], name=row["name"], asset_count=0, created_at=row["created_at"])


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, request: Request) -> dict[str, str]:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    ok = tag_repository.delete_tag(tag_id)
    if not ok:
        raise ApiError(status_code=404, code="TAG_NOT_FOUND", message="Tag does not exist.")
    return {"message": "Tag deleted successfully."}

