import asyncio

from aiogram.types import CallbackQuery

from main import bot
from bot.database.database import db
from bot.utils.status import send_status
from bot.keyboards import keyboards as kb
from bot.config.config import classes_dict, schedule_auto_send_delay
from bot.logs.log_config import custom_logger
from bot.utils.messages import del_msg_by_id
from bot.utils.utils import run_task_if_disabled, add_change_to_class
from bot.filters.filters import AutoSendFilter


async def auto_send_menu(query: CallbackQuery = 0, chat_id: int = 0) -> None:
    if not chat_id:
        chat_id = query.message.chat.id

    custom_logger.debug(chat_id)

    threads = await db.get_db_data(chat_id, 'autosend_classes')
    cls = await db.get_db_data(chat_id, 'school_class')
    threads = list(threads.split(', ') if threads else threads)
    threads.append(cls)

    classes = [classes_dict[cls[:-1]] for cls in reversed(threads)]
    autosend = await AutoSendFilter(chat_id).filter()
    autosend_states_list = ['🔴 Выключено', '🟠 Приостановлено', '🟢 Включено']
    autosend_delay = schedule_auto_send_delay
    txt = (
        'Меню настройки автоматического обновление расписания\n\n'
        f'🎓 Класс(ы): {", ".join(classes)}\n'
        f'🔄 Автообновление: {autosend_states_list[autosend]}\n'
        f"⏳ Проверка выполняется раз в {autosend_delay} минут"
    )
    await send_status(
        chat_id,
        text=txt,
        reply_markup=kb.auto_update_settings()
    )


async def edit_threads(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    custom_logger.debug(chat_id)

    threads = await db.get_db_data(chat_id, 'autosend_classes')
    threads = list(threads.split(', ') if threads else threads)

    callback_prefix = 'set_class_'
    cls: str = query.data[len(callback_prefix):]
    cls = await add_change_to_class(cls)

    main_class = await db.get_db_data(chat_id, 'school_class')
    if main_class == cls:
        await auto_send_menu(chat_id=chat_id)

        msg = await bot.send_message(chat_id, 'Нельзя удалить основной класс')
        await asyncio.sleep(3)
        await del_msg_by_id(chat_id, msg.message_id)

        return

    if cls in threads:
        await del_cls_from_threads(chat_id, threads, cls)
    else:
        await add_cls_to_threads(chat_id, threads, cls)

    await auto_send_menu(chat_id=chat_id)


async def add_cls_to_threads(chat_id: int, threads: list, cls: str) -> None:
    if len(threads) < 2:
        threads.append(cls)
    else:
        await auto_send_menu(chat_id=chat_id)
        txt = 'Нельзя добавить больше трех классов'
        msg = await bot.send_message(chat_id, txt)

        await asyncio.sleep(3)
        await del_msg_by_id(chat_id, msg.message_id)
        return

    threads = ', '.join(threads)
    await db.update_db_data(chat_id, autosend_classes=threads)


async def del_cls_from_threads(chat_id: int, threads: list,  cls: str) -> None:
    threads.remove(cls)
    threads = ', '.join(threads)
    await db.update_db_data(chat_id, autosend_classes=threads)


async def turn_schedule(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id

    if await db.get_db_data(chat_id, 'schedule_auto_send'):
        await db.update_db_data(chat_id, schedule_auto_send=0)

        await auto_send_menu(chat_id=chat_id)

    else:
        await db.update_db_data(chat_id, schedule_auto_send=1)

        await auto_send_menu(chat_id=chat_id)
        await asyncio.sleep(1)
        await run_task_if_disabled(chat_id, 'schedule_auto_send')
