"""Redis utilities for bot - active session management."""

import json
from typing import Any

from core.redis import get_redis


async def set_active_session(tg_id: int, chat_session_id: int, peer_tg_id: int) -> None:
    """
    Store active chat session info for a user.

    Args:
        tg_id: Telegram user ID
        chat_session_id: Database chat_session ID
        peer_tg_id: Peer's Telegram user ID
    """
    redis = await get_redis()
    key = f"active_session:{tg_id}"
    value = json.dumps(
        {
            "chat_session_id": chat_session_id,
            "peer_tg_id": peer_tg_id,
        }
    )
    # TTL: 24 hours (chat sessions expire after inactivity)
    await redis.setex(key, 86400, value)


async def get_active_session(tg_id: int) -> dict[str, Any] | None:
    """
    Get active chat session info for a user.

    Args:
        tg_id: Telegram user ID

    Returns:
        Dict with chat_session_id and peer_tg_id, or None if no active session
    """
    redis = await get_redis()
    key = f"active_session:{tg_id}"
    data = await redis.get(key)
    if not data:
        return None
    return json.loads(data)


async def clear_active_session(tg_id: int) -> None:
    """
    Clear active session for a user (on /end or /block).

    Args:
        tg_id: Telegram user ID
    """
    redis = await get_redis()
    key = f"active_session:{tg_id}"
    await redis.delete(key)
