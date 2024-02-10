import os

from dotenv import load_dotenv

from bot.config.config import *

load_dotenv()
token = os.getenv("token")

if token is None:
    raise Exception("token not exist in .env"
                    "check where you place .env it must be in"
                    "/bot/config/.env")
