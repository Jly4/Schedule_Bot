from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config.config import classes_dict, dev_id


def main() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    buttons: dict = {
        'schedule_for_day_menu': 'Расписание',
        'settings': 'Настройки'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def schedule_for_day(cls=0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    buttons = {
        'schedule_for_day_0': 'Понедельник',
        'schedule_for_day_1': 'Вторник',
        'schedule_for_day_2': 'Среда',
        'schedule_for_day_3': 'Четверг',
        'schedule_for_day_4': 'Пятница',
        'schedule_for_day_5': 'Суббота',
    }
    for callback, text in buttons.items():
        if cls:
            callback += f'_{cls}'
        kb.button(text=text, callback_data=callback).adjust(3)

    if not cls:
        kb.button(text='Другой класс', callback_data='choose_class')
        kb.button(text='Назад', callback_data='status').adjust(3)
    else:
        kb.button(text='Назад', callback_data='schedule_for_day_menu').adjust(3)

    return kb.as_markup()


def settings(*user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'set_class': 'Изменить класс',
        'autosend': 'Обновление расписания',
        'pin_schedule': 'Закреплять расписание',
        'color_menu': 'Изменить цвет расписания',
        'schedule_auto_delete': 'Удалять предыдущее расписание',
        'disable_bot': 'Отключить бота',
        'description': 'Информация о боте',
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    if dev_id == str(*user_id):
        kb.button(text='Dev', callback_data='dev_settings').adjust(2)

    kb.button(text='Закрыть настройки', callback_data='status').adjust(2)

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
        'status': 'Назад'
    }
    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(3)

    return kb.as_markup()


def choose_class_letter(class_number) -> InlineKeyboardMarkup:
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
            kb.button(text=text, callback_data=callback).adjust(3)

    kb.button(text='Назад', callback_data='set_class').adjust(3)
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
        'set color 255,204,153 Оранжевый': 'Оранжевый',
        'set color 255,255,143 желтый': 'Желтый',
        'set color 192,255,192 зеленый': 'Зеленый',
        'set color 204,255,255 голубой': 'Голубой',
        'set color 255,204,255 розовый': 'Розовый',
        'set color 192,192,255 фиолетовый': 'Фиолетовый',
        'set color 256,256,256 Белый': 'Белый',
        'settings': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(3)

    return kb.as_markup()


def dev_settings() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'announce_guide': 'Рассылка',
        'suspend_date_guide': 'Даты приостановки',
        'suspend_bot': 'Приостановить бота',
        'settings': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def auto_update_settings() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'turn_autosend': 'Вкл/Выкл',
        'edit_threads': 'Добавить/Удалить класс',
        'settings': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()

