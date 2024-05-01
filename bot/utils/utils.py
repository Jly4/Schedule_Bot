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
from bot.logs.log_config import custom_logger, loguru_config
from bot.config.config import second_change_nums, classes_dict
from bot.utils.messages import del_msg_by_db_name, del_msg_by_id


async def run_bot_tasks():
    loguru_config()  # load loguru config
    await db.database_init()
    chat_id_list = await get_active_user_list()

    if not chat_id_list:
        return

    for chat_id in chat_id_list:
        # noinspection PyAsyncCall
        asyncio.create_task(run_task_if_disabled(
            chat_id,
            'schedule_auto_send')
        )
        await asyncio.sleep(5)


async def get_active_user_list() -> list:
    """ true if the user was received a schedule for the last 90 days """
    active_user_list = []
    chat_id_list = await db.get_user_id_list()

    for chat_id in chat_id_list:
        school_class = await db.get_db_data(chat_id, 'school_class')
        bot_enabled = await db.get_db_data(chat_id, 'bot_enabled')
        active_time = await db.get_data_by_cls(
            chat_id,
            school_class,
            'last_print_time'
        )

        if not bot_enabled:
            custom_logger.info(chat_id, "<y>user was disable bot</>")
            continue

        if active_time == '':
            active_user_list.append(chat_id)
            continue

        datetime_format = datetime.strptime(active_time, '%d.%m.%Y. %H:%M:%S')
        difference = datetime.now() - datetime_format

        if difference.days > 90:
            custom_logger.info(chat_id, '<r>User was inactive in 90days</>')
            await db.delete_chat_id(chat_id)

        custom_logger.debug(chat_id, 'user is active')
        active_user_list.append(chat_id)

    return active_user_list


async def settings(query: CallbackQuery) -> None:
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    custom_logger.debug(chat_id)
    from bot.utils.status import status_message_text

    txt = await status_message_text(chat_id, settings=True)
    status_message_id = await db.get_status_msg_id(chat_id)

    await bot.edit_message_text(
        chat_id=chat_id,
        text=txt,
        message_id=status_message_id,
        reply_markup=kb.settings(user_id),
        parse_mode='Markdown'
    )


async def disable_bot(query: Union[CallbackQuery, Message]) -> None:
    if type(query) is CallbackQuery:
        chat_id = query.message.chat.id  # get chat_id
    else:
        chat_id = query.chat.id

    # clear chat
    id_list = []
    for cls in classes_dict.keys():
        cls = await add_change_to_class(cls)
        msg_id = await db.get_data_by_cls(
            chat_id,
            cls,
            'last_schedule_message_id'
        )
        if msg_id:
            id_list.append(msg_id)
            await del_msg_by_id(chat_id, msg_id, 'clear_chat')

    chat = await bot.get_chat(chat_id)
    if chat.type == 'private':
        status_id = await db.get_status_msg_id(chat_id)
        message_id = max(id_list) + 15 if id_list else status_id + 30
        # noinspection PyUnboundLocalVariable
        for msg_id in range(message_id, status_id - 30, -1):
            await del_msg_by_id(chat_id, msg_id, 'clear_chat')

    # disable bot for user
    await db.update_db_data(chat_id, bot_enabled=0)


async def start_command(message: Message) -> None:
    chat_id = message.chat.id
    custom_logger.debug(chat_id)
    user_id_list: list = await db.get_user_id_list()  # get chat_id list

    if chat_id not in user_id_list:  # check chat_id in db
        await db.add_new_chat_id(chat_id)  # add chat_id to db
        msg = 'Выберите цифру класса'
        await send_status(
            chat_id=chat_id,
            text=msg,
            edit=0,
            reply_markup=kb.choose_class_number()
        )

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

    await del_msg_by_db_name(chat_id, 'last_status_message_id')
    await send_status(chat_id, edit=0)
    await del_msg_by_id(chat_id, message.message_id, 'status command')


async def task_already_run(chat_id, task_name) -> bool:
    all_tasks = asyncio.all_tasks()

    for task in all_tasks:
        if task.get_name() == task_name and not task.done():
            custom_logger.debug(
                chat_id,
                f'<y>task: <r>{task_name} </> already running</>'
            )
            return True
    return False


async def run_task_if_disabled(chat_id: int, task: str) -> None:
    """
    :param chat_id: number of user id
    :param task:  class which the user as extra thread
    to get updates for schedule
    """
    threads = await db.get_db_data(chat_id, 'autosend_classes')
    cls = await db.get_db_data(chat_id, 'school_class')
    threads = list(threads.split(', ') if threads else threads)
    threads.append(cls)  # clear class from change and add to a thread list
    threads.sort(reverse=True)

    # if user have disabled autosend feature
    if not await db.get_db_data(chat_id, 'schedule_auto_send'):
        custom_logger.debug(chat_id, f'<y>task: <r>{task} </>disabled</>')
        return

    for thread in threads:
        task_name = f'{chat_id}_{task}_{thread}'
        if await task_already_run(chat_id, task_name):
            continue

        custom_logger.debug(chat_id, f'<y>task: <r>{task_name} </>starting</>')
        if task == 'schedule_auto_send':
            from bot.utils.schedule import schedule_auto_send
            # noinspection PyAsyncCall
            asyncio.create_task(
                schedule_auto_send(chat_id, thread),
                name=task_name
            )
        else:
            custom_logger.critical(chat_id, f'<y>Wrong task: <r>{task}</></>')
        # sleep time before starting the next thread(school_class)
        await asyncio.sleep(30)


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


async def add_change_to_class(school_class: str) -> str:
    if school_class[1:] in second_change_nums:
        school_class += '2'
    else:
        school_class += '1'

    return school_class
