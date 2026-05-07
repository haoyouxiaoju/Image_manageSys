from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from app.core.auth_context import get_current_user, require_editor_or_admin
from app.core.exceptions import ApiError
from app.repositories import asset_repository, collection_repository

router = APIRouter()


class CollectionResponse(BaseModel):
    id: int
    name: str
    description: str
    asset_count: int
    creator: str
    created_at: str


class CollectionDetailResponse(CollectionResponse):
    assets: list[dict]


class CollectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=1000)


class CollectionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)


class CollectionAssetAddRequest(BaseModel):
    asset_id: int


def _ensure_collection_manage_permission(user: dict, collection: dict) -> None:
    if user["role"] == "admin":
        return
    if user["role"] == "editor" and collection["creator"] == user["username"]:
        return
    raise ApiError(status_code=403, code="FORBIDDEN", message="No permission to modify this collection.")


def _to_collection_response(row: dict) -> CollectionResponse:
    return CollectionResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        asset_count=row["asset_count"],
        creator=row["creator"],
        created_at=row["created_at"],
    )


@router.get("", response_model=list[CollectionResponse])
async def list_collections() -> list[CollectionResponse]:
    rows = collection_repository.list_collections()
    return [_to_collection_response(row) for row in rows]


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(payload: CollectionCreateRequest, request: Request) -> CollectionResponse:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    row = collection_repository.create_collection(
        name=payload.name.strip(),
        description=payload.description.strip(),
        creator=user["username"],
    )
    return _to_collection_response(row)


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(collection_id: int) -> CollectionDetailResponse:
    row = collection_repository.get_collection_by_id(collection_id)
    if row is None:
        raise ApiError(status_code=404, code="COLLECTION_NOT_FOUND", message="Collection does not exist.")
    assets = collection_repository.list_collection_assets(collection_id)
    for asset in assets:
        asset["tags"] = asset_repository.list_asset_tag_names(asset["id"])
    return CollectionDetailResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        asset_count=row["asset_count"],
        creator=row["creator"],
        created_at=row["created_at"],
        assets=assets,
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(collection_id: int, payload: CollectionUpdateRequest, request: Request) -> CollectionResponse:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    existed = collection_repository.get_collection_by_id(collection_id)
    if existed is None:
        raise ApiError(status_code=404, code="COLLECTION_NOT_FOUND", message="Collection does not exist.")
    _ensure_collection_manage_permission(user, existed)

    row = collection_repository.update_collection(
        collection_id=collection_id,
        name=(payload.name if payload.name is not None else existed["name"]).strip(),
        description=(payload.description if payload.description is not None else existed["description"]).strip(),
    )
    return _to_collection_response(row)


@router.delete("/{collection_id}")
async def delete_collection(collection_id: int, request: Request) -> dict[str, str]:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    existed = collection_repository.get_collection_by_id(collection_id)
    if existed is None:
        raise ApiError(status_code=404, code="COLLECTION_NOT_FOUND", message="Collection does not exist.")
    _ensure_collection_manage_permission(user, existed)
    collection_repository.delete_collection(collection_id)
    return {"message": "Collection deleted successfully."}


@router.post("/{collection_id}/assets")
async def add_asset_to_collection(
    collection_id: int,
    payload: CollectionAssetAddRequest,
    request: Request,
) -> dict[str, str]:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    collection = collection_repository.get_collection_by_id(collection_id)
    if collection is None:
        raise ApiError(status_code=404, code="COLLECTION_NOT_FOUND", message="Collection does not exist.")
    _ensure_collection_manage_permission(user, collection)

    asset = asset_repository.get_asset_by_id(payload.asset_id)
    if asset is None:
        raise ApiError(status_code=404, code="ASSET_NOT_FOUND", message="Asset does not exist.")
    collection_repository.add_asset_to_collection(collection_id, payload.asset_id)
    return {"message": "Asset added to collection."}


@router.delete("/{collection_id}/assets/{asset_id}")
async def remove_asset_from_collection(collection_id: int, asset_id: int, request: Request) -> dict[str, str]:
    user = get_current_user(request, required=True)
    require_editor_or_admin(user)
    collection = collection_repository.get_collection_by_id(collection_id)
    if collection is None:
        raise ApiError(status_code=404, code="COLLECTION_NOT_FOUND", message="Collection does not exist.")
    _ensure_collection_manage_permission(user, collection)
    removed = collection_repository.remove_asset_from_collection(collection_id, asset_id)
    if not removed:
        raise ApiError(status_code=404, code="RELATION_NOT_FOUND", message="Asset is not in this collection.")
    return {"message": "Asset removed from collection."}

