from aiogram.fsm.state import StatesGroup, State


class ClassState(StatesGroup):
    set_class = State()
    choose_class = State()
