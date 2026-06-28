import random

from loguru import logger
from vkbottle import API
from vkbottle.tools import PhotoMessageUploader

from app.config import settings
from app.database import async_session
from app.services.client_service import get_or_create_client
from app.services.ai_service import generate_reply

vk_api = API(token=settings.vk_group_token)
photo_uploader = PhotoMessageUploader(vk_api)


async def handle_vk_event(data: dict):
    event_type = data.get("type")

    if event_type == "message_new":
        message = data["object"]["message"]
        await handle_incoming_message(message)
    elif event_type == "message_reply":
        pass
    else:
        logger.info(f"Unhandled VK event: {event_type}")


async def handle_incoming_message(message: dict):
    peer_id = message["peer_id"]
    from_id = message["from_id"]
    text = message.get("text", "")

    if not text:
        return

    logger.info(f"VK message from {from_id}: {text[:100]}")

    async with async_session() as session:
        client = await get_or_create_client(session, from_id, peer_id)
        reply = await generate_reply(session, client, text)
        await send_message(peer_id, reply)


async def send_message(peer_id: int, text: str):
    await vk_api.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=random.randint(1, 2**31),
    )


async def publish_post(text: str, photo_urls: list[str] | None = None) -> int | None:
    attachments = []

    if photo_urls:
        for url in photo_urls:
            try:
                photo = await photo_uploader.upload(url)
                attachments.append(photo)
            except Exception as e:
                logger.error(f"Failed to upload photo: {e}")

    try:
        post_id = await vk_api.wall.post(
            owner_id=-settings.vk_group_id,
            message=text,
            attachments=",".join(attachments) if attachments else None,
            from_group=True,
        )
        logger.info(f"Published VK post: {post_id}")
        return post_id
    except Exception as e:
        logger.error(f"Failed to publish post: {e}")
        return None
