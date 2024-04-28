from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.filters.filters import IsAdmin, IsDev
from bot.utils.colors import color_menu, bg_color_menu, text_color_menu
from bot.utils.colors import set_color, lessons_color, lessons_color_choose
from bot.utils.colors import lessons_color_group, lessons_color_lesson
from bot.utils.colors import edit_lessons, edit_groups
from bot.utils.utils import settings, del_msg_by_id, start_command
from bot.utils.utils import disable_bot
from bot.utils.description import Description
from bot.utils.dev_menu import suspend_date, suspend_bot, set_suspend_date
from bot.utils.dev_menu import dev_settings, announce, send_announce
from bot.utils.schedule import turn_schedule_pin, turn_deleting
from bot.utils.schedule import schedule_for_day
from bot.utils.school_classes import choose_class_letter, set_class
from bot.utils.school_classes import choose_class_number
from bot.utils.autosend_menu import turn_schedule, auto_send_menu, edit_threads
from bot.utils.states import MainStates

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
    await dev_settings(message, edit=0)


""" color handlers
"""

""" callback handlers """


@router.callback_query(F.data == 'color_menu')
async def color_menu_call(query: CallbackQuery) -> None:
    await color_menu(query)


@router.callback_query(F.data == 'bg_color_menu')
async def bg_color_menu_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.bg_color)
    await bg_color_menu(query)


@router.callback_query(F.data == 'text_color_menu')
async def text_color_menu_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.text_color)
    await text_color_menu(query)


@router.callback_query(F.data == 'lessons_color')
async def lessons_color_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.lessons_color)
    await lessons_color(query)


@router.callback_query(F.data == 'lessons_color_group')
async def lessons_color_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.lessons_color_group)
    await lessons_color_group(query)


@router.callback_query(F.data == 'lessons_color_choose')
async def lesson_color_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.lessons_color_lesson)
    await lessons_color_choose(query)


@router.callback_query(F.data.startswith('color_group_'))
async def lesson_color_call(query: CallbackQuery, state: FSMContext) -> None:
    prefix = 'color_group_'
    await state.update_data(lessons_color_lesson=query.data[len(prefix):])
    await lessons_color_lesson(query)


@router.callback_query(F.data.startswith('set_color_'), MainStates.bg_color)
async def set_bg_color_call(query: CallbackQuery) -> None:
    await set_color(query, target='bg')


@router.callback_query(F.data.startswith('set_color_'), MainStates.text_color)
async def set_bg_color_call(query: CallbackQuery) -> None:
    await set_color(query, target='text')

""" message handlers """


@router.message(MainStates.lessons_color_group, IsAdmin())
async def edit_groups_msg(message: Message) -> None:
    await edit_groups(message)


@router.message(MainStates.lessons_color_lesson, IsAdmin())
async def edit_lessons_msg(message: Message, state: FSMContext) -> None:
    group = await state.get_data()
    await edit_lessons(message, group['lessons_color_lesson'])


@router.message(MainStates.text_color, IsAdmin())
async def set_color_msg(message: Message, state: FSMContext) -> None:
    if await set_color(message, target='text'):
        await state.clear()


@router.message(MainStates.bg_color, IsAdmin())
async def set_color_msg(message: Message, state: FSMContext) -> None:
    if await set_color(message, target='bg'):
        await state.clear()


""" settings handlers
"""


@router.callback_query(F.data == 'settings')
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.settings)
    await settings(query)


""" schedule handlers
"""


@router.callback_query(F.data == 'autosend')
async def autosend_menu_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.autosend_menu)
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
    await state.set_state(MainStates.edit_threads)
    await choose_class_number(query.message.chat.id)


""" disable bot and description handlers
"""


@router.callback_query(F.data == 'disable_bot')
async def disable_bot_call(query: CallbackQuery) -> None:
    await disable_bot(query)


@router.callback_query(F.data == 'description')
async def description_call(query: CallbackQuery) -> None:
    await Description.main_descript(query.message.chat.id)


@router.callback_query(F.data == 'buttons_descript')
async def description_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.description)
    await Description.buttons_descript(query.message.chat.id)


@router.callback_query(F.data == 'autosend_descript', MainStates.autosend_menu)
async def description_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.descript_autosend)
    await Description.autosend_descript(query.message.chat.id)


@router.callback_query(F.data == 'autosend_descript')
async def description_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.description)
    await Description.autosend_descript(query.message.chat.id)


""" set class number, letter, and change handlers
"""


@router.callback_query(F.data == 'set_class')
async def set_class_call(query: CallbackQuery) -> None:
    await choose_class_number(query.message.chat.id)


@router.callback_query(F.data.startswith('class_number_'))
async def choose_class_letter_call(query: CallbackQuery) -> None:
    await choose_class_letter(query)


@router.callback_query(F.data.startswith('set_class_'), MainStates.choose_class)
async def set_class_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await schedule_for_day(query)


@router.callback_query(F.data.startswith('set_class_'), MainStates.edit_threads)
async def set_class_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_threads(query)


@router.callback_query(F.data.startswith('set_class_'))
async def set_class_call(query: CallbackQuery) -> None:
    await set_class(query)


""" Dev menu handlers
"""


@router.callback_query(F.data == 'dev_settings')
async def settings_call(query: CallbackQuery) -> None:
    await dev_settings(query)


@router.callback_query(F.data == 'suspend_bot', IsDev())
async def suspend_bot_call(query: CallbackQuery) -> None:
    await suspend_bot(query)


@router.callback_query(F.data == 'announce', IsDev())
async def announce_call(query: CallbackQuery, state=FSMContext) -> None:
    await state.set_state(MainStates.announce)
    await announce(query)


@router.callback_query(F.data == 'suspend_date', IsDev())
async def suspend_date_call(query: CallbackQuery, state=FSMContext) -> None:
    await state.set_state(MainStates.suspend_date)
    await suspend_date(query)


@router.message(MainStates.announce, IsDev())
async def send_announce_call(message: Message, state: FSMContext) -> None:
    await send_announce(message)
    await state.clear()


@router.message(MainStates.suspend_date, IsDev())
async def set_suspend_date_call(message: Message, state: FSMContext) -> None:
    if await set_suspend_date(message):
        await state.clear()


""" back_button handlers
"""


@router.callback_query(F.data == 'back_button', MainStates.descript_autosend)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await auto_send_menu(query)


@router.callback_query(F.data == 'back_button', MainStates.description)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await Description.main_descript(query.message.chat.id)


@router.callback_query(F.data == 'back_button', MainStates.edit_threads)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await auto_send_menu(query)


@router.callback_query(F.data == 'back_button', MainStates.choose_class)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await schedule_for_day(query)


@router.callback_query(F.data == 'back_button', MainStates.announce)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await dev_settings(query)


@router.callback_query(F.data == 'back_button', MainStates.suspend_date)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await dev_settings(query)


@router.callback_query(F.data == 'back_button', MainStates.bg_color)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await color_menu(query)


@router.callback_query(F.data == 'back_button', MainStates.text_color)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await color_menu(query)


@router.callback_query(F.data == 'back_button', MainStates.lessons_color)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.text_color)
    await text_color_menu(query)


@router.callback_query(F.data == 'back_button', MainStates.lessons_color_group)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.lessons_color)
    await lessons_color(query)


@router.callback_query(F.data == 'back_button', MainStates.lessons_color_lesson)
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.lessons_color)
    await lessons_color(query)


@router.callback_query(F.data == 'back_button')
async def settings_call(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MainStates.settings)
    await settings(query)
