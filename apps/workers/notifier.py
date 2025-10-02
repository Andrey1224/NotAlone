"""Notification service for sending messages to users via Telegram bot."""

import logging

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bot.keyboards.inline import get_match_confirmation_keyboard
from core.config import settings
from models import User

logger = logging.getLogger(__name__)


class Notifier:
    """Service for sending notifications to users."""

    def __init__(self) -> None:
        self.bot = Bot(token=settings.telegram_bot_token)

    async def send_match_proposal(self, db: AsyncSession, match_id: int, user_id: int, partner_id: int) -> bool:
        """
        Send match proposal notification to a user.

        Args:
            db: Database session
            match_id: Match ID
            user_id: User receiving notification
            partner_id: Partner user ID

        Returns:
            True if sent successfully
        """
        try:
            # Get user and partner info
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            partner_result = await db.execute(select(User).where(User.id == partner_id))
            partner = partner_result.scalar_one_or_none()

            if not user or not partner:
                logger.error(f"User or partner not found: user={user_id}, partner={partner_id}")
                return False

            # Send notification via bot
            text = f"""
🎯 Найден собеседник!

👤 Псевдоним: {partner.nickname}
🌍 Часовой пояс: {partner.tz}
📝 О себе: {partner.bio_short or "Не указано"}

У вас есть 5 минут, чтобы принять или отклонить предложение.
            """.strip()

            await self.bot.send_message(
                chat_id=user.tg_id, text=text, reply_markup=get_match_confirmation_keyboard(match_id, user_id)
            )

            return True

        except Exception as e:
            logger.error(f"Failed to send match proposal to user {user_id}: {e}")
            return False

    async def send_match_active(self, db: AsyncSession, user_id: int, partner_id: int) -> bool:
        """
        Send notification when match becomes active.

        Args:
            db: Database session
            user_id: User receiving notification
            partner_id: Partner user ID

        Returns:
            True if sent successfully
        """
        try:
            # Get user info
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            partner_result = await db.execute(select(User).where(User.id == partner_id))
            partner = partner_result.scalar_one_or_none()

            if not user or not partner:
                logger.error(f"User or partner not found: user={user_id}, partner={partner_id}")
                return False

            # Send intro message with rules
            intro_text = f"""
✅ Совпадение подтверждено!

👤 Собеседник: {partner.nickname}
🌍 Часовой пояс: {partner.tz}

⚠️ Правила безопасного общения:
1. Будьте уважительны и эмпатичны
2. Не давайте медицинские или юридические советы
3. Уважайте границы собеседника
4. Не делитесь личными данными
5. Не обещайте "всё исправить"

🆘 Если нужна срочная помощь:
• Телефон доверия: 8-800-2000-122
• Психологическая помощь: 051 (Москва)

💚 Начните разговор с приветствия! Помните: вы здесь, чтобы поддержать друг друга.

Для завершения диалога используйте команду /end
            """.strip()

            await self.bot.send_message(chat_id=user.tg_id, text=intro_text)

            return True

        except Exception as e:
            logger.error(f"Failed to send match active notification to user {user_id}: {e}")
            return False

    async def send_match_declined(self, db: AsyncSession, user_id: int) -> bool:
        """
        Send notification when partner declined match.

        Args:
            db: Database session
            user_id: User receiving notification

        Returns:
            True if sent successfully
        """
        try:
            # Get user info
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            text = "😔 Собеседник отклонил предложение.\n\nПродолжаю поиск для вас..."

            await self.bot.send_message(chat_id=user.tg_id, text=text)

            return True

        except Exception as e:
            logger.error(f"Failed to send match declined notification to user {user_id}: {e}")
            return False

    async def close(self) -> None:
        """Close bot session."""
        await self.bot.session.close()


# Global notifier instance
notifier = Notifier()
