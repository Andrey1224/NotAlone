"""Inline keyboard builders."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_topics_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for topic selection."""
    # TODO: Load topics from database
    topics = [
        ("💔 Развод", "topic_divorce"),
        ("🔥 Выгорание", "topic_burnout"),
        ("🏠 Переезд", "topic_relocation"),
        ("💼 Смена работы", "topic_job_change"),
        ("😢 Утрата", "topic_loss"),
        ("🌱 Личностный рост", "topic_growth"),
    ]

    buttons = [[InlineKeyboardButton(text=text, callback_data=callback)] for text, callback in topics]

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
