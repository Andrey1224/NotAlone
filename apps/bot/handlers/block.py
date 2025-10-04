"""Block handler for immediate session termination."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from apps.bot.api_client import api_client
from apps.bot.redis import clear_active_session, get_active_session

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("block"))
async def cmd_block(message: Message) -> None:
    """
    Handle /block command - immediately end active session and impose cooldown.

    This is a user-initiated block (not moderation action).
    Effects:
    - Ends active chat_session
    - Marks match as completed
    - Adds 30-day cooldown in both directions (prevents rematching)

    Requires active chat session to determine who to block.
    """
    if not message.from_user:
        return

    # Get active session from Redis
    session = await get_active_session(message.from_user.id)

    if not session:
        await message.answer(
            "❌ У вас нет активного диалога.\n\nКоманда /block доступна только во время активной беседы."
        )
        return

    peer_tg_id = session["peer_tg_id"]

    # Call API /reports/block
    try:
        response = await api_client.post(
            "/reports/block",
            json={"peer_tg": peer_tg_id},
            auth_bot=True,
            caller_tg_id=message.from_user.id,
        )

        if response.get("ok") is True:
            # Clear active session for caller
            await clear_active_session(message.from_user.id)

            await message.answer(
                "✅ Диалог завершён, пользователь заблокирован.\n\n"
                "Вы не будете снова сопоставлены с этим собеседником в течение 30 дней.\n\n"
                "Используйте /find, чтобы найти нового собеседника."
            )

            # Notify peer that session was ended
            try:
                await message.bot.send_message(
                    chat_id=peer_tg_id,
                    text="⚠️ Собеседник завершил диалог.\n\nИспользуйте /find, чтобы найти нового собеседника.",
                )
                # Clear peer's active session too
                await clear_active_session(peer_tg_id)

            except Exception as e:
                logger.error(f"Failed to notify peer {peer_tg_id} about block: {e}")

        else:
            await message.answer("❌ Не удалось заблокировать пользователя")

    except Exception as e:
        logger.error(f"Failed to block peer: {e}")
        await message.answer("❌ Ошибка при блокировке пользователя")
