"""Rate limiting middleware."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message


class RateLimitMiddleware(BaseMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, rate_limit: int = 5) -> None:
        """Initialize rate limiter.

        Args:
            rate_limit: Maximum requests per minute
        """
        self.rate_limit = rate_limit
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        """Process message with rate limiting."""
        # TODO: Implement Redis-based rate limiting
        # 1. Check request count for user in last minute
        # 2. Increment counter
        # 3. If exceeded, return error message
        # 4. Otherwise, pass to handler

        return await handler(event, data)
