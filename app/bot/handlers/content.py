from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.bot.keyboards import content_actions_kb, post_approve_kb
from app.database import async_session
from app.models.content import ContentPlan, ContentStatus
from app.services.ai_service import generate_post_text
from app.services.vk_service import publish_post

router = Router()


class NewPostStates(StatesGroup):
    waiting_topic = State()
    waiting_schedule = State()


@router.message(Command("plan"))
async def cmd_plan(message: Message):
    await message.answer("Контент-план:", reply_markup=content_actions_kb())


@router.callback_query(F.data == "menu:content")
async def menu_content(callback: CallbackQuery):
    await callback.message.edit_text("Контент-план:", reply_markup=content_actions_kb())
    await callback.answer()


@router.callback_query(F.data == "content:today")
async def content_today(callback: CallbackQuery):
    today = datetime.now(timezone.utc).date()
    async with async_session() as session:
        result = await session.execute(
            select(ContentPlan).where(
                ContentPlan.scheduled_at >= datetime.combine(today, datetime.min.time()),
                ContentPlan.status.in_([ContentStatus.APPROVED, ContentStatus.DRAFT]),
            )
        )
        posts = result.scalars().all()

    if not posts:
        await callback.message.edit_text("На сегодня постов нет.", reply_markup=content_actions_kb())
    else:
        text = "Посты на сегодня:\n\n"
        for p in posts:
            status_icon = "✅" if p.status == ContentStatus.APPROVED else "📝"
            time_str = p.scheduled_at.strftime("%H:%M") if p.scheduled_at else "—"
            text += f"{status_icon} {time_str} | {p.title}\n"
        await callback.message.edit_text(text, reply_markup=content_actions_kb())
    await callback.answer()


@router.callback_query(F.data == "content:generate")
async def content_generate(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите тему для поста:")
    await state.set_state(NewPostStates.waiting_topic)
    await callback.answer()


@router.message(NewPostStates.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    topic = message.text
    await message.answer("Генерирую пост...")

    text = await generate_post_text(topic)
    if not text:
        await message.answer("Не удалось сгенерировать пост. Попробуйте ещё раз.")
        await state.clear()
        return

    async with async_session() as session:
        post = ContentPlan(title=topic, text=text, status=ContentStatus.DRAFT)
        session.add(post)
        await session.commit()
        post_id = str(post.id)

    await message.answer(
        f"Сгенерированный пост:\n\n{text[:3000]}",
        reply_markup=post_approve_kb(post_id),
    )
    await state.clear()


@router.callback_query(F.data == "content:drafts")
async def content_drafts(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(ContentPlan).where(ContentPlan.status == ContentStatus.DRAFT).order_by(ContentPlan.created_at.desc()).limit(10)
        )
        posts = result.scalars().all()

    if not posts:
        await callback.message.edit_text("Черновиков нет.", reply_markup=content_actions_kb())
    else:
        for p in posts:
            await callback.message.answer(
                f"📝 {p.title}\n\n{p.text[:500]}...",
                reply_markup=post_approve_kb(str(p.id)),
            )
    await callback.answer()


@router.callback_query(F.data.startswith("post:"))
async def handle_post_action(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    post_id = parts[2]

    async with async_session() as session:
        result = await session.execute(select(ContentPlan).where(ContentPlan.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            await callback.answer("Пост не найден")
            return

        if action == "approve":
            post.status = ContentStatus.APPROVED
            await session.commit()
            await callback.message.edit_text(f"✅ Пост одобрен: {post.title}")

        elif action == "reject":
            post.status = ContentStatus.DRAFT
            await session.commit()
            await callback.message.edit_text(f"❌ Пост отклонён: {post.title}")

        elif action == "publish":
            media = post.media_urls if isinstance(post.media_urls, list) else []
            vk_post_id = await publish_post(post.text, media)
            if vk_post_id:
                post.vk_post_id = vk_post_id
                post.status = ContentStatus.PUBLISHED
                await session.commit()
                await callback.message.edit_text(f"🚀 Пост опубликован: {post.title}")
            else:
                await callback.message.edit_text(f"⚠️ Ошибка публикации: {post.title}")

    await callback.answer()
