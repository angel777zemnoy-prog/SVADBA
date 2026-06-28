from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models.content import ContentPlan, ContentStatus
from app.services.vk_service import publish_post

scheduler = AsyncIOScheduler()


async def publish_scheduled_posts():
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            select(ContentPlan).where(
                ContentPlan.status == ContentStatus.APPROVED,
                ContentPlan.scheduled_at <= now,
            )
        )
        posts = result.scalars().all()

        for post in posts:
            logger.info(f"Publishing scheduled post: {post.title}")
            media = post.media_urls if isinstance(post.media_urls, list) else []
            post_id = await publish_post(post.text, media)

            if post_id:
                post.vk_post_id = post_id
                post.status = ContentStatus.PUBLISHED
            else:
                post.status = ContentStatus.FAILED

            await session.commit()


def start_scheduler():
    scheduler.add_job(publish_scheduled_posts, "interval", minutes=1, id="publish_posts")
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped")
