from aiogram.fsm.state import StatesGroup, State


class MainStates(StatesGroup):
    # open settngs
    settings = State()

    # edit classes in autosend menu
    edit_threads = State()

    # chose class for get schedule
    choose_class = State()

    # open any description in description menu
    description = State()

    # open autosend menu
    autosend_menu = State()

    # description initiated from autosend menu
    descript_autosend = State()
