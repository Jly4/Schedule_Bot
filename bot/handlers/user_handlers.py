import re
import asyncio

from loguru import logger
from typing import Union
from aiogram import Router, F, types
from aiogram.filters import CommandStart

from main import bot
from bot.config.config_loader import dev_id
from bot.keyboards import keyboards as kb
from bot.database.db import bot_database as db
from bot.utils.status import send_status, status_auto_update
from bot.utils.schedule import send_schedule, schedule_auto_send
from bot.utils.utils import settings, del_msg_by_id, status_message_text
from bot.utils.utils import disable_bot, existing_school_class, format_school_class, start_command, get_admins_id_list
from bot.utils.utils import task_not_running, bot_enabled


router = Router()

""" bot commands handlers
"""

@router.callback_query(F.data == '')
async def any_callback(callback_query: types.CallbackQuery):
    logger.critical(callback_query.data)


@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    chat_id: int = message.chat.id  # save chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{message.chat.id}".rjust(15)} | </>get /start</>')

    await start_command(chat_id)  # start_command func
    await send_status(chat_id, edit=0)  # update status

    if await task_not_running(chat_id, f'{chat_id} status_auto_update'):  #
        asyncio.create_task(status_auto_update(chat_id), name=f'{chat_id} status_auto_update')

    await asyncio.sleep(1)
    await del_msg_by_id(chat_id, message.message_id, 'start command')  # delete start command


@router.message(F.text.lower() == '/status')
async def status_command(message: types.Message) -> None:
    logger.critical('aboba')
    chat_id: int = message.chat.id  # save chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{message.chat.id}".rjust(15)} | </>get /status</>')

    if await bot_enabled(chat_id):
        await del_msg_by_id(chat_id, message.message_id,
                            'status command')  # Удаляем команду, отправленную пользователем

        await send_status(chat_id, edit=0)  # update status


@router.message(F.text.lower() == '/disable')
async def disable_bot_command(message: types.Message) -> None:
    chat_id: int = message.chat.id  # save chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{message.chat.id}".rjust(15)} | </>get /disable</>')

    if await bot_enabled(chat_id) and await user_admin(message):
        await del_msg_by_id(chat_id, message.message_id,
                            'disable command')  # Удаляем команду, отправленную пользователем
        await disable_bot(message)  # start disable bot func


@router.message(F.text.lower() == '/dev')
async def dev_command(message: types.Message) -> None:
    chat_id = message.chat.id  # save chat_id
    user_id: int = message.from_user.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>get /dev command</>')

    await del_msg_by_id(chat_id, message.message_id, 'disable command')  # delete received command

    if user_id == dev_id:

        await send_status(chat_id, edit=0)

        status_message_id = await db.get_status_msg_id(chat_id)

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text='Hello, Dev!', message_id=status_message_id,
                                    reply_markup=kb.dev())

    else:
        text = ("hehe, I don't know how you found this command, but anyway "
                "only dev have access :)")

        dev_msg = await bot.send_message(chat_id, text)

        await asyncio.sleep(4)

        await del_msg_by_id(chat_id, dev_msg.message_id, 'dev command')  # delete received command


""" colour handlers
"""


@router.callback_query(F.data == 'status')
async def status_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>starting</>')

    await send_status(chat_id)


""" colour handlers
"""


@router.callback_query(F.data == 'color_menu')
async def color_set_menu_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>starting</>')
    if await user_admin(callback_query):
        # получаем id основного сообщения
        status_message_id = await db.get_status_msg_id(chat_id)

        text = 'Меню смены цвета фона расписания\n\n' \
               'Для смена цвета фона, отправьте сообщение по примеру снизу\n\n' \
               '`Set color 256, 256, 256`\n(Нажмите чтобы скопировать)\n' \
               'Замените цифры в на свои\n\n' \
               'Выбрать цвет в формате RGB можно ' \
               '[тут](https://www.google.com/search?q=rgb+color+picker).\n'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text,
                                    message_id=status_message_id,
                                    reply_markup=kb.choose_color(),
                                    disable_web_page_preview=True,
                                    parse_mode='MarkDown'
                                    )


@router.message(F.text.lower().startswith('set color '))
async def set_color_command(message: types.Message) -> None:
    chat_id = message.chat.id  # get chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | '
                                  f'</>starting</>')
    if await user_admin(message):
        def check_mask(string):
            pattern = re.compile(r'^\d{1,3},\s*\d{1,3},\s*\d{1,3}$')
            return bool(pattern.match(string))

        prefix = 'set color '  # set prefix
        color: str = await clear_callback(message, prefix)  # clear callback from prefix

        if check_mask(color):
            await send_status(chat_id)
            await db.update_db_data(chat_id, schedule_bg_color=color)  # set default color
            set_color_message = await bot.send_message(chat_id, 'Цвет успешно сменен')
            await send_schedule(chat_id, now=1)
        else:
            set_color_message = await bot.send_message(chat_id, 'Не правильный формат')

        await asyncio.sleep(2)
        await bot.delete_message(chat_id, message.message_id)  # delete color message
        await bot.delete_message(chat_id, set_color_message.message_id)  # delete color message


@router.callback_query(F.data == 'default_colour')
async def default_color_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>starting</>')

    if await user_admin(callback_query):
        # set default color
        await db.update_db_data(chat_id, schedule_bg_color="255,255,143")

        # получаем id основного сообщения
        status_message_id = await db.get_status_msg_id(chat_id)

        # переменная с отправленным сообщением
        text = 'Установлен цвет по умолчанию'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id)

        await asyncio.sleep(2)

        await send_status(chat_id)

        await send_schedule(chat_id, now=1)


""" settings handlers
"""


@router.callback_query(F.data == 'settings')
async def settings_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')
    if await user_admin(callback_query):
        await settings(chat_id)

""" schedule handlers
"""


@router.callback_query(F.data == 'update_schedule')
async def update_schedule_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')
    await callback_completion(callback_query)  # complete callback
    await send_schedule(chat_id, now=1)
    # update status
    await asyncio.sleep(1)
    await send_status(chat_id)


@router.callback_query(F.data == 'schedule_auto_send')
async def turn_schedule_auto_send_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id

    if await user_admin(callback_query):
        if await db.get_db_data(chat_id, 'schedule_auto_send'):

            await db.update_db_data(chat_id, schedule_auto_send=0)  # turn off schedule auto check

            # message for user
            schedule_auto_send_status_message = await bot.send_message(chat_id,
                                                                  'Автоматическое получение расписания '
                                                                  'при изменении, выключено'
                                                                  )
        else:
            await db.update_db_data(chat_id, schedule_auto_send=1)  # turn on schedule auto check

            # message for user
            schedule_auto_send_status_message = await bot.send_message(chat_id,
                                                                  'Автоматическое получение расписания '
                                                                  'при изменении, включено'
                                                                  )
        await send_status(chat_id)

        await asyncio.sleep(2)  # timer

        # удаление сообщения о переключении
        await del_msg_by_id(chat_id, schedule_auto_send_status_message.message_id, 'schedule_auto_send_status_message')

        # запуск
        if await db.get_db_data(chat_id, 'schedule_auto_send'):
            if await task_not_running(chat_id, f'{chat_id} schedule_auto_send'):
                asyncio.create_task(schedule_auto_send(chat_id), name=f'{chat_id} schedule_auto_send')


@router.callback_query(F.data == 'pin_schedule')
async def turn_pin_schedule_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    if await user_admin(callback_query):
        if await db.get_db_data(chat_id, 'pin_schedule_message'):

            await db.update_db_data(chat_id, pin_schedule_message=0)  # выключаем автообновление

            # сообщение пользователю
            pin_schedule_message = await bot.send_message(chat_id,
                                                          'Закрепление сообщений с расписанием '
                                                          'выключено'
                                                          )
        else:
            await db.update_db_data(chat_id, pin_schedule_message=1)  # включаем автообновление

            # сообщение пользователю
            pin_schedule_message = await bot.send_message(chat_id,
                                                          'Закрепление сообщений с расписанием '
                                                          'включено'
                                                          )
        await asyncio.sleep(2)  # timer

        # удаление сообщения о переключении
        await del_msg_by_id(chat_id, pin_schedule_message.message_id, 'pin_schedule_message')

        await callback_completion(callback_query)


@router.callback_query(F.data == 'disable_bot')
async def disable_bot_call(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        await disable_bot(callback_query)  # start disable bot func


@router.callback_query(F.data == 'description')
async def description_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    description_text = 'Вопросы и предложения по кнопке ниже:'
    send_status(chat_id, text=description_text, reply_markup=kb.description())


""" set class number, letter, and change handlers
"""
# variable to help set class
school_class: str = ''


@router.callback_query(F.data == 'choose_class')
async def choose_class_call(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        text = 'Выберите цифру класса'
        await send_status(chat_id=chat_id, text=text, 
                          reply_markup=kb.choose_class_number())

@router.callback_query(F.data.startswith('class_number_'))
async def class_number_call(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        global school_class
        chat_id = callback_query.message.chat.id  
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        prefix = 'school_class_number_'  # set prefix
        callback = await clear_callback(callback_query, prefix)  # clear callback from prefix

        if int(callback) in range(1, 12):
            school_class = callback
            text = 'Выберите цифру класса'
            await send_status(chat_id=chat_id, text=text,
                              reply_markup=kb.choose_class_letter(school_class)
                              )
        else:
            # Возвращаемся
            await settings(chat_id)


@router.callback_query(F.data.startswith('class_letter_'))
async def class_letter_call(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        global school_class
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        prefix = 'school_class_letter_callback_'  # set prefix
        callback = await clear_callback(callback_query, prefix)  # clear callback from prefix

        if callback in ['a', 'b', 'v', 'g', 'd', 'e', 'j', 'z']:
            school_class = callback + school_class
            logger.opt(colors=True).debug(
                f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>class: <r>{school_class}</></>')

            if await existing_school_class(school_class):
                await db.update_db_data(chat_id, school_class=school_class)  # set new class

                text = f'Установлен {await format_school_class(school_class)} класс'
                await send_status(chat_id, text=text, reply_markup=None)

                await asyncio.sleep(2)  # timer
                await send_status(chat_id)
                await send_schedule(chat_id, now=1)

            else:
                await send_status(chat_id, text='Несуществующий класс',
                                  reply_markup=None)

                await asyncio.sleep(2)  # timer
                await settings(chat_id)  # back to settings

        else:
            # Возвращаемся
            await settings(chat_id)


@router.callback_query(F.data == 'choose_change')
async def choose_change_call(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    if await user_admin(callback_query):
        text = 'Выберите смену'
        await send_status(chat_id, text=text, reply_markup=kb.choose_change())


@router.callback_query(F.data.startswith('class_change_'))
async def class_change_call(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        prefix = 'school_change_callback_'  # set prefix
        callback = await clear_callback(callback_query, prefix)  # clear callback from prefix

        if callback == '1':
            await db.update_db_data(chat_id, school_change=1)
            await send_status(chat_id, text='Установлена первая смена', reply_markup=None)

        elif callback == '2':
            await db.update_db_data(chat_id, school_change=2)
            await send_status(chat_id, text='Установлена вторая смена', reply_markup=None)

        else:
            await choose_class_call(callback_query)

        await asyncio.sleep(2)
        await send_status(chat_id)



""" applied functions
"""


async def clear_callback(query: Union[types.CallbackQuery, types.Message], prefix) -> str:
    """ clear callback from prefix
        example:
        clear_callback(school_class_number_callback_1)
            return 1
    """
    if type(query) is types.Message:
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{query.chat.id}".rjust(15)} | </>started</>')
        return query.text[len(prefix):]

    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{query.message.chat.id}".rjust(15)} | </>started</>')
    return query.data[len(prefix):]


async def callback_completion(callback_query: types.callback_query) -> None:
    await bot.answer_callback_query(callback_query.id)  # callback_completion


async def user_admin(query: Union[types.CallbackQuery, types.Message]) -> bool:
    if type(query) is types.CallbackQuery:
        await callback_completion(query)

    if type(query) is types.Message:
        chat_id = query.chat.id
    else:
        chat_id = query.message.chat.id

    username = query.from_user.username
    user_id = query.from_user.id

    logger.opt(colors=True).debug(
        f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>username: <r>{username} </>starting</>')

    if user_id in await get_admins_id_list(chat_id):
        logger.opt(colors=True).debug(
            f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>username: <r>{username} </>is admin: <r>True</></>')

        return True

    else:
        logger.opt(colors=True).debug(
            f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>username: <r>{username} </>is admin: <r>False</></>')
        # сообщение пользователю
        not_admin_message = await bot.send_message(chat_id,
                                                   f'Привет, {username}, \nнастройки доступны только администраторам'
                                                   )
        await asyncio.sleep(2)  # timer

        await del_msg_by_id(chat_id, not_admin_message.message_id)  # удаление сообщения о переключении

        if type(query) is types.Message:
            await del_msg_by_id(chat_id, message_id=query.message_id)

        return False
