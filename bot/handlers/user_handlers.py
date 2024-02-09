import re
import asyncio

from typing import Union
from aiogram import Router, F, types
from aiogram.filters import CommandStart

from main import bot

from bot.keyboards import keyboards as kb
from bot.config.config_loader import dev_id
from bot.logs.log_config import custom_logger
from bot.database.db import bot_database as db
from bot.utils.status import send_status
from bot.utils.schedule import send_schedule
from bot.utils.utils import run_task_if_disabled, bot_enabled, start_command
from bot.utils.utils import settings, del_msg_by_id, set_schedule_bg_color
from bot.utils.utils import disable_bot, format_school_class, \
     get_admins_id_list, del_msg_by_db_name

router = Router()

""" bot commands handlers
"""


@router.message(CommandStart())
async def start_msg(message: types.Message) -> None:
    if await user_not_admin(message):
        return
    chat_id: int = message.chat.id
    await start_command(chat_id)  # start_command func
    # open keyboard to choose class
    msg = 'Выберите цифру класса'
    await send_status(chat_id, msg, edit=0, reply_markup=kb.choose_class_num())

    await asyncio.sleep(1)
    await del_msg_by_id(chat_id, message.message_id, 'start command')


@router.message(F.text.lower() == '/status')
async def status_msg(message: types.Message) -> None:
    chat_id = message.chat.id
    custom_logger.debug(chat_id)

    if not await bot_enabled(chat_id):
        return
    await del_msg_by_id(chat_id, message.message_id, 'status command')
    await send_status(chat_id, edit=0)  # update status


@router.message(F.text.lower() == '/disable')
async def disable_bot_msg(message: types.Message) -> None:
    if await user_not_admin(message):
        return
    chat_id: int = message.chat.id
    if await bot_enabled(chat_id):
        await del_msg_by_id(chat_id, message.message_id, 'disable command')
        await disable_bot(message)  # start disable bot func


@router.message(F.text.lower() == '/dev')
async def dev_command_msg(message: types.Message) -> None:
    chat_id = message.chat.id  # save chat_id
    user_id: int = message.from_user.id
    await del_msg_by_id(chat_id, message.message_id, 'dev command')
    custom_logger.debug(chat_id)

    if user_id == dev_id:
        await send_status(chat_id, 'Hello, Dev!', reply_markup=kb.dev())

    else:
        text = ("hehe, I don't know how you found this command, but anyway "
                "only dev have access :)")
        dev_msg = await bot.send_message(chat_id, text)

        await asyncio.sleep(4)
        await del_msg_by_id(chat_id, dev_msg.message_id, 'dev command')


@router.callback_query(F.data == 'status')
async def status_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    custom_logger.debug(chat_id)
    await send_status(chat_id)


""" color handlers
"""


@router.callback_query(F.data == 'color_menu')
async def color_set_menu_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    status_message_id = await db.get_status_msg_id(chat_id)
    text = ('Для смены цвета фона расписания, вы можете воспользоваться'
            'одним из предложенных ниже цветом, либо отправить боту '
            'сообщение с кодом цвета в формате RGB по примеру ниже.\n'
            '`Set color 256, 256, 256`\n(Нажмите чтобы скопировать)\n'
            'Замените цифры в на свои\n\n'
            'Выбрать цвет в формате RGB можно '
            '[тут](https://www.google.com/search?q=rgb+color+picker).\n')

    await bot.edit_message_text(chat_id=chat_id, text=text,
                                message_id=status_message_id,
                                reply_markup=kb.choose_color(),
                                disable_web_page_preview=True,
                                parse_mode='MarkDown')


@router.message(F.text.lower().startswith('set color '))
async def set_color_msg(message: types.Message) -> None:
    if await user_not_admin(message):
        return
    chat_id = message.chat.id  # get chat_id
    prefix = 'set color '
    color = await clear_callback(message, prefix)
    color_pattern = re.compile(r'^\d{1,3},\s*\d{1,3},\s*\d{1,3}$')

    if bool(color_pattern.match(color)):
        await send_status(chat_id)
        await db.update_db_data(chat_id, schedule_bg_color=color)

        msg = await bot.send_message(chat_id, 'Цвет успешно сменен')
        await send_schedule(chat_id, now=1)

    else:
        msg = await bot.send_message(chat_id, 'Не правильный формат')

    await asyncio.sleep(2)
    await bot.delete_message(chat_id, message.message_id)
    await bot.delete_message(chat_id, msg.message_id)


@router.callback_query(F.data.startswith('set color '))
async def default_color_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return

    await set_schedule_bg_color(callback_query)


""" settings handlers
"""


@router.callback_query(F.data == 'settings')
async def settings_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return

    await settings(callback_query.message.chat.id)


""" schedule handlers
"""


@router.callback_query(F.data == 'update_schedule')
async def update_schedule_call(callback_query: types.CallbackQuery) -> None:
    await send_schedule(callback_query.message.chat.id, now=1)
    await callback_completion(callback_query)


@router.callback_query(F.data == 'schedule_auto_send')
async def turn_schedule_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    if await db.get_db_data(chat_id, 'schedule_auto_send'):
        await db.update_db_data(chat_id, schedule_auto_send=0)

        txt = 'Автоматическое получение расписания выключено'
        await send_status(chat_id, text=txt, reply_markup=None)

    else:
        await db.update_db_data(chat_id, schedule_auto_send=1)

        txt = 'Автоматическое получение расписания включено'
        await send_status(chat_id, text=txt, reply_markup=None)

        await send_schedule(chat_id, now=1)
        await run_task_if_disabled(chat_id, 'schedule_auto_send')

    await asyncio.sleep(2)
    await send_status(chat_id)


@router.callback_query(F.data == 'pin_schedule')
async def turn_pin_schedule_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    if await db.get_db_data(chat_id, 'pin_schedule_message'):
        await db.update_db_data(chat_id, pin_schedule_message=0)

        txt = 'Закрепление сообщений с расписанием выключено'
        await send_status(chat_id, text=txt, reply_markup=None)

    else:
        await db.update_db_data(chat_id, pin_schedule_message=1)

        txt = 'Закрепление сообщений с расписанием включено'
        await send_status(chat_id, text=txt, reply_markup=None)

    await asyncio.sleep(2)  # timer
    await send_status(chat_id)


@router.callback_query(F.data == 'disable_bot')
async def disable_bot_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    await disable_bot(callback_query)  # start disable bot func


@router.callback_query(F.data == 'description')
async def description_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    text = 'Вопросы и предложения по кнопке ниже:'
    await send_status(chat_id, text=text, reply_markup=kb.description())


""" set class number, letter, and change handlers
"""


@router.callback_query(F.data == 'choose_class')
async def choose_class_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    msg = 'Выберите цифру класса'
    await send_status(chat_id, msg, reply_markup=kb.choose_class_num())


@router.callback_query(F.data.startswith('class_number_'))
async def class_number_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    prefix = 'class_number_'
    callback = await clear_callback(callback_query, prefix)

    school_class = callback
    msg = 'Выберите цифру класса'
    await send_status(chat_id=chat_id,
                      text=msg,
                      reply_markup=kb.choose_class_letter(school_class))


@router.callback_query(F.data.startswith('set_class_'))
async def set_class_call(callback_query: types.CallbackQuery) -> None:
    if await user_not_admin(callback_query):
        return
    chat_id = callback_query.message.chat.id
    prefix = 'set_class_'  # set callback prefix
    school_class = await clear_callback(callback_query, prefix)
    await del_msg_by_db_name(chat_id, 'last_schedule_message_id')
    await db.update_db_data(chat_id, school_class=school_class)

    if school_class[-1] in ['2', '4']:
        await db.update_db_data(chat_id, school_change=2)

    else:
        await db.update_db_data(chat_id, school_change=1)

    formatted_class = await format_school_class(school_class)
    text = f'Установлен {formatted_class} класс'
    await send_status(chat_id, text=text, reply_markup=None)

    await asyncio.sleep(3)  # timer
    await send_status(chat_id)
    await send_schedule(chat_id, now=1)


""" applied functions
"""


async def clear_callback(query: Union[types.CallbackQuery, types.Message],
                         prefix) -> str:
    """ clear callback from prefix
        example:
        clear_callback(prefix='school_class_number_callback_5')
            return 5
    """
    if isinstance(query, types.Message):
        custom_logger.debug(query.chat.id)
        return query.text[len(prefix):]

    custom_logger.debug(query.message.chat.id)
    return query.data[len(prefix):]


async def callback_completion(callback_query: types.callback_query) -> None:
    await bot.answer_callback_query(callback_query.id)  # callback_completion


async def user_not_admin(query: Union[types.CallbackQuery, types.Message]) -> bool:
    if isinstance(query, types.Message):
        chat_id = query.chat.id
    else:
        chat_id = query.message.chat.id
    # start message for callback functions
    custom_logger.debug(chat_id, depth=1)

    username = query.from_user.username
    user_id = query.from_user.id
    custom_logger.debug(chat_id, f'<y>username: <r>{username} </>starting</>')

    if user_id in await get_admins_id_list(chat_id):
        custom_logger.debug(chat_id, '<y>is admin: <r>True</></>')
        return False

    else:
        custom_logger.debug(chat_id, '<y>is admin: <r>False</></>')
        txt = f'Привет, {username}, \nнастройки доступны только администраторам'
        msg = await bot.send_message(chat_id, text=txt, reply_markup=None)

        await asyncio.sleep(2)  # timer
        await del_msg_by_id(chat_id, msg.message_id)

        if isinstance(query, types.Message):
            await del_msg_by_id(chat_id, query.message_id)
        else:
            await callback_completion(query)

        return True
