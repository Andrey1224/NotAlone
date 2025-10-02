"""Reply keyboard builders."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build main menu reply keyboard."""
    buttons = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🔍 Найти собеседника")],
        [KeyboardButton(text="⭐ Чаевые"), KeyboardButton(text="❓ Помощь")],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
