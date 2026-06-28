from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    from app.bot.keyboards import main_menu_kb
    await message.answer(
        "Добро пожаловать в панель управления VK-агента!\n\n"
        "Команды:\n"
        "/plan — Контент-план\n"
        "/clients — Список клиентов\n"
        "/payments — Счета и оплаты\n"
        "/meetings — Встречи\n"
        "/help — Справка",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Команды бота:\n\n"
        "/plan — Управление контент-планом\n"
        "  • Посмотреть посты на сегодня\n"
        "  • Сгенерировать новый пост (AI)\n"
        "  • Одобрить/опубликовать черновики\n\n"
        "/clients — Список клиентов\n"
        "  • Информация о клиенте\n"
        "  • Выставить счёт\n"
        "  • Сформировать КП\n"
        "  • Записать на встречу\n\n"
        "/payments — Последние счета и оплаты\n\n"
        "/meetings — Предстоящие встречи\n\n"
        "Уведомления приходят автоматически:\n"
        "  • Новый клиент\n"
        "  • Оплата получена\n"
        "  • Новое сообщение в VK"
    )


@router.callback_query(lambda c: c.data == "menu:back")
async def menu_back(callback):
    from app.bot.keyboards import main_menu_kb
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb())
    await callback.answer()
