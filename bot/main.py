import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import config
from bot.database.session import init_db
from bot.handlers import booking, stats, callbacks
from bot.services.scheduler import setup_scheduler, shutdown_scheduler
from bot.middlewares import ChatFilterMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point."""
    if not config.bot_token:
        logger.error("BOT_TOKEN is not set!")
        sys.exit(1)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create bot and dispatcher
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Add middleware to restrict to specific chat only
    dp.message.middleware(ChatFilterMiddleware())
    dp.callback_query.middleware(ChatFilterMiddleware())

    # Register handlers
    dp.include_router(booking.router)
    dp.include_router(stats.router)
    dp.include_router(callbacks.router)

    # Setup scheduler
    setup_scheduler(bot)
    logger.info("Scheduler started")

    # Start polling
    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        shutdown_scheduler()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
