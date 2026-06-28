import random

from loguru import logger
from vkbottle import API

from app.config import settings
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.meeting import Meeting

vk_api = API(token=settings.vk_group_token)
_tg_bot = None


def set_telegram_bot(bot):
    global _tg_bot
    _tg_bot = bot


async def notify_manager(text: str):
    if not _tg_bot or not settings.telegram_manager_id:
        logger.warning("Telegram bot not configured for manager notifications")
        return
    try:
        await _tg_bot.send_message(chat_id=settings.telegram_manager_id, text=text)
    except Exception as e:
        logger.error(f"Failed to notify manager via Telegram: {e}")


async def notify_client_vk(client: Client, text: str):
    try:
        await vk_api.messages.send(
            peer_id=client.vk_user_id,
            message=text,
            random_id=random.randint(1, 2**31),
        )
    except Exception as e:
        logger.error(f"Failed to notify client {client.vk_user_id} via VK: {e}")


async def notify_payment_received(invoice: Invoice):
    await notify_manager(
        f"Оплата получена!\n"
        f"Сумма: {invoice.amount} руб.\n"
        f"Описание: {invoice.description}\n"
        f"ID клиента: {invoice.client_id}"
    )


async def notify_client_payment_link(client: Client, invoice: Invoice):
    await notify_client_vk(
        client,
        f"Для вас сформирован счёт на {invoice.amount} руб.\n"
        f"Описание: {invoice.description}\n"
        f"Ссылка для оплаты: {invoice.payment_url}"
    )
    await notify_manager(
        f"Счёт отправлен клиенту {client.name or client.vk_user_id}\n"
        f"Сумма: {invoice.amount} руб."
    )


async def notify_new_client(client: Client):
    await notify_manager(
        f"Новый клиент!\n"
        f"VK ID: {client.vk_user_id}\n"
        f"Имя: {client.name or 'Не указано'}"
    )


async def notify_meeting_scheduled(client: Client, meeting: Meeting):
    await notify_client_vk(
        client,
        f"Встреча запланирована!\n"
        f"Дата: {meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"Место: {meeting.location or 'Уточняется'}"
    )
    await notify_manager(
        f"Новая встреча!\n"
        f"Клиент: {client.name or client.vk_user_id}\n"
        f"Дата: {meeting.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"Место: {meeting.location or 'Уточняется'}"
    )
