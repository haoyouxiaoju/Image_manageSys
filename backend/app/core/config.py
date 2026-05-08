from dataclasses import dataclass, field
import os
from pathlib import Path


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _default_database_path() -> str:
    project_root = Path(__file__).resolve().parents[3]
    return str(project_root / "data" / "sqlite" / "app.db")


def _default_uploads_dir() -> str:
    project_root = Path(__file__).resolve().parents[3]
    return str(project_root / "data" / "uploads")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CLIP-Image_manageSys Backend")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    api_version: str = os.getenv("API_VERSION", "v1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cors_origins: list[str] = field(
        default_factory=lambda: _parse_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        )
    )
    request_id_header: str = os.getenv("REQUEST_ID_HEADER", "X-Request-ID")
    auth_header_name: str = os.getenv("AUTH_HEADER_NAME", "Authorization")
    database_path: str = os.getenv("DATABASE_PATH", _default_database_path())
    uploads_dir: str = os.getenv("UPLOADS_DIR", _default_uploads_dir())
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-change-this-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    clip_enabled: bool = _parse_bool(os.getenv("CLIP_ENABLED", "true"), default=True)
    clip_provider: str = os.getenv("CLIP_PROVIDER", "chinese_clip")
    clip_model_name: str = os.getenv("CLIP_MODEL_NAME", "OFA-Sys/chinese-clip-vit-base-patch16")
    clip_model_revision: str = os.getenv("CLIP_MODEL_REVISION", "main")
    clip_device: str = os.getenv("CLIP_DEVICE", "cpu")
    clip_required_on_upload: bool = _parse_bool(os.getenv("CLIP_REQUIRED_ON_UPLOAD", "false"), default=False)


settings = Settings()

