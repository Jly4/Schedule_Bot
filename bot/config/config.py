# Bot token
# Put your token in the /bot/config/.env file as follows:
# token=XXXXX

# Dev_id for access user to the /dev command.
# You can obtain your user ID using the following bot: https://t.me/getmyid_bot
# Put your user id in the /bot/config/.env file as follows:
# dev_id=XXXXX

# Auto send delay in min
schedule_auto_send_delay: float = 10

# Status update delay in min
status_auto_update_delay: float = 10

# The following parameter sets logging level:
# ['AIOGRAM_DEBUG', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
# 'AIOGRAM_DEBUG' also print aiogram auto logs
console_log_level: str = 'AIOGRAM_DEBUG'
