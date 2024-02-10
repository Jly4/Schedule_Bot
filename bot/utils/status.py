from typing import Optional

from loguru import logger
from aiogram.utils.keyboard import InlineKeyboardMarkup

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from main import bot
from bot.database.database import db
from bot.keyboards import keyboards as kb
from bot.logs.log_config import custom_logger
from bot.config.config_loader import classes_dict
from bot.utils.messages import del_msg_by_db_name, del_msg_by_id



async def send_status(
        chat_id: int,
        text: str = '',
        edit: int = 1,
        reply_markup: Optional[InlineKeyboardMarkup] = kb.main()
) -> None:
    custom_logger.debug(chat_id, f'<y>started, edit: <r>{edit}</></>')

    if text == '':
        text = await status_message_text(chat_id)

    args = {
        "chat_id": chat_id,  # Замените на фактический идентификатор чата
        "text": text,
        "message_id": await db.get_status_msg_id(chat_id),
        # Замените на фактический идентификатор сообщения
        "reply_markup": reply_markup,  # Замените на ваш объект клавиатуры
    }
    clear_old_msg = False

    if edit:
        try:
            await bot.edit_message_text(chat_id=args["chat_id"],
                                        text=args["text"],
                                        message_id=args["message_id"],
                                        reply_markup=args["reply_markup"])

            custom_logger.debug(chat_id, '<y>successful edited</>')

        except TelegramForbiddenError as e:
            msg = (f'<y>Bot was kicked or blocked, deleting '
                   f'chat_id from bd: <r>{e}</></>')

            custom_logger.error(chat_id, msg)
            await db.delete_chat_id(chat_id)  # delete chat_id from db

        except TelegramBadRequest as e:
            if "exactly the same as a current content" in str(e):
                custom_logger.error(chat_id, '<y>message have same content</>')

            elif "message to edit not found" in str(e):
                custom_logger.error(chat_id, '<y>message to edit not found</>')
                edit = 0
                clear_old_msg = 1

        except Exception as e:
            custom_logger.error(chat_id, f'<y>edit failed: </><r>{e}</>',
                                exception=True)

            edit = 0  # resend schedule

    if not edit:
        try:
            await del_msg_by_db_name(chat_id, 'last_status_message_id')

            # переменная с отправленным сообщением
            status_message = await bot.send_message(chat_id=args["chat_id"],
                                                    text=args["text"],
                                                    reply_markup=args[
                                                        "reply_markup"],
                                                    disable_notification=True)
            # update status id
            await db.update_db_data(chat_id,
                                    last_status_message_id=status_message.message_id)
            custom_logger.debug(chat_id, '<y>status successful sent</>')

            if clear_old_msg:
                '''if message to edit not found, clear old messages
                '''
                chat = await bot.get_chat(chat_id)  # get chat info
                chat_type = chat.type  # get a chat type
                status_id = status_message.message_id

                if chat_type == 'private':
                    custom_logger.debug(chat_id, f'<y>clear old msg, chat_type:'
                                                 f' <r>{chat_type}</></>')

                    for id in range(status_id - 1, status_id - 20, - 1):
                        await del_msg_by_id(chat_id, id, 'clear old messages')

        except TelegramForbiddenError as e:
            msg = (f'<y>Bot was kicked or blocked, deleting '
                   f'chat_id from bd: <r>{e}</></>')

            custom_logger.error(chat_id, msg)
            await db.delete_chat_id(chat_id)  # delete chat_id from db

        except Exception as e:
            logger.opt(colors=True, exception=True).error(
                f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>send failed '
                f'<r>{e}</></>')


async def status_message_text(chat_id: int) -> str:
    settings = await db.get_db_data(chat_id,
                                    'pin_schedule_message',
                                    'schedule_auto_send',
                                    'school_class',
                                    'last_printed_change_time',
                                    'last_check_schedule')

    # save settings into variables
    pin_schedule_message, schedule_auto_send, school_class, \
        last_printed_change_time, last_check_schedule = settings

    formatted_class = classes_dict[school_class]

    status_message = f"""
🔍 Проверка расписания: {last_check_schedule}
📅 Изменение расписания: {last_printed_change_time}\n
🎓 Класс: {formatted_class}
📌 Закреплять расписание: {['Нет', 'Да'][pin_schedule_message]}\n
⏳ Автоматическая проверка расписания:
{['🔴 Выключена', "🟢 Включена, проверка выполняется раз в 10 минут"][schedule_auto_send]}
"""
    return status_message

