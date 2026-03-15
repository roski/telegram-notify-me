import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import load_config
from bot.database.database import get_session_factory, init_db
from bot.database.models import Base
from bot.handlers import create_notification, scheduled_notifications, start
from bot.handlers import config as config_handler
from bot.handlers import timezone as timezone_handler
from bot.handlers import remind_later as remind_later_handler
from bot.scheduler.scheduler import init_scheduler, load_pending_notifications

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def create_tables(config) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(config.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def main() -> None:
    config = load_config()

    # Initialize database
    init_db(config)
    session_factory = get_session_factory()

    # Create tables (use Alembic in production; this is for convenience)
    await create_tables(config)

    # Initialize bot and dispatcher
    bot = Bot(
        token=config.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Inject database session into handlers
    async def session_middleware(handler, event, data):
        async with session_factory() as session:
            data["session"] = session
            return await handler(event, data)

    dp.update.outer_middleware(session_middleware)

    # Include routers
    dp.include_router(start.router)
    dp.include_router(timezone_handler.router)
    dp.include_router(config_handler.router)
    dp.include_router(create_notification.router)
    dp.include_router(scheduled_notifications.router)
    dp.include_router(remind_later_handler.router)

    # Initialize and start scheduler
    init_scheduler(bot, session_factory)
    await load_pending_notifications(session_factory)

    logger.info("Bot is starting...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
