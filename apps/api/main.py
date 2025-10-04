from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.middlewares.metrics import MetricsMiddleware
from apps.api.routers import chat, health, match, payments, reports, telegram, tips
from core import close_redis
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title="Ty Ne Odin API",
    description="API for peer-to-peer support matching bot",
    version="0.1.0",
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(match.router, prefix="/match", tags=["match"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(tips.router)  # Already has /tips prefix
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(reports.router)  # Already has /reports prefix
app.include_router(telegram.router, prefix="/telegram", tags=["telegram"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"status": "ok", "service": "ty-ne-odin"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
