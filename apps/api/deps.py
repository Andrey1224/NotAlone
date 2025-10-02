"""FastAPI dependencies."""

from collections.abc import AsyncGenerator

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db as _get_db
from core.redis import get_redis as _get_redis


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in _get_db():
        yield session


async def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    return await _get_redis()
