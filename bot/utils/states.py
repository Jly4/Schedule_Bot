from aiogram.fsm.state import StatesGroup, State


class MainStates(StatesGroup):
    # open settngs
    settings = State()

    # open autosend menu
    autosend_menu = State()

    """ color states """
    # open bg colors menu
    bg_color = State()

    # open text colors menu
    text_color = State()

    # open lessons colors menu
    lessons_color = State()

    # open lessons colors menu
    lessons_color_group = State()

    # open lessons colors menu
    lessons_color_lesson = State()

    """ description states """
    # open any description in description menu
    description = State()

    # description initiated from autosend menu
    descript_autosend = State()

    """ class states """
    # edit classes in autosend menu
    edit_threads = State()

    # chose class for get schedule
    choose_class = State()

    """ dev states """
    # open suspend date in dev menu
    suspend_date = State()

    # open announce menu in dev menu
    announce = State()
