import sys
import logging

from loguru import logger

from bot.configs import config


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = logger.level(record.levelname).name
        logger.log(level, record.getMessage())


# logging config
def loguru_config():
    log_level = config.console_log_level
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
        "DEBUG": "<blue>",
        "INFO": "<green>",
        "SUCCESS": "<green>",
        "WARNING": "<yellow>",
        "ERROR": "<red>",
        "CRITICAL": "<red>",
    }

    for level, color in level.items():
        logger.critical(f'<y>log level: <r>{level}</></>, <y>color: <r>{color}</></>')
        logger.level(level, color=color)

    # Log to file
    logger.add('bot/logs/bot.log',
               format=log_format,
               level='DEBUG',
               rotation='10 MB',
               compression='zip',
               enqueue=True,
               backtrace=True,
               diagnose=True,
               catch=True)

    # Start messages
    logger.opt(colors=True).info('<r>Bot started</>')
    logger.opt(colors=True).info(f'<y>log level: <r>{log_level}</></>')
    logger.opt(colors=True).info(f'<y>auto_schedule_delay = <r>'
                                 f'{config.auto_schedule_delay}</></>')
    logger.opt(colors=True).info(f'<y>auto_status_delay = <r>'
                                 f'{config.auto_status_delay}</></>')


"""
First example: Traceback
code:
    
    try:
        def zero_dev(a, b):
            res = a / b

        zero_dev(0, 0)
    except Exception as e:
        logger.opt(exception=True).info(f"An error occurred: {e}")


output:

2024-02-02 16:28:29.670 | INFO     | bot.logs.log_config  : loguru_config   : 48  - An error occurred: division by zero
Traceback (most recent call last):

      File "path", line 65, in <module>
        executor.start_polling(dp, skip_updates=False, relax=1)
        │        │             └ <aiogram.dispatcher.dispatcher.Dispatcher object at 0x000001B8FEFB7550>
        │        └ <function start_polling at 0x000001B8FFE5E700>
        └ <module 'aiogram.utils.executor' from 'C:\\Users\\user\\AppData\\Local\\pypoetry\\Cache\\virtualenvs\\schedule-bot-URf48MFE-p...
    
      File "path", line 45, in start_polling
        executor.start_polling(
        │        └ <function Executor.start_polling at 0x000001B8FFE71C60>
        └ <aiogram.utils.executor.Executor object at 0x000001B897E9B590>
      File "path", line 320, in start_polling
        loop.run_until_complete(self._startup_polling())
        │    │                  │    └ <function Executor._startup_polling at 0x000001B8FFE71F80>
        │    │                  └ <aiogram.utils.executor.Executor object at 0x000001B897E9B590>
        │    └ <function BaseEventLoop.run_until_complete at 0x000001B8FE47F6A0>
        └ <ProactorEventLoop running=True closed=False debug=False>
      File "path", line 640, in run_until_complete
        self.run_forever()
        │    └ <function ProactorEventLoop.run_forever at 0x000001B8FE54F600>
        └ <ProactorEventLoop running=True closed=False debug=False>
      File "path", line 321, in run_forever
        super().run_forever()
      File "path", line 607, in run_forever
        self._run_once()
        │    └ <function BaseEventLoop._run_once at 0x000001B8FE489440>
        └ <ProactorEventLoop running=True closed=False debug=False>
      File "path", line 1922, in _run_once
        handle._run()
        │      └ <function Handle._run at 0x000001B8FE3CEAC0>
        └ <Handle <TaskStepMethWrapper object at 0x000001B8982B1E10>()>
      File "path", line 80, in _run
        self._context.run(self._callback, *self._args)
        │    │            │    │           │    └ <member '_args' of 'Handle' objects>
        │    │            │    │           └ <Handle <TaskStepMethWrapper object at 0x000001B8982B1E10>()>
        │    │            │    └ <member '_callback' of 'Handle' objects>
        │    │            └ <Handle <TaskStepMethWrapper object at 0x000001B8982B1E10>()>
        │    └ <member '_context' of 'Handle' objects>
        └ <Handle <TaskStepMethWrapper object at 0x000001B8982B1E10>()>
    
      File "path", line 19, in run_bot
        await loguru_config()
              └ <function loguru_config at 0x000001B8FFEBD260>
    
    > File "path", line 49, in loguru_config
        zero_dev(0, 0)
        └ <function loguru_config.<locals>.zero_dev at 0x000001B8FE554E00>
    
      File "path", line 47, in zero_dev
        res = a / b
              │   └ 0
              └ 0
    
    ZeroDivisionError: division by zero


Second example: ignore depth

code:
    def wrapped_function():
        logger.opt(depth=0).info("Log message within the context of the parent function")

    wrapped_function() 
    
    def wrapped_function():
        logger.opt(depth=1).info("Log message within the context of the parent function")

    wrapped_function() 
    
    def wrapped_function():
        logger.opt(depth=2).info("Log message within the context of the parent function")

    wrapped_function() 
    
output:
    2024-02-02 16:30:03.110 | INFO     | bot.logs.log_config  : wrapped_function : 43  - Log message within the context of the parent function
                                                                ^^^^^^^^^^^^^^^
    2024-02-02 16:30:03.110 | INFO     | bot.logs.log_config  : loguru_config   : 50  - Log message within the context of the parent function
                                                               ^^^^^^^^^^^^^^^
    2024-02-02 16:30:03.111 | INFO     | __main__             : run_bot         : 19  - Log message within the context of the parent function
                                                               ^^^^^^^^^^^^^^^

"""
