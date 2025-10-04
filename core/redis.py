from typing import Any

import redis.asyncio as redis

from core.config import settings

_redis_client: redis.Redis[Any] | None = None


async def get_redis() -> redis.Redis[Any]:
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
