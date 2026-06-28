from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import client_actions_kb, client_list_kb
from app.database import async_session
from app.services.client_service import get_client_by_id, list_clients, get_client_phone

router = Router()


@router.message(Command("clients"))
async def cmd_clients(message: Message):
    async with async_session() as session:
        clients = await list_clients(session)
    if not clients:
        await message.answer("Клиентов пока нет.")
        return
    await message.answer("Список клиентов:", reply_markup=client_list_kb(clients))


@router.callback_query(F.data == "menu:clients")
async def menu_clients(callback: CallbackQuery):
    async with async_session() as session:
        clients = await list_clients(session)
    if not clients:
        await callback.message.edit_text("Клиентов пока нет.")
    else:
        await callback.message.edit_text("Список клиентов:", reply_markup=client_list_kb(clients))
    await callback.answer()


@router.callback_query(F.data.startswith("client:"))
async def client_info(callback: CallbackQuery):
    client_id = callback.data.split(":")[1]

    async with async_session() as session:
        client = await get_client_by_id(session, client_id)
        if not client:
            await callback.answer("Клиент не найден")
            return

        phone = get_client_phone(client)
        text = (
            f"👤 Клиент: {client.name or 'Не указано'}\n"
            f"VK ID: {client.vk_user_id}\n"
            f"📱 Телефон: {phone or 'Не указан'}\n"
            f"📧 Email: {client.email or 'Не указан'}\n"
            f"💍 Дата свадьбы: {client.wedding_date or 'Не указана'}\n"
            f"📋 Статус: {client.status.value}\n"
            f"📝 Заметки: {client.notes or '—'}"
        )
        await callback.message.edit_text(text, reply_markup=client_actions_kb(client_id))
    await callback.answer()
