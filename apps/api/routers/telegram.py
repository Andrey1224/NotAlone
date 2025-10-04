"""Telegram webhook router for FastAPI."""

from fastapi import APIRouter, Header, Request, Response, status
from fastapi.exceptions import HTTPException

from apps.bot.bot import bot, dp
from core.config import settings

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> Response:
    """Handle incoming Telegram webhook updates.

    This endpoint receives updates from Telegram and feeds them to the aiogram dispatcher.
    """
    # Validate secret token if configured (recommended for production)
    webhook_secret = getattr(settings, "telegram_webhook_secret", None)
    if webhook_secret and x_telegram_bot_api_secret_token != webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token",
        )

    # Get update data from request
    update_data = await request.json()

    # Feed update to dispatcher (aiogram will handle routing to handlers)
    # Use feed_webhook_update for proper webhook handling with timeout
    result = await dp.feed_webhook_update(bot=bot, update=update_data)

    # If handler returns a method to execute, handle it
    # (rare case, usually handlers don't return responses)
    if result:
        return Response(content=result.model_dump_json(), media_type="application/json")

    return Response(status_code=status.HTTP_200_OK)
