"""Match finding handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("find"))
async def cmd_find(message: Message) -> None:
    """Handle /find command - find a conversation partner."""
    # TODO: Implement match finding
    # 1. Check if user has profile
    # 2. Add to match queue
    # 3. Show waiting status
    # 4. Notify when match found

    await message.answer(
        "🔍 Поиск собеседника (в разработке)\n\n"
        "Скоро здесь можно будет:\n"
        "• Найти собеседника по интересам\n"
        "• Получить подходящие совпадения\n"
        "• Начать анонимный диалог"
    )
