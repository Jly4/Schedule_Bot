import re
import sys
import time
import asyncio
import logging
#import configs
import temp.temp_configs as configs
import pandas as pd
from os import getenv
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message

# Создаем объекты бота и диспетчера
bot: Bot = Bot(token=configs.token)
dp: Dispatcher = Dispatcher()





if __name__ == '__main__':
    dp.run_polling(bot)

"""
local_date = datetime(year=2023, month=9, day=1)

# schedule parsing
while True:
    last_edit = ''
    schedule = pd.read_html("https://web.archive.org/web/20221002202403/https://lyceum.tom.ru/raspsp/index.php", encoding="cp1251") # ptcp154, also work site:https://lyceum.tom.ru/raspsp/index.php?k=b10&s=1

    datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    edit = re.search(datetime_pattern, schedule[4][0][0]).group()

    if last_edit != edit:
        last_edit = edit
        day_of_week = local_date.weekday()
        print(schedule[5 + day_of_week])

    time.sleep(600)
"""