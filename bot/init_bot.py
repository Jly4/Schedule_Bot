from aiogram import Bot, Dispatcher

# temp config
from bot.configs import tconfig as config
# from bot.configs import config

"""
Создаем объекты бота, чтобы избежать ошибки взаимо импорта файлов
"""

# Создаем объекты бота и диспетчера, а также необходимые переменные
bot = Bot(token=config.token)
dp = Dispatcher(bot)