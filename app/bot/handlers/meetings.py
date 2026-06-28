from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database import async_session
from app.models.meeting import Meeting, MeetingStatus
from app.services.client_service import get_client_by_id
from app.services.notification_service import notify_meeting_scheduled

router = Router()


class MeetingStates(StatesGroup):
    waiting_datetime = State()
    waiting_location = State()


@router.message(Command("meetings"))
async def cmd_meetings(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Meeting)
            .where(Meeting.status.in_([MeetingStatus.PLANNED, MeetingStatus.CONFIRMED]))
            .order_by(Meeting.scheduled_at)
        )
        meetings = result.scalars().all()

    if not meetings:
        await message.answer("Предстоящих встреч нет.")
        return

    text = "Предстоящие встречи:\n\n"
    for m in meetings:
        status_icon = "📅" if m.status == MeetingStatus.PLANNED else "✅"
        text += (
            f"{status_icon} {m.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"   Место: {m.location or '—'}\n"
            f"   Заметки: {m.notes or '—'}\n\n"
        )
    await message.answer(text)


@router.callback_query(F.data == "menu:meetings")
async def menu_meetings(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Meeting)
            .where(Meeting.status.in_([MeetingStatus.PLANNED, MeetingStatus.CONFIRMED]))
            .order_by(Meeting.scheduled_at)
        )
        meetings = result.scalars().all()

    if not meetings:
        await callback.message.edit_text("Предстоящих встреч нет.")
    else:
        text = "Предстоящие встречи:\n\n"
        for m in meetings:
            status_icon = "📅" if m.status == MeetingStatus.PLANNED else "✅"
            text += f"{status_icon} {m.scheduled_at.strftime('%d.%m.%Y %H:%M')} — {m.location or '—'}\n"
        await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("meeting:create:"))
async def meeting_create_start(callback: CallbackQuery, state: FSMContext):
    client_id = callback.data.split(":")[2]
    await state.update_data(client_id=client_id)
    await callback.message.edit_text("Введите дату и время встречи (ДД.ММ.ГГГГ ЧЧ:ММ):")
    await state.set_state(MeetingStates.waiting_datetime)
    await callback.answer()


@router.message(MeetingStates.waiting_datetime)
async def process_datetime(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ")
        return

    await state.update_data(scheduled_at=dt.isoformat())
    await message.answer("Введите место встречи:")
    await state.set_state(MeetingStates.waiting_location)


@router.message(MeetingStates.waiting_location)
async def process_location(message: Message, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    scheduled_at = datetime.fromisoformat(data["scheduled_at"])
    location = message.text

    async with async_session() as session:
        client = await get_client_by_id(session, client_id)
        if not client:
            await message.answer("Клиент не найден.")
            await state.clear()
            return

        meeting = Meeting(
            client_id=client.id,
            scheduled_at=scheduled_at,
            location=location,
            status=MeetingStatus.PLANNED,
        )
        session.add(meeting)
        await session.commit()

        await notify_meeting_scheduled(client, meeting)
        await message.answer(
            f"✅ Встреча запланирована!\n"
            f"Дата: {scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Место: {location}"
        )
    await state.clear()
