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
from app.repositories import clip_repository
from app.services.clip_service import clip_service
from app.services.vector_search_service import vector_search_service

configure_logging()
init_database()
clip_service.initialize()
vector_search_service.initialize()
if vector_search_service.status()["ready"]:
    for item in clip_repository.list_ready_embeddings_assets():
        prompt = (item.get("generated_prompt") or item.get("suggested_description") or "").strip()
        if not prompt:
            continue
        vector_search_service.index_asset_prompt(
            asset_id=int(item["id"]),
            prompt=prompt,
            summary=item.get("suggested_description"),
            keywords=item.get("suggested_tags") or [],
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    clip_service.initialize()
    vector_search_service.initialize()
    if vector_search_service.status()["ready"]:
        for item in clip_repository.list_ready_embeddings_assets():
            prompt = (item.get("generated_prompt") or item.get("suggested_description") or "").strip()
            if not prompt:
                continue
            vector_search_service.index_asset_prompt(
                asset_id=int(item["id"]),
                prompt=prompt,
                summary=item.get("suggested_description"),
                keywords=item.get("suggested_tags") or [],
            )
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
register_middleware(app, settings)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)

uploads_dir = Path(settings.uploads_dir)
uploads_dir.mkdir(parents=True, exist_ok=True)
# Nginx 在上层处理 /uploads 静态文件，此 mount 仅在开发直连 FastAPI 时生效
app.mount("/files", StaticFiles(directory=str(uploads_dir)), name="files")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "backend", "version": settings.app_version}

