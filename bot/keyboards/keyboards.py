from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger


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
    skb = InlineKeyboardBuilder()
    skb.button(text='Выбрать смену', callback_data='choose_change')

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

    skb.attach(kb)
    return skb.as_markup()


def choose_change() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    change_dict = {
        'class_change_1': 'Первая',
        'class_change_2': 'Вторая'
    }

    for change, text in change_dict.items():
        kb.button(text=text, callback_data=change)

    return kb.as_markup(resize_keyboard=False)


@logger.catch
def choose_class_letter(class_number) -> InlineKeyboardMarkup:
    from bot.utils.utils import school_classes_dict
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
        class_existed = f'{class_number + text}' in school_classes_dict.values()

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
            InlineKeyboardButton(text='Закрыть описание',
                                 callback_data='settings')
        ]
    ])
    return kb


def choose_color() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Цвет по умолчанию',
                                 callback_data='default_colour'),
            InlineKeyboardButton(text='Назад', callback_data='settings')
        ]
    ])
    return kb


def dev() -> InlineKeyboardMarkup:
    """keyboard for edit settings
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Mmm',
                                 callback_data='close_settings_callback'),
            InlineKeyboardButton(text='Назад', callback_data='close_settings')
        ]
    ])
    return kb
