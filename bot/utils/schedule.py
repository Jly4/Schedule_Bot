import re
import pytz
import asyncio
import warnings
import platform
import pandas as pd

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import FSInputFile, CallbackQuery

from main import bot
from bot.utils.status import send_status
from bot.database.database import db as db
from bot.logs.log_config import custom_logger
from bot.config.config_loader import schedule_auto_send_delay
from bot.utils.messages import del_msg_by_db_name, del_msg_by_id
from bot.utils.utils import run_task_if_disabled
from bot.utils.schedule_logic import ScheduleLogic
from bot.keyboards import keyboards as kb

# Подавление предупреждений BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

local_timezone = pytz.timezone('Asia/Tomsk')
system_type = platform.system()


async def schedule_auto_send(chat_id: int):
    custom_logger.debug(chat_id)

    while await db.get_db_data(chat_id, 'schedule_auto_send'):
        if await schedule_time_filter():
            await send_schedule(chat_id)

        await asyncio.sleep(schedule_auto_send_delay * 60)


async def send_schedule(chat_id: int, now: int = 0, day: int = None):
    custom_logger.debug(chat_id, f'<y> now: <r>{now}</></>')
    local_date = datetime.now(local_timezone)
    logic = ScheduleLogic(chat_id)
    should_send = await logic.should_send()
    schedule_day = await logic.schedule_day()

    # get schedule
    schedule = await update_schedule_from_site(chat_id)
    if not schedule:
        return

    # if argument day is not empty
    if isinstance(day, int):
        schedule_day = day

    if should_send or now:
        last_print_time = local_date.strftime('%d.%m.%Y. %H:%M:%S')
        # get time change schedule on site
        change_time = await db.get_db_data(chat_id, 'schedule_change_time')
        last_printed_change_time = change_time

        formatted_schedule = await format_schedule(schedule, schedule_day)
        prev_schedule_json = formatted_schedule.to_json()

        await generate_schedule_image(chat_id, formatted_schedule)
        await del_old_schedule(chat_id)

        try:
            txt = await schedule_msg_txt(schedule_day, last_printed_change_time)
            schedule_img = FSInputFile("bot/data/schedule.png")

            schedule_msg = await bot.send_photo(chat_id, caption=txt,
                                                photo=schedule_img)

        except Exception as e:
            msg = f'<y>Schedule image to bot sending error: <r>{e}</></>'
            custom_logger.error(chat_id, msg)
            await bot.send_message(chat_id, 'Ошибка отправки расписания')
            await asyncio.sleep(60)
            return

        await pin_schedule(chat_id, schedule_msg.message_id)

        data = {'last_schedule_message_id': schedule_msg.message_id}
        await db.update_db_data(chat_id, **data)

    if should_send:
        data = {
            'last_print_time_day': local_date.day,
            'last_print_time_hour': local_date.hour,
            'last_print_time': last_print_time,
            'last_printed_change_time': last_printed_change_time,
            'prev_schedule_json': prev_schedule_json
        }
    await db.update_db_data(chat_id, **data)
    await send_status(chat_id)


async def schedule_msg_txt(schedule_day, last_printed_change_time) -> str:
    day = {0: 'Понедельник',
           1: 'Вторник',
           2: 'Среда',
           3: 'Четверг',
           4: 'Пятница',
           5: 'Суббота'
           }[schedule_day]

    msg = f'{day} - последние изменение: [{last_printed_change_time}]\n\n'

    return msg


# генерация изображения
async def generate_schedule_image(chat_id, formatted_schedule):
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
        font = ImageFont.truetype("arial.ttf", 18)  # for windows
    elif system_type == "Linux":
        font = ImageFont.truetype("DejaVuSans.ttf", 16)  # for linux
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
        y += 30  # Высота строки
        x = 10

    # Сохраняем изображение
    image.save('bot/data/schedule.png')


# pull schedule of day from dataframe
async def format_schedule(schedule, schedule_day) -> pd.DataFrame:
    # получаем номер нужного дня
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


async def turn_schedule(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    if await db.get_db_data(chat_id, 'schedule_auto_send'):
        await db.update_db_data(chat_id, schedule_auto_send=0)

        txt = 'Автоматическое получение расписания выключено'
        await send_status(chat_id, text=txt, reply_markup=None)
        await asyncio.sleep(1)
        await send_status(chat_id)

    else:
        await db.update_db_data(chat_id, schedule_auto_send=1)

        txt = 'Автоматическое получение расписания включено'
        await send_status(chat_id, text=txt, reply_markup=None)
        await send_schedule(chat_id, now=1)
        await run_task_if_disabled(chat_id, 'schedule_auto_send')


async def update_schedule_from_site(chat_id) -> list:
    local_date = datetime.now(local_timezone)
    cls = await db.get_db_data(chat_id, 'school_class')
    chng = await db.get_db_data(chat_id, 'school_change')
    site = f"https://lyceum.tom.ru/raspsp/index.php?k={cls}&s={chng}"

    try:
        # get schedule. ptcp154 encoding work too
        schedule = pd.read_html(site, encoding="cp1251")

    except Exception as e:
        custom_logger.error(chat_id, f'<y>site unreachable, error:<r>{e}</></>')
        await asyncio.sleep(schedule_auto_send_delay * 60)
        await bot.send_message(chat_id=chat_id,
                               text='Сайт недоступен',
                               disable_notification=True)
        return []

    # update check time
    last_check_schedule = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    # update schedule_change_time
    time_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    schedule_change_time = re.search(time_pattern, schedule[3][0][0]).group()
    # creat json with formatted schedule
    formatted_schedule = await format_schedule(schedule, local_date.weekday())
    schedule_json = formatted_schedule.to_json()

    data = {
        'last_check_schedule': last_check_schedule,
        'schedule_json': schedule_json,
        'schedule_change_time': schedule_change_time,
    }
    await db.update_db_data(chat_id, **data)

    return schedule


async def del_old_schedule(chat_id) -> None:
    """ if user have enabled 'del_old_schedule' delete previous schedule """
    del_parameter = await db.get_db_data(chat_id, 'del_old_schedule')

    if del_parameter:
        await del_msg_by_db_name(chat_id, 'last_schedule_message_id')


async def schedule_for_day(callback_query: CallbackQuery) -> None:
    chat_id = callback_query.message.chat.id
    custom_logger.debug(chat_id)

    if callback_query.data == 'schedule_for_day_menu':
        await send_status(chat_id, reply_markup=kb.schedule_for_day())

    else:
        callback_prefix = 'schedule_for_day_'
        day = int(callback_query.data[len(callback_prefix):])
        await send_schedule(chat_id, now=1, day=day)


async def pin_schedule(chat_id, schedule_msg_id) -> None:
    """ pin schedule msg if the user has enabled this feature """
    if await db.get_db_data(chat_id, 'pin_schedule_message'):
        await bot.pin_chat_message(chat_id, schedule_msg_id)
        await del_msg_by_id(chat_id, schedule_msg_id + 1)


async def schedule_time_filter() -> bool:
    local_date = datetime.now(local_timezone)
    hour = local_date.hour
    month = local_date.month

    if hour < 6:
        return False

    if month in [6, 7, 8]:
        return False

    return True
