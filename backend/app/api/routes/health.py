"""Health & readiness probes + Prometheus metrics passthrough."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.cache import get_cache
from app.core.config import settings
from app.db.session import engine
from app.services.engine_service import get_engine

router = APIRouter(tags=["system"])


@router.get("/health")
async def health():
    """Liveness: process is up."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}


@router.get("/ready")
async def ready():
    """Readiness: dependencies reachable."""
    db_ok = True
    try:
        async with engine.connect() as conn:  # noqa: F841
            pass
    except Exception:  # noqa: BLE001
        db_ok = False
    cache_ok = await get_cache().ping()
    products = len(get_engine().products)
    ok = db_ok and cache_ok
    return {
        "status": "ready" if ok else "degraded",
        "database": db_ok,
        "cache": cache_ok,
        "catalog_size": products,
        "llm_provider": settings.LLM_PROVIDER,
    }
