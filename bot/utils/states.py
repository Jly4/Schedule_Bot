from aiogram.fsm.state import StatesGroup, State


class ClassState(StatesGroup):
    set_class = State()
    edit_threads = State()
    choose_class = State()


class DescriptionState(StatesGroup):
    autosend_menu = State()
    description = State()
