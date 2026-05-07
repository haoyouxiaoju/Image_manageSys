from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware

configure_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)
register_middleware(app, settings)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "backend", "version": settings.app_version}

