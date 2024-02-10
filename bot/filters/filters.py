import asyncio
from typing import Union

from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter

from main import bot
from bot.utils.utils import del_msg_by_id
from bot.logs.log_config import custom_logger


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
