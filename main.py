import asyncio

from loguru import logger

from bot.init_bot import bot, dp
from bot.logs.log_config import loguru_config
from bot.utils.status import auto_status
from bot.utils.schedule import auto_schedule
from bot.db.database import bot_database as db
from bot.handlers.user_handlers import router


async def run_bot():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)

    loguru_config()  # load loguru config

    await db.database_init()  # db initialising
    logger.opt(colors=True).info('<y>database inited</>')

    # get chat_id list
    chat_id_list = await db.get_user_id_list()
    logger.opt(colors=True).debug(f'<y>user_id_list: '
                                  f'<cyan>{chat_id_list}</></>\n')

    if chat_id_list:  # if chat_id not empty
        for chat_id in chat_id_list:
            # get user settings
            auto_send_status = await db.get_db_data(chat_id, 'bot_enabled')
            auto_send_schedule = await db.get_db_data(chat_id, 'auto_schedule')

            # проверяем включено ли у пользователя автоматическое получение статуса
            if auto_send_status:
                asyncio.create_task(auto_status(chat_id), name=f'{chat_id} auto_status')

                if auto_send_schedule:
                    logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>auto_schedule: <r>enabled</></>')
                    logger.opt(colors=True).info('')
                    asyncio.create_task(auto_schedule(chat_id), name=f'{chat_id} auto_schedule')
                else:
                    logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>auto_schedule: <r>disabled</></>')
                    logger.opt(colors=True).info('')
            else:
                logger.opt(colors=True).info(f'<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </>Bot disabled</>')
                logger.opt(colors=True).info('')

            """ если время последней активности больше месяца назад, удаляем пользователя
            """
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        # loop = asyncio.get_event_loop()
        # loop.create_task(run_bot())
        asyncio.run(run_bot())
    except Exception as e:
        logger.opt(exception=True).critical(f'Dead: {e}')
        # Отправка уведомления в случае ошибки
        asyncio.run(send_error_message(e))
