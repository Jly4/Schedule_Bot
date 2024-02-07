# bot token
# put your token in the /bot/config/.env file as follows:
# token=XXXXX

# dev_id
# receiving errors if bot crash and access to the /dev command.
# You can obtain your user ID using the following bot: https://t.me/getmyid_bot
# put your user id in the /bot/config/.env file as follows:
# dev_id=XXXXX

# auto send delay in min
auto_schedule_delay: float = 10

# status update delay in min
auto_status_delay: float = 10

# The following parameter sets logging level:
# ['AIOGRAM_DEBUG', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
# 'AIOGRAM_DEBUG' also print aiogram auto logs
console_log_level: str = 'AIOGRAM_DEBUG'
