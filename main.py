import re
import time
import configs
import calendar
import pandas as pd
from datetime import datetime
from aiogram import Bot, Dispatcher, types
#import configs
import temp_configs as configs

local_date = datetime(year=2023, month=9, day=1)
bot = Bot(token=configs.token)
dp = Dispatcher(bot)

while True:
    last_edit = ''
    shedule = pd.read_html("https://web.archive.org/web/20221002202403/https://lyceum.tom.ru/raspsp/index.php", encoding="cp1251") # ptcp154, also work site:https://lyceum.tom.ru/raspsp/index.php?k=b10&s=1

    datetime_pattern = r'\d{2}\.\d{2}\.\d{4}\. (\d{2}:\d{2}:\d{2})'
    edit = re.search(datetime_pattern, shedule[4][0][0]).group()

    if last_edit != edit:
        last_edit = edit
        day_of_week = local_date.weekday()
        print(shedule[5 + day_of_week])

    time.sleep(600)
