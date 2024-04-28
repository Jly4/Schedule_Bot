from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from bot.config.config import classes_dict, dev_id


def main() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    buttons: dict = {
        'schedule_for_menu': 'Расписание',
        'settings': 'Настройки'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def back() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='Назад', callback_data='back_button').adjust(2)

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
            callback = f'{callback[:12]}_cls_{callback[17:]}_{cls}'
        kb.button(text=text, callback_data=callback).adjust(3)

    if not cls:
        kb.button(text='Другой класс', callback_data='choose_class')
        kb.button(text='Назад', callback_data='status').adjust(3)
    else:
        kb.button(text='Назад', callback_data='schedule_for_menu').adjust(3)

    return kb.as_markup()


def settings(*user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'set_class': 'Изменить класс',
        'autosend': 'Автообновление',
        'pin_schedule': 'Закреплять расписание',
        'schedule_auto_delete': 'Удалять предыдущее расписание',
        'color_menu': 'Настройки цвета',
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
        'back_button': 'Назад'
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
    kb = InlineKeyboardBuilder()

    buttons = {
        'autosend_descript': 'Автообновление',
        'buttons_descript': 'Описание кнопок',
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback)

    kb.button(text='Поддержка', url='https://t.me/Yosqe')
    kb.button(text='Назад', callback_data='back_button').adjust(2)
    return kb.as_markup()


def dev_settings(menu: bool = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'announce': 'Рассылка',
        'suspend_date': 'Даты приостановки',
        'suspend_bot': 'Приостановить бота',
    }

    if menu:
        for callback, text in buttons.items():
            kb.button(text=text, callback_data=callback).adjust(2)

    kb.button(text='Назад', callback_data='back_button').adjust(2)

    return kb.as_markup()


def auto_update_settings() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'turn_autosend': 'Вкл/Выкл',
        'edit_threads': 'Добавить/Удалить класс',
        'autosend_descript': 'Описание работы',
        'back_button': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


""" color keyboards
"""


def color_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'bg_color_menu': 'Цвет фона',
        'text_color_menu': 'Цвет текста',
        'back_button': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def text_color_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'set_color_000,000,000_Черный': 'Черный',
        'set_color_256,256,256_Белый': 'Белый',
        'set_color_000,256,000_Зеленый': 'Зеленый',
        'lessons_color': 'Цвета предметов',
        'back_button': 'Назад',
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(3)

    return kb.as_markup()


def lessons_color() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'lessons_color_group': 'Редакт. группы',
        'lessons_color_choose': 'Редакт. предметы',
        'back_button': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(2)

    return kb.as_markup()


def choose_color_group(groups) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for group in groups:
        callback = f'color_group_{group}'
        kb.button(text=group, callback_data=callback).adjust(2)

    kb.button(text='Назад', callback_data='back_button').adjust(2)

    return kb.as_markup()


def choose_bg_color() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    buttons = {
        'set_color_255,204,153_Оранжевый': 'Оранжевый',
        'set_color_255,255,143_Желтый': 'Желтый',
        'set_color_192,255,192_Зеленый': 'Зеленый',
        'set_color_204,255,255_Голубой': 'Голубой',
        'set_color_255,204,255_Розовый': 'Розовый',
        'set_color_192,192,255_Фиолетовый': 'Фиолетовый',
        'set_color_000,000,000_Черный': 'Черный',
        'set_color_256,256,256_Белый': 'Белый',
        'back_button': 'Назад'
    }

    for callback, text in buttons.items():
        kb.button(text=text, callback_data=callback).adjust(3)

    return kb.as_markup()
