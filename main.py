import asyncio

from aiogram import Bot, Dispatcher

from bot.config.config import token


bot = Bot(token=token)
dp = Dispatcher()


async def start():
    from bot.handlers import admin_handlers, user_handlers
    from bot.utils.utils import run_bot_tasks

    dp.include_routers(
        user_handlers.router,
        admin_handlers.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(run_bot_tasks())
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(start())
