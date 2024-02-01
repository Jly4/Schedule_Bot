import re
import asyncio

from typing import Union
from aiogram import types, Dispatcher

from bot.init_bot import bot
from bot.configs.config import dev_id
from loguru import logger
from bot.keyboards import keyboards as kb
from bot.utils.status import auto_status, send_status
from bot.databases.database import bot_database as db
from bot.utils.schedule import auto_schedule, send_schedule
from bot.utils.utils import settings, delete_msg_by_id, delete_msg_by_column_name, status_message_text
from bot.utils.utils import disable_bot, existing_school_class, format_school_class, start_command, get_admins_id_list
from bot.utils.utils import task_not_running, bot_enabled

""" bot commands handlers
"""


async def start_handler(message: types.Message) -> None:
    logger.opt(colors=True).debug(f'<y>get /start , chat_id: <r>{message.chat.id}</></>')
    # save chat_id
    chat_id: int = message.chat.id

    await start_command(chat_id)  # start_command func

    await send_status(chat_id, edit=0)  # update status

    if await task_not_running(f'{chat_id} auto_status'):
        asyncio.create_task(auto_status(chat_id), name=f'{chat_id} auto_status')
    else:
        await send_status(chat_id)

    await asyncio.sleep(1)
    await delete_msg_by_id(chat_id, message.message_id, 'start command')  # delete start command


async def status_handler(message: types.Message) -> None:
    # save chat_id
    chat_id: int = message.chat.id

    if await bot_enabled(chat_id):
        logger.opt(colors=True).debug(f'<y>get /status , chat_id: <r>{message.chat.id}</></>')

        await delete_msg_by_id(chat_id, message.message_id,
                               'status command')  # Удаляем команду, отправленную пользователем

        await send_status(chat_id, edit=0)  # update status


async def disable_bot_command_handler(message: types.Message) -> None:
    # save chat_id
    chat_id: int = message.chat.id
    logger.opt(colors=True).debug(f'<y>get /disable , chat_id: <r>{message.chat.id}</></>')

    if await bot_enabled(chat_id):
        if await user_admin(message):
            await delete_msg_by_id(chat_id, message.message_id,
                                   'disable command')  # Удаляем команду, отправленную пользователем
            await disable_bot(message)  # start disable bot func


async def dev_command_handler(message: types.Message) -> None:
    # save chat_id
    chat_id = message.chat.id
    user_id: int = message.from_user.id
    logger.opt(colors=True).info(f'Get Dev! command, chat_id: {chat_id}')

    await delete_msg_by_id(chat_id, message.message_id, 'disable command')  # delete received command

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

        await delete_msg_by_id(chat_id, dev_msg.message_id, 'dev command')  # delete received command


""" colour handlers
"""


async def set_color_menu_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        # get chat_id
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>starting</>')

        # получаем id основного сообщения
        status_message_id = await db.get_status_msg_id(chat_id)

        text = f'Меню смены цвета фона расписания\n\n' \
               f'Для смена цвета фона, отправьте сообщение по примеру снизу\n\n' \
               f'`Set color 256, 256, 256`\n(Нажмите чтобы скопировать)\n' \
               f'Замените цифры в на свои\n\n' \
               f'Выбрать цвет в формате RGB можно [тут](https://www.google.com/search?q=rgb+color+picker).\n'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text,
                                    message_id=status_message_id,
                                    reply_markup=kb.choose_color(),
                                    disable_web_page_preview=True,
                                    parse_mode='MarkDown'
                                    )


async def set_color_handler(message: types.Message) -> None:
    chat_id = message.chat.id  # get chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>starting</>')
    if await user_admin(message):
        def check_mask(string):
            pattern = re.compile(r'^\d{1,3},\s*\d{1,3},\s*\d{1,3}$')

            return bool(pattern.match(string))

        prefix = 'set color '  # set prefix
        color: str = await clear_callback_from_prefix(message, prefix)  # clear callback from prefix

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
        # get chat_id
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>starting</>')

        await db.update_db_data(chat_id, schedule_bg_color="255,255,143")  # set default color

        # получаем id основного сообщения
        status_message_id = await db.get_status_msg_id(chat_id)

        # переменная с отправленным сообщением
        text = f'Установлен цвет по умолчанию'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id)

        await asyncio.sleep(2)

        await send_status(chat_id)

        await send_schedule(chat_id, now=1)


""" settings handlers
"""


async def settings_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  # get chat_id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </> started</>\n')

    await callback_completion(callback_query)

    if await user_admin(callback_query):
        await settings(chat_id)


async def close_settings_handler(callback_query: types.CallbackQuery) -> None:
    # get chat_id
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </> started</>\n')

    if await user_admin(callback_query):
        await send_status(chat_id)


""" schedule handlers
"""


async def send_schedule_handler(callback_query: types.CallbackQuery) -> None:
    # get chat_id
    chat_id = callback_query.message.chat.id

    await callback_completion(callback_query)  # complete callback

    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{callback_query.message.chat.id}".ljust(15)} | </> started</>\n')

    await send_schedule(chat_id, now=1)

    # update status
    await asyncio.sleep(1)
    await send_status(chat_id)


async def auto_schedule_handler(callback_query: types.CallbackQuery) -> None:
    # get chat_id
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
        await delete_msg_by_id(chat_id, auto_schedule_status_message.message_id, 'auto_schedule_status_message')

        # запуск
        if await db.get_db_data(chat_id, 'auto_schedule'):
            if await task_not_running(f'{chat_id} auto_schedule'):
                asyncio.create_task(auto_schedule(chat_id), name=f'{chat_id} auto_schedule')


async def pin_schedule_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  # get chat_id
    logger.opt(colors=True).debug(f'got pin_schedule_callback, chat_id: {callback_query.message.chat.id}')

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
        await delete_msg_by_id(chat_id, pin_schedule_message.message_id, 'pin_schedule_message')

        await callback_completion(callback_query)


""" disable bot handler
"""


async def disable_bot_callback_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        await disable_bot(callback_query)  # start disable bot func


""" description handlers
"""


async def description_open_handler(callback_query: types.CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id  # get chat_id
    logger.opt(colors=True).debug(f'description(chat_id: {chat_id}) starting')

    # получаем настройки пользователя
    status_message_id = await db.get_status_msg_id(chat_id)

    # переменная с отправленным сообщением
    description_text = f'Незамеченное летающее масло\n\nВопросы и предложения по кнопке ниже:'
    # редактируем сообщение
    await bot.edit_message_text(chat_id=chat_id, text=description_text, message_id=status_message_id,
                                reply_markup=kb.description())


async def description_close_handler(callback_query: types.CallbackQuery) -> None:
    # get chat_id
    chat_id = callback_query.message.chat.id
    logger.opt(colors=True).debug(f'description(chat_id: {chat_id}) starting')

    # получаем настройки пользователя
    status_message_id = await db.get_status_msg_id(chat_id)

    #
    status_text = await status_message_text(chat_id)

    # редактируем сообщение
    await bot.edit_message_text(chat_id=chat_id, text=status_text, message_id=status_message_id,
                                reply_markup=kb.settings())


""" set class number, letter, and change handlers
"""


async def choose_main_change_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        # get chat_id
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'choose_main_change_handler(chat_id: {chat_id}) starting')

        # получаем id основного сообщения
        status_message_id = await db.get_status_msg_id(chat_id)

        # переменная с отправленным сообщением
        text = f'Выберите смену'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id,
                                    reply_markup=kb.choose_school_change())


async def choose_class_change_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        # get chat_id
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'choose_class_change_handler(chat_id: {chat_id}) starting')

        prefix = 'school_change_callback_'  # set prefix

        callback = await clear_callback_from_prefix(callback_query, prefix)  # clear callback from prefix

        if callback == '1':
            await db.update_db_data(chat_id, school_change=1)  # выключаем автообновление

            change_message = await bot.send_message(chat_id, 'Установлена первая смена ')  # сообщение пользователю

            await asyncio.sleep(2)  # timer

            await delete_msg_by_id(chat_id, change_message.message_id, 'change_message')

        elif callback == '2':
            await db.update_db_data(chat_id, school_change=2)  # включаем автообновление

            change_message = await bot.send_message(chat_id, 'Установлена вторая смена ')  # сообщение пользователю

            await asyncio.sleep(2)  # timer

            await delete_msg_by_id(chat_id, change_message.message_id, 'change_message')
        else:
            await choose_main_class_handler(callback_query)

        # возвращаемся
        await settings(chat_id)


# variable to help set class
school_class: str = ''


async def choose_main_class_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        # get chat_id
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'choose_school_class_handler(chat_id: {chat_id}) starting')

        # get id status message
        status_message_id = await db.get_status_msg_id(chat_id)

        # переменная с отправленным сообщением
        text = f'Выберите цифру класса'

        # редактируем сообщение
        await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id,
                                    reply_markup=kb.choose_school_class_number())


async def choose_class_number_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        global school_class

        chat_id = callback_query.message.chat.id  # get chat_id
        logger.opt(colors=True).debug(f'choose_class_number_handler(chat_id: {chat_id}) starting')

        prefix = 'school_class_number_callback_'  # set prefix

        callback = await clear_callback_from_prefix(callback_query, prefix)  # clear callback from prefix

        if int(callback) in range(1, 12):
            school_class = callback

            # получаем id основного сообщения
            status_message_id = await db.get_status_msg_id(chat_id)

            # переменная с отправленным сообщением
            text = f'Выберите букву класса'

            # редактируем сообщение
            await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id,
                                        reply_markup=kb.choose_school_class_letter())
        else:
            # Возвращаемся
            await settings(chat_id)


async def choose_class_letter_handler(callback_query: types.CallbackQuery) -> None:
    if await user_admin(callback_query):
        global school_class
        # get chat_id
        chat_id = callback_query.message.chat.id
        logger.opt(colors=True).debug(f'choose_class_letter_handler(chat_id: {chat_id}) starting')

        prefix = 'school_class_letter_callback_'  # set prefix

        callback = await clear_callback_from_prefix(callback_query, prefix)  # clear callback from prefix

        if callback in ['a', 'b', 'v', 'g', 'd', 'e', 'j', 'z']:
            school_class = callback + school_class
            logger.opt(colors=True).debug(f'choose_class_letter_handler: school_class: {school_class}')

            if await existing_school_class(school_class):
                await db.update_db_data(chat_id, school_class=school_class)  # set new class

                text = f'Установлен {await format_school_class(school_class)} класс'

                status_message_id = await db.get_status_msg_id(chat_id)  # get id status msg

                await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id)

                await delete_msg_by_column_name(chat_id, 'last_schedule_message_id')  # delete schedule msg

                await asyncio.sleep(2)  # timer

                await send_status(chat_id)
                await send_schedule(chat_id, now=1)

            else:
                text = 'Несуществующий класс'

                status_message_id = await db.get_status_msg_id(chat_id)  # status msg id

                # редактируем сообщение
                await bot.edit_message_text(chat_id=chat_id, text=text, message_id=status_message_id)

                await asyncio.sleep(2)  # timer

                # Возвращаемся
                await settings(chat_id)

        else:
            # Возвращаемся
            await settings(chat_id)


""" applied functions
"""


async def clear_callback_from_prefix(query: Union[types.CallbackQuery, types.Message], prefix) -> str:
    if type(query) == types.Message:
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{query.message_id}".ljust(15)} | </> started</>\n')
        return query.text[len(prefix):]

    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{query.message.message_id}".ljust(15)} | </> started</>\n')
    return query.data[len(prefix):]


async def callback_completion(callback_query: types.callback_query) -> None:
    await bot.answer_callback_query(callback_query.id)  # callback_completion


async def user_admin(query: Union[types.CallbackQuery, types.Message]) -> bool:
    await callback_completion(query) if type(query) == types.callback_query else None  # complete collaback

    chat_id = query.chat.id if type(query) == types.Message else query.message.chat.id  # get chat_id
    username = query.from_user.username  # get message send user id
    user_id = query.from_user.id

    logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>username: <r>{username} </>starting</>')

    if user_id in await get_admins_id_list(chat_id):
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>username: <r>{username} </>is admin: <r>True</></>')

        return True

    else:
        logger.opt(colors=True).debug(f'<y>chat_id: <r>{f"{chat_id}".ljust(15)} | </>username: <r>{username} </>is admin: <r>False</></>')
        # сообщение пользователю
        not_admin_message = await bot.send_message(chat_id,
                                                   f'Привет, {username}, \nнастройки доступны только администраторам'
                                                   )
        await asyncio.sleep(2)  # timer

        await delete_msg_by_id(chat_id, not_admin_message.message_id)  # удаление сообщения о переключении

        if type(query) == types.Message:
            await delete_msg_by_id(chat_id, message_id=query.message_id)

        return False


""" callback and handlers register
"""


def register_user_handlers(dp: Dispatcher) -> None:
    """Register handlers
    """
    # message handlers
    dp.register_message_handler(start_handler, commands=['start'])
    dp.register_message_handler(status_handler, commands=['status'])
    dp.register_message_handler(disable_bot_command_handler, commands=['disable'])
    dp.register_message_handler(dev_command_handler, commands=['dev'])

    # callbacks handlers
    dp.register_callback_query_handler(send_schedule_handler, text='send_schedule_callback')
    dp.register_callback_query_handler(settings_handler, text='settings_callback')

    dp.register_callback_query_handler(auto_schedule_handler, text='auto_schedule_callback')
    dp.register_callback_query_handler(pin_schedule_handler, text='pin_schedule_callback')
    dp.register_callback_query_handler(disable_bot_callback_handler, text='disable_bot_callback')
    dp.register_callback_query_handler(description_open_handler, text='description_callback')
    dp.register_callback_query_handler(description_close_handler, text='description_close_callback')
    dp.register_callback_query_handler(close_settings_handler, text='close_settings_callback')

    # color callbacks
    dp.register_callback_query_handler(set_color_menu_handler, text='set_colour_menu_callback')
    dp.register_callback_query_handler(default_color_handler, text='default_colour_callback')
    dp.register_message_handler(set_color_handler, lambda message: message.text.lower().startswith('set color '))

    # choose class callbacks
    dp.register_callback_query_handler(choose_main_class_handler, text='choose_main_class_callback')
    dp.register_callback_query_handler(choose_main_change_handler, text='choose_main_change_callback')

    dp.register_callback_query_handler(choose_class_change_handler,
                                       lambda c: c.data.startswith('school_change_callback_'))
    dp.register_callback_query_handler(choose_class_number_handler,
                                       lambda c: c.data.startswith('school_class_number_callback_'))
    dp.register_callback_query_handler(choose_class_letter_handler,
                                       lambda c: c.data.startswith('school_class_letter_callback_'))
