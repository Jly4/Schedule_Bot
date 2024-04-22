import asyncio

from aiogram.types import CallbackQuery

from bot.database.database import db
from bot.utils.status import send_status
from bot.keyboards import keyboards as kb
from bot.utils.schedule import send_schedule
from bot.utils.messages import del_msg_by_db_name
from bot.config.config import classes_dict
from bot.utils.utils import add_change_to_class
from bot.utils.autosend_menu import del_cls_from_threads


async def choose_class_number(chat_id: int) -> None:
    msg = 'Выберите цифру класса'
    await send_status(
        chat_id=chat_id,
        text=msg,
        reply_markup=kb.choose_class_number()
    )


async def choose_class_letter(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    prefix = 'class_number_'  # callback prefix
    callback = callback_query.data[len(prefix):]  # delete prefix
    school_class = callback

    msg = 'Выберите букву класса'
    await send_status(
        chat_id=chat_id,
        text=msg,
        reply_markup=kb.choose_class_letter(school_class)
    )


async def set_class(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id

    # get class from callback
    prefix = 'set_class_'
    school_class = callback_query.data[len(prefix):]

    # del old class schedule
    await del_msg_by_db_name(chat_id, 'last_schedule_message_id')

    # get classes threads list and delete new class from it, if exist
    threads = await db.get_db_data(chat_id, 'autosend_classes')
    threads = list(threads.split(', ') if threads else threads)
    if school_class in threads:
        await del_cls_from_threads(chat_id, threads, school_class)

    # add change to school class and update data in a database
    school_class = await add_change_to_class(school_class)
    await db.update_db_data(chat_id, school_class=school_class)

    # send a message to user
    formatted_class = classes_dict[school_class[:-1]]
    text = f'Установлен {formatted_class} класс'
    await send_status(chat_id, text=text, reply_markup=None)

    # send schedule for new class
    await asyncio.sleep(1.5)
    await send_schedule(chat_id, now=1)
