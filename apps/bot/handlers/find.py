"""Match finding handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.api_client import api_client
from models import User, UserTopic

router = Router()


@router.message(Command("find"))  # type: ignore[misc]
async def cmd_find(message: Message, db: AsyncSession) -> None:
    """Handle /find command - find a conversation partner."""
    # Check if user exists and has profile
    result = await db.execute(select(User).where(User.tg_id == message.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ Сначала создайте профиль командой /profile\n\nЭто займет всего 2 минуты!")
        return

    # Check if user has at least 2 topics
    result = await db.execute(select(UserTopic).where(UserTopic.user_id == user.id))
    topics_count = len(result.scalars().all())

    if topics_count < 2:
        await message.answer("❌ Добавьте минимум 2 темы в профиле\n\nИспользуйте команду /profile для настройки")
        return

    # Check if user confirmed safety rules
    if not user.safety_ack:
        await message.answer("❌ Подтвердите правила безопасности в профиле: /profile")
        return

    # Add user to match queue via API
    try:
        response = await api_client.post("/match/find", json={"user_id": user.id})
        if response.get("status") == "queued":
            await message.answer(
                "🔍 Ищу для вас собеседника...\n\n"
                "Это может занять до минуты. Я пришлю вам уведомление, когда найду подходящего человека."
            )
        else:
            await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
    except Exception as e:
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
        import logging

        logging.error(f"Failed to add user to match queue: {e}")


@router.callback_query(F.data.startswith("match_accept_"))  # type: ignore[misc]
async def handle_match_accept(callback: CallbackQuery, db: AsyncSession) -> None:
    """Handle match acceptance."""
    # Extract match_id from callback data
    match_id = int(callback.data.split("_")[2])

    # Get user from database
    result = await db.execute(select(User).where(User.tg_id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        # Call API to confirm match
        response = await api_client.post(
            "/match/confirm", json={"match_id": match_id, "action": "accept", "user_id": user.id}
        )

        if response.get("status") == "active":
            await callback.message.edit_text(
                "✅ Совпадение!\n\n"
                "Чат создан. Ваш собеседник сейчас получит интро-сообщение и правила.\n\n"
                "Будьте уважительны и помните о правилах безопасного общения! 💚"
            )
        elif response.get("status") == "expired":
            await callback.message.edit_text("⏰ Время ожидания истекло. Попробуйте /find снова.")
        else:
            await callback.message.edit_text("✅ Вы приняли предложение\n\nОжидаем ответа от собеседника...")
        await callback.answer()
    except Exception as e:
        await callback.answer("⚠️ Ошибка. Попробуйте позже.", show_alert=True)
        import logging

        logging.error(f"Failed to accept match: {e}")


@router.callback_query(F.data.startswith("match_decline_"))  # type: ignore[misc]
async def handle_match_decline(callback: CallbackQuery, db: AsyncSession) -> None:
    """Handle match decline."""
    # Extract match_id from callback data
    match_id = int(callback.data.split("_")[2])

    # Get user from database
    result = await db.execute(select(User).where(User.tg_id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    try:
        # Call API to decline match
        response = await api_client.post(
            "/match/confirm", json={"match_id": match_id, "action": "decline", "user_id": user.id}
        )

        if response.get("status") == "declined":
            await callback.message.edit_text(
                "👌 Хорошо, пропускаем этого собеседника.\n\nПродолжаю искать для вас подходящего человека..."
            )
        await callback.answer()
    except Exception as e:
        await callback.answer("⚠️ Ошибка. Попробуйте позже.", show_alert=True)
        import logging

        logging.error(f"Failed to decline match: {e}")
