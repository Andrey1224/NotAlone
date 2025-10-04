"""Report handler for complaints about peers."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from apps.bot.api_client import api_client
from apps.bot.redis import get_active_session

router = Router()
logger = logging.getLogger(__name__)

VALID_REASONS = {
    "spam": "Спам / реклама",
    "abuse": "Оскорбления",
    "danger": "Опасное поведение",
    "other": "Другое",
}


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    """
    Handle /report command - show reason selection keyboard.

    Requires active chat session to determine who to report.
    Context comes from Redis (active_session:{tg_id}).
    """
    if not message.from_user:
        return

    # Get active session from Redis
    session = await get_active_session(message.from_user.id)

    if not session:
        await message.answer("❌ У вас нет активного диалога.\n\nЖалоба доступна только во время активной беседы.")
        return

    # Build inline keyboard with reasons
    buttons = []
    for reason_key, reason_label in VALID_REASONS.items():
        callback_data = f"report:{session['chat_session_id']}:{session['peer_tg_id']}:{reason_key}"
        buttons.append([InlineKeyboardButton(text=reason_label, callback_data=callback_data)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "⚠️ Пожаловаться на собеседника\n\nВыберите причину жалобы. Мы рассмотрим ваше обращение и примем меры.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("report:"))
async def on_report_callback(callback: CallbackQuery) -> None:
    """
    Handle report reason selection callback.

    Callback data format: report:<chat_session_id>:<peer_tg_id>:<reason>

    Steps:
    1. Parse callback data
    2. Call API /reports with HMAC auth
    3. Show confirmation or error message
    """
    if not callback.data or not callback.from_user:
        await callback.answer("❌ Ошибка обработки", show_alert=True)
        return

    # Parse callback data
    try:
        _, chat_session_id_str, peer_tg_id_str, reason = callback.data.split(":")
        chat_session_id = int(chat_session_id_str)
        peer_tg_id = int(peer_tg_id_str)
    except ValueError:
        await callback.answer("❌ Некорректные данные", show_alert=True)
        return

    # Validate reason
    if reason not in VALID_REASONS:
        await callback.answer("❌ Неизвестная причина", show_alert=True)
        return

    # Send report to API
    try:
        response = await api_client.post(
            "/reports",
            json_data={
                "chat_session_id": chat_session_id,
                "to_user_tg": peer_tg_id,
                "reason": reason,
                "comment": None,
            },
            auth_bot=True,
            caller_tg_id=callback.from_user.id,
        )

        if response.get("ok") is True:
            await callback.answer("✅ Жалоба отправлена. Спасибо!", show_alert=True)

            # Edit message to show confirmation
            if callback.message:
                await callback.message.edit_text(
                    f"✅ Жалоба отправлена\n\n"
                    f"Причина: {VALID_REASONS[reason]}\n\n"
                    f"Мы рассмотрим ваше обращение в ближайшее время."
                )

        else:
            await callback.answer("❌ Не удалось отправить жалобу", show_alert=True)

    except Exception as e:
        logger.error(f"Failed to submit report: {e}")
        await callback.answer("❌ Ошибка отправки жалобы", show_alert=True)
