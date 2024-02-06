import asyncio

from aiogram import Dispatcher
from aiogram.utils import executor

from bot.configs import config
from bot.init_bot import bot, dp
from bot.logs.log_config import loguru_config
from bot.utils.status import auto_status
from bot.utils.schedule import auto_schedule
from bot.databases.database import bot_database as db
from bot.handlers.user_handlers import register_user_handlers
from loguru import logger


async def run_bot():
    register_handler(dp)  # register handlers

    await db.database_init()  # db initialising
    logger.opt(colors=True).info('<y>database inited</>')

    # создаем список айди в базе
    user_id_list = await db.get_user_id_list()
    logger.opt(colors=True).debug(f'<y>user_id_list: <cyan>{user_id_list}</></>\n')

    # Если база данных не пуста
    if user_id_list:
        # цикл по пользователям
        for chat_id in user_id_list:
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


# register handlers
def register_handler(dp: Dispatcher) -> None:
    register_user_handlers(dp)


# Сообщение о завершении работы
async def send_error_message(error):
    logger.opt(colors=True).error(f'<r>Bot was crashed with error:\n{e}</>')

    await bot.send_message(config.dev_id, text=f'Бот завершил работу из-за ошибки: {str(error)}')


if __name__ == '__main__':
    loguru_config()  # load loguru config

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(run_bot())
        executor.start_polling(dp, skip_updates=False, relax=1)
    except Exception as e:
        logger.opt(exception=True).critical(f'Dead: {e}')
        # Отправка уведомления в случае ошибки
        asyncio.run(send_error_message(e))
