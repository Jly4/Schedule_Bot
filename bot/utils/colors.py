import asyncio
from typing import Union

from aiogram.types import Message, CallbackQuery

from main import bot
from bot.database.database import db
from bot.utils.schedule import send_schedule
from bot.keyboards import keyboards as kb
from bot.logs.log_config import custom_logger
from bot.utils.messages import del_msg_by_db_name, del_msg_by_id
from bot.filters.filters import check_pattern


async def color_menu(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    status_id = await db.get_status_msg_id(chat_id)
    text = (
        'Меню настройки цвета\n\n'
        'В данном меню вы можете сменить цвет фона или текста расписания. '
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_id,
        reply_markup=kb.color_menu(),
        disable_web_page_preview=True,
        parse_mode='MarkDown'
    )

""" text color
"""


async def text_color_menu(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    status_id = await db.get_status_msg_id(chat_id)
    text = (
        'Для того чтобы изменить основной цвет текста расписания вы '
        'можете воспользоваться одним из предложенных ниже цветов, '
        'либо отправьте боту сообщение с кодом цвета в '
        'формате RGB по примеру ниже, заменив цифры на свои.\n\n'
        'Пример: (нажмите на пример чтобы скопировать)\n'
        '`256, 256, 256` - Установить белый цвет\n\n'
        'Выбрать цвет в формате RGB можно '
        '[тут](https://www.google.com/search?q=rgb+color+picker).\n\n'
        'Также можно сменить цвет для конкретных предметов, нажав на кнопку '
        '"Цвет предметов"\n'
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_id,
        reply_markup=kb.text_color_menu(),
        disable_web_page_preview=True,
        parse_mode='markdown'
    )

""" lessons color
"""


async def lessons_color(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    status_id = await db.get_status_msg_id(chat_id)

    text = (
        'Для того чтобы изменить цвет для конкретных предметов, вам сначала '
        'нужно создать группу-цвет, нажав на кнопку "редакт. группы".\n'
        'После того как у вас есть хотя-бы одна группа, '
        'вы можете можете добавить в нее предметы, '
        'которые будут окрашиваться в цвет этой группы.\n\n'
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_id,
        reply_markup=kb.lessons_color(),
        disable_web_page_preview=True,
        parse_mode='HTML'
    )


async def lessons_color_group(query: Union[CallbackQuery, Message]) -> None:
    if isinstance(query, CallbackQuery):
        chat_id = query.message.chat.id
    else:
        chat_id = query.chat.id
    status_id = await db.get_status_msg_id(chat_id)

    data = await db.get_db_data(chat_id, 'lessons_by_color')
    groups = '\n'.join(eval(data).keys()) if data else ''

    text = (
        'Для того чтобы добавить группу, отправьте боту сообщение с кодом '
        'цвета в формате RGB.\nЭто одновременно будет и название группы, '
        'и цветом в которую будут окрашиваться предметы находящиеся в ней.\n'
        'Чтобы удалить группу, отправьте цвет группы, но в начале поставьте '
        'знак "-".\n\nПримеры: (нажмите на пример чтобы скопировать)\n'
        '`256, 256, 256` - чтобы добавить группу с белым цветом. \n'
        '`-256, 256, 256` - чтобы удалить группу с белым цветом. \n\n'
        'Выбрать цвет в формате RGB можно '
        '[тут](https://www.google.com/search?q=rgb+color+picker).\n\n'
        f'Существующие группы(ы): \n{groups}'
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_id,
        reply_markup=kb.back(),
        disable_web_page_preview=True,
        parse_mode='markdown'
    )


async def edit_groups(query: Message) -> None:
    chat_id = query.chat.id
    group = query.text
    remove = query.text.startswith('-')
    group = group[1:] if remove else group

    await del_msg_by_id(chat_id, query.message_id)
    if not await check_pattern(chat_id, group, pattern='color'):
        return

    # get the old lessons list
    data = await db.get_db_data(chat_id, 'lessons_by_color')
    data = eval(data) if data else {}

    if remove:
        del data[group]
    else:
        data[group] = ''

    str_dict = f'{data}'
    await db.update_db_data(chat_id, lessons_by_color=str_dict)
    await lessons_color_group(query)

    msg = await bot.send_message(chat_id, 'Группы отредактированы')
    await asyncio.sleep(1.5)
    await bot.delete_message(chat_id, msg.message_id)


async def lessons_color_choose(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id

    data = await db.get_db_data(chat_id, 'lessons_by_color')
    groups = eval(data).keys() if data else {}

    text = (
        'Выберите группу для редактирования предметов.'
    )

    status_id = await db.get_status_msg_id(chat_id)
    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_id,
        reply_markup=kb.choose_color_group(groups),
        disable_web_page_preview=True,
        parse_mode='markdown'
    )


async def lessons_color_lesson(
        query: Union[CallbackQuery, Message],
        group: str = ''
) -> None:
    if isinstance(query, CallbackQuery):
        chat_id = query.message.chat.id
    else:
        chat_id = query.chat.id

    if not group:
        prefix = 'color_group_'
        group = query.data[len(prefix):]

    data = await db.get_db_data(chat_id, 'lessons_by_color')
    groups = eval(data) if data else {}
    lessons = groups[group]

    text = (
        'Для того чтобы добавить предмет в группу, отправьте боту сообщение с '
        'названием предмета, или предметов через запятую.\n'
        'Чтобы удалить предметы из группы отправьте такое же сообщение, '
        'но перед предметом/предметами поставьте знак "-".\n\n'
        'Примеры: (нажмите на пример чтобы скопировать)\n'
        '`русский` - чтобы добавить в группу.\n'
        '`математика, английский` - чтобы добавить в группу.\n'
        '`-математика, русский` - чтобы удалить из группы\n\n'
    
        f'*Выбранная группа: {group}*\n'
        f'Предметы в группе: {lessons}'
    )

    status_id = await db.get_status_msg_id(chat_id)
    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_id,
        reply_markup=kb.back(),
        disable_web_page_preview=True,
        parse_mode='markdown'
    )


async def edit_lessons(query: Message, group) -> None:
    """ not exist in the other group """
    chat_id = query.chat.id
    new_data = query.text.lower()
    remove = query.text.startswith('-')
    new_data = new_data[1:] if remove else new_data

    await del_msg_by_id(chat_id, query.message_id)
    if not await check_pattern(chat_id, new_data, pattern='lesson'):
        return

    # get the new lessons list
    new_list = new_data.split(', ')
    new_lessons = new_list if isinstance(new_list, list) else [new_list]

    # get the old lessons list
    data = await db.get_db_data(chat_id, 'lessons_by_color')
    data = eval(data) if data else {}
    lessons = set(data[group].split(', '))
    print(set(new_lessons))
    print(lessons)
    print()
    if remove:
        lessons -= set(new_lessons)
    else:
        # check if the lesson does not already exist in the other group
        new_lessons = await check_if_in_groups(chat_id, new_lessons, data)
        lessons |= set(new_lessons)

    print(lessons)
    data[group] = ', '.join(lessons).strip(',').strip(' ')
    str_dict = f'{data}'
    await db.update_db_data(chat_id, lessons_by_color=str_dict)
    await lessons_color_lesson(query, group)

    msg = await bot.send_message(chat_id, 'Предметы отредактированы')
    await asyncio.sleep(1.5)
    await bot.delete_message(chat_id, msg.message_id)


async def check_if_in_groups(chat_id: int, new_lsns: list, lsns: dict) -> list:
    for value in lsns.values():
        for lsn in new_lsns:
            if lsn in value:
                txt = f'{lsn} уже находится в этой или другой группе.'
                msg = await bot.send_message(chat_id, txt)
                await asyncio.sleep(2)
                await bot.delete_message(chat_id, msg.message_id)

                new_lsns.remove(lsn)

    return new_lsns

""" bg color
"""


async def bg_color_menu(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    status_message_id = await db.get_status_msg_id(chat_id)
    text = (
        'Для смены цвета фона расписания вы можете воспользоваться '
        'одним из предложенных ниже цветов, либо отправить боту '
        'сообщение с кодом цвета в формате RGB по примеру ниже, заменив '
        'цифры на свои.\n\n'
        'Примеры:(нажмите на пример чтобы скопировать)\n'
        '`256, 256, 256`\n\n'
        'Выбрать цвет в формате RGB можно '
        '[тут](https://www.google.com/search?q=rgb+color+picker).\n'
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        text=text,
        message_id=status_message_id,
        reply_markup=kb.choose_bg_color(),
        disable_web_page_preview=True,
        parse_mode='MarkDown'
    )


async def set_color(query: Union[CallbackQuery, Message], target=None) -> bool:
    if isinstance(query, Message):
        """ receive color code from a message """
        chat_id = query.chat.id
        custom_logger.debug(chat_id, 'set color msg')
        color = query.text
        await bot.delete_message(chat_id, query.message_id)

        if not await check_pattern(chat_id, color, pattern='color'):
            return False

        await update_color(chat_id, target, color)
        return True

    if isinstance(query, CallbackQuery):
        """ receive color code from keyboard button """
        chat_id = query.message.chat.id
        custom_logger.debug(chat_id, 'set_color_callback')

        color = query.data[10:21]
        await update_color(chat_id, target, color)

        return True


async def update_color(chat_id: int, target: str, color: str) -> None:
    if target == 'text':
        await db.update_db_data(chat_id, main_text_color=color)
    else:
        await db.update_db_data(chat_id, schedule_bg_color=color)

    txt = 'Цвет успешно сменен'
    msg = await bot.send_message(chat_id, text=txt)

    await del_msg_by_db_name(chat_id, 'last_schedule_message_id')
    await asyncio.sleep(2)
    await del_msg_by_id(chat_id, msg.message_id)

    await send_schedule(chat_id, now=1)


async def get_color_for_lesson(chat_id: int, text: str) -> Union[str, tuple]:
    data = await db.get_db_data(chat_id, 'lessons_by_color')
    data = eval(data) if data else {}
    color_str = ''

    for value in data.values():
        if text in value:
            color_str = list(data.keys())[list(data.values()).index(value)]

    if not color_str:
        print(text, color_str)
        color_str = await db.get_db_data(chat_id, 'main_text_color')

    color = tuple(int(i) for i in color_str.split(','))
    return color
