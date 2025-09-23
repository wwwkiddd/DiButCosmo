from datetime import date

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession


from app.open_webapp_bot.AI.database.clear_chats import clear_history_periodically
from app.open_webapp_bot.AI.database.orm_query import orm_get_user_id, orm_get_user, orm_update_balance, \
    orm_add_promo_code, orm_get_promo_codes, orm_delete_promo_code
from app.open_webapp_bot.AI.filters.chat_type import IsAdmin
from app.open_webapp_bot.AI.kbds.inline import get_callback_btns

admin_router = Router()
admin_router.message.filter(IsAdmin())

class AdminState(StatesGroup):
    # дать токенов
    to_whom = State()
    amount = State()

    # промокод
    delete_code = State()
    code = State()
    value = State()
    date = State()

@admin_router.message(Command('admin'))
async def enter_admin(message: types.Message):
    await message.answer('Здравствуй, мой админ что ты хочешь сделать сегодня?', reply_markup=get_callback_btns(btns={
        'Установить таймер': 'set_timer',
        'Дать токенов': 'give_tk',
        'Промокоды': 'admin_promo_code',
        'Проверить пользователя': 'check_a_man'
    }))

################################## timer ####################################################################
@admin_router.callback_query(F.data == 'set_timer')
async def set_timer(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer('установлен таймер на 90 дней')
    await clear_history_periodically(session)

################################## tokens ####################################################################

@admin_router.callback_query(F.data == 'give_tk')
async def give_tokens(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Кому необходимо начислить токены? (user_name)')
    await state.set_state(AdminState.to_whom)

@admin_router.message(AdminState.to_whom)
async def get_user_for_tk(message: types.Message, session: AsyncSession, state: FSMContext):
    user_name = message.text[1:]
    user_id = await orm_get_user_id(session, user_name)
    user = await orm_get_user(session, user_id)
    if user:
        await state.update_data(to_whom=(user_id, user_name))
        await message.answer('Сколько токенов начислить')
        await state.set_state(AdminState.amount)
    else:
        await message.answer('Такого пользователя нет')

@admin_router.message(AdminState.amount)
async def amount_tk(message: types.Message, session: AsyncSession, state: FSMContext):
    amount = int(message.text)
    data = await state.get_data()
    user_id = data['to_whom'][0]
    user_name = data['to_whom'][-1]

    await orm_update_balance(session, user_id, amount)
    await message.answer(f'Пользователю @{user_name} начислено {amount} токенов')
    await state.clear()

################################## promo codes ####################################################################

@admin_router.callback_query(F.data == 'admin_promo_code')
async def deal_promo_code(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer('Что вы хотите сделать?', reply_markup=get_callback_btns(btns={
        'Добавить промокод': 'add_code',
        'Посмотреть промокоды': 'check_codes',
        'Удалить промокод': 'delete_code'
    }))

@admin_router.callback_query(F.data == 'add_code')
async def add_code(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите промокод')
    await state.set_state(AdminState.code)

@admin_router.message(AdminState.code)
async def add_value(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)

    await message.answer('Теперь введите ценность промокода')
    await state.set_state(AdminState.value)


@admin_router.message(AdminState.value)
async def add_date(message: types.Message, state: FSMContext):
    await state.update_data(value=int(message.text))

    await message.answer('Теперь дату когда промокод перестанет работать\nПо образцу: 21/07/2025')
    await state.set_state(AdminState.date)

@admin_router.message(AdminState.date)
async def add_full_code(message: types.Message, session: AsyncSession, state: FSMContext):
    year = int(message.text.split('/')[-1])
    month = int(message.text.split('/')[-2])
    day = int(message.text.split('/')[0])
    d = date(year, month, day)
    await state.update_data(date=d)

    data = await state.get_data()
    await orm_add_promo_code(session, data)
    await message.answer('Промокод добавлен!')
    await state.clear()


@admin_router.callback_query(F.data == 'check_codes')
async def check_codes(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    text = ''
    for promo_code in await orm_get_promo_codes(session):
        user_names = ''
        usage = promo_code.used_by
        for user in usage:
            raw_user = await orm_get_user(session, user)
            user_names += f'@{raw_user.username} '

        text += f'\nКод: {promo_code.code}\nЦенность: {promo_code.value}\nДата окончания: {promo_code.date_end}\nБыл использован: {user_names}\n'
    if text:
        await callback.message.answer(text)
    else:
        await callback.message.answer('Промокодов нет')


@admin_router.callback_query(F.data == 'delete_code')
async def code_to_delete(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Введите промокод, который хотите удалить')
    await state.set_state(AdminState.delete_code)

@admin_router.message(AdminState.delete_code)
async def delete_code(message: types.Message, session: AsyncSession, state: FSMContext):
    code = message.text
    await orm_delete_promo_code(session, code)
    await message.answer('Промокод удалён')

    await state.clear()



################################## check a man ####################################################################

# @admin_router.message(startswith_())
# async def check_user(message: types.Message, session: AsyncSession):
#     user = await orm_get_user(session, int(message.text))
#     if user:
#         await message.answer(f'Имя пользователя: {user.first_name} {user.last_name}\n'
#                              f'Username: {user.username}\n'
#                              f'tokens: {user.tokens}')
#     else:
#         await message.answer('Такого пользователя нет')




