"""Tips/payment handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("tips"))
async def cmd_tips(message: Message) -> None:
    """Handle /tips command - send tips to conversation partner."""
    # TODO: Implement tips
    # 1. Check if user has active or recent chat
    # 2. Show tip amount options
    # 3. Create Telegram Stars invoice
    # 4. Process payment

    await message.answer(
        "⭐ Чаевые (в разработке)\n\n"
        "Скоро здесь можно будет:\n"
        "• Отблагодарить собеседника\n"
        "• Отправить чаевые через Telegram Stars\n"
        "• Поддержать проект"
    )
