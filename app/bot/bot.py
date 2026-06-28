from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.bot.handlers import clients, content, invoices, meetings, notifications
from app.config import settings
from app.services.notification_service import set_telegram_bot

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(notifications.router)
dp.include_router(content.router)
dp.include_router(clients.router)
dp.include_router(invoices.router)
dp.include_router(meetings.router)


async def start_bot():
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not set, skipping bot start")
        return

    set_telegram_bot(bot)
    logger.info("Starting Telegram bot...")
    await dp.start_polling(bot)


async def stop_bot():
    logger.info("Stopping Telegram bot...")
    await dp.stop_polling()
    await bot.session.close()
