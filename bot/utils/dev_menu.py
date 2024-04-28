import re
import asyncio

from typing import Union
from datetime import datetime, timedelta
from aiogram.types import Message, CallbackQuery

from main import bot
from bot.utils.status import send_status
from bot.keyboards import keyboards as kb
from bot.database.database import db as db
from bot.logs.log_config import custom_logger
from bot.utils.messages import del_msg_by_id
from bot.utils.utils import get_active_user_list


async def dev_settings(query: Union[Message, CallbackQuery], edit=1) -> None:
    if type(query) is CallbackQuery:
        chat_id = query.message.chat.id  # get chat_id
    else:
        chat_id = query.chat.id
        await del_msg_by_id(chat_id, query.message_id, 'dev_settings')

    custom_logger.debug(chat_id)

    suspend = await db.get_dev_data('suspend_bot')
    dates = await db.get_dev_data('suspend_date')

    txt = (
        'Dev Menu\n\n'
        f'Приостановлен: {["🔴", "🟢"][suspend]}\n'
        f'Даты приостановки: \n{dates}'
    )

    await send_status(
        chat_id,
        text=txt,
        edit=edit,
        reply_markup=kb.dev_settings(menu=True)
    )


async def suspend_bot(query: CallbackQuery) -> None:
    custom_logger.debug(query.from_user.id)

    await db.turn_suspend_bot(query.from_user.id)
    await dev_settings(query)


async def announce(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    custom_logger.debug(chat_id)

    txt = (
        'Отправьте боту сообщение, которое он отправит всем '
        'активным пользователям бота, для отмены нажмите "Назад"'
    )
    status_id = await db.get_status_msg_id(chat_id)
    await bot.edit_message_text(
        chat_id=chat_id,
        text=txt,
        message_id=status_id,
        reply_markup=kb.dev_settings(),
        parse_mode='MarkDown'
    )


async def send_announce(message: Message) -> None:
    await del_msg_by_id(message.chat.id, message.message_id)

    chat_id_list = await get_active_user_list()
    chat_id_list.remove(message.from_user.id)
    msg = message.text

    await dev_settings(message)
    for chat_id in chat_id_list:
        await bot.send_message(chat_id, text=msg)
        await asyncio.sleep(1)


""" suspend dates
"""


async def check_date(message: Message) -> str:
    pattern = re.compile(r'(?:|-)(\d{2}.\d{2}.\d{2})(-(\d{2}.\d{2}.\d{2}))?$')
    new_date = message.text

    if bool(pattern.match(new_date)):
        return new_date

    msg = await bot.send_message(message.chat.id, 'Неправильный формат')

    await asyncio.sleep(2)
    await bot.delete_message(message.chat.id, msg.message_id)
    return ''


async def format_dates(dates: set, new_date: str) -> set:
    remove = new_date.startswith('-')
    if remove:
        new_date = new_date[1:]
    new_date = new_date.split('-')

    if len(new_date) > 1:
        start_date = datetime.strptime(new_date[0], '%d.%m.%y')
        end_date = datetime.strptime(new_date[1], '%d.%m.%y')

        delta = (end_date - start_date).days
        date_range = [end_date - timedelta(days=x) for x in range(delta + 1)]

        new_date = [day.strftime("%d.%m.%y") for day in date_range]

    if remove:
        dates -= set(new_date)
    else:
        dates |= set(new_date)

    return dates


async def purge_old_suspend_dates(dates: set) -> set:
    today = datetime.today() - timedelta(days=1)
    for date in dates.copy():
        if datetime.strptime(date, '%d.%m.%y') < today:
            dates.discard(date)

    return dates


async def save_dates(dates: set) -> None:
    dates = ', '.join(dates)
    await db.update_dev_data(suspend_date=dates)


async def suspend_date(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    custom_logger.debug(chat_id)

    txt = (
        'Чтобы добавить даты в список, отправьте дату или диапазон дат через '
        'знак "-". Чтобы удалить даты из списка, поставьте знак "-" перед '
        'датой начале сообщения\n\nПримеры:\n'
        '`01.01.25` - Добавить 1 Января 2025 в список\n'
        '`-01.01.25` - Убрать 1 Января 2025 из списка\n'
        '`07.04.24-20.04.25` - Добавить даты с 7 по 20 апреля 2025 в список\n'
        '`-07.04.24-20.04.25` - Убрать даты с 7 по 20 апреля 2025 из списка\n\n'
        '_Бот не даст добавить дату которая ужа прошла_'
    )

    status_id = await db.get_status_msg_id(chat_id)
    await bot.edit_message_text(
        chat_id=chat_id,
        text=txt,
        message_id=status_id,
        reply_markup=kb.dev_settings(),
        parse_mode='MarkDown'
    )


async def set_suspend_date(message: Message) -> bool:
    custom_logger.debug(message.chat.id)
    await del_msg_by_id(message.chat.id, message.message_id)

    dates = await db.get_dev_data('suspend_date')
    dates = set(dates.split(', ') if dates else dates)
    new_date = await check_date(message)
    if not new_date:
        return False

    dates = await format_dates(dates, new_date)
    await purge_old_suspend_dates(dates)
    await save_dates(dates)
    await dev_settings(message)

    return True

