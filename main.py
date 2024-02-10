import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config.config_loader import token


bot = Bot(token=token, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def start():
    from bot.utils.utils import run_bot_tasks
    await run_bot_tasks()
    from bot.handlers import admin_handlers, user_handlers
    dp.include_routers(
        user_handlers.router,
        admin_handlers.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(start())
