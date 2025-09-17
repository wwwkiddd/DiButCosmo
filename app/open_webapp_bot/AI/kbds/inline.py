from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder




# def mode_choice_btns(sizes: tuple[int] = (2,)):
#     keyboard = InlineKeyboardBuilder()
#     btns = {'Генерация изображений': 'pics',
#             'Текст': 'text'
#             }
#     for text, callback in btns.items():
#         keyboard.add(InlineKeyboardButton(text=text, callback_data=callback))
#     return keyboard.adjust(*sizes).as_markup()

class ImageCallBack(CallbackData, prefix='image'):
    prompt: str | None = None
    images: str | None = None



def get_callback_btns(*, btns: dict[str,str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, callback in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=callback))

    return keyboard.adjust(*sizes).as_markup()

kbd_tk = get_callback_btns(btns={
        '💰 Купить токены': 'pay',
        '🎯 Задания': 'challenge',
        'Промокод': 'user_promo_code'})