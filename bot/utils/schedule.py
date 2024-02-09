import re
import pytz
import asyncio
import warnings
import platform
import pandas as pd

from datetime import datetime
from urllib.error import URLError
from aiogram.types import FSInputFile
from PIL import Image, ImageDraw, ImageFont

from main import bot
from bot.utils.status import send_status
from bot.logs.log_config import custom_logger
from bot.database.db import bot_database as db
from bot.utils.utils import del_msg_by_db_name, del_msg_by_id
from bot.config.config_loader import schedule_auto_send_delay

# Подавление предупреждений BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

local_timezone = pytz.timezone('Asia/Tomsk')
system_type = platform.system()


async def schedule_auto_send(chat_id: int):
    custom_logger.debug(chat_id)

    while await db.get_db_data(chat_id, 'schedule_auto_send'):
        await send_schedule(chat_id)  # start
        await asyncio.sleep(schedule_auto_send_delay * 60)  # задержка сканирования


async def send_schedule(chat_id: int,  now: int = 0):
    custom_logger.debug(chat_id, f'<y> now: <r>{now}</></>')

    settings = await db.get_db_data(
        chat_id, 'school_class', 'school_change', 'last_check_schedule',
        'last_print_time', 'last_print_time_hour',
        'last_print_time_day', 'prev_schedule', 'last_printed_change_time'
    )

    # save settings from db
    school_class, school_change, last_check_schedule, \
        last_print_time, last_print_time_hour, \
        last_print_time_day, prev_schedule, last_printed_change_time = settings

    datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    local_date = datetime.now(local_timezone)
    schedule = list()

    # Цикл для избежания ошибок из-за недоступности сайта
    while True:
        try:
            cls = school_class
            chng = school_change
            site = f"https://lyceum.tom.ru/raspsp/index.php?k={cls}&s={chng}"
            schedule = pd.read_html(site,
                                    keep_default_na=True,
                                    encoding="cp1251"
                                    )  # ptcp154, also work
            last_check_schedule = local_date.strftime('%d.%m.%Y %H:%M:%S')
            break

        except URLError:
            custom_logger.critical('site unreachable')
            await asyncio.sleep(schedule_auto_send_delay * 60)

        except Exception as e:
            custom_logger.critical(f'Site parse error:\n{e}')
            await asyncio.sleep(schedule_auto_send_delay * 60)


    # получаем время последнего изменения расписания
    schedule_change_time = re.search(datetime_pattern, schedule[3][0][0]).group()

    # получаем schedule в виде json
    formatted_schedule = await format_schedule(schedule, local_date.weekday())
    schedule_json = formatted_schedule.to_json()

    # Функция определяет, будет ли выполняться отправка расписания и если да, то на какой день недели
    # Функция возвращает лист, например [0, 0]. Первая цифра отвечает за то, будет ли выполняться отправка,
    # вторая за то в какой день она будет выполняться
    def send_logic(local_date, schedule_change_time, last_printed_change_time, prev_schedule, last_print_time_day, last_print_time_hour, schedule_json):
        # создаем переменные для часа и дня недели
        hour = local_date.hour
        weekday = local_date.weekday()

        # изменилось ли расписание на сайте
        site_schedule_change = now == 1 or last_printed_change_time != schedule_change_time

        # изменилось ли расписание текущего дня
        # либо если last_print_time_day (== первый запуск)
        printed_schedule_change = now == 1 or (prev_schedule != schedule_json) and (last_print_time_day == local_date.day)

        # сейчас не ( (суббота и больше 9) или (воскресенье и меньше 20) )
        weekend_condition = not ((int(weekday) == 5 and int(hour) > 9) or (int(weekday) == 6 and int(hour) < 20))

        # Не печаталось на завтра
        print_to_tomorrow = last_print_time_day != local_date.day or last_print_time_hour < 15

        if site_schedule_change:  # расписание изменилось на сайте
            if weekend_condition:  # сейчас не ((суббота и больше 9) или (воскресенье и меньше 20))
                if printed_schedule_change:  # Расписание изменилось на сегодняшний день
                    if hour < 15:
                        custom_logger.debug(chat_id, '<y>send logic condition: <r>1</></>')
                        result = [1, 0]  # если оно изменилось, и сейчас меньше 15, то обновляем
                    else:
                        custom_logger.debug(chat_id, '<y>send logic condition: <r>2</></>')
                        result = [1, 1]  # если сейчас больше 15, то отправляем на завтра
                else:
                    custom_logger.debug(chat_id, '<y>send logic condition: <r>3</></>')
                    result = [1, 1]  # если не изменилось, то отправляем на завтра
            else:
                custom_logger.debug(chat_id, '<y>send logic condition: <r>4</></>')
                result = [0, 0]  # то не отправляем
        else:
            if print_to_tomorrow:  # если не печаталось на завтра
                if hour > 20 and weekend_condition:  # если больше 20
                    custom_logger.debug(chat_id, '<y>send logic condition: <r>5</></>')
                    result = [1, 1]  # то отправляем на завтра
                else:
                    custom_logger.debug(chat_id, '<y>send logic condition: <r>6</></>')
                    result = [0, 0]  # то не отправляем
            else:
                custom_logger.debug(chat_id, '<y>send logic condition: <r>7</></>')
                result = [0, 0]  # то не отправляем

        # меняем воскресенье после 20 на понедельник
        day = (local_date.weekday() + result[1])

        result[1] = day if day not in [6, 7] else 0

        return result

    # send_logic
    send_logic_res = send_logic(local_date, schedule_change_time, last_printed_change_time, prev_schedule, last_print_time_day, last_print_time_hour, schedule_json)
    msg = f'<y>send logic res: {send_logic_res}, now: <r>{now}</></>'
    custom_logger.error(chat_id, msg)

    # Отправляем расписание если send_logic_res[0] == 1
    if send_logic_res[0] or now:
        # Удаление предыдущего расписания
        await del_msg_by_db_name(chat_id, 'last_schedule_message_id')

        # обновляем время последнего отправленного расписания
        last_print_time = local_date.strftime('%d.%m.%Y. %H:%M:%S')

        # время изменения на сайте, последнего напечатанного расписания
        last_printed_change_time = schedule_change_time

        # определяем нужный день для отправки расписания
        schedule_day = send_logic_res[1]

        # Получаем форматированную таблицу с расписанием
        formatted_schedule = await format_schedule(schedule, schedule_day)

        # сохраняем последнее напечатанное расписание в json
        prev_schedule = formatted_schedule.to_json()

        # генерируем изображение в папку temp
        await generate_image(chat_id, formatted_schedule)
        while True:
            try:
                text = f'{await text_day_of_week(schedule_day)} - Последние изменение: [{last_printed_change_time}]\n\n' # text

                # Отправляем фотографию
                schedule_img = FSInputFile("bot/data/schedule.png")
                schedule_msg = await bot.send_photo(chat_id, caption=text,
                                                  photo=schedule_img)

                if await db.get_db_data(chat_id, 'pin_schedule_message'):
                    # Закрепляем сообщение
                    await bot.pin_chat_message(chat_id=chat_id,
                                               message_id=schedule_msg.message_id)
                    # delete service message "bot pinned message"
                    await del_msg_by_id(chat_id, schedule_msg.message_id + 1)
                    custom_logger.error(chat_id, f'<y>now: <r>{now}, </>printed</>')

                last_print_time_day = local_date.day
                last_print_time_hour = local_date.hour

                await db.update_db_data(chat_id,
                                        last_schedule_message_id=schedule_msg.message_id)

                await asyncio.sleep(1)
                await send_status(chat_id)
                break

            except Exception as e:
                msg = f'<y>Schedule image to bot sending error: <r>{e}</></>'
                custom_logger.error(chat_id, msg)
                await asyncio.sleep(60)
                continue

    await db.update_db_data(chat_id,
                            last_print_time=last_print_time,
                            last_printed_change_time=last_printed_change_time,
                            last_check_schedule=last_check_schedule,
                            prev_schedule=prev_schedule,
                            last_print_time_day=last_print_time_day,
                            last_print_time_hour=last_print_time_hour
                            )


async def text_day_of_week(schedule_day):
    day = {0: 'Понедельник',
           1: 'Вторник',
           2: 'Среда',
           3: 'Четверг',
           4: 'Пятница',
           5: 'Суббота'
           }[schedule_day]
    return day


# генерация изображения
async def generate_image(chat_id, formatted_schedule):
    # Задаем ширину строки
    column_widths = [max(formatted_schedule[col].astype(str).apply(len).max() + 1, len(str(col))) for col in formatted_schedule.columns]

    # get user color settings
    color_str = await db.get_db_data(chat_id, 'schedule_bg_color')
    color = tuple(int(i) for i in color_str.split(','))

    # Создаем изображение
    width = sum(column_widths) * 10  # Множитель 10 для более читаемого изображения
    height = (9 if len(formatted_schedule) != 4 else 8) * 30  # Высота строки
    image = Image.new("RGB", (width, height), color)  # Создаем картинку с фоном с заданным цветом
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
        for i, (col, width) in enumerate(zip(formatted_schedule.columns, column_widths)):
            text = str(row[col])
            draw.text((x, y), text, fill="black", font=font)
            x += width * 10  # Множитель 10 для более читаемого изображения
        y += 30  # Высота строки
        x = 10

    # Сохраняем изображение
    image.save('bot/data/schedule.png')


# pull schedule of day from dataframe
async def format_schedule(schedule, schedule_day):
    # получаем номер нужного дня
    day_number = schedule[4 + schedule_day].fillna('-').iloc[:, 1:]
    return day_number


