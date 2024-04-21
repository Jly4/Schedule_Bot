from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.filters.filters import IsAdmin, IsDev
from bot.utils.colors import color_set_menu, set_bg_color
from bot.utils.utils import settings, del_msg_by_id, start_command
from bot.utils.utils import description, disable_bot
from bot.utils.dev_menu import suspend_date, suspend_bot, suspend_date_guide
from bot.utils.dev_menu import announce_guide, dev_settings, announce
from bot.utils.schedule import turn_schedule_pin, turn_deleting
from bot.utils.schedule import schedule_for_day
from bot.utils.school_classes import choose_class_letter, set_class
from bot.utils.school_classes import choose_class_number
from bot.utils.autosend_menu import turn_schedule, auto_send_menu, edit_threads
from bot.utils.states import ClassState

router = Router()

""" 
add admin filter to callbacks 

message handler demand user additional filter '(filter, IsAdmin()))'
otherwise it intercepts all messages
"""
router.callback_query.filter(IsAdmin())


""" bot commands handlers
"""


@router.message(Command('start'), IsAdmin())
async def start_msg(message: Message) -> None:
    await start_command(message)


@router.message(Command('disable'), IsAdmin())
async def disable_bot_msg(message: Message) -> None:
    await del_msg_by_id(message.chat.id, message.message_id, 'disable command')
    await disable_bot(message)  # start disable bot func


@router.message(Command('dev'), IsDev())
async def dev_msg(message: Message) -> None:
    await dev_settings(message)


@router.message(Command('announce'), IsDev())
async def dev_msg(message: Message) -> None:
    await announce(message)


@router.message(Command('suspend_date'), IsDev())
async def dev_msg(message: Message) -> None:
    await suspend_date(message)


""" color handlers
"""


@router.callback_query(F.data == 'color_menu')
async def color_set_menu_call(query: CallbackQuery) -> None:
    await color_set_menu(query)


@router.message(F.text.lower().startswith('set color '), IsAdmin())
async def set_color_msg(message: Message) -> None:
    await set_bg_color(message)


@router.callback_query(F.data.startswith('set color '))
async def set_color_call(query: CallbackQuery) -> None:
    await set_bg_color(query)


""" settings handlers
"""


@router.callback_query(F.data == 'settings')
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ClassState.set_class)
    await settings(query)


@router.callback_query(F.data == 'dev_settings')
async def settings_call(query: CallbackQuery) -> None:
    await dev_settings(query)


""" schedule handlers
"""


@router.callback_query(F.data == 'autosend')
async def turn_auto_schedule_call(query: CallbackQuery) -> None:
    await auto_send_menu(query)


@router.callback_query(F.data == 'turn_autosend')
async def turn_auto_schedule_call(query: CallbackQuery) -> None:
    await turn_schedule(query)


@router.callback_query(F.data == 'pin_schedule')
async def turn_pin_schedule_call(query: CallbackQuery) -> None:
    await turn_schedule_pin(query)


@router.callback_query(F.data == 'schedule_auto_delete')
async def turn_deleting_call(query: CallbackQuery) -> None:
    await turn_deleting(query)


@router.callback_query(F.data == 'edit_threads')
async def edit_threads_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ClassState.edit_threads)
    await choose_class_number(query.message.chat.id)


""" disable bot and description handlers
"""


@router.callback_query(F.data == 'disable_bot')
async def disable_bot_call(query: CallbackQuery) -> None:
    await disable_bot(query)


@router.callback_query(F.data == 'description')
async def description_call(query: CallbackQuery) -> None:
    await description(query.message.chat.id)


""" set class number, letter, and change handlers
"""


@router.callback_query(F.data == 'set_class')
async def set_class_call(query: CallbackQuery) -> None:
    await choose_class_number(query.message.chat.id)


@router.callback_query(F.data.startswith('class_number_'))
async def choose_class_letter_call(query: CallbackQuery) -> None:
    await choose_class_letter(query)


@router.callback_query(F.data.startswith('set_class_'), ClassState.choose_class)
async def set_class_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await schedule_for_day(query)


@router.callback_query(F.data.startswith('set_class_'), ClassState.edit_threads)
async def set_class_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_threads(query)


@router.callback_query(F.data.startswith('set_class_'))
async def set_class_call(query: CallbackQuery) -> None:
    await set_class(query)


""" Dev menu handlers
"""


@router.callback_query(F.data == 'suspend_bot', IsDev())
async def suspend_bot_call(query: CallbackQuery) -> None:
    await suspend_bot(query)


@router.callback_query(F.data == 'announce_guide', IsDev())
async def announce_guide_call(query: CallbackQuery) -> None:
    await announce_guide(query)


@router.callback_query(F.data == 'suspend_date_guide', IsDev())
async def suspend_date_guide_call(query: CallbackQuery) -> None:
    await suspend_date_guide(query)
