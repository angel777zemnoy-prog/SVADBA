import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.health import router as health_router
from app.api.payment_webhook import router as payment_router
from app.api.vk_webhook import router as vk_router
from app.bot.bot import start_bot, stop_bot
from app.config import settings
from app.services.scheduler_service import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VK Agent...")
    start_scheduler()
    asyncio.create_task(start_bot())
    logger.info(f"Server running on {settings.app_host}:{settings.app_port}")
    yield
    logger.info("Shutting down VK Agent...")
    stop_scheduler()
    await stop_bot()


app = FastAPI(title="VK Svadba Agent", version="1.0.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(vk_router)
app.include_router(payment_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
