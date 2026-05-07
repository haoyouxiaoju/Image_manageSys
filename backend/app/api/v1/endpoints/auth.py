from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, status

from app.core.exceptions import ApiError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.repositories import user_repository

router = APIRouter()
ADMIN_ROLE = "admin"
EDITOR_ROLE = "editor"


class CredentialsRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: str


def _token_response(username: str, role: str) -> TokenResponse:
    token, expires_in = create_access_token(username, role)
    return TokenResponse(access_token=token, expires_in=expires_in, role=role)


def _read_current_user(request: Request) -> dict:
    token = getattr(request.state, "access_token", None)
    if not token:
        raise ApiError(status_code=401, code="MISSING_TOKEN", message="Authorization token is required.")

    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise ApiError(status_code=401, code="INVALID_TOKEN", message="Token subject is missing.")

    user = user_repository.get_user_by_username(username)
    if user is None:
        raise ApiError(status_code=401, code="USER_NOT_FOUND", message="User for this token does not exist.")
    return user


def _require_admin(user: dict) -> None:
    if user["role"] != ADMIN_ROLE:
        raise ApiError(status_code=403, code="FORBIDDEN", message="Admin role is required for this operation.")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: CredentialsRequest) -> TokenResponse:
    existed = user_repository.get_user_by_username(payload.username)
    if existed is not None:
        raise ApiError(status_code=409, code="USER_EXISTS", message="Username is already registered.")

    user_count = user_repository.count_users()
    role = ADMIN_ROLE if user_count == 0 else EDITOR_ROLE
    password_hash = hash_password(payload.password)
    user_repository.create_user(payload.username, password_hash, role)
    return _token_response(payload.username, role)


@router.post("/login", response_model=TokenResponse)
async def login(payload: CredentialsRequest) -> TokenResponse:
    user = user_repository.get_user_by_username(payload.username)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise ApiError(status_code=401, code="INVALID_CREDENTIALS", message="Username or password is incorrect.")
    return _token_response(user["username"], user["role"])


@router.get("/me", response_model=UserResponse)
async def me(request: Request) -> UserResponse:
    user = _read_current_user(request)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        created_at=user["created_at"],
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(request: Request) -> list[UserResponse]:
    current_user = _read_current_user(request)
    _require_admin(current_user)

    users = user_repository.list_users()
    return [
        UserResponse(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            created_at=user["created_at"],
        )
        for user in users
    ]

