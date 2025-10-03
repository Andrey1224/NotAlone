#!/usr/bin/env python3
"""
Script to set bot commands in Telegram via BotFather API.
Run this script to register all available commands.
"""

import asyncio
import os

from aiogram import Bot


async def set_bot_commands():
    """Set bot commands via Telegram Bot API."""

    # Load token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return

    bot = Bot(token=token)

    commands = [
        {"command": "start", "description": "начать"},
        {"command": "profile", "description": "профиль"},
        {"command": "find", "description": "найти собеседника"},
        {"command": "end", "description": "завершить текущий диалог"},
        {"command": "edit_topics", "description": "изменить темы"},
        {"command": "tips", "description": "оставить чаевые"},
        {"command": "help", "description": "правила и помощь"},
    ]

    try:
        success = await bot.set_my_commands(commands)
        if success:
            print("✅ Bot commands successfully registered!")
            print("Registered commands:")
            for cmd in commands:
                print(f"  /{cmd['command']} - {cmd['description']}")
        else:
            print("❌ Failed to register bot commands")
    except Exception as e:
        print(f"❌ Error registering commands: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(set_bot_commands())
