"""Chat message relay handler."""

import logging

from aiogram import F, Router
from aiogram.types import Message

from apps.bot.api_client import api_client

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message) -> None:
    """
    Handle text messages and relay them to active chat peer.

    This is a catch-all handler for text messages (not commands).
    It must be registered LAST in bot.py to avoid intercepting commands.
    """
    if not message.text or not message.from_user:
        return

    try:
        # Call API to relay message
        response = await api_client.post(
            "/chat/relay", json_data={"from_user": message.from_user.id, "text": message.text}
        )

        peer_tg_id = response.get("peer_tg_id")
        sender_nickname = response.get("peer_nickname", "Собеседник")  # Use nickname from API

        if peer_tg_id:
            # Lazy import to avoid circular dependency
            from apps.bot.bot import bot

            # Send message to peer with sender's nickname
            await bot.send_message(chat_id=peer_tg_id, text=f"✉️ {sender_nickname}: {message.text}")

            # Optional: send confirmation to sender
            # await message.answer("✅ Отправлено")

        else:
            await message.answer("❌ Нет активного диалога. Используйте /find для поиска собеседника.")

    except Exception as e:
        logger.error(f"Failed to relay message: {e}")
        await message.answer(
            "❌ Нет активного диалога. Используйте /find для поиска собеседника.\n\n"
            "Если вы только что приняли матч, подождите несколько секунд и попробуйте снова."
        )
