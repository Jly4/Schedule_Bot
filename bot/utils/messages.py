from aiogram.exceptions import TelegramBadRequest

from main import bot
from bot.logs.log_config import custom_logger
from bot.database.database import db


async def del_msg_by_id(chat_id: int, msg_id: int, msg_name: str = '') -> None:
    custom_logger.debug(chat_id, f'<y>message name: <r>{msg_name}</></>')
    try:
        await bot.delete_message(chat_id, msg_id)

    except TelegramBadRequest:
        msg = f'<y>message: <r>{msg_name}, </>error: </><r>MsgNotFound</>'
        custom_logger.debug(chat_id, msg)

    except Exception as e:
        msg = f'<y>message: <r>{msg_name}</> error: </><r>{e}</>'
        custom_logger.debug(chat_id, msg)


async def del_msg_by_db_name(chat_id: int, msg_id_db_name: str) -> None:
    custom_logger.debug(chat_id, f'<y>message: <r>{msg_id_db_name}</></>')

    message_id: int = await db.get_db_data(chat_id, msg_id_db_name)

    await del_msg_by_id(chat_id, message_id, msg_id_db_name)


async def send_message(chat_id: int, msg: str, **kwargs) -> None:
    """ func let avoids the need to import a bot object from main """
    await bot.send_message(chat_id=chat_id, msg=msg, **kwargs)


async def clear_chat(chat_id: int) -> None:
    """if a message to edit not found, clear old messages """
    chat = (await bot.get_chat(chat_id))
    status_id = await db.get_status_msg_id(chat_id)

    if chat.type == 'private':
        custom_logger.debug(chat_id, f'<y>clear old msg, chat_type:'
                                     f' <r>{chat.type}</></>')

        for ids in range(status_id - 1, status_id - 20, - 1):
            await del_msg_by_id(chat_id, ids, 'clear old messages')
