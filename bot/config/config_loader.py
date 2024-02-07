import os

from dotenv import load_dotenv

from bot.config.config import *

load_dotenv()
token = os.getenv("token")
dev_id = os.getenv("dev_id")

if dev_id is None or token is None:
    raise Exception("token or dev_id not exist in .env"
                    "check where you place .env it must be in"
                    "/bot/config/.env")

