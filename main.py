import logging
import re
import asyncio
import warnings
from datetime import datetime
import pandas as pd
import pytz
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher
from aiogram.utils import executor
# from configs import config
from configs import tconfig as config

# Подавление предупреждений BeautifulSoup
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

# log config
basic_log = False
debug_log = False

if 'log_level' in dir(config) and config.log_level >= 1:
    basic_log = True
    if config.log_level >= 2:
        debug_log = True
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filename='bot.log', encoding='UTF-8', datefmt='%Y-%m-%d %H:%M:%S')
    log = logging.getLogger()


# Создаем объекты бота и диспетчера, а также необходимые переменные
bot = Bot(token=config.token)
dp = Dispatcher(bot)

# получение текущего времени
local_timezone = pytz.timezone('Asia/Tomsk')


# Переменная для хранения времени последней проверки расписания
last_print_schedule = 'еще не проверялось'  # Переменная последнего изменения
last_check_schedule = 'еще не проверялось'  # Переменная последнего изменения
prev_schedule = list()  # Переменная послденего отправленного расписания


# функция для получения получение дня недели в текстовом виде
def text_day_of_week(day_of_week):
    return {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг', 4: 'Пятница', 5: 'Суббота'}[day_of_week]


# генерация изображения
def generate_image(schedule):
    # Задаем ширину строки
    column_widths = [max(schedule[col].astype(str).apply(len).max() + 1, len(str(col))) for col in schedule.columns]

    # Создаем изображение
    width = sum(column_widths) * 10  # Множитель 10 для более читаемого изображения
    height = (9 if len(schedule) != 4 else 8) * 30  # Высота строки
    image = Image.new("RGB", (width, height), (255, 255, 143))  # Создаем картинку с фоном с заданным цветом
    draw = ImageDraw.Draw(image)

    # Создаем шрифт по умолчанию для PIL
    # font = ImageFont.truetype("DejaVuSans.ttf", 16) # для linux
    font = ImageFont.truetype("arial.ttf", 18)  # для винды

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


# запуск бота
async def start(dp):
    # отправляем статус
    status = f"""🤖 Бот запущен!\n🕓 Время последнего обновления: {datetime.now(local_timezone).strftime('%Y-%m-%d %H:%M')}\n\n
📅 Последнее изменение расписания: {last_print_schedule}\n
🔍 Последняя проверка расписания: {last_check_schedule}\n\n
🎓 Класс и смена: {config.school_class}, {['первая', 'вторая'][config.school_change - 1]}\n
🔄 Автоматическая отправка расписания:\n{['🔴 Выключена', f"🟢 Включена, проверка выполняется раз в {config.auto_send_delay // 60} минут."][config.auto_send]}\n\n"""

    send_status = await bot.send_message(config.schedule_chat_id, status, disable_notification=True)

    if config.auto_send:
        await asyncio.gather(status_updater(send_status), schedule_auto_sending())
    else:
        await status_updater(send_status)


# Сообщение со статусом
async def status_updater(send_status):
    while True:
        await asyncio.sleep(3)
        status = f"""🤖 Бот запущен!\n🕓 Время последнего обновления: {datetime.now(local_timezone).strftime('%Y-%m-%d %H:%M')}\n\n
📅 Последнее изменение расписания: {last_print_schedule}\n
🔍 Последняя проверка расписания: {last_check_schedule}\n\n
🎓 Класс и смена: {config.school_class}, {['первая', 'вторая'][config.school_change - 1]}\n
🔄 Автоматическая отправка расписания:\n{['🔴 Выключена', f"🟢 Включена, проверка выполняется раз в {config.auto_send_delay // 60} минут."][config.auto_send]}\n\n"""

        await bot.edit_message_text(status, chat_id=config.schedule_chat_id, message_id=send_status.message_id)
        await asyncio.sleep(config.status_delay)


# отправка расписания каждые 15м
async def schedule_auto_sending():
    global last_print_schedule  # Переменная последнего изменения
    global last_check_schedule  # Переменная последнего изменения
    global last_print_time_day  # переменная дня печати
    global prev_schedule  # Переменная послденего отправленного расписания
    global last_print_time_hour  # час последнего изменения
    schedule = list()

    # паттерн  для поиска даты последн. изменения в датафрейме
    datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    while True:
        # Обновляем текущую локальную дату и время
        local_date = datetime.now(local_timezone)

        # Цикл для избежания ошибок из-за недоступности сайта
        while True:
            try:
                # Получение данных со страницы с расписанием
                schedule = pd.read_html(f"https://lyceum.tom.ru/raspsp/index.php?k={config.school_class}&s={config.school_change}", keep_default_na=True, encoding="cp1251")  # ptcp154, also work
                last_check_schedule = local_date.strftime('%d.%m.%Y %H:%M:%S')
                print()
                print(local_date.strftime('%Y-%m-%d %H:%M'))
                print('parsing', '\n    scheduel:', type(schedule), '\n    prev_schedule', type(prev_schedule))
                break

            except:
                # Уведомление о недоступности сайта
                await bot.send_message(config.chat_id, 'Сайт умер. Следующая попытка через 15м.', disable_notification=True)

                # timer
                await asyncio.sleep(config.auto_send_delay)
                continue

        # Получаем время последнего изменения расписания
        schedule_change_time = re.search(datetime_pattern, schedule[3][0][0]).group()

        # Проверяем изменилось ли расписание с момента последнего уведомления.
        # или
        # Если сейчас больше 8 или позже и после 15 расписание не присылалось.
        if (last_print_schedule != schedule_change_time and local_date.weekday() != 5) or (local_date.hour >= 20 and (local_date.weekday() != 5 and (last_print_time_hour < 15 and local_date.weekday() != 6 or last_print_time_day != local_date.day))):

            # обовляем время последнего отправленного расписания
            last_print_schedule = schedule_change_time
            day_of_week = local_date.weekday()  # номер дня недели 0-6

            # Правила для отправки расписания на следующий день
            if day_of_week + 1 in [6, 7]:  # Если суббота или воскресенье
                if local_date.hour >= 10:  # и больше 10 часов
                    day_of_week = 0
            else:
                if (local_date.hour >= 15) or (prev_schedule == schedule):
                    day_of_week += 1

            # Обновляем последние отправленное расписание
            prev_schedule = schedule.copy()

            print('after', '\n    scheduel:', type(schedule), '\n    prev_schedule', type(prev_schedule))

            # Получаем таблицу с раписанием нужного дня из датафрейма
            formatted_schedule = schedule[3 + (day_of_week + 1) % 7].fillna('-').iloc[:, 1:]

            # генерируем изображение в папку temp
            generate_image(formatted_schedule)

            # цикл отправляющий картинку с текстом в телеграм
            # видимо иногда выдает ошибку и выключает бота, по этому через while и try-except
            while True:
                try:
                    # Открываем фотографию, которую хотим отправить
                    with open('temp/schedule.png', 'rb') as photo_file:
                        # Отправляем фотографию
                        await bot.send_photo(config.chat_id, photo_file, f'{text_day_of_week(day_of_week)} - Последние изменение: [{last_print_schedule}]\n\n')
                        last_print_time_day = local_date.day
                        last_print_time_hour = local_date.hour
                    break

                except:
                    continue

        # задержка сканирования
        await asyncio.sleep(config.auto_send_delay)


# Сообщение о завершении работы
async def send_error_message(error):
    print('Error:', error)
    await bot.send_message(config.control_chat_id, text=f'Бот завершил работу из-за ошибки: {str(error)}')


if __name__ == '__main__':
    print('Bot started')
    # Отправка уведомления в случае ошибки
    try:
        executor.start_polling(dp, skip_updates=False, relax=1, on_startup=start)
    except Exception as e:
        # Отправка уведомления в случае ошибки
        asyncio.run(send_error_message(e))
