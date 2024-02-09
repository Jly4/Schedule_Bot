import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config.config_loader import token

bot = Bot(token=token, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def start():
    try:
        from bot.utils.utils import run_bot_tasks
        await run_bot_tasks()

        from bot.handlers.user_handlers import router
        dp.include_router(router)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
