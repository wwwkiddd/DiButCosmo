from _datetime import datetime

from aiogram import types, Router, F, Bot
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import LabeledPrice, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.open_webapp_bot.AI.database.orm_query import orm_get_balance, orm_update_balance, orm_get_promo_code, \
    orm_delete_promo_code, orm_use_promo_code
from app.open_webapp_bot.AI.kbds.inline import get_callback_btns, kbd_tk

user_processes_ai = Router()
CURRENCY_1 = 'XTR'

class Processes(StatesGroup):
    promo_code = State()


################################## COMMANDS ####################################################################

@user_processes_ai.message(Command('help'))
async def help_cmd(message: types.Message):
    await message.answer \
        ('<strong>Чтобы бот отвечал на нужном языке, пишите ему прям в чате, на каком языке отвечать.</strong>\n\n'
         'В нашем боте нет подписок, вместо этого есть <i>токены (внутрення валюта)</i>. Благодаря которым вы можете платить только за те функции, которыми пользуетесь и не переплачивать за остальное!\n'
         'Купить токены /balance\n\n'
         'Если бот не отвечает или отвечает некорректно попробуйте вернуться в главное меню /start\n\n'
         'Если нашли ошибку в боте, напишите нам @aitb_support',)

@user_processes_ai.message(Command('suggest'))
async def suggest_an_idea(message: types.Message):
    await message.answer('⭐️ Предложите идею по улучшению бота и, если она будет реализована, вы получите вознаграждение в виде telegram stars!!! ⭐️\n@aitb_support')


@user_processes_ai.message(or_f(Command('balance'), F.text == '💲 Баланс'))
async def balance_cmd(message: types.Message, session: AsyncSession):
    balance = await orm_get_balance(session, message.from_user.id)
    balance = str(balance)
    if balance[-1] in ['0', '5', '6', '7', '8', '9']:
        tk = 'токенов'
    elif balance[-1] in ['2', '3', '4']:
        tk = 'токена'
    else:
        tk = 'токен'
    await message.answer(f'💰<b> БАЛАНС</b>:\n{balance} {tk}\n\n'
                               'Пополнить баланс ты можешь несколькими способами:\n- Купить токены 💰\n- Выполнить задания 🎯\n- Ввести промокод', reply_markup=kbd_tk)

################################## PAYMENTS ####################################################################
@user_processes_ai.callback_query(F.data == 'pay_for_ai')
async def payment_proc(callback: types.CallbackQuery):

    await callback.answer()
    await callback.message.answer('Выберите количество токенов (tk):', reply_markup=get_callback_btns(btns={
        '200 tk - 100⭐️': 'tk_200_100',
        '300 tk - 125⭐️': 'tk_300_125',
        '500 tk - 250⭐️': 'tk_500_250',
        '1000 tk - 400⭐️': 'tk_1000_400',
        '5000 tk - 1600⭐️': 'tk_5000_1600',
        '7500 tk - 2200⭐️': 'tk_7500_2000',
        '10000 tk - 3000⭐️': 'tk_10000_3000',
    }))

@user_processes_ai.callback_query(F.data.startswith('tk_'))
async def to_pay(callback: types.CallbackQuery,):
    amount_tk = callback.data.split('_')[1]
    amount_xtr = int(callback.data.split('_')[-1])
    await callback.answer()
    prices = [LabeledPrice(label=CURRENCY_1, amount=amount_xtr)]

    await callback.message.answer_invoice(title='Оплата',
                                          description=f'Покупка {amount_tk} токенов',
                                          prices=prices,
                                          payload=f'purchase_{amount_tk}',
                                          currency=CURRENCY_1)

@user_processes_ai.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@user_processes_ai.message(F.successful_payment)
async def successful_payment(message: types.Message, session: AsyncSession, bot: Bot):
    amount_tk = message.successful_payment.invoice_payload.split('_')[-1]
    user_id = message.from_user.id

    try:
        await orm_update_balance(session, message.from_user.id, int(amount_tk))
        await message.answer(f'Вы приобрели {amount_tk} токенов!\nБаланс обновится в течении 1 минуты')
    except Exception as e:
        print(e)
        await message.answer('К сожалению, произошла непредвиденная ошибка\n Звезды будут возвращены на ваш счёт')
        await bot.refund_star_payment(user_id=message.from_user.id,
                                      telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id)

################################## REFERRALS ####################################################################


@user_processes_ai.callback_query(F.data == 'challenge')
async def challenge(callback: types.CallbackQuery):
    is_challenge = False
    await callback.answer()

    if is_challenge:
        await callback.message.answer('✨ <b>Получайте токены за подписки!</b> ✨\n'
                                      'Подписка на каждый канал стоит - ')
    else:
        await callback.message.answer('В этом разделе будут появляться задания...')

################################## PROMO CODES ####################################################################

@user_processes_ai.callback_query(F.data == 'user_promo_code')
async def promo_code(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.answer('Введите промокод...\n\nПосле каждой попытки, чтобы еще раз ввести промокод необходимо снова нажать на кнопку☝️')
    await state.set_state(Processes.promo_code)

@user_processes_ai.message(Processes.promo_code)
async def get_promo_code(message: types.Message, session: AsyncSession, state: FSMContext):
    code = await orm_get_promo_code(session, message.text)

    if code:
        user_id = message.from_user.id
# проверить
#         print(code.date_end, datetime.now())
        if code.date_end < datetime.now():
            await message.answer('Срок действия промокода истёк...')
            await state.clear()
            await orm_delete_promo_code(session, code.code)
            return
        if user_id not in code.used_by:
            await orm_use_promo_code(session, code.code, user_id)
            await orm_update_balance(session, user_id, code.value)
            await message.answer(f'Промокод активирован! Вам начислено {code.value} токенов')
        else:
            await message.answer('Вы уже использовали этот промокод')
    else:
        await message.answer('Промокод неверный')

    await state.clear()






