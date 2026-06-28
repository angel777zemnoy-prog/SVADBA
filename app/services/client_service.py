import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client, ClientStatus
from app.models.conversation import Conversation, ContextType
from app.utils.helpers import encrypt_value, decrypt_value


async def get_or_create_client(session: AsyncSession, vk_user_id: int, peer_id: int) -> Client:
    result = await session.execute(select(Client).where(Client.vk_user_id == vk_user_id))
    client = result.scalar_one_or_none()

    if not client:
        client = Client(vk_user_id=vk_user_id, status=ClientStatus.NEW)
        session.add(client)
        await session.flush()

        conversation = Conversation(
            client_id=client.id,
            vk_peer_id=peer_id,
            context_type=ContextType.INQUIRY,
        )
        session.add(conversation)
        await session.commit()
        logger.info(f"New client created: VK {vk_user_id}")

    return client


async def get_client_by_id(session: AsyncSession, client_id: uuid.UUID) -> Client | None:
    result = await session.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


async def list_clients(session: AsyncSession, status: ClientStatus | None = None) -> list[Client]:
    query = select(Client).order_by(Client.created_at.desc())
    if status:
        query = query.where(Client.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_client_personal_data(
    session: AsyncSession,
    client: Client,
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    wedding_date=None,
):
    if name:
        client.name = name
    if phone:
        client.phone = encrypt_value(phone)
    if email:
        client.email = email
    if wedding_date:
        client.wedding_date = wedding_date

    client.personal_data_consent = True
    client.consent_date = datetime.now(timezone.utc)
    await session.commit()


def get_client_phone(client: Client) -> str | None:
    if client.phone:
        try:
            return decrypt_value(client.phone)
        except Exception:
            return None
    return None


async def get_active_conversation(session: AsyncSession, client: Client) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.client_id == client.id,
            Conversation.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()
