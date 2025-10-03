"""End chat session handler."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from apps.bot.api_client import api_client

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("end"))  # type: ignore[misc]
async def cmd_end(message: Message) -> None:
    """
    Handle /end command - end active chat session.

    Shows confirmation button before actually ending.
    """
    if not message.from_user:
        return

    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, завершить диалог", callback_data=f"end_confirm:{message.from_user.id}"
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="end_cancel"),
            ]
        ]
    )

    await message.answer(
        "❓ Вы уверены, что хотите завершить диалог?\n\nЭто остановит пересылку сообщений между вами и собеседником.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("end_confirm:"))  # type: ignore[misc]
async def handle_end_confirm(callback: CallbackQuery) -> None:
    """Handle end confirmation callback."""
    if not callback.from_user or not callback.message:
        return

    # Parse user_id from callback data
    try:
        _, user_id_str = callback.data.split(":")  # type: ignore[union-attr]
        user_id = int(user_id_str)

        # Security: ensure user can only end their own chats
        if callback.from_user.id != user_id:
            await callback.answer("❌ Ошибка авторизации", show_alert=True)
            return

        # Call API to end chat
        response = await api_client.post("/chat/end", json={"user_id": user_id})

        peer_tg_id = response.get("peer_tg_id")
        match_id = response.get("match_id")

        # Create tips CTA keyboard for initiator
        tips_keyboard = None
        if match_id and peer_tg_id:
            from apps.bot.handlers.tips import PRESETS

            buttons = []
            for amount in PRESETS[:2]:  # Show only first 2 presets (5, 10 Stars)
                callback_data = f"tip:{match_id}:{peer_tg_id}:{amount}"
                buttons.append(InlineKeyboardButton(text=f"💙 Отправить {amount} ⭐", callback_data=callback_data))

            tips_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

        # Notify initiator
        await callback.message.edit_text(
            "✅ Диалог завершён. Спасибо за общение!\n\n"
            "💚 Вы можете начать новый поиск командой /find\n\n"
            "💙 Хотите поблагодарить собеседника?",
            reply_markup=tips_keyboard,
        )

        # Notify peer with tips CTA
        if peer_tg_id:
            # Lazy import to avoid circular dependency
            from apps.bot.bot import bot

            # Create tips keyboard for peer (reverse: peer can tip the initiator)
            peer_tips_keyboard = None
            if match_id and callback.from_user:
                from apps.bot.handlers.tips import PRESETS

                buttons = []
                for amount in PRESETS[:2]:  # Show only first 2 presets
                    callback_data = f"tip:{match_id}:{callback.from_user.id}:{amount}"
                    buttons.append(InlineKeyboardButton(text=f"💙 Отправить {amount} ⭐", callback_data=callback_data))

                peer_tips_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

            await bot.send_message(
                chat_id=peer_tg_id,
                text="📞 Собеседник завершил диалог.\n\n"
                "Спасибо за общение! Надеемся, что разговор был полезным.\n\n"
                "💚 Вы можете начать новый поиск командой /find\n\n"
                "💙 Хотите поблагодарить собеседника?",
                reply_markup=peer_tips_keyboard,
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Failed to end chat: {e}")
        await callback.answer("❌ Нет активного диалога", show_alert=True)


@router.callback_query(F.data == "end_cancel")  # type: ignore[misc]
async def handle_end_cancel(callback: CallbackQuery) -> None:
    """Handle end cancellation callback."""
    if not callback.message:
        return

    await callback.message.edit_text("↩️ Отменено. Диалог продолжается.")
    await callback.answer()
