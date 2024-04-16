import re
import asyncio
from typing import Union

from aiogram.types import Message, CallbackQuery

from main import bot
from bot.database.database import db
from bot.utils.status import send_status
from bot.utils.schedule import send_schedule
from bot.keyboards import keyboards as kb
from bot.logs.log_config import custom_logger
from bot.utils.messages import del_msg_by_db_name


async def color_set_menu(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    status_message_id = await db.get_status_msg_id(chat_id)
    text = (
        'Для смены цвета фона расписания вы можете воспользоваться '
        'одним из предложенных ниже цветов, либо отправить боту '
        'сообщение с кодом цвета в формате RGB по примеру ниже.\n\n'
        '`Set color 256, 256, 256`\n(Нажмите, чтобы скопировать)\n'
        'Замените цифры на свои\n\n'
        'Выбрать цвет в формате RGB можно '
        '[тут](https://www.google.com/search?q=rgb+color+picker).\n'
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_message_id,
        reply_markup=kb.choose_color(),
        disable_web_page_preview=True,
        parse_mode='MarkDown'
    )


async def set_bg_color(query: Union[CallbackQuery, Message]) -> None:
    if isinstance(query, Message):
        """ receive color code from a message """
        chat_id = query.chat.id
        custom_logger.debug(chat_id, 'set color msg')

        prefix = 'set color '  # message  prefix
        color = query.text[len(prefix):]  # delete prefix
        color_pattern = re.compile(r'^\d{1,3},\s*\d{1,3},\s*\d{1,3}$')

        if bool(color_pattern.match(color)):
            await db.update_db_data(chat_id, schedule_bg_color=color)

            msg = 'Цвет успешно сменен'
            await send_status(chat_id, text=msg, edit=0, reply_markup=None)
            await del_msg_by_db_name(chat_id, 'last_schedule_message_id')

            await asyncio.sleep(1.5)
            await send_schedule(chat_id, now=1)
        else:
            msg = await bot.send_message(chat_id, 'Неправильный формат')

            await asyncio.sleep(2)
            await bot.delete_message(chat_id, msg.message_id)

        await bot.delete_message(chat_id, query.message_id)

    if isinstance(query, CallbackQuery):
        """ receive color code from callback """
        chat_id = query.message.chat.id
        custom_logger.debug(chat_id, 'set color callback')

        color_code = query.data[10:22]
        color_name = query.data[22:]

        await db.update_db_data(chat_id, schedule_bg_color=color_code)
        txt = f'Установлен {color_name} цвет'

        await send_status(chat_id, text=txt, reply_markup=None)
        await del_msg_by_db_name(chat_id, 'last_schedule_message_id')

        await asyncio.sleep(1.5)
        await send_schedule(chat_id, now=1)
