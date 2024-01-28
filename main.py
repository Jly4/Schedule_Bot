import asyncio
import logging
import re
import traceback
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
last_print_time = 'еще не проверялось'  # Переменная последнего изменения
last_check_schedule = 'еще не проверялось'  # Переменная последнего изменения
prev_schedule = list()  # Переменная послднего отправленного расписания
last_print_time_day = 0
last_print_time_hour = 25

# функция для получения получение дня недели в текстовом виде
def text_day_of_week(schedule_day):
    return {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг', 4: 'Пятница', 5: 'Суббота'}[schedule_day]


# генерация изображения
def generate_image(formatted_schedule):
    # Задаем ширину строки
    column_widths = [max(formatted_schedule[col].astype(str).apply(len).max() + 1, len(str(col))) for col in formatted_schedule.columns]

    # Создаем изображение
    width = sum(column_widths) * 10  # Множитель 10 для более читаемого изображения
    height = (9 if len(formatted_schedule) != 4 else 8) * 30  # Высота строки
    image = Image.new("RGB", (width, height), (255, 255, 143))  # Создаем картинку с фоном с заданным цветом
    draw = ImageDraw.Draw(image)

    # Создаем шрифт по умолчанию для PIL
    # font = ImageFont.truetype("DejaVuSans.ttf", 16) # для linux
    font = ImageFont.truetype("arial.ttf", 18)  # для винды

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
    image.save('temp/schedule.png')


# запуск бота
async def start(dp):
    # отправляем статус
    status = f"""🤖 Бот запущен!\n🕓 Время последнего обновления: {datetime.now(local_timezone).strftime('%Y-%m-%d %H:%M')}\n\n
📅 Последнее изменение расписания: {last_print_time}\n
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
📅 Последнее изменение расписания: {last_print_time}\n
🔍 Последняя проверка расписания: {last_check_schedule}\n\n
🎓 Класс и смена: {config.school_class}, {['первая', 'вторая'][config.school_change - 1]}\n
🔄 Автоматическая отправка расписания:\n{['🔴 Выключена', f"🟢 Включена, проверка выполняется раз в {config.auto_send_delay // 60} минут."][config.auto_send]}\n\n"""

        await bot.edit_message_text(status, chat_id=config.schedule_chat_id, message_id=send_status.message_id)
        await asyncio.sleep(config.status_delay)


# отправка расписания каждые 15м
async def schedule_auto_sending():
    global last_print_time  # Переменная последнего изменения
    global last_check_schedule  # Переменная последнего изменения
    global last_print_time_day  # День последнего изменения
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
                print('last_check_schedule:', local_date.strftime('%d.%m.%Y %H:%M:%S'))
                break

            except Exception as e:
                # Здесь мы печатаем полную информацию об ошибке
                traceback.print_exc()

                # Можете также обработать ошибку более детально или выполнить другие действия
                print(f"Произошла ошибка: {e}")

                # Уведомление о недоступности сайта
                await bot.send_message(config.chat_id, 'Сайт умер. Следующая попытка через 15м.', disable_notification=True)

                # timer
                await asyncio.sleep(config.auto_send_delay)
                continue





        # Получаем время последнего изменения расписания
        schedule_change_time = re.search(datetime_pattern, schedule[3][0][0]).group()

        # Функция определяет будет ли выполняться отправка расписания и если да, то на какой день недели
        # Функция возвращает лист [0, 0]. Первая цифра отвечает за то, будет ли выполняться отправка, вторая за то в какой день она будет выполняться
        def send_logic(local_date, schedule_change_time, last_print_time, schedule, prev_schedule, last_print_time_day, last_print_time_hour):

            hour = local_date.hour
            weekday = local_date.weekday()

            # изменилось ли расписание на сайте
            site_schedule_change = last_print_time != schedule_change_time

            # изменилось ли расписание текущего дня
            printed_schedule_change = not ((prev_schedule == schedule) and (last_print_time_day != local_date.day))

            # сейчас не ( (суббота и больше 9) или (воскресенье и меньше 20) )
            weekend_condition = not ((weekday == 5 and hour > 9) or (weekday == 6 and hour < 20))

            # Отправлялось ли сегодня расписание на завтра
            print_to_tomorrow = last_print_time_day == local_date.day and last_print_time_hour < 15

            if site_schedule_change:  # расписание изменилось на сайте
                if weekend_condition:  # сейчас не ((суббота и больше 9) или (воскресенье и меньше 20))
                    if printed_schedule_change:  # Расписание изменилось на сегодняшний день
                        if hour < 15:
                            result = [1, 0]  # если оно изменилось, и сейчас меньше 15, то обновляем
                        else:
                            result = [1, 1]  # если сейчас больше 15, то отправляем на завтра
                    else:
                        result = [1, 1]  # если не изменилось, то отправляем на завтра
                else:
                    result = [0, 0]  # то не отправляем
            else:
                if print_to_tomorrow:  # если больше 20, и сегодня не печаталось
                    result = [0, 0]  # то не отправляем
                else:
                    if hour > 20:
                        result = [1, 1]  # то отправляем на завтра
                    else:
                        result = [0, 0]  # то не отправляем

            # меняем воскресенье после 20 на понедельник
            result[1] = (local_date.weekday() + result[1]) % 7

            return result

            # Если вариант с result[1] = (local_date.day + result[1]) % 7 не сработает
            # # прибавляем текущий день недели к логике
            # result[1] = local_date.day + result[1]
            #
            # # меняем воскресенье после 20 на понедельник
            # result[1] == 0 if local_date.day + result[1] == 7 else local_date.day + result[1]

        # send_logic
        send_logic_res = send_logic(local_date, schedule_change_time, last_print_time, schedule, prev_schedule, last_print_time_day, last_print_time_hour)
        print('send logic res:', send_logic_res, '\n')

        # Отправляем расписание если send_logic_res[0] == 1
        if send_logic_res[0]:
            # обновляем время последнего отправленного расписания
            last_print_time = schedule_change_time

            # определяем нужный день для отправки расписания
            schedule_day = send_logic_res[1]

            # функция, которая достает и форматирует из датафрейма расписание на день переданный в нее
            def formatted_schedule_for_day(schedule_day):
                nonlocal schedule
                return schedule[4 + schedule_day].fillna('-').iloc[:, 1:]

            # Получаем форматированную таблицу с расписанием
            formatted_schedule = formatted_schedule_for_day(schedule_day)

            # сохраняем последнее отправленное расписание
            prev_schedule = formatted_schedule

            # генерируем изображение в папку temp
            generate_image(formatted_schedule)

            # цикл отправляющий картинку с текстом в телеграм
            # видимо иногда выдает ошибку и выключает бота, по этому через while и try-except
            while True:
                try:
                    # Открываем фотографию, которую хотим отправить
                    with open('temp/schedule.png', 'rb') as photo_file:
                        # Отправляем фотографию
                        await bot.send_photo(config.chat_id, photo_file, f'{text_day_of_week(schedule_day)} - Последние изменение: [{last_print_time}]\n\n')
                        last_print_time_day = local_date.day
                        last_print_time_hour = local_date.hour
                    break

                except Exception as e:
                    # Здесь мы печатаем полную информацию об ошибке
                    traceback.print_exc()
                    # Можете также обработать ошибку более детально или выполнить другие действия
                    print(f"Произошла ошибка: {e}")
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
        # Здесь мы печатаем полную информацию об ошибке
        traceback.print_exc()
        # Отправка уведомления в случае ошибки
        asyncio.run(send_error_message(e))
