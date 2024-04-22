import re
import pytz
import asyncio
import warnings
import platform
import pandas as pd

from typing import Optional
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import FSInputFile, CallbackQuery, Message
from aiogram.exceptions import TelegramRetryAfter

from main import bot
from bot.utils.status import send_status
from bot.database.database import db
from bot.logs.log_config import custom_logger
from bot.exceptions.exceptions import retry_after, not_enough_rights_to_pin
from bot.config.config import schedule_auto_send_delay
from bot.config.config import classes_dict
from bot.utils.messages import del_msg_by_id
from bot.utils.utils import old_data_cleaner
from bot.utils.utils import add_change_to_class
from bot.utils.schedule_logic import ScheduleLogic
from bot.keyboards import keyboards as kb
from bot.filters.filters import AutoSendFilter


# Подавление предупреждений BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

local_timezone = pytz.timezone('Asia/Tomsk')
system_type = platform.system()


async def schedule_auto_send(chat_id: int, cls: str) -> None:
    """
    if autosend filter == 0 > stops cycle
    if autosend filter == 1 > wait while bot will unsuspend
    if autosend filter == 2 > normal working
    """
    custom_logger.debug(chat_id)
    autosend = AutoSendFilter(chat_id)
    autosend_filter = await autosend.filter()

    while autosend_filter:
        if autosend_filter == 2:
            await old_data_cleaner()  # clean bot/data folder from old files
            await send_schedule(chat_id, cls=cls)

        await asyncio.sleep(schedule_auto_send_delay * 60)
        autosend_filter = await autosend.filter()


async def send_schedule(
        chat_id: int,
        now: int = 0,
        day: int = None,
        cls: str = ''
) -> None:
    custom_logger.debug(chat_id, f'<y>now: <r>{now}</>, cls: <r>{cls}</></>')
    local_date = datetime.now(local_timezone)
    schedule_day = await ScheduleLogic.schedule_day()

    # if argument day is not empty
    if isinstance(day, int):
        schedule_day = day

    if not cls:
        cls = str(await db.get_db_data(chat_id, 'school_class'))

    # get schedule
    schedule = await update_schedule(chat_id, schedule_day, cls)
    if not schedule:
        return

    # logic
    logic = ScheduleLogic(chat_id, cls)
    should_send = await logic.should_send()
    custom_logger.debug(chat_id, f'<y>schedule_day: <r>{schedule_day}</></>')
    custom_logger.debug(chat_id, f'<y>should_send: <r>{should_send}</></>')

    if should_send or now:
        last_print_time = local_date.strftime('%d.%m.%Y. %H:%M:%S')
        # get time change schedule on site
        change_time = await db.get_data_by_cls(
            chat_id,
            cls,
            'schedule_change_time'
        )
        last_printed_change_time = change_time

        formatted_schedule = await format_schedule(schedule, schedule_day)
        prev_schedule_json = formatted_schedule.to_json()
        image_path = await schedule_file_name(chat_id, schedule_day)

        await generate_image(chat_id, formatted_schedule, image_path, cls)
        await del_old_schedule(chat_id, cls)

        txt = await schedule_txt(schedule_day, last_printed_change_time, cls)
        schedule_img = FSInputFile(image_path)
        schedule_msg = await send_schedule_image(chat_id, txt, schedule_img)

        if schedule_msg is None:
            return

        await db.update_data_by_cls(
            chat_id,
            cls,
            last_schedule_message_id=schedule_msg.message_id,
            last_printed_change_time=last_printed_change_time
        )

    if should_send:
        # noinspection PyUnboundLocalVariable
        await db.update_data_by_cls(
            chat_id,
            cls,
            last_print_time_day=schedule_day,
            last_print_time_hour=local_date.hour,
            last_print_time=last_print_time,
            prev_schedule_json=prev_schedule_json
        )

    await asyncio.sleep(0.5)
    await send_status(chat_id)


async def send_schedule_image(chat_id, txt, schedule_img) -> Optional[Message]:
    try:
        schedule_msg = await bot.send_photo(
            chat_id,
            caption=txt,
            photo=schedule_img
        )
        await pin_schedule(chat_id, schedule_msg.message_id)

        return schedule_msg

    except TelegramRetryAfter:
        await retry_after(chat_id)
        await send_schedule_image(chat_id, txt, schedule_img)

    except Exception as e:
        msg = f'<y>Schedule image to bot sending error: <r>{e}</></>'
        custom_logger.critical(chat_id, msg)

        await bot.send_message(chat_id, 'Ошибка отправки расписания')
        await asyncio.sleep(10)
        return


async def schedule_txt(schedule_day, last_printed_change_time, cls) -> str:
    formatted_class = classes_dict[cls[:-1]]
    day = {0: 'Понедельник',
           1: 'Вторник',
           2: 'Среда',
           3: 'Четверг',
           4: 'Пятница',
           5: 'Суббота'
           }[schedule_day]

    msg = (
        f'{formatted_class} {day} - последние изменение: '
        f'[{last_printed_change_time}]\n\n'
    )

    return msg


async def generate_image(chat_id, formatted_schedule, img, cls) -> None:
    """ this func generates an image with schedule
    1. if it doesn't exist in data folder
    2. if schedule change_time has been changed on site
    """
    logic = ScheduleLogic(chat_id, cls)
    if not await logic.should_regen_img(img):
        return

    # Задаем ширину строки
    column_widths = [
        max(formatted_schedule[col].astype(str).apply(len).max() + 1,
            len(str(col))) for col in formatted_schedule.columns]

    # get user color settings
    color_str = await db.get_db_data(chat_id, 'schedule_bg_color')
    color = tuple(int(i) for i in color_str.split(','))

    # Создаем изображение
    width = sum(
        column_widths) * 10  # Множитель 10 для более читаемого изображения
    height = (9 if len(formatted_schedule) != 4 else 8) * 30  # Высота строки
    image = Image.new("RGB", (width, height),
                      color)  # Создаем картинку с фоном с заданным цветом
    draw = ImageDraw.Draw(image)

    # Создаем шрифт по умолчанию для PIL
    if system_type == "Windows":
        font = ImageFont.truetype("arial.ttf", 18)
    elif system_type == "Linux":
        font = ImageFont.truetype(
            "Montserrat-VariableFont_wght.ttf",
            17,
            327680
        )
    else:
        font = ImageFont.load_default()  # ну, а кто его знает

    # Устанавливаем начальные координаты для текста
    x, y = 10, 10

    # Рисуем таблицу
    for index, row in formatted_schedule.iterrows():
        for i, (col, width) in enumerate(
                zip(formatted_schedule.columns, column_widths)):
            text = str(row[col])
            draw.text((x, y), text, fill="black", font=font)
            x += width * 10  # Множитель 10 для более читаемого изображения
        y += 30
        x = 10
    image.save(img)


# pull schedule of day from dataframe
async def format_schedule(schedule, schedule_day) -> pd.DataFrame:
    # got schedule for day
    day_number = schedule[4 + schedule_day].fillna('-').iloc[:, 1:]
    return day_number


async def turn_schedule_pin(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    if await db.get_db_data(chat_id, 'pin_schedule_message'):
        await db.update_db_data(chat_id, pin_schedule_message=0)

        txt = 'Закрепление сообщений с расписанием выключено'
        await send_status(chat_id, text=txt, reply_markup=None)

    else:
        await db.update_db_data(chat_id, pin_schedule_message=1)

        txt = 'Закрепление сообщений с расписанием включено'
        await send_status(chat_id, text=txt, reply_markup=None)

    await asyncio.sleep(1.5)  # timer
    await send_status(chat_id)


async def update_schedule(chat_id, schedule_day, cls) -> list:
    """ update schedule from site """
    site = f"https://lyceum.tom.ru/raspsp/index.php?k={cls[:-1]}&s={cls[-1]}"

    try:
        # get schedule. ptcp154 encoding work too
        schedule = pd.read_html(site, encoding="cp1251")

    except Exception as e:
        custom_logger.error(chat_id, f'<y>site unreachable, error:<r>{e}</></>')
        await asyncio.sleep(schedule_auto_send_delay * 60)
        await bot.send_message(
            chat_id=chat_id,
            text='Сайт недоступен',
            disable_notification=True
        )
        return []

    # update check time
    last_check_schedule = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    # update schedule_change_time
    time_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    schedule_change_time = re.search(time_pattern, schedule[3][0][0]).group()
    # creat json with formatted schedule
    formatted_schedule = await format_schedule(schedule, schedule_day)
    schedule_json = formatted_schedule.to_json()

    await db.update_data_by_cls(
        chat_id,
        cls,
        last_check_schedule=last_check_schedule,
        schedule_json=schedule_json,
        schedule_change_time=schedule_change_time
    )

    return schedule


async def del_old_schedule(chat_id, cls) -> None:
    """ if user have enabled 'del_old_schedule' delete previous schedule """
    del_parameter = await db.get_db_data(chat_id, 'del_old_schedule')

    if del_parameter:
        msg_id = await db.get_data_by_cls(
            chat_id,
            cls,
            'last_schedule_message_id'
        )
        await del_msg_by_id(chat_id, msg_id)


async def schedule_for_day(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    custom_logger.debug(chat_id)

    if query.data == 'schedule_for_day_menu':
        await send_status(chat_id, reply_markup=kb.schedule_for_day())
    else:
        if query.data.startswith('set_class_'):
            callback_prefix = 'set_class_'
            cls = query.data[len(callback_prefix):]
            cls = await add_change_to_class(cls)

            await send_status(chat_id, reply_markup=kb.schedule_for_day(cls))
        elif len(query.data) > 18:
            day_prefix = 'schedule_for_day_'
            cls_prefix = 'schedule_for_day_0_'
            day = int(query.data[len(day_prefix):(len(day_prefix) + 1)])
            cls = query.data[len(cls_prefix):]

            await send_status(chat_id)
            await send_schedule(chat_id, now=1, cls=cls, day=day)
        else:
            callback_prefix = 'schedule_for_day_'
            day: int = int(query.data[len(callback_prefix):])

            await send_status(chat_id)
            await send_schedule(chat_id, now=1, day=day)


async def pin_schedule(chat_id, schedule_msg_id) -> None:
    """ pin schedule msg if the user has enabled this feature """
    if await db.get_db_data(chat_id, 'pin_schedule_message'):
        try:
            await bot.pin_chat_message(chat_id, schedule_msg_id)

        except Exception as e:
            custom_logger.critical(chat_id, f'<y>pin error: <r>{e}</></>')
            if "not enough rights to manage pinned messages" in str(e):
                await not_enough_rights_to_pin(chat_id)


async def turn_deleting(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    if await db.get_db_data(chat_id, 'del_old_schedule'):
        await db.update_db_data(chat_id, del_old_schedule=0)

        txt = 'Автоматическое удаление предыдущего расписания выключено'
        await send_status(chat_id, text=txt, reply_markup=None)
        await asyncio.sleep(3.5)
        await send_status(chat_id)

    else:
        await db.update_db_data(chat_id, del_old_schedule=1)

        txt = 'Автоматическое удаление предыдущего расписания включено'
        await send_status(chat_id, text=txt, reply_markup=None)
        await asyncio.sleep(3.5)
        await send_status(chat_id)


async def schedule_file_name(chat_id, day) -> str:
    user_class = await db.get_db_data(chat_id, 'school_class')
    color = await db.get_db_data(chat_id, 'schedule_bg_color')

    img = f'bot/data/schedule_{user_class}_{day}_{color}.png'

    return img
