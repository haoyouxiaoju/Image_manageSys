from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_database
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.services.clip_service import clip_service

configure_logging()
init_database()
clip_service.initialize()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    clip_service.initialize()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
register_middleware(app, settings)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)

uploads_dir = Path(settings.uploads_dir)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "backend", "version": settings.app_version}

