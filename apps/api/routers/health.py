"""Health check endpoints."""

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.deps import get_db, get_redis_client

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, str]:
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/db")
async def health_check_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Database health check."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/redis")
async def health_check_redis(redis_client: redis.Redis = Depends(get_redis_client)) -> dict[str, str]:
    """Redis health check."""
    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}
