from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.logs.log_config import custom_logger


def main() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons: dict = {
        'update_schedule': 'Получить расписание',
        'settings': 'Настройки'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def settings() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'choose_class': 'Настроить класс',
        'schedule_auto_send': 'Автоматическое обновление',
        'pin_schedule': 'Закреплять расписание',
        'color_menu': 'Цвет фона расписания',
        'disable_bot': 'Отключить бота',
        'description': 'Информация о боте',
        'status': 'Закрыть настройки'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def choose_class_number() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    buttons = {
        'class_number_1': '1',
        'class_number_2': '2',
        'class_number_3': '3',
        'class_number_4': '4',
        'class_number_5': '5',
        'class_number_6': '6',
        'class_number_7': '7',
        'class_number_8': '8',
        'class_number_9': '9',
        'class_number_10': '10',
        'class_number_11': '11',
        'settings': 'Назад'
    }
    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(3)

    return kb.as_markup()


def choose_class_letter(class_number) -> InlineKeyboardMarkup:
    from bot.utils.utils import classes_dict
    kb = InlineKeyboardBuilder()

    buttons = {
        'class_letter_a': 'а',
        'class_letter_b': 'б',
        'class_letter_v': 'в',
        'class_letter_g': 'г',
        'class_letter_d': 'д',
        'class_letter_e': 'е',
        'class_letter_j': 'ж',
        'class_letter_z': 'з'
    }

    for callback, text in buttons.items():
        button_prefix = 'class_letter_'
        school_class = callback[len(button_prefix):] + class_number
        class_existed = f'{school_class}' in classes_dict.keys()

        if class_existed:
            callback = f'set_class_{school_class}'
            custom_logger.critical(callback)
            kb.button(text=text, callback_data=callback).adjust(3)

    kb.button(text='Назад', callback_data='choose_class').adjust(3)
    return kb.as_markup()


def description() -> InlineKeyboardMarkup:

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='@yosqe', url="https://t.me/Yosqe"),
            InlineKeyboardButton(text='Назад', callback_data='settings')
        ]
    ])
    return kb


def choose_color() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'default_colour': 'Цвет по умолчанию',
        'settings': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def dev() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='...', callback_data='status'),
            InlineKeyboardButton(text='Назад', callback_data='status')
        ]
    ])
    return kb
