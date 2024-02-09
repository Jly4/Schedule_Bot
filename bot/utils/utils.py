import asyncio

from aiogram import types
from loguru import logger
from typing import Union
from datetime import datetime
from aiogram.exceptions import TelegramBadRequest

from main import bot
from bot.logs.log_config import custom_logger
from bot.logs.log_config import loguru_config
from bot.database.db import bot_database as db
from bot.keyboards import keyboards as kb


classes_dict = {
    'a1': '1а', 'b1': '1б', 'v1': '1в', 'g1': '1г', 'd1': '1д', 'e1': '1е',
    'j1': '1ж', 'z1': '1з',
    'a2': '2а', 'b2': '2б', 'v2': '2в', 'g2': '2г', 'd2': '2д', 'e2': '2е',
    'j2': '2ж', 'z2': '2з',
    'a3': '3а', 'b3': '3б', 'v3': '3в', 'g3': '3г', 'd3': '3д', 'e3': '3е',
    'a4': '4а', 'b4': '4б', 'v4': '4в', 'g4': '4г', 'd4': '4д',
    'a5': '5а', 'b5': '5б', 'v5': '5в', 'g5': '5г',
    'a6': '6а', 'b6': '6б', 'v6': '6в', 'g6': '6г',
    'a7': '7а', 'b7': '7б', 'v7': '7в', 'g7': '7г', 'd7': '7д',
    'a8': '8а', 'b8': '8б', 'v8': '8в', 'g8': '8г',
    'a9': '9а', 'b9': '9б', 'v9': '9в',
    'a10': '10а', 'b10': '10б',
    'a11': '11а', 'b11': '11б'
}


async def run_bot_tasks():
    loguru_config()  # load loguru config
    await db.database_init()

    chat_id_list = await db.get_user_id_list()
    if not chat_id_list:
        return

    for chat_id in chat_id_list:
        bot_enabled = await db.get_db_data(chat_id, 'bot_enabled')
        if not bot_enabled:
            return

        active_user = await user_is_active(chat_id)
        if not active_user:
            await db.delete_chat_id(chat_id)
            continue

        from bot.utils.status import send_status
        await send_status(chat_id)

        await run_task_if_disabled(chat_id, 'schedule_auto_send')


async def user_is_active(chat_id: int) -> bool:
    active_time = await db.get_db_data(chat_id, 'last_print_time')
    if active_time == 'еще не проверялось':
        return True

    datetime_format = datetime.strptime(active_time, '%d.%m.%Y. %H:%M:%S')
    difference = datetime.now() - datetime_format
    if difference.days > 90:
        custom_logger.info(chat_id, '<r>User was inactive in last 90days</>')
        return False
    return True


async def del_msg_by_id(chat_id: int, msg_id: types.message_id, msg_name:
str = '') -> None:
    try:
        await bot.delete_message(chat_id, msg_id)  # deleting message
    except TelegramBadRequest:
        msg = f'<y>message: <r>{msg_name}, </>error: </><r>MsgNotFound</>'
        custom_logger.debug(chat_id, msg)
    except Exception as e:
        msg = f'<y>message: <r>{msg_name}</> error: </><r>{e}</>'
        custom_logger.debug(chat_id, msg)


async def del_msg_by_db_name(chat_id: int, msg_id_column_name: Union[int,
str]) -> None:
    custom_logger.debug(chat_id, f'<y>message: <r>{msg_id_column_name}</></>')

    message_id: int = await db.get_db_data(chat_id, msg_id_column_name)

    await del_msg_by_id(chat_id, message_id, msg_id_column_name)


async def settings(chat_id: int) -> None:
    custom_logger.debug(chat_id)
    from bot.utils.status import send_status

    await send_status(chat_id, edit=1, reply_markup=kb.settings())


async def status_message_text(chat_id: int) -> str:
    settings = await db.get_db_data(chat_id,
                                    'pin_schedule_message',
                                    'schedule_auto_send',
                                    'school_class',
                                    'last_printed_change_time',
                                    'last_check_schedule')

    # save settings into variables
    pin_schedule_message, schedule_auto_send, school_class, \
    last_printed_change_time, last_check_schedule = settings

    formatted_class = await format_school_class(school_class)

    status_message = f"""
🔍 Проверка расписания: {last_check_schedule}
📅 Изменение расписания: {last_printed_change_time}\n
🎓 Класс: {formatted_class}
📌 Закреплять расписание: {['Нет', 'Да'][pin_schedule_message]}\n
⏳ Автоматическая проверка расписания:
{['🔴 Выключена', "🟢 Включена, проверка выполняется раз в 10 минут"][schedule_auto_send]}
"""
    return status_message


async def format_school_class(school_class) -> str:
    """return school class name to a status message

    :param school_class:
    :return:
    """
    return classes_dict[school_class]


async def disable_bot(query: Union[types.CallbackQuery, types.Message]) -> None:
    if type(query) is types.CallbackQuery:
        chat_id = query.message.chat.id  # get chat_id
    else:
        chat_id = query.chat.id

    chat = await bot.get_chat(chat_id)  # get chat info
    chat_type = chat.type

    if chat_type == 'private':
        status_id = await db.get_status_msg_id(chat_id)
        for msg_id in range(status_id + 10, status_id - 25, -1):
            await del_msg_by_id(chat_id, msg_id)

    # Удаляем сообщений бота
    await del_msg_by_db_name(chat_id, 'last_schedule_message_id')
    await del_msg_by_db_name(chat_id, 'last_status_message_id')

    await db.update_db_data(chat_id,
                            schedule_auto_send=0,
                            bot_enabled=0,
                            last_status_message_id=0)


async def start_command(chat_id: int) -> None:
    user_id_list: list = await db.get_user_id_list()  # get chat_id list

    if chat_id not in user_id_list:  # check chat_id in db
        await db.add_new_chat_id(chat_id)  # add chat_id to db

    await db.update_db_data(chat_id, schedule_auto_send=0, bot_enabled=1)

    await del_msg_by_db_name(chat_id, 'last_status_message_id')


async def get_admins_id_list(chat_id: int) -> list:
    chat = await bot.get_chat(chat_id)  # get chat info
    chat_type = chat.type  # get a chat type
    custom_logger.debug(chat_id)

    if chat_type == 'private':
        return [chat_id]

    else:
        admins = await bot.get_chat_administrators(chat_id)

        admins_list = [admin.user.id for admin in admins]
        custom_logger.debug(chat_id, f'<y>admin_list: <r>{admins_list}</></>')

        return admins_list


async def run_task_if_disabled(chat_id: int, task_name: str) -> None:
    all_tasks = asyncio.all_tasks()
    task_name_with_id = f'{chat_id}_{task_name}'

    for task in all_tasks:
        if task.get_name() == task_name_with_id and not task.done():
            custom_logger.debug(chat_id,
                                f'<y>task: <r>{task_name} </>running</>')
            return
    if not await db.get_db_data(chat_id, 'schedule_auto_send'):
        custom_logger.debug(chat_id, f'<y>task: <r>{task_name} </>disabled</>')
        return
    custom_logger.debug(chat_id, f'<y>task: <r>{task_name} </>starting</>')
    if task_name == 'schedule_auto_send':
        from bot.utils.schedule import schedule_auto_send
        asyncio.create_task(schedule_auto_send(chat_id), name=task_name_with_id)
    else:
        custom_logger.error(chat_id, f'<y>Wrong task: <r>{task_name}</></>')


async def bot_enabled(chat_id: int) -> bool:
    is_bot_enabled = await db.get_db_data(chat_id, 'bot_enabled')

    if is_bot_enabled:
        return True
    else:
        msg = 'bot отключен, отправьте /start для включения'
        disable_msg = await bot.send_message(chat_id, msg)

        await asyncio.sleep(3)
        await bot.delete_message(chat_id, disable_msg)


async def set_schedule_bg_color(callback_query) -> None:
    chat_id = callback_query.message.chat.id
    custom_logger.debug(chat_id)

    color_code = callback_query.data[10:22]
    color_name = callback_query.data[22:]

    await db.update_db_data(chat_id, schedule_bg_color=color_code)
    txt = f'Установлен {color_name} цвет'

    from bot.utils.status import send_status
    from bot.utils.schedule import send_schedule

    await del_msg_by_db_name(chat_id, 'last_schedule_message_id')
    await send_status(chat_id, text=txt, reply_markup=None)

    await asyncio.sleep(2)
    await send_status(chat_id)
    await send_schedule(chat_id, now=1)


