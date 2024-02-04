import asyncio

from loguru import logger
from aiogram.utils.exceptions import BotKicked, BotBlocked, MessageNotModified, ChatNotFound, CantInitiateConversation
from aiogram.utils.exceptions import MessageToEditNotFound
from aiogram.types.inline_keyboard import InlineKeyboardMarkup

from bot.init_bot import bot
from bot.configs import config
from bot.keyboards import keyboards as kb
from bot.databases.database import bot_database as db
from bot.utils.utils import del_msg_by_db_name, status_message_text


# Функция управляющая отправкой статуса
async def auto_status(chat_id: int) -> None:
    logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>auto_status: started</>')

    while await db.get_db_data(chat_id, 'bot_enabled'):
        # запуск
        await send_status(chat_id)

        # задержка сканирования
        await asyncio.sleep(config.auto_status_delay * 60)


# Сообщение со статусом
async def send_status(chat_id: int, edit: int = 1, keyboard: InlineKeyboardMarkup = kb.main_keyboard()) -> None:
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | start: </>edit: <r>{edit}</></>')

    status_message_id = await db.get_status_msg_id(chat_id)  # get status message id
    status_text = await status_message_text(chat_id)  # update status text

    if edit:
        try:
            await bot.edit_message_text(chat_id=chat_id, text=status_text,
                                        message_id=status_message_id,
                                        reply_markup=keyboard
                                        )

            logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>status successful edited </>')

        except (BotKicked, BotBlocked, ChatNotFound) as e:
            logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>Bot was kicked or blocked,'
                                          f' deleting chat_id from bd: </><r>{e}</>')
            await db.delete_chat_id(chat_id)  # delete chat_id from db

        except MessageNotModified as e:
            logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>status not edited</>')

        except MessageToEditNotFound as e:
            logger.opt(colors=True).error(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>edit failed: </><r>{e}</>')
            edit = 0  # resend schedule

        except Exception as e:
            logger.opt(colors=True, exception=True).error(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>edit failed: </><r>{e}</>')
            edit = 0  # resend schedule

    if not edit:
        try:
            await del_msg_by_db_name(chat_id, 'last_status_message_id')  # delete old status message if exist

            # переменная с отправленным сообщением
            status_message_id = await bot.send_message(chat_id,
                                                       text=status_text,
                                                       disable_notification=True,
                                                       reply_markup=keyboard
                                                       )
            # update status id
            await db.update_db_data(chat_id, last_status_message_id=status_message_id.message_id)
            logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>status successful sent</>')

        except (BotKicked, BotBlocked, ChatNotFound, CantInitiateConversation) as e:
            logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>Bot was kicked or blocked: '
                                          f'Deleting chat_id from bd: <r>{e}</></>'
                                          )
            await db.delete_chat_id(chat_id)  # delete chat_id from db

        except Exception as e:
            logger.opt(colors=True, exception=True).error(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>send failed </><r>{e}</>')


