from typing import Optional

from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram import exceptions

from main import bot
from bot.database.database import db
from bot.keyboards import keyboards as kb
from bot.config.config import classes_dict, schedule_auto_send_delay
from bot.logs.log_config import custom_logger
from bot.exceptions.exceptions import retry_after
from bot.utils.messages import del_msg_by_db_name, clear_chat


async def send_status(
        chat_id: int,
        text: str = None,
        edit: int = 1,
        reply_markup: Optional[InlineKeyboardMarkup] = kb.main()
) -> None:
    status_msg_id = await db.get_status_msg_id(chat_id)
    if not status_msg_id:
        return

    if text is None:
        text = await status_message_text(chat_id)

    args = {
        "chat_id": chat_id,
        "text": text,
        "message_id": status_msg_id,
        "reply_markup": reply_markup,
    }

    if edit:
        await edit_status(args)

    else:
        await resend_status(args)


async def edit_status(args) -> None:
    chat_id: int = args["chat_id"]
    try:
        await bot.edit_message_text(
            chat_id=args["chat_id"],
            text=args["text"],
            message_id=args["message_id"],
            reply_markup=args["reply_markup"]
        )

        custom_logger.debug(chat_id, '<y>successful edited</>')

    except exceptions.TelegramForbiddenError as e:
        msg = (f'<y>Bot was kicked or blocked, deleting '
               f'chat_id from bd: <r>{e}</></>')
        custom_logger.error(chat_id, msg)

        await db.delete_chat_id(chat_id)  # delete chat_id from db

    except exceptions.TelegramBadRequest as e:
        if "exactly the same as a current content" in str(e):
            custom_logger.debug(chat_id, '<y>message have same content</>')
            return

        elif "message to edit not found" in str(e):
            custom_logger.error(chat_id, '<y>message to edit not found</>')
            await resend_status(args, clean=1)

        else:
            custom_logger.error(chat_id, f'<y>edit error: <r>{e}</></>')
            await resend_status(args, clean=1)

    except exceptions.TelegramNetworkError as e:
        return

    except Exception as e:
        custom_logger.critical(
            chat_id,
            msg=f'<y>edit error: <r>{e}</></>',
            exception=True)

        await resend_status(args, clean=1)


async def resend_status(args: dict, clean: int = 0) -> None:
    chat_id = args["chat_id"]
    try:
        await del_msg_by_db_name(chat_id, 'last_status_message_id')
        status_msg = await bot.send_message(
            chat_id=args["chat_id"],
            text=args["text"],
            reply_markup=args["reply_markup"],
            disable_notification=True
        )
        # update status id
        msg_id = status_msg.message_id
        await db.update_db_data(chat_id, last_status_message_id=msg_id)

        custom_logger.debug(chat_id, '<y>status successful sent</>')

        if clean:
            await clear_chat(chat_id)

    except exceptions.TelegramForbiddenError as e:
        msg = (f'<y>Bot was kicked or blocked, '
               f'deleting chat_id from bd: <r>{e}</></>')
        custom_logger.info(chat_id, msg)

        await db.delete_chat_id(chat_id)  # delete chat_id from db

    except exceptions.TelegramRetryAfter:
        await retry_after(chat_id)

    except Exception as e:
        custom_logger.critical(chat_id, f'<y>edit status error: <r>{e}</></>')


async def status_message_text(chat_id: int, settings: bool = False) -> str:
    data = await db.get_db_data(
        chat_id,
        'del_old_schedule',
        'pin_schedule_message',
        'schedule_auto_send',
        'school_class',
    )
    (del_old_schedule, pin_schedule_message, auto_send,
     school_class) = data

    data = await db.get_data_by_cls(
        chat_id,
        school_class,
        'last_printed_change_time',
        'last_check_schedule'
    )
    last_printed_change_time, last_check_schedule = data

    formatted_class = classes_dict[school_class[:-1]]
    delay = schedule_auto_send_delay
    if auto_send:
        auto_send_msg = f'🟢 Включена, проверка выполняется раз в {delay} минут'
    else:
        auto_send_msg = '🔴 Выключена'

    status_message = (
        f"🔍 Проверка расписания: {last_check_schedule}\n"
        f"📅 Изменение расписания: {last_printed_change_time}\n\n"
        f"🎓 Класс: {formatted_class}\n"
        f"⏳ Автоматическая проверка расписания: \n"
        f"{auto_send_msg}"
    )

    settings_message = (
        f'🎓 Класс: {formatted_class}\n'
        f'📌 Закреплять расписание: {["🔴", "🟢"][pin_schedule_message]}\n'
        f'🗑️ Удалять предыдущее расписание: {["🔴", "🟢"][del_old_schedule]}\n'
        f'⏳ Автоматическое обновление: {["🔴", "🟢"][auto_send]}\n\n'
        '_Информацию по всем параметрам можно получить по кнопке '
        '"Информация о боте"_'
    )

    if settings:
        return settings_message
    return status_message
