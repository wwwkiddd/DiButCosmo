from aiogram.types import KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_keyboard(
        *btns: str,
        placeholder: str = None,
        request_contact: list[int] = None,
        request_location: list[int] = None,
        sizes: tuple[int] = (2,)
):
    keyboard = ReplyKeyboardBuilder()

    for text in btns:
        keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder
    )
del_kbd = ReplyKeyboardRemove()

main_kbd = get_keyboard('📝 Текст',
                       '🖼️ Изображения',
                       '👨‍🍳 Рецепты по фото',
                       '💲 Баланс',
                       '🤖❗️GPT 5❗️🤖',
                       placeholder='Выберите режим',
                       )


text_kbd = get_keyboard('🗑 Отчистить историю диалога', '🔙 Назад')