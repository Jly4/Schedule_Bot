import asyncio

from typing import Union
from loguru import logger
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.exceptions import TelegramNotFound, TelegramBadRequest, \
    TelegramForbiddenError

from main import bot
from bot.keyboards import keyboards as kb
from bot.database.db import bot_database as db
from bot.utils.utils import del_msg_by_db_name, status_message_text, del_msg_by_id
from bot.config.config_loader import status_auto_update_delay

# Функция управляющая отправкой статуса
async def status_auto_update(chat_id: int) -> None:
    logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | '
                                 f'</>status_auto_update: started</>')

    while await db.get_db_data(chat_id, 'bot_enabled'):
        # запуск
        await send_status(chat_id)

        # задержка сканирования
        await asyncio.sleep(status_auto_update_delay * 60)


# Сообщение со статусом
async def send_status(
        chat_id: int,
        text: str = '',
        edit: int = 1,
        reply_markup: Union[InlineKeyboardMarkup, None] = kb.main()
) -> None:
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | '
                                  f'</>edit: <r>{edit}</></>')

    if text == '':
        text = await status_message_text(chat_id)

    args = {
        "chat_id": chat_id,  # Замените на фактический идентификатор чата
        "text": text,
        "message_id": await db.get_status_msg_id(chat_id),  # Замените на фактический идентификатор сообщения
        "reply_markup": reply_markup,  # Замените на ваш объект клавиатуры
    }
    clear_old_msg = False

    if edit:
        try:
            await bot.edit_message_text(chat_id=args["chat_id"],
                                        text=args["text"],
                                        message_id=args["message_id"],
                                        reply_markup=args["reply_markup"]
                                        )

            logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>status successful edited </>')

        except TelegramForbiddenError as e:
            logger.opt(colors=True).debug(f'<y>chat_id: <r>'
                                          f'{f"{chat_id}".rjust(15)} | </>Bot was kicked or blocked,'
                                          f' deleting chat_id from bd: <r>{e}</></>')
            await db.delete_chat_id(chat_id)  # delete chat_id from db

        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                logger.opt(colors=True).error(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>edit failed: </><r>{e}</>')

            else:
                logger.opt(colors=True).error(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>edit failed: </><r>{e}</>')
                edit = 0  # resend schedule

        except Exception as e:
            logger.opt(colors=True, exception=True).error(
                f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>edit failed: <r>{e}</></>')
            edit = 0  # resend schedule

    if not edit:
        try:
            await del_msg_by_db_name(chat_id, 'last_status_message_id')  # delete old status message if exist

            # переменная с отправленным сообщением
            status_message = await bot.send_message(chat_id=args["chat_id"],
                                                    text=args["text"],
                                                    reply_markup=args["reply_markup"],
                                                    disable_notification=True
                                                    )
            # update status id
            await db.update_db_data(chat_id, last_status_message_id=status_message.message_id)
            logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>status successful sent</>')

            if clear_old_msg:
                '''if message to edit not found, clear old messages
                '''
                chat = await bot.get_chat(chat_id)  # get chat info
                chat_type = chat.type  # get chat type
                status_id = status_message.message_id

                if chat_type == 'private':
                    logger.opt(colors=True).critical(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>clear old msg, '
                                                     f'chat_type: <r>{chat_type}</></>')
                    for id in range(status_id - 1, status_id - 10, - 1):
                        # logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>try delete message {id}</>')
                        await del_msg_by_id(chat_id, id, 'clear old messages')

        except TelegramForbiddenError as e:
            logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>Bot was kicked or blocked: '
                                          f'Deleting chat_id from bd: <r>{e}</></>'
                                          )
            await db.delete_chat_id(chat_id)  # delete chat_id from db

        except Exception as e:
            logger.opt(colors=True, exception=True).error(
                f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>send failed <r>{e}</></>')
