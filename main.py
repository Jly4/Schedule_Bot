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
    #font = ImageFont.truetype("DejaVuSans.ttf", 18) # для linux
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
    print('image saved')

@dp.message_handler(commands=['notify_schedule'])
async def send_photo(message: types.Message):

    # паттерн  для поиска даты последн. изменения в датафрейме
    datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'

    # Переменная для хранения времени последней проверки расписания
    last_check = '' # Переменная последнего изменения
    print('schedule printing started')


    while True:

        # Получаем текущую локальную дату и время
        local_timezone = pytz.timezone('Asia/Tomsk')
        local_date = datetime.now(local_timezone)

        # Получение данных со страницы с расписанием
        schedule = pd.read_html("https://lyceum.tom.ru/raspsp/index.php?k=b11&s=1", keep_default_na=True, encoding="cp1251") # ptcp154, also work

        # Получаем время последнего изменения расписания
        schedule_change = re.search(datetime_pattern, schedule[3][0][0]).group()

        # Проверяем изменилось ли расписание с момента последнего уведомления
        if last_check != schedule_change:

            # обовляем время последнего отправленного расписания
            last_check = schedule_change
            day_of_week = local_date.weekday() # номер дня недели 0-6

            # Правила для отправки расписания на следующий день
            if day_of_week + 1 in [6, 7]:
                if local_date.hour >= 10:
                    day_of_week = 0
            else:
                if local_date.hour >= 15:
                        day_of_week += 1

            # Переменная содержащая день недели в текстовом виде
            text_day_of_week = {0:'Понедельник', 1:'Вторник', 2:'Среда', 3:'Четверг', 4:'Пятница', 5:'Суббота'}[day_of_week]

            # Получаем таблицу с раписанием нужного дня из датафрейма
            schedule = schedule[3 + (day_of_week + 1) % 7].fillna('-').iloc[:, 1:]

            # генерируем изображение в папку temp
            generate_image(schedule)

            # цикл отправляющий картинку с текстом в телеграм
            # видимо иногда выдает ошибку и выключает бота, по этому через while и try-except
            while True:
                try:
                    # Открываем фотографию, которую хотим отправить
                    with open('temp/schedule.png', 'rb') as photo_file:
                        # Отправляем фотографию
                        await message.reply_photo(photo_file, caption=f'{text_day_of_week} - Последние изменение: [{last_check}]\n\n')
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