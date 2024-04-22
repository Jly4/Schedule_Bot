from aiogram.fsm.state import StatesGroup, State


class MainStates(StatesGroup):
    set_class = State()
    edit_threads = State()
    choose_class = State()
    autosend_menu = State()
    description = State()
