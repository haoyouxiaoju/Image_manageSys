from dataclasses import dataclass, field
import os


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


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


settings = Settings()

