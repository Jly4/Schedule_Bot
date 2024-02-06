from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# основная инлайн клавиатура
def main_keyboard() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    mkb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Получить расписание', callback_data='send_schedule_callback')
        ],
        [
            InlineKeyboardButton('Настройки', callback_data='settings_callback')
        ]
    ])
    return mkb


# инлайн клавиатура настроек
def settings() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    skb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Настроить класс', callback_data='choose_main_class_callback'),
            InlineKeyboardButton('Автоматическое обновление', callback_data='auto_schedule_callback')
        ],
        [
            InlineKeyboardButton('Закреплять расписание', callback_data='pin_schedule_callback'),
            InlineKeyboardButton('Цвет фона расписания', callback_data='set_colour_menu_callback')
        ],
        [
            InlineKeyboardButton('Отключить бота', callback_data='disable_bot_callback'),
            InlineKeyboardButton('Информация о боте', callback_data='description_callback')
        ],
        [
            InlineKeyboardButton('Закрыть настройки', callback_data='close_settings_callback')
        ]
    ])
    return skb


def choose_school_change() -> InlineKeyboardMarkup:
    """keyboard for choose school change
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Первая смена', callback_data='school_change_callback_1'),
            InlineKeyboardButton('Вторая смена', callback_data='school_change_callback_2')
        ],
        [
            InlineKeyboardButton('Назад', callback_data='settings_callback')
        ]
    ])
    return kb


def choose_school_class_number() -> InlineKeyboardMarkup:
    """keyboard for choose class number
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Выбрать смену', callback_data='choose_main_change_callback')
        ],
        [
            InlineKeyboardButton('1', callback_data='school_class_number_callback_1'),
            InlineKeyboardButton('2', callback_data='school_class_number_callback_2'),
            InlineKeyboardButton('3', callback_data='school_class_number_callback_3')
        ],
        [
            InlineKeyboardButton('4', callback_data='school_class_number_callback_4'),
            InlineKeyboardButton('5', callback_data='school_class_number_callback_5'),
            InlineKeyboardButton('6', callback_data='school_class_number_callback_6')
        ],
        [
            InlineKeyboardButton('7', callback_data='school_class_number_callback_7'),
            InlineKeyboardButton('8', callback_data='school_class_number_callback_8'),
            InlineKeyboardButton('9', callback_data='school_class_number_callback_9')
        ],
        [
            InlineKeyboardButton('10', callback_data='school_class_number_callback_10'),
            InlineKeyboardButton('11', callback_data='school_class_number_callback_11'),
            InlineKeyboardButton('Назад', callback_data='settings_callback'),
        ]
    ])
    return kb


# инлайн клавиатура настроек
def choose_school_class_letter() -> InlineKeyboardMarkup:
    """keyboard for choose class letter
    """
    from bot.utils.utils import school_classes_dict


    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('a', callback_data='school_class_letter_callback_a'),
            InlineKeyboardButton('б', callback_data='school_class_letter_callback_b'),
            InlineKeyboardButton('в', callback_data='school_class_letter_callback_v')
        ],
        [
            InlineKeyboardButton('г', callback_data='school_class_letter_callback_g'),
            InlineKeyboardButton('д', callback_data='school_class_letter_callback_d'),
            InlineKeyboardButton('е', callback_data='school_class_letter_callback_e')
        ],
        [
            InlineKeyboardButton('ж', callback_data='school_class_letter_callback_j'),
            InlineKeyboardButton('з', callback_data='school_class_letter_callback_z'),
            InlineKeyboardButton('Назад', callback_data='settings_callback')
        ]
    ])
    return kb


# инлайн клавиатура настроек
def description() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('@yosqe', url="https://t.me/Yosqe"),
            InlineKeyboardButton('Закрыть описание', callback_data='description_close_callback')
        ]
    ])
    return kb


# инлайн клавиатура настроек
def choose_color() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Цвет по умолчанию', callback_data='default_colour_callback'),
            InlineKeyboardButton('Назад', callback_data='settings_callback')
        ]
    ])
    return kb


# инлайн клавиатура настроек
def dev() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Mmm', callback_data='close_settings_callback'),
            InlineKeyboardButton('Назад', callback_data='close_settings_callback')
        ]
    ])
    return kb

