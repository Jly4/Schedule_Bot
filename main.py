import re
import time
from datetime import datetime
import pandas as pd
import pytz
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# import configs
import temp.temp_configs as configs

# Получаем текущую локальную дату и время
local_timezone = pytz.timezone('Asia/Tomsk')
local_date = datetime.now(local_timezone)

# Создаем объекты бота и диспетчера
bot = Bot(token=configs.token)
dp = Dispatcher(bot)

@dp.message_handler(commands=['notify_schedule'])
async def send_photo(message: types.Message):
    last_edit = ''
    print('schedule printing started')
    # schedule parsing
    while True:
        schedule = pd.read_html("https://lyceum.tom.ru/raspsp/index.php?k=b11&s=1", keep_default_na=True, encoding="cp1251") # ptcp154, also work
        datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
        edit = re.search(datetime_pattern, schedule[3][0][0]).group()

        if last_edit != edit:
            last_edit = edit
            day_of_week = local_date.weekday()
            if local_date.hour > 15:
                day_of_week += 1
            text_day_of_week = {0:'Понедельник', 1:'Вторник', 2:'Среда', 3:'Четверг', 4:'Пятница', 5:'Суббота', 6:'Понедельник'}[day_of_week]
            schedule = schedule[4 + day_of_week % 5 - day_of_week // 5].fillna('-').iloc[:, 1:]
            column_widths = [max(schedule[col].astype(str).apply(len).max(), len(str(col))) for col in schedule.columns]

            # Создаем изображение
            width = sum(column_widths) * 10  # Множитель 10 для более читаемого изображения
            height = len(schedule) * 30  # Высота строки
            image = Image.new("RGB", (width, height), (255, 255, 143))
            draw = ImageDraw.Draw(image)

            # Задаем моноширинный шрифт
            font = ImageFont.truetype("arial.ttf", 18)

            # Устанавливаем начальные координаты для текста
            x, y = 10, 10

            # Рисуем таблицу
            #draw.text((x, y), f'{text_day_of_week} - Последние изменение: [{last_edit}]\n\n', fill="black", font=font)
            #y += 30
            for index, row in schedule.iterrows():
                for i, (col, width) in enumerate(zip(schedule.columns, column_widths)):
                    text = str(row[col])
                    draw.text((x, y), text, fill="black", font=font)
                    x += width * 10  # Множитель 10 для более читаемого изображения
                y += 30  # Высота строки
                x = 10

            # Сохраняем изображение
            image.save('temp/table_image.png')
            try:
                # Загрузите фотографию, которую хотите отправить (замените 'photo.jpg' на путь к вашей фотографии)
                with open('temp/table_image.png', 'rb') as photo_file:
                    # Отправьте фотографию пользователю
                    await message.reply_photo(photo_file, caption=f'{text_day_of_week} - Последние изменение: [{last_edit}]\n\n')
            except:
                continue


        time.sleep(1200)

if __name__ == '__main__':
    print('Bot started')
    executor.start_polling(dp, skip_updates=False, relax = 1)