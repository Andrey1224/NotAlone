#!/usr/bin/env python3
"""
Script to check user topics in the database.
"""

import asyncio
import os
import sys

from sqlalchemy import select

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import AsyncSessionLocal
from models.topic import Topic, UserTopic
from models.user import User


async def check_user_topics(nickname: str):
    """Check topics for a specific user by nickname."""

    async with AsyncSessionLocal() as db:
        try:
            # Find user by nickname
            result = await db.execute(select(User).where(User.nickname == nickname))
            user = result.scalar_one_or_none()

            if not user:
                print(f"❌ Пользователь с ником '{nickname}' не найден")
                return

            print(f"✅ Найден пользователь: {user.nickname} (ID: {user.id}, TG ID: {user.tg_id})")
            print(f"   Часовой пояс: {user.tz}")
            print(f"   Описание: {user.bio_short or 'не указано'}")
            print(f"   Создан: {user.created_at}")
            print()

            # Get user topics
            topics_result = await db.execute(
                select(Topic, UserTopic.weight)
                .join(UserTopic)
                .where(UserTopic.user_id == user.id)
                .order_by(Topic.title)
            )
            topics = topics_result.all()

            if not topics:
                print("📝 У пользователя нет выбранных тем")
            else:
                print(f"📝 Темы пользователя ({len(topics)}):")
                for topic, weight in topics:
                    print(f"   • {topic.title} (slug: {topic.slug}, вес: {weight})")

        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")


async def list_all_users():
    """List all users in the database."""

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).order_by(User.created_at))
            users = result.scalars().all()

            if not users:
                print("👥 В базе данных нет пользователей")
                return

            print(f"👥 Все пользователи в базе данных ({len(users)}):")
            for user in users:
                # Get topic count for each user
                topics_count_result = await db.execute(select(UserTopic).where(UserTopic.user_id == user.id))
                topics_count = len(topics_count_result.scalars().all())

                print(f"   • {user.nickname} (ID: {user.id}, TG ID: {user.tg_id}, тем: {topics_count})")

        except Exception as e:
            print(f"❌ Ошибка при получении списка пользователей: {e}")


async def list_all_topics():
    """List all available topics."""

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Topic).order_by(Topic.title))
            topics = result.scalars().all()

            if not topics:
                print("📋 В базе данных нет тем")
                return

            print(f"📋 Все доступные темы ({len(topics)}):")
            for topic in topics:
                print(f"   • {topic.title} (slug: {topic.slug})")

        except Exception as e:
            print(f"❌ Ошибка при получении списка тем: {e}")


async def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  {sys.argv[0]} <nickname>     - показать темы пользователя")
        print(f"  {sys.argv[0]} --users        - показать всех пользователей")
        print(f"  {sys.argv[0]} --topics       - показать все темы")
        return

    command = sys.argv[1]

    if command == "--users":
        await list_all_users()
    elif command == "--topics":
        await list_all_topics()
    else:
        nickname = command
        await check_user_topics(nickname)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
