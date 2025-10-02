"""Profile management handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    """Handle /profile command."""
    # TODO: Implement profile management
    # 1. Show current profile or create new
    # 2. Allow editing: nickname, bio, topics, timezone
    # 3. Save to database

    await message.answer(
        "🔧 Настройка профиля (в разработке)\n\n"
        "Скоро здесь можно будет:\n"
        "• Установить псевдоним\n"
        "• Выбрать темы для обсуждения\n"
        "• Указать часовой пояс\n"
        "• Добавить краткое описание"
    )
