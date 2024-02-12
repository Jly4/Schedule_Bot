from aiogram import Router, F, types
from aiogram.filters import Command

from bot.keyboards import keyboards as kb

from bot.utils.status import send_status
from bot.filters.filters import IsAdmin
from bot.utils.colors import color_set_menu, set_schedule_bg_color
from bot.utils.utils import settings, del_msg_by_id, start_command
from bot.utils.utils import disable_bot
from bot.utils.schedule import turn_schedule_pin, turn_schedule, turn_deleting
from bot.utils.school_classes import choose_class, set_class_number, set_class

router = Router()

""" add admin filter to file """
router.callback_query.filter(IsAdmin())
router.message.filter(IsAdmin())


""" bot commands handlers
"""


@router.message(Command('start'))
async def start_msg(message: types.Message) -> None:
    await start_command(message)


@router.message(Command('disable'))
async def disable_bot_msg(message: types.Message) -> None:
    await del_msg_by_id(message.chat.id, message.message_id, 'disable command')
    await disable_bot(message)  # start disable bot func


""" color handlers
"""


@router.callback_query(F.data == 'color_menu')
async def color_set_menu_call(callback_query: types.CallbackQuery) -> None:
    await color_set_menu(callback_query)


@router.message(F.text.lower().startswith('set color '))
async def set_color_msg(message: types.Message) -> None:
    await set_schedule_bg_color(message)


@router.callback_query(F.data.startswith('set color '))
async def set_color_call(callback_query: types.CallbackQuery) -> None:
    await set_schedule_bg_color(callback_query)


""" settings handlers
"""


@router.callback_query(F.data == 'settings')
async def settings_call(callback_query: types.CallbackQuery) -> None:
    await settings(callback_query.message.chat.id)


""" schedule handlers
"""


@router.callback_query(F.data == 'schedule_auto_send')
async def turn_auto_schedule_call(callback_query: types.CallbackQuery) -> None:
    await turn_schedule(callback_query)


@router.callback_query(F.data == 'pin_schedule')
async def turn_pin_schedule_call(callback_query: types.CallbackQuery) -> None:
    await turn_schedule_pin(callback_query)


@router.callback_query(F.data == 'schedule_auto_delete')
async def turn_deleting_call(callback_query: types.CallbackQuery) -> \
        None:
    await turn_deleting(callback_query)


""" disable bot and description handlers
"""


@router.callback_query(F.data == 'disable_bot')
async def disable_bot_call(callback_query: types.CallbackQuery) -> None:
    await disable_bot(callback_query)


@router.callback_query(F.data == 'description')
async def description_call(callback_query: types.CallbackQuery) -> None:
    await send_status(chat_id=callback_query.message.chat.id,
                      text='Вопросы и предложения по кнопке ниже:',
                      reply_markup=kb.description())


""" set class number, letter, and change handlers
"""


@router.callback_query(F.data == 'choose_class')
async def choose_class_call(callback_query: types.CallbackQuery) -> None:
    await choose_class(callback_query.message.chat.id)


@router.callback_query(F.data.startswith('class_number_'))
async def class_number_call(callback_query: types.CallbackQuery) -> None:
    await set_class_number(callback_query)


@router.callback_query(F.data.startswith('set_class_'))
async def set_class_call(callback_query: types.CallbackQuery) -> None:
    await set_class(callback_query)
