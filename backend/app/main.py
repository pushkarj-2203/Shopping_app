"""
PriceWise AI Engine — application entrypoint.

Composes the production stack: structured logging, request-id middleware,
CORS, dependency-based rate limiting, Prometheus metrics, a global exception
handler, and the versioned API router. Database tables and the demo catalog are
initialised on startup via the lifespan handler.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import alerts, auth, chat, engine, health
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, request_id_ctx
from app.db.session import init_db
from app.services.engine_service import get_engine

configure_logging()
logger = get_logger("pricewise")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (env=%s)", settings.APP_NAME, settings.ENVIRONMENT)
    await init_db()
    get_engine()  # warm the singleton + seed catalog
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="3.0.0",
    description="Consumer-first AI engine for honest product recommendations.",
    docs_url="/docs",
    lifespan=lifespan,
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    request_id_ctx.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        raise
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["x-request-id"] = rid
    response.headers["x-response-time-ms"] = f"{elapsed:.1f}"
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method, request.url.path, response.status_code, elapsed,
        extra={"extra_fields": {"method": request.method, "path": request.url.path,
                                "status": response.status_code, "latency_ms": round(elapsed, 1)}},
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("500 on %s %s", request.method, request.url.path)
    detail = str(exc) if settings.DEBUG else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


try:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
except Exception:  # noqa: BLE001
    logger.info("prometheus-fastapi-instrumentator not installed; /metrics disabled")


p = settings.API_V1_PREFIX
app.include_router(health.router)
app.include_router(auth.router, prefix=p)
app.include_router(engine.router, prefix=p)
app.include_router(chat.router, prefix=p)
app.include_router(alerts.router, prefix=p)


@app.get("/", tags=["system"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "3.0.0",
        "docs": "/docs",
        "philosophy": "We ask what you need, then tell you honestly whether to buy it.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
