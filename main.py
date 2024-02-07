import asyncio

from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.logs.log_config import loguru_config
from bot.config.config_loader import token, dev_id

bot = Bot(token=token, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def start():
    try:
        # loop = asyncio.get_event_loop()
        # loop.create_task(run_bot())
        loguru_config()  # load loguru config

        from bot.handlers.user_handlers import router
        dp.include_router(router)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logger.opt(colors=True, exception=True).critical(f'<r>Dead: {e}</>')

        text = f'Бот завершил работу из-за ошибки: {str(e)}'
        asyncio.run(bot.send_message(dev_id, text=text))


if __name__ == '__main__':
    asyncio.run(start())





#     dp.register_callback_query_handler(auto_schedule_handler, text='auto_schedule_callback')
#     dp.register_callback_query_handler(pin_schedule_handler, text='pin_schedule_callback')
#     dp.register_callback_query_handler(disable_bot_callback_handler, text='disable_bot_callback')
#     dp.register_callback_query_handler(description_open_handler, text='description_callback')
#     dp.register_callback_query_handler(description_close_handler, text='description_close_callback')
#     dp.register_callback_query_handler(close_settings_handler, text='close_settings_callback')
#
#     # color callbacks
#     dp.register_callback_query_handler(set_color_menu_handler, text='set_colour_menu_callback')
#     dp.register_callback_query_handler(default_color_handler, text='default_colour_callback')
#     dp.register_message_handler(set_color_handler, lambda message: message.text.lower().startswith('set color '))
#
#     # choose class callbacks
#     dp.register_callback_query_handler(class_main_handler, text='choose_main_class_callback')
#     dp.register_callback_query_handler(change_main_handler, text='choose_main_change_callback')
#
#     dp.register_callback_query_handler(class_change_handler,
#                                        lambda c: c.data.startswith('school_change_callback_'))
#     dp.register_callback_query_handler(class_number_handler,
#                                        lambda c: c.data.startswith('school_class_number_callback_'))
#     dp.register_callback_query_handler(class_letter_handler,
#                                        lambda c: c.data.startswith('school_class_letter_callback_'))
