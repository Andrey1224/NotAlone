"""SOS handler for emergency hotlines and crisis support."""

import json
import logging
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)

# Path to SOS data file
SOS_DATA_PATH = Path(__file__).parent.parent / "data" / "sos_ru.json"


@router.message(Command("sos"))
async def cmd_sos(message: Message) -> None:
    """
    Handle /sos command - display emergency hotlines and crisis support.

    Shows list of crisis hotlines, psychological help services, and emergency contacts.
    Data loaded from apps/bot/data/sos_ru.json.
    """
    try:
        # Load SOS data from JSON file
        if not SOS_DATA_PATH.exists():
            logger.error(f"SOS data file not found: {SOS_DATA_PATH}")
            await message.answer(
                "🆘 Экстренная помощь\n\n"
                "📞 Телефон доверия: 8-800-2000-122 (круглосуточно, бесплатно)\n"
                "📞 Психологическая помощь: 051 (Москва)\n"
                "🚑 Скорая помощь: 112\n\n"
                "⚠️ При серьезных проблемах обращайтесь к специалистам!"
            )
            return

        with open(SOS_DATA_PATH, encoding="utf-8") as f:
            sos_data = json.load(f)

        # Build message from loaded data
        lines = ["🆘 Экстренная помощь\n"]

        # Add hotlines
        if "hotlines" in sos_data:
            for hotline in sos_data["hotlines"]:
                name = hotline.get("name", "")
                phone = hotline.get("phone", "")
                hours = hotline.get("hours", "")
                lines.append(f"📞 {name}: {phone}")
                if hours:
                    lines.append(f"   {hours}")

        # Add emergency services
        if "emergency" in sos_data:
            lines.append("")
            for service in sos_data["emergency"]:
                name = service.get("name", "")
                phone = service.get("phone", "")
                lines.append(f"🚑 {name}: {phone}")

        # Add disclaimer
        lines.append("\n⚠️ При серьезных проблемах обращайтесь к специалистам!")
        lines.append("Этот бот не заменяет профессиональную медицинскую или психологическую помощь.")

        await message.answer("\n".join(lines))

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse SOS data: {e}")
        await message.answer(
            "🆘 Экстренная помощь\n\n"
            "📞 Телефон доверия: 8-800-2000-122 (круглосуточно, бесплатно)\n"
            "📞 Психологическая помощь: 051 (Москва)\n"
            "🚑 Скорая помощь: 112\n\n"
            "⚠️ При серьезных проблемах обращайтесь к специалистам!"
        )

    except Exception as e:
        logger.error(f"Failed to load SOS data: {e}")
        await message.answer(
            "🆘 Экстренная помощь\n\n"
            "📞 Телефон доверия: 8-800-2000-122 (круглосуточно, бесплатно)\n"
            "📞 Психологическая помощь: 051 (Москва)\n"
            "🚑 Скорая помощь: 112\n\n"
            "⚠️ При серьезных проблемах обращайтесь к специалистам!"
        )
