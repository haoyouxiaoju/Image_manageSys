from fastapi import Request

from app.core.exceptions import ApiError
from app.core.security import decode_access_token
from app.repositories import user_repository


def get_current_user(request: Request, required: bool = True) -> dict | None:
    token = getattr(request.state, "access_token", None)
    if not token:
        if required:
            raise ApiError(status_code=401, code="MISSING_TOKEN", message="Authorization token is required.")
        return None

    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise ApiError(status_code=401, code="INVALID_TOKEN", message="Token subject is missing.")

    user = user_repository.get_user_by_username(username)
    if user is None:
        raise ApiError(status_code=401, code="USER_NOT_FOUND", message="User for this token does not exist.")
    return user


def require_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise ApiError(status_code=403, code="FORBIDDEN", message="Admin role is required for this operation.")

