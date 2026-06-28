import uuid
from decimal import Decimal

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration, Payment

from app.config import settings
from app.database import async_session
from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.services.notification_service import notify_payment_received, notify_client_payment_link

Configuration.account_id = settings.yokassa_shop_id
Configuration.secret_key = settings.yokassa_secret_key


async def create_invoice(
    session: AsyncSession,
    client: Client,
    amount: Decimal,
    description: str,
) -> Invoice:
    payment = Payment.create({
        "amount": {"value": str(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": f"{settings.app_base_url}/payment/success"},
        "capture": True,
        "description": description,
        "metadata": {"client_id": str(client.id)},
    })

    invoice = Invoice(
        client_id=client.id,
        amount=amount,
        description=description,
        yokassa_payment_id=payment.id,
        payment_url=payment.confirmation.confirmation_url,
        status=InvoiceStatus.PENDING,
    )
    session.add(invoice)
    await session.commit()

    await notify_client_payment_link(client, invoice)

    logger.info(f"Invoice created: {invoice.id} for {amount} RUB")
    return invoice


async def handle_payment_notification(data: dict):
    event = data.get("event")
    payment_obj = data.get("object", {})
    payment_id = payment_obj.get("id")

    if not payment_id:
        return

    async with async_session() as session:
        result = await session.execute(
            select(Invoice).where(Invoice.yokassa_payment_id == payment_id)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            logger.warning(f"Invoice not found for payment {payment_id}")
            return

        if event == "payment.succeeded":
            invoice.status = InvoiceStatus.PAID
            await session.commit()
            await notify_payment_received(invoice)
            logger.info(f"Payment received: {invoice.id}")

        elif event == "payment.canceled":
            invoice.status = InvoiceStatus.CANCELLED
            await session.commit()
            logger.info(f"Payment cancelled: {invoice.id}")

        elif event == "refund.succeeded":
            invoice.status = InvoiceStatus.REFUNDED
            await session.commit()
            logger.info(f"Payment refunded: {invoice.id}")


async def get_client_invoices(session: AsyncSession, client_id: uuid.UUID) -> list[Invoice]:
    result = await session.execute(
        select(Invoice).where(Invoice.client_id == client_id).order_by(Invoice.created_at.desc())
    )
    return list(result.scalars().all())
