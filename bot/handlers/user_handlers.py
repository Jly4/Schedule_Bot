import re
import asyncio

from loguru import logger
from typing import Union
from aiogram import types, Dispatcher

from bot.init_bot import bot
from bot.configs.config import dev_id
from bot.keyboards import keyboards as kb
from bot.utils.status import auto_status, send_status
from bot.databases.database import bot_database as db
from bot.utils.schedule import auto_schedule, send_schedule
from bot.utils.utils import settings, del_msg_by_id, del_msg_by_db_name, status_message_text
from bot.utils.utils import disable_bot, existing_school_class, format_school_class, start_command, get_admins_id_list
from bot.utils.utils import task_not_running, bot_enabled

""" bot commands handlers
"""


async def start_handler(message: types.Message) -> None:
    chat_id: int = message.chat.id  # save chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{message.chat.id}".rjust(15)} | </>get /start</>')

    await start_command(chat_id)  # start_command func
    await send_status(chat_id, edit=0)  # update status

    if await task_not_running(chat_id, f'{chat_id} auto_status'):  # create update status task
        asyncio.create_task(auto_status(chat_id), name=f'{chat_id} '
                                                        f'auto_status')

    await asyncio.sleep(1)
    await del_msg_by_id(chat_id, message.message_id, 'start command')  # delete start command


async def status_handler(message: types.Message) -> None:
    chat_id: int = message.chat.id  # save chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{message.chat.id}".rjust(15)} | </>get /status</>')

    if await bot_enabled(chat_id):
        await del_msg_by_id(chat_id, message.message_id,
                            'status command')  # Удаляем команду, отправленную пользователем

        await send_status(chat_id, edit=0)  # update status


async def disable_bot_command(message: types.Message) -> None:
    chat_id: int = message.chat.id  # save chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{message.chat.id}".rjust(15)} | </>get /disable</>')

    if await bot_enabled(chat_id) and await user_admin(message):
        await del_msg_by_id(chat_id, message.message_id,
                            'disable command')  # Удаляем команду, отправленную пользователем
        await disable_bot(message)  # start disable bot func


async def dev_command_handler(message: types.Message) -> None:
    chat_id = message.chat.id
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
        text = "hehe, I don't know how you found this command, but anyway only dev have access :)"

        dev_msg = await bot.send_message(chat_id, text)

        await asyncio.sleep(4)

        await del_msg_by_id(chat_id, dev_msg.message_id, 'dev command')  # delete received command


""" colour handlers
"""


async def set_color_menu_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>starting</>')
    if await user_admin(callback_query):
        # получаем id основного сообщения
        status_message_id = await db.get_status_msg_id(chat_id)

        text = 'Меню смены цвета фона расписания\n\n' \
               'Для смена цвета фона, отправьте сообщение по примеру снизу\n\n' \
               '`Set color 256, 256, 256`\n(Нажмите чтобы скопировать)\n' \
               'Замените цифры в на свои\n\n' \
               'Выбрать цвет в формате RGB можно [тут](https://www.google.com/search?q=rgb+color+picker).\n'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text,
                                    message_id=status_message_id,
                                    reply_markup=kb.choose_color(),
                                    disable_web_page_preview=True,
                                    parse_mode='MarkDown'
                                    )


async def set_color_handler(message: types.Message) -> None:
    chat_id = message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>starting</>')
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


async def default_color_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>starting</>')

        await db.update_db_data(chat_id, schedule_bg_color="255,255,143")  # set default color

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


async def settings_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    await callback_completion(callback_query)

    if await user_admin(callback_query):
        await settings(chat_id)


async def close_settings(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    if await user_admin(callback_query):
        await send_status(chat_id)


""" schedule handlers
"""


async def update_schedule(callback_query: types.CallbackQuery) -> None:
    await callback_completion(callback_query)  # complete callback
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    await send_schedule(chat_id, now=1)

    # update status
    await asyncio.sleep(1)
    await send_status(chat_id)


async def auto_schedule_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id

    if await user_admin(callback_query):
        if await db.get_db_data(chat_id, 'auto_schedule'):

            await db.update_db_data(chat_id, auto_schedule=0)  # turn off schedule auto check

            # message for user
            auto_schedule_status_message = await bot.send_message(chat_id,
                                                                  'Автоматическое получение расписания '
                                                                  'при изменении, выключено'
                                                                  )
        else:
            await db.update_db_data(chat_id, auto_schedule=1)  # turn on schedule auto check

            # message for user
            auto_schedule_status_message = await bot.send_message(chat_id,
                                                                  'Автоматическое получение расписания '
                                                                  'при изменении, включено'
                                                                  )
        await send_status(chat_id)

        await asyncio.sleep(2)  # timer

        # удаление сообщения о переключении
        await del_msg_by_id(chat_id, auto_schedule_status_message.message_id, 'auto_schedule_status_message')

        # запуск
        if await db.get_db_data(chat_id, 'auto_schedule'):
            if await task_not_running(chat_id, f'{chat_id} auto_schedule'):
                asyncio.create_task(auto_schedule(chat_id), name=f'{chat_id} auto_schedule')


async def pin_schedule_handler(callback_query: types.CallbackQuery) -> None:
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


""" disable bot handler
"""


async def disable_bot_callback(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        await disable_bot(callback_query)  # start disable bot func


""" description handlers
"""


async def disadescription_open(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    # получаем настройки пользователя
    status_message_id = await db.get_status_msg_id(chat_id)

    # переменная с отправленным сообщением
    description_text = 'Незамеченное летающее масло\n\nВопросы и предложения по кнопке ниже:'
    # редактируем сообщение
    await bot.edit_message_text(chat_id=chat_id, text=description_text, message_id=status_message_id,
                                reply_markup=kb.description())


async def disadescription_close(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    # получаем настройки пользователя
    status_message_id = await db.get_status_msg_id(chat_id)

    #
    status_text = await status_message_text(chat_id)

    # редактируем сообщение
    await bot.edit_message_text(chat_id=chat_id, text=status_text, message_id=status_message_id,
                                reply_markup=kb.settings())


""" set class number, letter, and change handlers
"""


async def change_main_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

    if await user_admin(callback_query):
        text = 'Выберите смену'
        await send_status(chat_id, text=text, keyboard=kb.choose_school_change())


async def class_change_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        prefix = 'school_change_callback_'  # set prefix
        callback = await clear_callback(callback_query, prefix)  # clear callback from prefix

        if callback == '1':
            await db.update_db_data(chat_id, school_change=1)
            await send_status(chat_id, text='Установлена первая смена', keyboard=None)

        elif callback == '2':
            await db.update_db_data(chat_id, school_change=2)
            await send_status(chat_id, text='Установлена вторая смена', keyboard=None)

        else:
            await class_main_handler(callback_query)


        # возвращаемся
        await asyncio.sleep(2)
        await send_status(chat_id)


# variable to help set class
school_class: str = ''


async def class_main_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        text = 'Выберите цифру класса'
        await send_status(chat_id=chat_id, text=text, keyboard=kb.choose_school_class_number())


async def class_number_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        global school_class
        chat_id = callback_query.message.chat.id  
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>started</>')

        prefix = 'school_class_number_callback_'  # set prefix
        callback = await clear_callback(callback_query, prefix)  # clear callback from prefix

        if int(callback) in range(1, 12):
            school_class = callback
            text = 'Выберите цифру класса'
            await send_status(chat_id=chat_id, text=text, keyboard=kb.choose_school_class_letter())
        else:
            # Возвращаемся
            await settings(chat_id)


async def class_letter_handler(callback_query: types.CallbackQuery) -> None:
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
                await send_status(chat_id, text=text, keyboard=None)

                await asyncio.sleep(2)  # timer
                await send_status(chat_id)
                await send_schedule(chat_id, now=1)

            else:
                await send_status(chat_id, text='Несуществующий класс', keyboard=None)

                await asyncio.sleep(2)  # timer
                await settings(chat_id)  # back to settings

        else:
            # Возвращаемся
            await settings(chat_id)


""" applied functions
"""


async def clear_callback(query: Union[types.CallbackQuery, types.Message], prefix) -> str:
    """ clear callback from prefix
        example:
        clear_callback(school_class_number_callback_1)
            return 1
    """
    if type(query) == types.Message:
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{query.chat.id}".rjust(15)} | </>started</>')
        return query.text[len(prefix):]

    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{query.message.chat.id}".rjust(15)} | </>started</>')
    return query.data[len(prefix):]


async def callback_completion(callback_query: types.callback_query) -> None:
    await bot.answer_callback_query(callback_query.id)  # callback_completion


async def user_admin(query: Union[types.CallbackQuery, types.Message]) -> bool:
    await callback_completion(query) if type(query) == types.callback_query else None  # complete collaback
    chat_id = query.chat.id if type(query) == types.Message else query.message.chat.id  
    username = query.from_user.username  # get message send user id
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

        if type(query) == types.Message:
            await del_msg_by_id(chat_id, message_id=query.message_id)

        return False


""" callback and handlers register
"""


def register_user_handlers(dp: Dispatcher) -> None:
    """Register handlers
    """
    # message handlers
    dp.register_message_handler(start_handler, commands=['start'])
    dp.register_message_handler(status_handler, commands=['status'])
    dp.register_message_handler(disable_bot_command, commands=['disable'])
    dp.register_message_handler(dev_command_handler, commands=['dev'])

    # callbacks handlers
    dp.register_callback_query_handler(update_schedule, text='send_schedule_callback')
    dp.register_callback_query_handler(settings_handler, text='settings_callback')

    dp.register_callback_query_handler(auto_schedule_handler, text='auto_schedule_callback')
    dp.register_callback_query_handler(pin_schedule_handler, text='pin_schedule_callback')
    dp.register_callback_query_handler(disable_bot_callback, text='disable_bot_callback')
    dp.register_callback_query_handler(disadescription_open, text='description_callback')
    dp.register_callback_query_handler(disadescription_close, text='description_close_callback')
    dp.register_callback_query_handler(close_settings, text='close_settings_callback')

    # color callbacks
    dp.register_callback_query_handler(set_color_menu_handler, text='set_colour_menu_callback')
    dp.register_callback_query_handler(default_color_handler, text='default_colour_callback')
    dp.register_message_handler(set_color_handler, lambda message: message.text.lower().startswith('set color '))

    # choose class callbacks
    dp.register_callback_query_handler(class_main_handler, text='choose_main_class_callback')
    dp.register_callback_query_handler(change_main_handler, text='choose_main_change_callback')

    dp.register_callback_query_handler(class_change_handler,
                                       lambda c: c.data.startswith('school_change_callback_'))
    dp.register_callback_query_handler(class_number_handler,
                                       lambda c: c.data.startswith('school_class_number_callback_'))
    dp.register_callback_query_handler(class_letter_handler,
                                       lambda c: c.data.startswith('school_class_letter_callback_'))
