import os
import time
import asyncio

from typing import Union
from datetime import datetime
from aiogram.types import Message, CallbackQuery

from main import bot
from bot.utils.status import send_status
from bot.keyboards import keyboards as kb
from bot.database.database import db as db
from bot.logs.log_config import custom_logger
from bot.logs.log_config import loguru_config
from bot.utils.messages import del_msg_by_db_name, del_msg_by_id


async def run_bot_tasks():
    loguru_config()  # load loguru config
    await db.database_init()

    chat_id_list = await db.get_user_id_list()
    if not chat_id_list:
        return

    for chat_id in chat_id_list:
        from bot.utils.status import send_status
        await send_status(chat_id)
        # if user have disabled bot
        bot_enabled = await db.get_db_data(chat_id, 'bot_enabled')
        if not bot_enabled:
            custom_logger.info(chat_id, "<y>user was disable bot</>")
            return

        # if user hasn't received schedule for 90 last days
        user_active = await user_is_active(chat_id)
        if user_active:
            await run_task_if_disabled(chat_id, 'schedule_auto_send')
        else:
            await db.delete_chat_id(chat_id)


async def user_is_active(chat_id: int) -> bool:
    """ true if the user was received a schedule for the last 90 days """
    active_time = await db.get_db_data(chat_id, 'last_print_time')
    if active_time == 'еще не проверялось':
        return True

    datetime_format = datetime.strptime(active_time, '%d.%m.%Y. %H:%M:%S')
    difference = datetime.now() - datetime_format

    if difference.days > 90:
        custom_logger.info(chat_id, '<r>User was inactive in last 90days</>')
        return False
    custom_logger.debug(chat_id, 'user is active')
    return True


async def settings(chat_id: int) -> None:
    custom_logger.debug(chat_id)
    from bot.utils.status import send_status
    await send_status(chat_id, edit=1, reply_markup=kb.settings())


async def disable_bot(query: Union[CallbackQuery, Message]) -> None:
    if type(query) is CallbackQuery:
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

    await db.update_db_data(chat_id, bot_enabled=0)


async def start_command(message: Message) -> None:
    chat_id = message.chat.id
    custom_logger.debug(chat_id)
    user_id_list: list = await db.get_user_id_list()  # get chat_id list

    if chat_id not in user_id_list:  # check chat_id in db
        await db.add_new_chat_id(chat_id)  # add chat_id to db
        msg = 'Выберите цифру класса'
        await send_status(chat_id, msg, edit=0,
                          reply_markup=kb.choose_class_num())

    else:
        await db.update_db_data(chat_id, bot_enabled=1)
        await del_msg_by_db_name(chat_id, 'last_status_message_id')
        await send_status(chat_id, edit=0, reply_markup=kb.main())

    await asyncio.sleep(1)
    await del_msg_by_id(chat_id, message.message_id, 'start command')


async def status_command(message: Message) -> None:
    chat_id = message.chat.id
    if not await db.get_db_data(chat_id, 'bot_enabled'):
        return

    await send_status(chat_id, edit=0)
    await del_msg_by_id(chat_id, message.message_id, 'status command')


async def run_task_if_disabled(chat_id: int, task_name: str) -> None:
    all_tasks = asyncio.all_tasks()
    task_name_with_id = f'{chat_id}_{task_name}'

    for task in all_tasks:
        if task.get_name() == task_name_with_id and not task.done():
            custom_logger.debug(
                chat_id,
                f'<y>task: <r>{task_name} </> already running</>'
            )
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


async def old_data_cleaner() -> None:
    files = os.listdir('bot/data')
    current_time = time.time()

    for f in files:
        file_modify_time = os.stat(f'bot/data/{f}').st_mtime
        file_age = current_time - file_modify_time

        if file_age > 3600 * 24 * 7:
            os.remove(f'bot/data/{f}')


async def del_pin_message(message: Message) -> None:
    chat_id = message.chat.id
    chat = await bot.get_chat(chat_id)
    custom_logger.debug(chat_id)

    message_id = message.message_id
    pinned_message_id = chat.pinned_message.message_id
    about_pin_message = message.pinned_message is not None

    if about_pin_message:
        await del_msg_by_id(chat_id, message_id, 'pin_msg')
    else:
        custom_logger.critical(chat_id, f'<y>pin_id: <r>{pinned_message_id}')
        custom_logger.critical(chat_id, f'<y>message_id: <r>{message_id}')
        custom_logger.critical(message)
