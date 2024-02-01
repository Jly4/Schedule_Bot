import asyncio

from aiogram import types
from loguru import logger
from typing import Union
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from bot.databases.database import bot_database as db
from bot.keyboards import keyboards as kb
from bot.init_bot import bot


async def delete_msg_by_id(chat_id: int, message_id: types.message_id, message_name: str = '') -> None:
    try:
        await bot.delete_message(chat_id, message_id)  # deleting message
    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
        logger.opt(colors=True).error(f'<y>Error deleting message: <r>{message_name}, </>error: </>'
                                      f'<r>MessageToDeleteNotFound</>')
    except Exception as e:
        logger.opt(exception=True, colors=True).error(f'<y>Error deleting message: <r>{message_name}, </>error: </>'
                                                      f'<r>{e}</>')


async def delete_msg_by_column_name(chat_id: int, message_id_column_name: Union[int, str]) -> None:
    logger.opt(colors=True).debug(f'<yellow>chat_id: <r>{f"{chat_id}".ljust(15)} | </> message: <r>{message_id_column_name}</></>')
    message_id: int = await db.get_db_data(chat_id, message_id_column_name)  # Получение id сообщения

    await delete_msg_by_id(chat_id, message_id, message_id_column_name)


async def settings(chat_id: int) -> None:
    logger.opt(colors=True).debug(f'(chat_id: {chat_id}) starting')

    # получаем настройки пользователя
    status_message_id = await db.get_status_msg_id(chat_id)

    # обновляем сообщение со статусом
    status_text = await status_message_text(chat_id)

    # отправляем сообщение с найстркоами
    await bot.edit_message_text(chat_id=chat_id,
                                text=status_text,
                                message_id=status_message_id,
                                reply_markup=kb.settings())


async def status_message_text(chat_id: int) -> str:
    # получаем настройки пользователя

    settings = await db.get_db_data(chat_id, 'pin_schedule_message', 'auto_schedule', 'school_class', 'school_change',
                                    'last_printed_change_time', 'last_check_schedule', 'last_status_message_id')

    # сохраняем настройки в переменную
    pin_schedule_message, auto_schedule, school_class, school_change, \
    last_printed_change_time, last_check_schedule, last_status_message_id = settings

    formatted_class = await format_school_class(school_class)

    # обновляем и отправляем переменную статуса
    message = f"""
🔍 Последняя проверка расписания: {last_check_schedule}
📅 Последнее изменение расписания: {last_printed_change_time}\n
🎓 Класс: {formatted_class}
📚 Смена: {['первая', 'вторая'][school_change - 1]}
📌 Закреплять расписание: {['Нет', 'Да'][pin_schedule_message]}\n
⏳ Автоматическая проверка расписания:\n{['🔴 Выключена', f"🟢 Включена, проверка выполняется раз в 10 минут."][auto_schedule]}\n\n
"""
    return message


# format school class
async def format_school_class(school_class):
    # set value
    school_class_dict = {
        'a1': '1а', 'b1': '1б', 'v1': '1в', 'g1': '1г', 'd1': '1д', 'e1': '1е', 'j1': '1ж', 'z1': '1з',
        'a2': '2а', 'b2': '2б', 'v2': '2в', 'g2': '2г', 'd2': '2д', 'e2': '2е', 'j2': '2ж', 'z2': '2з',
        'a3': '3а', 'b3': '3б', 'v3': '3в', 'g3': '3г', 'd3': '3д', 'e3': '3е',
        'a4': '4а', 'b4': '4б', 'v4': '4в', 'g4': '4г', 'd4': '4д',
        'a5': '5а', 'b5': '5б', 'v5': '5в', 'g5': '5г',
        'a6': '6а', 'b6': '6б', 'v6': '6в', 'g6': '6г',
        'a7': '7а', 'b7': '7б', 'v7': '7в', 'g7': '7г', 'd7': '7д',
        'a8': '8а', 'b8': '8б', 'v8': '8в', 'g8': '8г',
        'a9': '9а', 'b9': '9б', 'v9': '9в',
        'a10': '10а', 'b10': '10б',
        'a11': '11а', 'b11': '11б'
    }

    return school_class_dict[school_class]


# format school class
async def existing_school_class(school_class):
    # set value
    school_class_dict = {
        'a1': '1а', 'b1': '1б', 'v1': '1в', 'g1': '1г', 'd1': '1д', 'e1': '1е', 'j1': '1ж', 'z1': '1з',
        'a2': '2а', 'b2': '2б', 'v2': '2в', 'g2': '2г', 'd2': '2д', 'e2': '2е', 'j2': '2ж', 'z2': '2з',
        'a3': '3а', 'b3': '3б', 'v3': '3в', 'g3': '3г', 'd3': '3д', 'e3': '3е',
        'a4': '4а', 'b4': '4б', 'v4': '4в', 'g4': '4г', 'd4': '4д',
        'a5': '5а', 'b5': '5б', 'v5': '5в', 'g5': '5г',
        'a6': '6а', 'b6': '6б', 'v6': '6в', 'g6': '6г',
        'a7': '7а', 'b7': '7б', 'v7': '7в', 'g7': '7г', 'd7': '7д',
        'a8': '8а', 'b8': '8б', 'v8': '8в', 'g8': '8г',
        'a9': '9а', 'b9': '9б', 'v9': '9в',
        'a10': '10а', 'b10': '10б',
        'a11': '11а', 'b11': '11б'
    }

    return 1 if school_class in school_class_dict.keys() else 0


async def disable_bot(query: Union[types.CallbackQuery, types.Message]) -> None:
    if type(query) is types.CallbackQuery:
        chat_id = query.message.chat.id  # get chat_id
    else:
        chat_id = query.chat.id

    chat = await bot.get_chat(chat_id)  # get chat info
    chat_type = chat.type  # get chat type

    if chat_type == 'private':
        status_id = await db.get_status_msg_id(chat_id)
        for msg_id in range(status_id + 10, status_id - 10, -1):
            await delete_msg_by_id(chat_id, msg_id)

    # Удаляем сообщений бота
    await delete_msg_by_column_name(chat_id, 'last_schedule_message_id')
    await delete_msg_by_column_name(chat_id, 'last_status_message_id')

    await db.update_db_data(chat_id,
                            auto_schedule=0,
                            bot_enabled=0,
                            last_status_message_id=0)


async def start_command(chat_id: int) -> None:
    user_id_list: list = await db.get_user_id_list()  # Получаем список id пользователей из базы данных

    if chat_id not in user_id_list:  # если человек нет в базе данных
        logger.info(f'New user: {chat_id}')

        await db.add_new_chat_id(chat_id)  # add chat_id to db

    await db.update_db_data(chat_id, auto_schedule=0, bot_enabled=1)

    await delete_msg_by_column_name(chat_id, 'last_status_message_id')
    await delete_msg_by_column_name(chat_id, 'last_disable_message_id')


async def get_admins_id_list(chat_id: int) -> list:
    chat = await bot.get_chat(chat_id)  # get chat info
    chat_type = chat.type  # get chat type
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>starting</>')

    if chat_type == 'private':
        return [chat_id]

    else:
        admins = await bot.get_chat_administrators(chat_id)

        admins_list = [admin.user.id for admin in admins]
        logger.opt(colors=True).debug(f'<y>admin_list: <r>{admins_list}</></>')

        return admins_list


async def task_not_running(task_name: str) -> bool:
    all_tasks = asyncio.all_tasks()

    for task in all_tasks:
        if task.get_name() == task_name and not task.done():
            logger.opt(colors=True).info(f'<yellow>{task_name}: <r>Running</></>')

            return False

    logger.opt(colors=True).info(f'<yellow>{task_name}: <r>Not Running</></>')
    return True


async def bot_enabled(chat_id: int) -> bool:
    is_bot_enabled = await db.get_db_data(chat_id, 'bot_enabled')

    if is_bot_enabled:
        return True
    else:
        disabled_msg = await bot.send_message(chat_id, 'bot отключен, отправьте /start для включения')

        await asyncio.sleep(3)
        await bot.delete_message(chat_id, disabled_msg)
