"""FSM states for profile creation."""

from aiogram.fsm.state import State, StatesGroup


class ProfileForm(StatesGroup):
    """States for profile creation and editing."""

    nickname = State()
    timezone = State()
    topics = State()
    bio = State()
    safety_confirmation = State()
