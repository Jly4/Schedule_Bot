import asyncio

from main import bot
from bot.logs.log_config import custom_logger


async def retry_after(chat_id) -> None:
    """ notify user about this error and resend status message """
    from bot.utils.utils import del_msg_by_id
    from bot.utils.status import send_status
    custom_logger.info(chat_id)

    sent = 0
    while not sent:
        try:
            await asyncio.sleep(4)
            txt = 'Слишком быстро, телеграм ругается)'
            msg = await bot.send_message(chat_id, text=txt)
            await asyncio.sleep(5)
            await del_msg_by_id(chat_id, msg.message_id)
            await send_status(chat_id)
            sent = 1

        except Exception as e:
            continue

