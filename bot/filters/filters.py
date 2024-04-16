import pytz
import asyncio
from datetime import datetime
from typing import Union

from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter

from main import bot
from bot.utils.utils import del_msg_by_id
from bot.logs.log_config import custom_logger
from bot.config.config import dev_id
from bot.database.database import db

local_timezone = pytz.timezone('Asia/Tomsk')


class IsDev(BaseFilter):
    async def __call__(self, query: Message):
        if str(query.from_user.id) == dev_id:
            return True
        else:
            return False


class IsAdmin(BaseFilter):
    async def __call__(self, query: Union[CallbackQuery, Message]) -> bool:
        if query.from_user.is_bot:
            return False

        if isinstance(query, Message):
            chat_id = query.chat.id
            chat_type = query.chat.type
        else:
            chat_id = query.message.chat.id
            chat_type = query.message.chat.type
            await bot.answer_callback_query(query.id)  # complete callback
        custom_logger.debug(chat_id, depth=1)

        username = query.from_user.username
        user_id = query.from_user.id

        msg = f'<y>username: <r>{username} </>starting</>'
        custom_logger.debug(chat_id, msg)

        if user_id in await get_admins_id_list(chat_id, chat_type):
            custom_logger.debug(chat_id, '<y>is admin: <r>True</></>')
            return True

        else:
            custom_logger.debug(chat_id, '<y>is admin: <r>False</></>')
            txt = (f'Привет, {username}! Настройки доступны '
                   f'только администраторам.')
            msg = await bot.send_message(chat_id, text=txt, reply_markup=None)

            await asyncio.sleep(2)  # timer
            await del_msg_by_id(chat_id, msg.message_id)

            if isinstance(query, Message):
                await del_msg_by_id(chat_id, query.message_id)
            return False


async def get_admins_id_list(chat_id: int, chat_type: str) -> list:
    custom_logger.debug(chat_id)
    if chat_type == 'private':
        return [chat_id]
    else:
        admins = await bot.get_chat_administrators(chat_id)

        admins_list = [admin.user.id for admin in admins]
        custom_logger.debug(chat_id, f'<y>admin_list: <r>{admins_list}</></>')

        return admins_list


class AutoSendFilter:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id

    async def filter(self) -> int:
        if await self.bot_and_autosend():
            return 0

        if await db.get_dev_data('suspend_bot'):
            return 1

        if not await self.time_filter():
            return 1

        return 2

    async def bot_and_autosend(self) -> int:
        conditions = await db.get_db_data(
            self.chat_id,
            'schedule_auto_send',
            'bot_enabled'
        )

        if not (conditions[0] and conditions[1]):
            custom_logger.debug(
                self.chat_id,
                f'cond: {conditions[0], conditions[1]}')

            return False

    @staticmethod
    async def time_filter() -> int:
        local_date = datetime.now(local_timezone)
        hour = local_date.hour
        month = local_date.month
        formatted_date = local_date.strftime("%d.%m.%y")
        dates_str = await db.get_dev_data('suspend_date')
        dates = set(dates_str.split(', '))

        if hour < 6:
            return False

        if month in [6, 7, 8]:
            return False

        if formatted_date in dates:
            custom_logger.debug(msg='suspended by date')
            return False

        return True

