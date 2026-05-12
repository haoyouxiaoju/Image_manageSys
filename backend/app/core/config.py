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


def _default_vector_db_path() -> str:
    project_root = Path(__file__).resolve().parents[3]
    return str(project_root / "data" / "vector_db")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Image_manageSys Backend")
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
    vision_enabled: bool = _parse_bool(os.getenv("VISION_ENABLED", "true"), default=True)
    vision_provider: str = os.getenv("VISION_PROVIDER", "qwen3_vl")
    vision_model_name: str = os.getenv("VISION_MODEL_NAME", "qwen3-vl-plus")
    vision_model_revision: str = os.getenv("VISION_MODEL_REVISION", "main")
    vision_required_on_upload: bool = _parse_bool(os.getenv("VISION_REQUIRED_ON_UPLOAD", "false"), default=False)
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", os.getenv("bailian-DASHSCOPE_API_KEY",""))
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    text_embedding_model: str = os.getenv("TEXT_EMBEDDING_MODEL", "text-embedding-v4")
    vector_enabled: bool = _parse_bool(os.getenv("VECTOR_ENABLED", "true"), default=True)
    vector_provider: str = os.getenv("VECTOR_PROVIDER", "qdrant")
    vector_collection_name: str = os.getenv("VECTOR_COLLECTION_NAME", "asset_prompts")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", _default_vector_db_path())
    agent_enabled: bool = _parse_bool(os.getenv("AGENT_ENABLED", "true"), default=True)
    agent_chat_model: str = os.getenv("AGENT_CHAT_MODEL", "qwen-plus")
    agent_max_tool_calls: int = int(os.getenv("AGENT_MAX_TOOL_CALLS", "5"))


settings = Settings()

