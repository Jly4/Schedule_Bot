import sys
import logging

from loguru import logger

from bot.config.config import console_log_level


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        msg = (f'<white>{"--AIOGRAM--".center(23)}</> <r>|'
               f'</> <y>{record.getMessage()}</>')
        logger.opt(depth=3, colors=True).log(level, msg)


# logging config
def loguru_config():
    log_level = console_log_level
    logger.level("AIOGRAM_DEBUG", no=8)

    if log_level == 'AIOGRAM_DEBUG':
        logging.getLogger('aiogram').setLevel(logging.DEBUG)
        logging.getLogger('aiogram').addHandler(InterceptHandler())
        logging.getLogger('asyncio').setLevel(logging.DEBUG)
        logging.getLogger('asyncio').addHandler(InterceptHandler())

    # Delete default logger
    logger.remove()

    # Log format
    log_format = "<yellow>{time:YYYY-MM-DD HH:mm:ss.SSS}</yellow> | " \
                 "<lvl>{level: <8}</lvl> | <magenta>{name: >26}</magenta> : " \
                 "<lvl>{function: >20}</lvl>: <yellow>{line: <3}</yellow> - " \
                 "<bold><green>{message}</green></bold>"

    # Пересоздаем обработчик
    logger.add(sink=sys.stdout,
               colorize=True,
               backtrace=True,
               diagnose=True,
               catch=True,
               format=log_format,
               level=log_level
               )

    # add custom level colors
    level = {
        "TRACE": "<cyan>",
        "INFO": "<green>",
        "SUCCESS": "<green>",
        "WARNING": "<yellow>",
        "ERROR": "<red>"
    }

    for level, color in level.items():
        logger.level(level, color=color)

    # Log to file
    logger.add('bot/logs/bot.log',
               format=log_format,
               level='DEBUG',
               rotation='100 MB',
               compression='zip',
               retention="30 days",
               enqueue=True,
               backtrace=True,
               diagnose=True,
               catch=True)

    # Start messages
    logger.opt(colors=True).info('<r>Bot started</>')
    logger.opt(colors=True).info(f'<y>log level: <r>{log_level}</></>')


class CustomLogger:
    @staticmethod
    def opt_args(exception: bool = False, depth: int = 1) -> dict:
        if exception:
            return {"colors": True, "depth": depth, "exception": True}
        else:
            return {"colors": True, "depth": depth}

    @staticmethod
    def add_chat_id(chat_id: int, msg: str) -> str:
        if not msg:
            msg = '<y>started</>'

        log = f"""<y>chat_id: <r>{f"{chat_id}".rjust(15)} | </></>{msg}"""
        return log

    def debug(self, chat_id: int = None, msg: str = '', **kwargs) -> None:
        logger.opt(**self.opt_args(**kwargs)).debug(self.add_chat_id(
            chat_id, msg
        ))

    def info(self, chat_id: int = None, msg: str = '', **kwargs) -> None:
        logger.opt(**self.opt_args(**kwargs)).info(self.add_chat_id(
            chat_id, msg
        ))

    def warning(self, chat_id: int = None, msg: str = '', **kwargs) -> None:
        logger.opt(**self.opt_args(**kwargs)).warning(self.add_chat_id(
            chat_id, msg
        ))

    def error(self, chat_id: int = None, msg: str = '', **kwargs) -> None:
        logger.opt(**self.opt_args(**kwargs)).error(self.add_chat_id(
            chat_id, msg
        ))

    def critical(self, chat_id: int = None, msg: str = '', **kwargs) -> None:
        logger.opt(**self.opt_args(**kwargs)).critical(self.add_chat_id(
            chat_id, msg)
        )


custom_logger = CustomLogger()
