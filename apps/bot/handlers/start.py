"""Start and help command handlers."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    welcome_text = """
👋 Добро пожаловать в "Ты не один"!

Это сервис для поиска собеседников по общим интересам и жизненным ситуациям.

Здесь вы можете:
• Найти поддержку от людей с похожим опытом
• Поделиться своими переживаниями анонимно
• Помочь другим своим опытом

⚠️ Важно: Это не замена профессиональной помощи. При серьезных проблемах обращайтесь к специалистам.

Команды:
/profile - настроить профиль
/find - найти собеседника
/help - помощь и правила
    """.strip()

    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = """
📖 Правила безопасного общения:

1. Будьте уважительны и эмпатичны
2. Не давайте медицинские или юридические советы
3. Уважайте границы собеседника
4. Не делитесь личными данными
5. Не обещайте "всё исправить"

🆘 Если вам нужна срочная помощь:
• Телефон доверия: 8-800-2000-122
• Психологическая помощь: 051 (Москва)

Команды:
/start - начать
/profile - профиль
/find - найти собеседника
/tips - оставить чаевые
    """.strip()

    await message.answer(help_text)
