import anthropic
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client
from app.models.conversation import Conversation, Message, MessageDirection, ContextType

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """Ты — AI-ассистент свадебного агентства. Ты общаешься с клиентами через ВКонтакте.

Твои задачи:
1. Отвечать на вопросы о услугах свадебного агентства (организация свадеб, декор, координация)
2. Собирать информацию о клиенте: имя, дату свадьбы, пожелания, бюджет
3. Предлагать встречу для обсуждения деталей
4. Формировать коммерческое предложение (КП) на основе пожеланий
5. Отвечать на вопросы опросов и интервью

Правила:
- Будь вежливым, дружелюбным и профессиональным
- Отвечай кратко и по делу (до 300 символов в сообщении)
- Если клиент хочет встречу — предложи удобное время и место
- Если клиент спрашивает о ценах — дай общую информацию и предложи КП
- Если клиент даёт персональные данные (имя, телефон, email) — подтверди получение
- Пиши на русском языке

Информация о клиенте:
Имя: {client_name}
Дата свадьбы: {wedding_date}
Статус: {status}
"""


async def generate_reply(session: AsyncSession, client_obj: Client, user_message: str) -> str:
    conversation = await _get_or_create_conversation(session, client_obj)

    incoming = Message(
        conversation_id=conversation.id,
        direction=MessageDirection.INCOMING,
        text=user_message,
    )
    session.add(incoming)
    await session.flush()

    history = await _build_message_history(session, conversation)

    system_prompt = SYSTEM_PROMPT.format(
        client_name=client_obj.name or "Не указано",
        wedding_date=str(client_obj.wedding_date) if client_obj.wedding_date else "Не указана",
        status=client_obj.status.value,
    )

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=history,
        )
        reply_text = response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        reply_text = "Спасибо за сообщение! Наш менеджер свяжется с вами в ближайшее время."

    outgoing = Message(
        conversation_id=conversation.id,
        direction=MessageDirection.OUTGOING,
        text=reply_text,
        is_ai_generated=True,
    )
    session.add(outgoing)
    await session.commit()

    intent = await _classify_intent(user_message)
    if intent:
        conversation.context_type = intent
        await session.commit()

    return reply_text


async def generate_post_text(topic: str, keywords: list[str] | None = None) -> str:
    prompt = f"""Напиши пост для свадебного агентства во ВКонтакте на тему: "{topic}".
Ключевые слова: {', '.join(keywords) if keywords else 'свадьба, организация, декор'}

Требования:
- Длина: 500-1000 символов
- Стиль: вдохновляющий, профессиональный
- Добавь 3-5 хештегов в конце
- Используй эмодзи умеренно
"""
    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error generating post: {e}")
        return ""


async def generate_commercial_proposal(client_obj: Client, services: list[str], budget: str | None = None) -> str:
    prompt = f"""Сформируй коммерческое предложение (КП) для клиента свадебного агентства.

Клиент: {client_obj.name or 'Не указано'}
Дата свадьбы: {client_obj.wedding_date or 'Не указана'}
Запрошенные услуги: {', '.join(services)}
Бюджет: {budget or 'Не указан'}

Формат КП:
1. Приветствие
2. Список услуг с описанием
3. Примерная стоимость каждой услуги
4. Итого
5. Контакты и следующие шаги
"""
    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error generating proposal: {e}")
        return ""


async def _classify_intent(text: str) -> ContextType | None:
    keywords_map = {
        ContextType.MEETING: ["встреча", "встретиться", "приехать", "прийти", "записаться"],
        ContextType.PROPOSAL: ["цена", "стоимость", "прайс", "кп", "предложение", "сколько стоит"],
        ContextType.SURVEY: ["опрос", "отзыв", "анкета", "интервью"],
    }
    text_lower = text.lower()
    for intent, keywords in keywords_map.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    return None


async def _get_or_create_conversation(session: AsyncSession, client_obj: Client) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.client_id == client_obj.id,
            Conversation.is_active == True,  # noqa: E712
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            client_id=client_obj.id,
            vk_peer_id=client_obj.vk_user_id,
            context_type=ContextType.INQUIRY,
        )
        session.add(conversation)
        await session.flush()

    return conversation


async def _build_message_history(session: AsyncSession, conversation: Conversation) -> list[dict]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    messages = list(reversed(result.scalars().all()))

    history = []
    for msg in messages:
        role = "user" if msg.direction == MessageDirection.INCOMING else "assistant"
        history.append({"role": role, "content": msg.text})

    return history
