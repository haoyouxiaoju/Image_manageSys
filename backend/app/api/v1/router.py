from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.audit_logs import router as audit_logs_router
from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.clip import router as clip_router
from app.api.v1.endpoints.collections import router as collections_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.share_links import router as share_links_router
from app.api.v1.endpoints.tags import router as tags_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(assets_router, prefix="/assets", tags=["assets"])
router.include_router(clip_router, prefix="/clip", tags=["clip"])
router.include_router(search_router, prefix="/search", tags=["search"])
router.include_router(tags_router, prefix="/tags", tags=["tags"])
router.include_router(collections_router, prefix="/collections", tags=["collections"])
router.include_router(share_links_router, prefix="/share-links", tags=["share-links"])
router.include_router(audit_logs_router, prefix="/audit-logs", tags=["audit-logs"])

