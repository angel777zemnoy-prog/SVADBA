from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Контент-план", callback_data="menu:content")],
        [InlineKeyboardButton(text="Клиенты", callback_data="menu:clients")],
        [InlineKeyboardButton(text="Счета и оплаты", callback_data="menu:invoices")],
        [InlineKeyboardButton(text="Встречи", callback_data="menu:meetings")],
    ])


def content_actions_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посты на сегодня", callback_data="content:today")],
        [InlineKeyboardButton(text="Создать пост (AI)", callback_data="content:generate")],
        [InlineKeyboardButton(text="Все черновики", callback_data="content:drafts")],
        [InlineKeyboardButton(text="Назад", callback_data="menu:back")],
    ])


def post_approve_kb(post_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Одобрить", callback_data=f"post:approve:{post_id}"),
            InlineKeyboardButton(text="Отклонить", callback_data=f"post:reject:{post_id}"),
        ],
        [InlineKeyboardButton(text="Опубликовать сейчас", callback_data=f"post:publish:{post_id}")],
    ])


def client_list_kb(clients: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in clients[:10]:
        name = c.name or f"VK {c.vk_user_id}"
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"client:{c.id}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def client_actions_kb(client_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выставить счёт", callback_data=f"invoice:create:{client_id}")],
        [InlineKeyboardButton(text="Сформировать КП", callback_data=f"proposal:{client_id}")],
        [InlineKeyboardButton(text="Записать на встречу", callback_data=f"meeting:create:{client_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="menu:clients")],
    ])
