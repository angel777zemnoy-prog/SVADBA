from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.database import async_session
from app.models.invoice import Invoice, InvoiceStatus
from app.services.client_service import get_client_by_id
from app.services.payment_service import create_invoice

router = Router()


class InvoiceStates(StatesGroup):
    waiting_amount = State()
    waiting_description = State()


@router.message(Command("payments"))
async def cmd_payments(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Invoice).order_by(Invoice.created_at.desc()).limit(10)
        )
        invoices = result.scalars().all()

    if not invoices:
        await message.answer("Счетов пока нет.")
        return

    text = "Последние счета:\n\n"
    for inv in invoices:
        status_icon = {"pending": "⏳", "paid": "✅", "cancelled": "❌", "refunded": "↩️"}
        icon = status_icon.get(inv.status.value, "❓")
        text += f"{icon} {inv.amount} руб. — {inv.description[:50]}\n"
    await message.answer(text)


@router.callback_query(F.data == "menu:invoices")
async def menu_invoices(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Invoice).order_by(Invoice.created_at.desc()).limit(10)
        )
        invoices = result.scalars().all()

    if not invoices:
        await callback.message.edit_text("Счетов пока нет.")
    else:
        text = "Последние счета:\n\n"
        for inv in invoices:
            status_icon = {"pending": "⏳", "paid": "✅", "cancelled": "❌", "refunded": "↩️"}
            icon = status_icon.get(inv.status.value, "❓")
            text += f"{icon} {inv.amount} руб. — {inv.description[:50]}\n"
        await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("invoice:create:"))
async def invoice_create_start(callback: CallbackQuery, state: FSMContext):
    client_id = callback.data.split(":")[2]
    await state.update_data(client_id=client_id)
    await callback.message.edit_text("Введите сумму счёта (в рублях):")
    await state.set_state(InvoiceStates.waiting_amount)
    await callback.answer()


@router.message(InvoiceStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = Decimal(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except (ValueError, ArithmeticError):
        await message.answer("Введите корректную сумму (число больше 0):")
        return

    await state.update_data(amount=str(amount))
    await message.answer("Введите описание (за что выставляется счёт):")
    await state.set_state(InvoiceStates.waiting_description)


@router.message(InvoiceStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    amount = Decimal(data["amount"])
    description = message.text

    async with async_session() as session:
        client = await get_client_by_id(session, client_id)
        if not client:
            await message.answer("Клиент не найден.")
            await state.clear()
            return

        invoice = await create_invoice(session, client, amount, description)
        await message.answer(
            f"✅ Счёт создан!\n"
            f"Сумма: {invoice.amount} руб.\n"
            f"Описание: {invoice.description}\n"
            f"Ссылка: {invoice.payment_url}"
        )
    await state.clear()
