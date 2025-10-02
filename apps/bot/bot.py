"""Main bot module with webhook setup."""

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from apps.bot.handlers import find, profile, start, tips
from apps.bot.middlewares.database import DatabaseMiddleware
from apps.bot.middlewares.rate_limit import RateLimitMiddleware
from core.config import settings

# Initialize bot and dispatcher
bot = Bot(token=settings.telegram_bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Register middlewares
dp.message.middleware(DatabaseMiddleware())
dp.callback_query.middleware(DatabaseMiddleware())
dp.message.middleware(RateLimitMiddleware())

# Register handlers
dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(find.router)
dp.include_router(tips.router)


async def on_startup(app: web.Application) -> None:
    """Set webhook on startup."""
    webhook_url = f"{settings.public_base_url}/telegram/webhook"
    await bot.set_webhook(webhook_url)
    print(f"Webhook set to: {webhook_url}")


async def on_shutdown(app: web.Application) -> None:
    """Clean up on shutdown."""
    await bot.delete_webhook()
    await bot.session.close()


def create_app() -> web.Application:
    """Create aiohttp application with bot."""
    app = web.Application()

    # Setup webhook handler
    webhook_path = "/telegram/webhook"
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)

    # Setup application
    setup_application(app, dp, bot=bot)

    # Register startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=settings.bot_port)
