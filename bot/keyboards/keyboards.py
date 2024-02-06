from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

def main() -> InlineKeyboardMarkup:
    mkb = InlineKeyboardBuilder()

    buttons: dict = {
        'update_schedule': 'Получить расписание',
        'settings': 'Настройки'
    }

    for callback, text in buttons.items():
        mkb.button(text=text, callback_data=callback).adjust(2)

    return mkb.as_markup()


def settings() -> InlineKeyboardMarkup:
    skb = InlineKeyboardBuilder()

    buttons = {
        'choose_class_main': 'Настроить класс',
        'auto_schedule': 'Автоматическое обновление',
        'pin_schedule': 'Закреплять расписание',
        'color_menu': 'Цвет фона расписания',
        'disable_bot': 'Отключить бота',
        'description': 'Информация о боте',
        'settings': 'Закрыть настройки'
    }

    for callback, text in buttons.items():
        skb.button(text=text, callback_data=callback).adjust(2)

    return skb.as_markup()


def choose_school_change() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Первая смена', callback_data='school_change_callback_1'),
            InlineKeyboardButton(text='Вторая смена', callback_data='school_change_callback_2')
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data='settings_callback')
        ]
    ])
    return kb


def choose_school_class_number() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
         'school_class_number_1': '1',
         'school_class_number_2': '2',
         'school_class_number_3': '3',
         'school_class_number_4': '4',
         'school_class_number_5': '5',
         'school_class_number_6': '6',
         'school_class_number_7': '7',
         'school_class_number_8': '8',
         'school_class_number_9': '9',
         'school_class_number_10': '10',
         'school_class_number_11': '11',
         'settings': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(3)

    return kb.as_markup()

@logger.catch
def choose_school_class_letter(class_number) -> InlineKeyboardMarkup:
    from bot.utils.utils import school_classes_dict
    kb = InlineKeyboardBuilder()

    buttons = {
        'school_class_letter_a': 'а',
        'school_class_letter_b': 'б',
        'school_class_letter_v': 'в',
        'school_class_letter_g': 'г',
        'school_class_letter_d': 'д',
        'school_class_letter_e': 'е',
        'school_class_letter_j': 'ж',
        'school_class_letter_z': 'з'
    }

    for callback, text in buttons.items():
        class_existed = f'{class_number+text}' in school_classes_dict.values()

        if class_existed:
            kb.button(text=text, callback_data=callback).adjust(3)

    kb.button(text='Назад', callback_data='choose_class_main').adjust(3)
    return kb.as_markup()


def description() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='@yosqe', url="https://t.me/Yosqe"),
            InlineKeyboardButton(text='Закрыть описание', callback_data='description_close_callback')
        ]
    ])
    return kb


def choose_color() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Цвет по умолчанию', callback_data='default_colour_callback'),
            InlineKeyboardButton(text='Назад', callback_data='settings')
        ]
    ])
    return kb


def dev() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Mmm', callback_data='close_settings_callback'),
            InlineKeyboardButton(text='Назад', callback_data='close_settings')
        ]
    ])
    return kb

