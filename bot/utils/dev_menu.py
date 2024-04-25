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


async def dev_settings(query: Union[Message, CallbackQuery]) -> None:
    if type(query) is CallbackQuery:
        chat_id = query.message.chat.id  # get chat_id
        edit = 1
    else:
        chat_id = query.chat.id
        edit = 0
        await del_msg_by_id(chat_id, query.message_id, 'dev_settings')

    custom_logger.debug(chat_id)

    suspend = await db.get_dev_data('suspend_bot')
    dates = await db.get_dev_data('suspend_date')
    if not dates:
        dates = '-'

    txt = (
        'Dev Menu\n\n'
        f'Приостановлен: {["🔴", "🟢"][suspend]}\n'
        f'Даты приостановки: \n{dates}'
    )

    await send_status(
        chat_id,
        text=txt,
        edit=edit,
        reply_markup=kb.dev_settings()
    )


async def suspend_bot(query: CallbackQuery) -> None:
    custom_logger.debug(query.from_user.id)

    await db.turn_suspend_bot(query.from_user.id)
    await dev_settings(query)


async def announce_guide(query: CallbackQuery) -> None:
    custom_logger.debug(query.from_user.id)

    txt = (
        'Чтобы отправить сообщение всем активным пользователям бота, '
        'отправьте боту сообщение с префикcом `/announce `*текст*'
    )

    msg = await bot.send_message(
        query.message.chat.id,
        text=txt,
        parse_mode='MarkDown'
    )

    await asyncio.sleep(4)
    await del_msg_by_id(query.message.chat.id, msg.message_id)


async def announce(message: Message) -> None:
    custom_logger.debug(message.chat.id)

    await del_msg_by_id(message.chat.id, message.message_id)
    prefix = '/announce '
    msg = message.text[len(prefix):]

    chat_id_list = await get_active_user_list()
    chat_id_list.remove(message.from_user.id)

    for chat_id in chat_id_list:
        await bot.send_message(chat_id, text=msg)
        await asyncio.sleep(1)


async def suspend_date_guide(query: CallbackQuery) -> None:
    custom_logger.debug(query.from_user.id)

    txt = (
        'Чтобы добавить даты в список, отправьте боту сообщение с префиксом '
        '`/suspend_date`, после которого идет дата или диапазон дат '
        'через знак "-"\n\nЧтобы удалить даты из списка, '
        'поставьте знак "-" в начале сообщения\n\nПримеры:\n'
        '`/suspend_date 01.01.22` - Добавить 1 Января 22г. в список\n'
        '`/suspend_date -01.01.22` - Убрать 1 Января 22г. из списка\n'
        '`/suspend_date 07.04.24-20.04.24` - Добавить даты с 7 по 20 апреля '
        'в список\n`/suspend_date -07.04.24-20.04.24` - Убрать даты с 7 по '
        '20 апреля из списка'
    )

    msg = await bot.send_message(
        chat_id=query.message.chat.id,
        text=txt,
        parse_mode='MarkDown'
    )

    await asyncio.sleep(10)
    await del_msg_by_id(query.message.chat.id, msg.message_id)


async def check_and_clear_date(message: Message) -> str:
    pattern = re.compile(r'(?:|-)(\d{2}.\d{2}.\d{2})(-(\d{2}.\d{2}.\d{2}))?$')
    prefix = '/suspend_date '
    new_date = message.text[len(prefix):]

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


async def suspend_date(message: Message) -> None:
    custom_logger.debug(message.chat.id)
    await del_msg_by_id(message.chat.id, message.message_id)

    dates = await db.get_dev_data('suspend_date')
    dates = set(dates.split(', ') if dates else dates)
    new_date = await check_and_clear_date(message)
    if not new_date:
        return

    dates = await format_dates(dates, new_date)
    await purge_old_suspend_dates(dates)
    await save_dates(dates)