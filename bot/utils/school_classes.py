import asyncio

from aiogram.types import CallbackQuery

from bot.database.database import db
from bot.utils.status import send_status
from bot.keyboards import keyboards as kb
from bot.utils.schedule import send_schedule
from bot.utils.messages import del_msg_by_db_name
from bot.config.config_loader import classes_dict, second_change_classes_nums


async def choose_class(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    msg = 'Выберите цифру класса'
    await send_status(chat_id, msg, reply_markup=kb.choose_class_num())


async def set_class_number(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    prefix = 'class_number_'  # callback prefix
    callback = callback_query.data[len(prefix):]  # delete prefix
    school_class = callback
    msg = 'Выберите цифру класса'
    await send_status(chat_id=chat_id,
                      text=msg,
                      reply_markup=kb.choose_class_letter(school_class))


async def set_class(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    prefix = 'set_class_'  # callback prefix
    school_class = callback_query.data[len(prefix):]  # delete prefix
    class_number = school_class[-1]

    await del_msg_by_db_name(chat_id, 'last_schedule_message_id')
    await db.update_db_data(chat_id, school_class=school_class)

    if class_number in second_change_classes_nums:
        await db.update_db_data(chat_id, school_change=2)

    else:
        await db.update_db_data(chat_id, school_change=1)

    formatted_class = classes_dict[school_class]
    text = f'Установлен {formatted_class} класс'
    await send_status(chat_id, text=text, reply_markup=None)

    await asyncio.sleep(1.5)  # timer
    await send_schedule(chat_id, now=1)
