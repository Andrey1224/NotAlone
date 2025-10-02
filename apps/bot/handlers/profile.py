"""Profile management handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.keyboards.inline import get_timezones_keyboard, get_topics_keyboard
from apps.bot.states.profile import ProfileForm
from models import Topic, User, UserTopic

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext, db: AsyncSession) -> None:
    """Handle /profile command - start or edit profile."""
    # Check if user exists
    result = await db.execute(select(User).where(User.tg_id == message.from_user.id))
    user = result.scalar_one_or_none()

    if user:
        # User exists, show profile
        await show_profile(message, user, db)
    else:
        # Start profile creation
        await state.set_state(ProfileForm.nickname)
        await message.answer(
            "👤 Давайте создадим ваш профиль!\n\n" "Введите псевдоним (как вас будут видеть собеседники):"
        )


async def show_profile(message: Message, user: User, db: AsyncSession) -> None:
    """Display user profile."""
    # Load user topics
    result = await db.execute(select(Topic).join(UserTopic).where(UserTopic.user_id == user.id))
    topics = result.scalars().all()
    topics_text = ", ".join(t.title for t in topics) if topics else "не указаны"

    profile_text = f"""
📋 Ваш профиль:

👤 Псевдоним: {user.nickname}
🌍 Часовой пояс: {user.tz}
💬 Темы: {topics_text}
📝 О себе: {user.bio_short or 'не указано'}

Для редактирования используйте команды:
/edit_nickname - изменить псевдоним
/edit_topics - изменить темы
/edit_bio - изменить описание
    """.strip()

    await message.answer(profile_text)


@router.message(ProfileForm.nickname)
async def process_nickname(message: Message, state: FSMContext) -> None:
    """Process nickname input."""
    nickname = message.text.strip()

    if len(nickname) < 2 or len(nickname) > 64:
        await message.answer("Псевдоним должен быть от 2 до 64 символов. Попробуйте снова:")
        return

    await state.update_data(nickname=nickname)
    await state.set_state(ProfileForm.timezone)

    await message.answer(
        f"✅ Отлично, {nickname}!\n\n" "🌍 Теперь выберите ваш часовой пояс:", reply_markup=get_timezones_keyboard()
    )


@router.callback_query(F.data.startswith("tz_"), ProfileForm.timezone)
async def process_timezone(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    """Process timezone selection."""
    timezone = callback.data.split("_", 1)[1]
    await state.update_data(tz=timezone)
    await state.set_state(ProfileForm.topics)

    await callback.message.edit_text(
        f"✅ Часовой пояс: {timezone}\n\n"
        "📌 Выберите темы, которые вас интересуют (минимум 2):\n"
        "Нажимайте на кнопки, чтобы выбрать или отменить выбор.",
        reply_markup=get_topics_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("topic_"), ProfileForm.topics)
async def process_topic_selection(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    """Process topic selection (toggle)."""
    topic_slug = callback.data.split("_", 1)[1]

    # Get current selected topics
    data = await state.get_data()
    selected_topics = data.get("selected_topics", set())

    # Toggle topic
    if topic_slug in selected_topics:
        selected_topics.remove(topic_slug)
    else:
        selected_topics.add(topic_slug)

    await state.update_data(selected_topics=selected_topics)

    # Update keyboard
    await callback.message.edit_reply_markup(reply_markup=get_topics_keyboard(selected_topics))
    await callback.answer(f"Выбрано тем: {len(selected_topics)}")


@router.callback_query(F.data == "topics_done", ProfileForm.topics)
async def process_topics_done(callback: CallbackQuery, state: FSMContext) -> None:
    """Finish topic selection."""
    data = await state.get_data()
    selected_topics = data.get("selected_topics", set())

    if len(selected_topics) < 2:
        await callback.answer("Выберите минимум 2 темы", show_alert=True)
        return

    await state.set_state(ProfileForm.bio)
    await callback.message.edit_text(
        f"✅ Выбрано тем: {len(selected_topics)}\n\n"
        "📝 Напишите немного о себе (до 160 символов).\n"
        "Или отправьте /skip чтобы пропустить этот шаг."
    )
    await callback.answer()


@router.message(ProfileForm.bio, Command("skip"))
async def skip_bio(message: Message, state: FSMContext) -> None:
    """Skip bio step."""
    await state.update_data(bio_short=None)
    await state.set_state(ProfileForm.safety_confirmation)
    await send_safety_confirmation(message)


@router.message(ProfileForm.bio)
async def process_bio(message: Message, state: FSMContext) -> None:
    """Process bio input."""
    bio = message.text.strip()

    if len(bio) > 160:
        await message.answer(
            f"Описание слишком длинное ({len(bio)} символов). " "Максимум 160 символов. Попробуйте короче:"
        )
        return

    await state.update_data(bio_short=bio)
    await state.set_state(ProfileForm.safety_confirmation)
    await send_safety_confirmation(message)


async def send_safety_confirmation(message: Message) -> None:
    """Send safety rules for confirmation."""
    safety_text = """
⚠️ Правила безопасного общения:

1. Будьте уважительны и эмпатичны
2. Не давайте медицинские или юридические советы
3. Уважайте границы собеседника
4. Не делитесь личными данными (телефон, адрес, банковские данные)
5. Не обещайте "всё исправить"

🆘 Если вам нужна срочная помощь:
• Телефон доверия: 8-800-2000-122
• Психологическая помощь: 051 (Москва)

⚠️ Этот сервис НЕ заменяет профессиональную помощь психолога или врача!

Нажмите "Я понимаю", чтобы подтвердить, что вы прочитали и согласны с правилами.
    """.strip()

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Я понимаю", callback_data="safety_accept")]]
    )

    await message.answer(safety_text, reply_markup=keyboard)


@router.callback_query(F.data == "safety_accept", ProfileForm.safety_confirmation)
async def process_safety_confirmation(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    """Save profile after safety confirmation."""
    data = await state.get_data()

    # Create user
    user = User(
        tg_id=callback.from_user.id,
        nickname=data["nickname"],
        tz=data["tz"],
        bio_short=data.get("bio_short"),
        safety_ack=True,
    )
    db.add(user)
    await db.flush()

    # Load topics from DB
    selected_topics = data.get("selected_topics", set())
    result = await db.execute(select(Topic).where(Topic.slug.in_(selected_topics)))
    topics = result.scalars().all()

    # Create user-topic relationships
    for topic in topics:
        user_topic = UserTopic(user_id=user.id, topic_id=topic.id, weight=1)
        db.add(user_topic)

    await db.commit()

    await callback.message.edit_text(
        f"✅ Профиль создан, {user.nickname}!\n\n" "Теперь вы можете найти собеседника командой /find"
    )
    await callback.answer()
    await state.clear()
