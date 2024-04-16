import os

from dotenv import load_dotenv

load_dotenv()
token = os.getenv("token")
dev_id = os.getenv("dev_id")

# Put your token and dev_id in the /bot/config/.env file
if token is None:
    raise Exception("token not exist in .env"
                    "check where you place .env. It must be in"
                    "/bot/config/.env")

if dev_id is None:
    raise Exception("dev_id not exist in .env"
                    "check where you place .env. It must be in"
                    "/bot/config/.env")

# Auto send delay in min
schedule_auto_send_delay: float = 15

# The following parameter sets logging level:
# ['AIOGRAM_DEBUG', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
# 'AIOGRAM_DEBUG' also print aiogram auto logs
console_log_level: str = 'AIOGRAM_DEBUG'

# dictionary with classes
classes_dict = {
    'a1': '1а', 'b1': '1б', 'v1': '1в', 'g1': '1г', 'd1': '1д', 'e1': '1е',
    'j1': '1ж', 'z1': '1з',
    'a2': '2а', 'b2': '2б', 'v2': '2в', 'g2': '2г', 'd2': '2д', 'e2': '2е',
    'j2': '2ж', 'z2': '2з',
    'a3': '3а', 'b3': '3б', 'v3': '3в', 'g3': '3г', 'd3': '3д', 'e3': '3е',
    'a4': '4а', 'b4': '4б', 'v4': '4в', 'g4': '4г', 'd4': '4д',
    'a5': '5а', 'b5': '5б', 'v5': '5в', 'g5': '5г',
    'a6': '6а', 'b6': '6б', 'v6': '6в', 'g6': '6г',
    'a7': '7а', 'b7': '7б', 'v7': '7в', 'g7': '7г', 'd7': '7д',
    'a8': '8а', 'b8': '8б', 'v8': '8в', 'g8': '8г',
    'a9': '9а', 'b9': '9б', 'v9': '9в',
    'a10': '10а', 'b10': '10б',
    'a11': '11а', 'b11': '11б'
}

# list with second change classes
second_change_nums = ['2', '4']
