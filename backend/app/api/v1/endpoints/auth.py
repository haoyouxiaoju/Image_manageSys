from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    version: str = "0.1.0"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    token = f"dev-token-{payload.username}"
    return LoginResponse(token=token)

