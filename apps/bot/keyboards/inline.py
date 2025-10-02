"""Inline keyboard builders."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_topics_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    """Build inline keyboard for topic selection."""
    if selected is None:
        selected = set()

    topics = [
        ("💔 Развод", "divorce"),
        ("🔥 Выгорание", "burnout"),
        ("🏠 Переезд", "relocation"),
        ("💼 Смена работы", "job_change"),
        ("😢 Утрата", "loss"),
        ("🌱 Личностный рост", "growth"),
        ("😰 Тревога", "anxiety"),
        ("🫂 Одиночество", "loneliness"),
        ("👶 Родительство", "parenting"),
        ("🏥 Здоровье", "health"),
        ("💑 Отношения", "relationships"),
        ("📈 Карьера", "career"),
    ]

    buttons = []
    for text, slug in topics:
        # Add checkmark if selected
        display_text = f"✅ {text}" if slug in selected else text
        buttons.append([InlineKeyboardButton(text=display_text, callback_data=f"topic_{slug}")])

    # Add "Done" button
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="topics_done")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_timezones_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for timezone selection."""
    timezones = [
        ("🇷🇺 Москва (МСК)", "Europe/Moscow"),
        ("🇷🇺 Екатеринбург (МСК+2)", "Asia/Yekaterinburg"),
        ("🇷🇺 Новосибирск (МСК+4)", "Asia/Novosibirsk"),
        ("🇷🇺 Владивосток (МСК+7)", "Asia/Vladivostok"),
        ("🇺🇦 Киев", "Europe/Kiev"),
        ("🇰🇿 Алматы", "Asia/Almaty"),
        ("🇧🇾 Минск", "Europe/Minsk"),
        ("🇬🇪 Тбилиси", "Asia/Tbilisi"),
        ("🇦🇲 Ереван", "Asia/Yerevan"),
        ("🇦🇿 Баку", "Asia/Baku"),
    ]

    buttons = [[InlineKeyboardButton(text=text, callback_data=f"tz_{tz}")] for text, tz in timezones]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_match_confirmation_keyboard(match_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for match confirmation."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"match_accept_{match_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"match_decline_{match_id}"),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tip_amount_keyboard(match_id: int) -> InlineKeyboardMarkup:
    """Build keyboard for tip amount selection."""
    amounts = [50, 100, 200, 500]
    buttons = [
        [InlineKeyboardButton(text=f"⭐ {amount}", callback_data=f"tip_{match_id}_{amount}")] for amount in amounts
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
