import logging
import re
import time
from datetime import datetime
import pandas as pd
import pytz
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
# from configs import config
from configs import tconfig as config

# log config
basic_log = False
debug_log = False

if 'log_level' in dir(config) and config.log_level >= 1:
    basic_log = True
    if config.log_level >= 2:
        debug_log = True
    logging.basicConfig(level=logging.INFO, filename='bot.log', encoding='UTF-8', datefmt='%Y-%m-%d %H:%M:%S')
    log = logging.getLogger()


# Создаем объекты бота и диспетчера
bot = Bot(token=config.token)
dp = Dispatcher(bot)



def generate_image(schedule):
    # Задаем ширину строки
    column_widths = [max(schedule[col].astype(str).apply(len).max() + 1, len(str(col))) for col in schedule.columns]

    # Создаем изображение
    width = sum(column_widths) * 10  # Множитель 10 для более читаемого изображения
    height = (9 if len(schedule) != 4 else 8) * 30  # Высота строки
    image = Image.new("RGB", (width, height), (255, 255, 143)) # Создаем картинку с фоном с заданным цветом
    draw = ImageDraw.Draw(image)

    # Создаем шрифт по умолчанию для PIL
    #font = ImageFont.truetype("DejaVuSans.ttf", 16) # для linux
    font = ImageFont.truetype("arial.ttf", 18) # для винды

    # Устанавливаем начальные координаты для текста
    x, y = 10, 10

    # Рисуем таблицу
    for index, row in schedule.iterrows():
        for i, (col, width) in enumerate(zip(schedule.columns, column_widths)):
            text = str(row[col])
            draw.text((x, y), text, fill="black", font=font)
            x += width * 10  # Множитель 10 для более читаемого изображения
        y += 30  # Высота строки
        x = 10

    # Сохраняем изображение
    image.save('temp/schedule.png')


@dp.message_handler(commands=['notify_schedule'])
async def send_photo(message: types.Message):

    # паттерн  для поиска даты последн. изменения в датафрейме
    datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    local_timezone = pytz.timezone(config.local_timezone_cfg)
    local_date = datetime.now(local_timezone)

    # Переменная для хранения времени последней проверки расписания
    last_print_schedule = '' # Переменная последнего изменения
    last_print_time_day = local_date.day # переменная дня печати
    prev_schedule = 0 # Переменная послденего отправленного расписания
    last_print_time_hour = local_date.hour # час последнего изменения
    print('schedule printing started')


    while True:

        # Обновляем текущую локальную дату и время
        local_date = datetime.now(local_timezone)
        # Получение данных со страницы с расписанием
        schedule = pd.read_html("https://lyceum.tom.ru/raspsp/index.php?k=b11&s=1", keep_default_na=True, encoding="cp1251") # ptcp154, also work

        # Получаем время последнего изменения расписания
        schedule_change_time = re.search(datetime_pattern, schedule[3][0][0]).group()

        # Проверяем изменилось ли расписание с момента последнего уведомления.
        # или
        # Если сейчас больше 8 или позже и после 15 расписание не присылалось.
        if (last_print_schedule != schedule_change_time and local_date.weekday() != 5) or (local_date.hour >= 20 and (local_date.weekday() != 5 and (last_print_time_hour < 15 or last_print_time_day != local_date.day))):

            # обовляем время последнего отправленного расписания
            last_print_schedule = schedule_change_time
            day_of_week = local_date.weekday() # номер дня недели 0-6

            # Правила для отправки расписания на следующий день
            if day_of_week + 1 in [6, 7]:
                if local_date.hour >= 10:
                    day_of_week = 0
            else:
                if local_date.hour >= 15 or prev_schedule != 0 and prev_schedule == (schedule[3 + (day_of_week + 1) % 7].fillna('-').iloc[:, 1:]):
                    day_of_week += 1

            # Переменная содержащая день недели в текстовом виде
            text_day_of_week = {0:'Понедельник', 1:'Вторник', 2:'Среда', 3:'Четверг', 4:'Пятница', 5:'Суббота'}[day_of_week]

            # Получаем таблицу с раписанием нужного дня из датафрейма
            schedule = schedule[3 + (day_of_week + 1) % 7].fillna('-').iloc[:, 1:]

            # Обновляем последние отправленное расписание
            prev_schedule = schedule

            # генерируем изображение в папку temp
            generate_image(schedule)

            # цикл отправляющий картинку с текстом в телеграм
            # видимо иногда выдает ошибку и выключает бота, по этому через while и try-except
            while True:
                try:
                    # Открываем фотографию, которую хотим отправить
                    with open('temp/schedule.png', 'rb') as photo_file:
                        # Отправляем фотографию
                        await message.reply_photo(photo_file, caption=f'{text_day_of_week} - Последние изменение: [{last_print_schedule}]\n\n')
                        last_print_time_day = local_date.day
                        last_print_time_hour = local_date.hour
                    break

                except:
                    continue

        # печаетаем время последней проверки расписания
        print("last update:", local_date)

        # задержка сканирования
        time.sleep(900)

if __name__ == '__main__':
    print('Bot started')
    executor.start_polling(dp, skip_updates=False, relax=1)