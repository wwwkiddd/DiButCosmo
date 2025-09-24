import asyncio
import os


from aiogram import Router, F, types, Bot
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile, BufferedInputFile
from openai import BadRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from app.open_webapp_bot.AI.api_requests.deepseek import deepseek
from app.open_webapp_bot.AI.api_requests.grok import grok_for_receipt
from app.open_webapp_bot.AI.api_requests.nano_banana import nano_banana
from app.open_webapp_bot.AI.api_requests.open_ai import gpt_5
from app.open_webapp_bot.AI.api_requests.perplexity import perp_send_request
from app.open_webapp_bot.AI.database.orm_query import orm_delete_gpt_chat_history, orm_get_user, orm_add_user, \
    orm_update_user_name, orm_update_first_name, orm_update_last_name, orm_delete_perplexity_chat_history, \
    orm_delete_gemini_chat_history
#
# from openai import BadRequestError
#
from app.open_webapp_bot.AI.kbds.inline import get_callback_btns, kbd_tk
from app.open_webapp_bot.AI.kbds.reply import main_kbd, get_keyboard
from app.open_webapp_bot.AI.handlers.processing import check_balance, send_typing_action, get_image_for_ai, send_long_text, \
    use_model

ai_func = Router()

BOT_TOKEN = os.getenv("BOT_TOKEN")

class AISelected(StatesGroup):

    #text models
    receipt = State()
    deepseek = State()
    perplexity = State()
    sonar_deep_research = State()
    gpt_5 = State()

    #image models
    image = State()
    image_editing = State()
    image_adding = State()

    #music models
    music = State()
    # make_cover = State()
    # music_adding_prompt = State()
    # long_track = State()

    #video models
    video = State()
    video_adding_prompt = State()
    video_editing = State()


@ai_func.callback_query(F.data == 'ai')
async def start_ai(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback.from_user.id
    user = await orm_get_user(session, callback.from_user.id)
    if not user:
        data = {'user_id': user_id,
                'first_name': callback.from_user.first_name,
                'last_name': callback.from_user.last_name,
                'tokens': 200,
                'username': callback.from_user.username
                }
        await orm_add_user(session, data)
    elif user.username != callback.from_user.username:
        await orm_update_user_name(session, user_id, callback.from_user.username)
    elif user.first_name != callback.from_user.first_name:
        await orm_update_first_name(session, user_id, callback.from_user.first_name)
    elif user.last_name != callback.from_user.last_name:
        await orm_update_last_name(session, user_id, callback.from_user.last_name)

    await callback.message.answer(
        '<b>✨ Привет, я собрал в себе все популярные нейросети для вашего удобства!</b>\n\n<u>Вот что я умею:</u>\n\n'
        '📝 Генерировать текст\n\n'
        '🖼️ Создавать и редактировать изображения\n\n'
        '🎬 Генерировать видео\n\n'
        '🎸 Писать и изменять музыку\n\n'
        '‍👨‍🍳 Подбирать рецепты по фото продуктов и рассчитывать КБЖУ\n\n'
        '<i>Чтобы узнать больше выберите режим 👇</i>',
        reply_markup=main_kbd)
    await callback.answer()


    await state.clear()
#
#
################################## For FSM ####################################################################

@ai_func.message(F.text == '📝 Текст')
async def work_with_text(message: types.Message, state: FSMContext):
    await state.clear()

    await message.delete()
    await message.answer('В этом разделе представлены 3 генеративные модели:\n\n'
                         '1) Нейросеть, которая обладает сильными <b>логическими и креативными</b> способностями. Умеет хорошо генерировать идеи, писать тексты. Идеально подходит <i>креаторам и для повседневных задач</i>.\n'
                         '📥 Может принимать на вход: <u>текст, фото, видео, голосовые сообщения, документы</u> (PDF, Python, TXT, HTML, CSS и т.д.)\n'
                         '⏳ Время ответа - <u>до 1 минуты(текст)</u>\n'
                         '                                   <u>1-2 минуты(документы)</u>\n'
                         '💰 Стоимость запроса: <b>2 токена</b>\n\n'
                         '2) Лучшая нейросеть для <i>учебы и работы</i>, в ней сделан акцент на <b>веб-поиск и проверку фактов</b>\n'
                         '📥 Может принимать на вход: <u>текст, фото</u>\n'
                         '⏳ Время ответа - <u>до 1 минуты</u>\n'
                         '💰 Стоимость запроса: <b>8 токенов</b>\n\n'
                         '3) Нейросеть, предназначенная для <b>глубокого поиска</b>.'
                         ' Мощнейший инструмент, который может разбивать сложный вопрос на подзадачи, анализировать сотни источников, и выдавать подробные, структурированные отчёты. '
                         'Подходит для <i>профессиональной аналитики</i>\n'
                         '📥 Может принимать на вход: <u>текст</u>\n'
                         '⏳ Время ответа - <u>1-5 минут</u>\n'
                         '💰 Стоимость запроса: <b>160 токенов</b>\n\n'
                         '<tg-spoiler>🤖 Пожалуйста, периодически отчищайте историю диалога с ИИ, это помогает ускорить работу бота и избежать возможных ошибок</tg-spoiler>',
                         reply_markup=get_callback_btns(btns={
                             '1) Лёгкая 🌠': 'deepseek',
                             '2) Для работы 👨‍💻': 'perplexity',
                             '3) Глубокий поиск 🧑‍🎓': 'sonar-deep-research'
                         }))


@ai_func.callback_query(F.data == 'deepseek')
async def enter_to_gemini(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AISelected.deepseek)

    await callback.message.answer('Выбранная модель: <b>Универсальная 🌠</b>\nНапишите запрос...',
                                  reply_markup=get_keyboard('🗑 Отчистить историю диалога'))


@ai_func.callback_query(F.data == 'perplexity')
async def enter_to_perplexity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Выбранная модель: <b>Для работы 👨‍💻</b>\nНапишите запрос...',
                                  reply_markup=get_keyboard('🗑 Отчистить историю диалога'))

    await state.set_state(AISelected.perplexity)

#
# @ai_func.callback_query(F.data == 'sonar-deep-research')
# async def enter_to_sonar_deep(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
#     await callback.message.answer('Выбранная модель: <b>Глубокий поиск 🧑‍🎓</b>\nНапишите запрос...',
#                                   reply_markup=get_keyboard('🗑 Отчистить историю диалога'))
#
#     await state.set_state(AISelected.sonar_deep_research)


@ai_func.message(F.text == '🖼️ Изображения')
async def work_with_image(message: types.Message, state: FSMContext):
    await message.delete()

    await message.answer('✨ <b>Создавайте и редактируйте фото прямо в чате!</b> ✨\n\n'
                                                    'Чтобы начать, отправьте изображения (от 1 до 10), которое(ые) вы хотите изменить, и напишите запрос или просто напишите в чат, что нужно создать\n\n'
                                                    'Генерация изображения по запросу - 40 токенов\n'
                                                    'Обработка вашего фото - 70 токенов ')

    await state.set_state(AISelected.image)


# @ai_func.message(F.text == '🎬 Видео')
# async def work_with_image(message: types.Message, state: FSMContext):
#     await message.delete()
#     photo = FSInputFile('./files/aspect_ratio.png')
#     await message.answer_photo(photo=photo, caption='✨ <b>Создавайте видео прямо в чате!</b> ✨ \n\n'
#                                                     'Сгенерируйте видео только <i>по текстовому запросу</i> или, <i>прикрепив к сообщению фото</i>, которое станет начальным кадром.\n\n'
#                                                     'По умолчанию видео длится 5 секунд, но можно его продлить до 10, для этого в запросе напишите "продлить" в начале запроса\n\n'
#                                                     'Также вы можете указать в запросе соотношение сторон видео(см. фото)☝️\n\n'
#                                                     'Цена генерации: 105 токенов (5 сек)\n'
#                                                     '                            200 токенов (10 сек)')
#
#     await state.set_state(AISelected.video)
#
#
# @ai_func.message(F.text == '🎸 Музыка')
# async def work_with_music(message: types.Message, state: FSMContext):
#     await message.delete()
#
#     await message.answer('✨ <b>Создавайте музыку прямо в чате!</b> ✨'
#                          '\nНапишите запрос и нейросеть создаст трек для вас\n\nЦена генерации - 30 токенов')
#
#     await state.set_state(AISelected.music)
#
#
@ai_func.message(F.text == '🤖❗️GPT 5❗️🤖')
async def work_with_gpt_5(message: types.Message, state: FSMContext):
    await message.delete()

    photo = FSInputFile('app/open_webapp_bot/AI/files/gpt_5.jpg')
    await message.answer_photo(photo=photo, caption='''❗Последня нейросеть от OpenAI уже в телеграм!!!\n\n🚀
✨ 📏 Масштаб — GPT‑5 в разы больше и «умнее»: триллионы параметров против сотен миллиардов у GPT‑4.\n
🖼 Мультимодальность — понимает не только текст, но и изображения.\n
🧠 Логика — умеет решать задачи пошагово (chain‑of‑thought), что даёт глубокое и точное мышление.\n
💬 Память и контекст — GPT‑5 помнит больше, поддерживает длинные и осмысленные диалоги.\n
🤖 Автономность — может работать как ИИ‑агент, выполняя многошаговые задания без постоянного вмешательства.\n
🎯 Уровень интеллекта — GPT‑4 можно сравнить со школьником, GPT‑5 — с аспирантом (PhD).\n
⚡ Эффективность — быстрее, точнее и экономичнее в работе.\n\n
GPT‑5 — это не просто чат‑бот, а универсальный помощник для науки, бизнеса, программирования и творчества.\n\n
Стоимость запроса: 10 токенов''', reply_markup=get_keyboard('🗑 Отчистить историю диалога'))

    await state.set_state(AISelected.gpt_5)


@ai_func.message(F.text == '👨‍🍳 Рецепты по фото')
async def work_with_receipt(message: types.Message, state: FSMContext):
    await message.delete()

    await message.answer('✨ <b>Привет, я твой помощник по питанию!</b> ✨\n\n'
                         'Просто 📎 прикрепи к сообщению фото или отправь мне список продуктов, которые у тебя есть, и я составлю вкусные рецепты с указанием КБЖУ\n\n'
                         'В описании к фото или вместе со списком можешь написать дополнительные пожелания👨‍🍳 <i>(для набора массы для похудения и т.д.)</i>\n\n'
                         'Один запрос стоит 15 токенов')

    await state.set_state(AISelected.receipt)

# ################################## For TEXT ####################################################################
#

@ai_func.message(AISelected.gpt_5, F.text == '🗑 Отчистить историю диалога')
async def clear_history_gpt(message: types.Message, session: AsyncSession):
    await orm_delete_gpt_chat_history(session, message.from_user.id)
    await message.answer('ℹ️ История диалога удалена, вы можете продолжать общение с ботом')

@ai_func.message(AISelected.gpt_5)
async def text_gpt(message: types.Message, session: AsyncSession, bot: Bot, http_session: aiohttp.ClientSession):
    print('going_to_gpt')
    user_id = message.from_user.id
    if await check_balance(session, user_id, 'gpt_5'):

        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id, stop_typing))


        try:
            if message.text:
                response = await gpt_5(session, user_id, prompt=message.text)

            elif message.photo:
                print('its photo')
                image, file = await get_image_for_ai(bot, http_session, user_id=user_id,
                                                      photo_id=message.photo[-1].file_id)
                os.remove(file)

                response = await gpt_5(session, user_id, prompt=message.caption, image=image)

            else:
                return

            # Останавливаем typing
            stop_typing.set()
            await typing_task


            chunks = await send_long_text(response)
            for chunk in chunks:
                try:
                    await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    print(e)
                    try:
                        await message.answer(chunk)
                    except Exception as e:
                        print(e)
                        await message.answer(chunk, parse_mode=None)

            # await use_model(session, user_id, 'gpt_5')



        except Exception as e:
            stop_typing.set()
            await typing_task
            print(e)
            await message.answer("Произошла ошибка при обработке запроса. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support")
    else:
        await message.answer(
        'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
        reply_markup=kbd_tk)


@ai_func.message(AISelected.perplexity, F.text == '🗑 Отчистить историю диалога')
async def clear_history_perplexity(message: types.Message, session: AsyncSession):
    await orm_delete_perplexity_chat_history(session, message.from_user.id)
    await message.answer('ℹ️ История диалога удалена, вы можете продолжать общение с ботом')

@ai_func.message(AISelected.perplexity)
async def text_perplexity(message: types.Message, bot: Bot, session: AsyncSession, http_session: aiohttp.ClientSession):
    user_id = message.from_user.id



    if await check_balance(session, user_id, 'perplexity'):

        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id, stop_typing))
        try:
            image = None

            if message.photo:
                image, file = await get_image_for_ai(bot, http_session, user_id=user_id,
                                                     photo_id=message.photo[-1].file_id)
                os.remove(file)


                content  = message.caption if message.caption else 'Опиши фото'

            else:
                content = message.text
                if content[0] == "/": return

            print(content)
            ans, citations= await perp_send_request(session, user_id, content, image)


            # Останавливаем typing
            stop_typing.set()
            await typing_task

            digits = []
            for i in range(len(citations)):
                digits.append(str(i))
            for d in digits:
                ans = ans.replace(f'[{d}]', f' [{d}]({citations[int(d) - 1]})')

            chunks = await send_long_text(ans)

            for chunk in chunks:

                try:
                    await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    print(e)
                    for d in digits:
                        chunk = chunk.replace(f' [{d}]({citations[int(d)-1]})', '')
                    try:
                        await message.answer(chunk)
                    except Exception as e:
                        print(e)
                        await message.answer(chunk, parse_mode=None)

            await use_model(session, user_id, 'perplexity')

            if citations:
                citations_message = '<strong>Ссылки на источники:</strong>\n'

                k = 1
                for citation in citations:
                    citations_message += f'{k} - {citation}\n'
                    k += 1

                await message.answer(citations_message)

        except Exception as e:
            stop_typing.set()
            await typing_task
            print(e)
            await message.answer("Произошла ошибка при обработке запроса. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support")
    else:
        await message.answer(
            'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
            reply_markup=kbd_tk)


# @ai_func.message(AISelected.sonar_deep_research, F.text == '🗑 Отчистить историю диалога')
# async def clear_history_sonar_deep(message: types.Message, session: AsyncSession):
#     await orm_delete_sonar_deep_chat_history(session, message.from_user.id)
#     await message.answer('ℹ️ История диалога удалена, вы можете продолжать общение с ботом')
#
# @ai_func.message(AISelected.sonar_deep_research)
# async def text_sonar_deep(message: types.Message, session: AsyncSession, http_session: aiohttp.ClientSession, bot: Bot):
#     content = message.text
#     if content[0] == "/": return
#     user_id = message.from_user.id
#     await bot.send_chat_action(chat_id=message.chat.id, action='typing')
#
#     if await check_balance(session, user_id, 'sonar-deep-research'):
#         await message.answer("🧠 Обрабатываю, пожалуйста подождите...")
#         ans, citations = await perp_deep_research_send_request(session, http_session,content, user_id)
#
#     # вынести цитаты наверх +
#         digits = []
#         for i in range(len(citations)):
#                 digits.append(str(i))
#         for d in digits:
#             ans = ans.replace(f'[{d}]', f' [{d}]({citations[int(d)-1]})')
#         ans = ans.replace('<think>', 'Анализирую:\n')
#         ans = ans.replace('</think>', '\nПерехожу к ответу:\n')
#         chunks = await send_long_text(ans)
#
#         for chunk in chunks:
#
#             try:
#                 await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
#             except Exception as e:
#                 print(e)
#                 for d in digits:
#                     chunk = chunk.replace(f' [{d}]({citations[int(d)-1]})', '')
#                 try:
#                     await message.answer(chunk)
#                 except Exception as e:
#                     print(e)
#                     await message.answer(chunk, parse_mode=None)
#
#         await use_model(session, user_id, 'sonar-deep-research')
#
#         if citations:
#             citations_message = '<strong>Ссылки на источники:</strong>\n'
#
#             k = 1
#             for citation in citations:
#                 citations_message += f'{k} - {citation}\n'
#                 k += 1
#
#             await message.answer(citations_message)
#     else:
#         await message.answer(
#             'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
#             reply_markup=kbd_tk)
#
#
#
@ai_func.message(AISelected.deepseek, F.text == '🗑 Отчистить историю диалога')
async def clear_history_ds(message: types.Message, session: AsyncSession):
    await orm_delete_gemini_chat_history(session, message.from_user.id)
    await message.answer('ℹ️ История диалога удалена, вы можете продолжать общение с ботом')

@ai_func.message(AISelected.deepseek, F.text)
async def text_deepseek(message: types.Message, bot: Bot, session: AsyncSession):
    user_id = message.from_user.id


    if not await check_balance(session, user_id, 'gemini'):
        await message.answer(
            'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
            reply_markup=kbd_tk)
        return

    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(send_typing_action(bot, message.chat.id, stop_typing))
    try:
        prompt = message.text

        if prompt == "/":
            return

        ans = await deepseek(session, user_id, prompt)
        if ans:
            # Останавливаем typing
            stop_typing.set()
            await typing_task

        chunks = await send_long_text(ans)
        for chunk in chunks:
            try:
                await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                print(e)
                try:
                    await message.answer(chunk)
                except Exception as e:
                    print(e)
                    await message.answer(chunk, parse_mode=None)

        await use_model(session, user_id, 'gemini')

    except Exception as e:
        stop_typing.set()
        await typing_task
        print(e)
        await message.answer("Произошла ошибка при обработке запроса. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support")



@ai_func.message(AISelected.receipt)
async def get_receipt(message: types.Message, bot: Bot, session: AsyncSession, http_session: aiohttp.ClientSession):
    try:
        user_id = message.from_user.id
        if await check_balance(session, message.from_user.id, 'receipt'):
            await message.answer("🧠 Обрабатываю, пожалуйста подождите...")
            image = None
            if message.photo:
                image, file = await get_image_for_ai(bot, http_session, user_id=user_id,
                                                     photo_id=message.photo[-1].file_id)
                os.remove(file)

                user_prompt = 'Ты помощник по питанию. Изучи фото определи какие продукты на нем, напиши рецепты блюд которые можно из низ приготовить, добавь КБЖУ для каждого блюда. В конце ответа не задавай вопросы'
                if message.caption:
                    user_prompt += message.caption

            elif message.text:
                user_prompt = message.text + 'Ты помощник по питанию. Изучи список, напиши рецепты блюд которые можно из продуктов в нем приготовить, добавь КБЖУ для каждого блюда. В конце ответа не задавай вопросы'
            else:
                return

            ans = await grok_for_receipt(user_prompt, image)



            chunks = await send_long_text(ans)
            for chunk in chunks:
                try:
                    await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    print(e)
                    try:
                        await message.answer(chunk)
                    except Exception as e:
                        print(e)
                        await message.answer(chunk, parse_mode=None)

            await use_model(session, message.from_user.id, 'receipt')

        else:
            await message.answer('К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
                                 reply_markup=kbd_tk)

    except Exception as e:
        print(e)
        await message.answer("Произошла ошибка при обработке запроса. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support")

#
# ######################################################################################################
#
#
# ################################## IMAGE #############################################################

users_collages = {}

# не срабатывают callback кнопки
# при нажатии изменить или
# раздельной отправке не учитывает фото +
@ai_func.message(AISelected.image_adding, F.text)
async def image_adding_gpt(message: types.Message, state: FSMContext, session: AsyncSession):
    prompt = message.text
    data = await state.get_data()
    key = data['image_adding']
    model = 'img2img'
    images = users_collages[key]
    print(images)

    try:
        await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет 2-3 минуты...\nПожалуйста, не переходите в другой режим пока не закончится генерация")
        image_out = await nano_banana(users_collages[key], prompt)
    except BadRequestError as e:
        print(e)
        if e.code == 'moderation_blocked':
            await message.answer(
                '🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
            del users_collages[key]
            await state.set_state(AISelected.image)
        return
    except Exception as e:
        print(e)
        await message.answer('Возникла непредвиденная ошибка, пожалуйста, повторите попытку позже.\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support')
        return

    del users_collages[key]
    await state.update_data(image=(prompt, images, image_out, model))
    input_file = BufferedInputFile(file=image_out, filename="your_image.jpeg")

    await state.set_state(AISelected.image)

    await message.answer_document(input_file)
    await message.answer_photo(photo=input_file, caption='Ваше изображение😌', reply_markup=get_callback_btns(btns={
        '🔄 Повторить': 'repeat',
        '✏️ Изменить': 'edit'
    }))

    await use_model(session, message.from_user.id, model)




@ai_func.message(or_f(AISelected.image, AISelected.image_adding))
async def to_nano_banana(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession, http_session: aiohttp.ClientSession):
    model = 'img2img'
    user_id = message.from_user.id

    if message.document:
        await message.answer('Пожалуйста, отправьте фото другим способом')
        return

    await state.update_data(image=None)


    images = []

# случай если медиа группа с описанием
    if message.media_group_id:
        if await check_balance(session, user_id, model):
            key  = user_id
            if key not in users_collages:
                users_collages[key] = []



            image, file = await get_image_for_ai(bot, http_session, user_id=user_id, photo_id=message.photo[-1].file_id)
            users_collages[key].append(image)
            await state.update_data(image_adding=key)
            await state.set_state(AISelected.image_adding)

            if message.caption:
                prompt = message.caption
            else:
                 return


            try:
                await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет 2-3 минуты...\nПожалуйста, не переходите в другой режим пока не закончится генерация")
                image_out = await nano_banana(prompt, users_collages[key])
                os.remove(file)
            except BadRequestError as e:
                print(e)
                if e.code == 'moderation_blocked':
                    await message.answer('🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
                return
            except Exception as e:
                print(e)
                await message.answer('Возникла непредвиденная ошибка, пожалуйста, повторите попытку позже.\n Если ошибка продолжает возникать, дайте нам знать @aitb_support')
                return

        else:
            await message.answer(
                'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
                reply_markup=kbd_tk)
            return

#случай когда фото с описанием

    elif message.caption and message.photo:
        if await check_balance(session, user_id, model):
            image, file = await get_image_for_ai(bot, http_session, user_id=user_id, photo_id=message.photo[-1].file_id)
            images.append(image)
            prompt = message.caption



            try:
                await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет 2-3 минуты...")
                image_out = await nano_banana(prompt, images)
                os.remove(file)

            except BadRequestError as e:
                print(e)
                if e.code == 'moderation_blocked':
                    await message.answer('🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
                return
            except Exception as e:
                print(e)
                await message.answer('Возникла непредвиденная ошибка, пожалуйста, повторите попытку позже.\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support')
                return

        else:
            await message.answer(
                'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
                reply_markup=kbd_tk)
            return

    elif message.photo:
        if await check_balance(session, user_id, model):
            key = user_id


            users_collages[key] = []


            image, file = await get_image_for_ai(bot, http_session, user_id=user_id, photo_id=message.photo[-1].file_id)
            users_collages[key].append(image)
            os.remove(file)

            await state.update_data(image_adding=key)
            await state.set_state(AISelected.image_adding)
            await message.answer('Отлично! Теперь напиши, что сделать с этим фото...')
            return

        else:
            await message.answer(
                'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
                reply_markup=kbd_tk)
            return


    elif message.text:
        model = 'img2txt'
        if await check_balance(session, user_id, model):

            try:
                prompt = message.text
                await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет 2-3 минуты...")
                image_out, ans = await nano_banana(prompt)
            except BadRequestError as e:
                if e.code == 'moderation_blocked':
                    await message.answer('🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
                return
            except Exception as e:
                print(e)
                await message.answer('Возникла непредвиденная ошибка, пожалуйста, повторите попытку позже.\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support')
                return

        else:
            await message.answer(
                'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
                reply_markup=kbd_tk)
            return
    else:
        return

    await state.update_data(image=(prompt, images, image_out, model))
    input_file = BufferedInputFile(file=image_out, filename="your_image.jpeg")
    if user_id in users_collages:
        del users_collages[user_id]

    await message.answer_document(input_file)
    await message.answer_photo(photo=input_file, caption=ans, reply_markup=get_callback_btns(btns={
        '🔄 Повторить': 'repeat',
        '✏️ Изменить': 'edit'
    }))
    await use_model(session, user_id, model)



@ai_func.callback_query(or_f(AISelected.image_adding, AISelected.image), F.data == 'repeat')
async def repeat_image_gpt(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    print('in_repeat')
    await callback.answer()
    data = await state.get_data()
    images = data['image'][1]
    prompt =data['image'][0]
    model = data['image'][-1]
    # print(images, prompt, model)
    user_id = callback.from_user.id

    if await check_balance(session, user_id, model):

        await callback.message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет 2-3 минуты...")

        try:
                image_out = await nano_banana(prompt, images)
        except BadRequestError as e:
            if e.code == 'moderation_blocked':
                await callback.message.answer(
                    '🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
            return

        except Exception as e:
            print(e)
            await callback.message.answer('Возникла непредвиденная ошибка, пожалуйста, повторите попытку позже.\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support')
            return

        await state.update_data(image=(prompt, images, image_out, model))
        input_file = BufferedInputFile(file=image_out, filename="your_image.jpeg")
        await state.set_state(AISelected.image)

        await callback.message.answer_document(input_file)
        await callback.message.answer_photo(photo=input_file, caption='Ваше изображение😌', reply_markup=get_callback_btns(btns={
            '🔄 Повторить': 'repeat',
            '✏️ Изменить': 'edit'
        }))

        await use_model(session, user_id, model)

    else:
        await callback.message.answer(
            'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
            reply_markup=kbd_tk)



@ai_func.callback_query(or_f(AISelected.image_adding, AISelected.image), F.data == 'edit')
async def enter_edit_gpt(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    if await check_balance(session, callback.from_user.id, 'img2img'):
        print('editing')
        await callback.answer()
        await callback.message.answer("Что бы вы хотели изменить?")
        await state.set_state(AISelected.image_editing)

    else:
        await callback.message.answer(
            'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
            reply_markup=kbd_tk)



@ai_func.message(AISelected.image_editing, F.text)
async def editing_gpt(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession, http_session: aiohttp.ClientSession):

    #реализовать добавление фото
    model = 'img2img'
    prompt = message.text
    data = await state.get_data()
    image_bytes = data['image'][-2]
    image, file = await get_image_for_ai(bot, http_session, user_id=message.from_user.id, photo_bytes=image_bytes)
    print(image)

    await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет 2-3 минуты...")
    try:
        image_out = await nano_banana(prompt, image)
        os.remove(file)

    except BadRequestError as e:
        if e.code == 'moderation_blocked':
            await message.answer('🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
        return
    except Exception as e:
        print(e)
        await message.answer('Возникла непредвиденная ошибка, пожалуйста, повторите попытку позже.\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support')
        return

    await state.update_data(image=(prompt, image, image_out, model))
    input_file = BufferedInputFile(file=image_out, filename="your_image.jpeg")

    await state.set_state(AISelected.image)

    await message.answer_document(input_file)
    await message.answer_photo(photo=input_file, caption='Ваше изображение😌',
                                        reply_markup=get_callback_btns(btns={
                                            '🔄 Повторить': 'repeat',
                                            '✏️ Редактировать': 'edit'
                                        }))

    await use_model(session, message.from_user.id, model)






# ######################################################################################################
#
#
# ################################## MUSIC #############################################################
#
# async def send_result(message: types.Message, session: AsyncSession, task_id, http_session: aiohttp.ClientSession):
#
#     try:
#         status, music, name, lyrics = await suno_wait_for_task_and_get_file(task_id, http_session)
#         if status == 'SENSITIVE_WORD_ERROR':
#             await message.answer('🤖 К сожалению, я не могу создать это фото, так как запрос противоречит моей политике в отношении контента.')
#             return
#         track = URLInputFile(url=music, filename=f"{name}.mp3")
#
#         await message.answer_document(document=track)
#         await message.answer('Ваш трек готов😌\n\n'
#                              f'Название: {name}\n'
#                              f'Текст: {lyrics}')
#         await use_model(session, message.from_user.id, 'suno_song')
#     except Exception as e:
#         print(e)
#         await message.answer('Произошла непредвиденная ошибка, повторите попытку.\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support')
#         return
#
#
#
# @ai_func.message(AISelected.music, F.text)
# async def create_song(message: types.Message, session: AsyncSession, http_session: aiohttp.ClientSession):
#     if await check_balance(session, message.from_user.id, 'suno_song'):
#         prompt = message.text
#         await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет около 5 минут...")
#
#         data = await suno_get_song(prompt, http_session)
#
#         await send_result(message, session, data, http_session)
#
#
#     else:
#         await message.answer(
#             'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
#             reply_markup=kbd_tk)
#
#
#
# # @ai_func.message(AISelected.make_cover, or_f(F.audio, F.voice))
# # async def make_cover(message: types.Message, bot: Bot, session: AsyncSession, state: FSMContext):
# #     user_id = message.from_user.id
# #
# #     if not await check_balance(session, user_id, 'suno_song'):
# #         await message.answer(
# #             'К сожалению, у вас закончились токены.\n\n Пожалуйста, пополните счёт, и я с удовольствием выполню ваш запрос!',
# #             reply_markup=kbd_tk)
# #         return
# #
# #     if message.audio or message.voice:
# #         file_id = message.audio.file_id if message.audio else message.voice.file_id
# #         file_info = await bot.get_file(file_id)
# #         file_path = file_info.file_path
# #         file_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}'
# #         response = requests.get(file_url)
# #
# #
# #
# #         track = f'audio_to_sep{user_id}.mp3'
# #         with open(track, "wb") as f:
# #             f.write(response.content)
# #
# #         audio_url = await suno_upload_track(track)
# #         print(audio_url)
# #
# #         os.remove(track)
# #
# #         if not message.caption:
# #             await message.answer('Отлично трек загружен!\nТеперь напишите как его изменить...')
# #             await state.set_state(AISelected.music_adding_prompt)
# #             await state.update_data(music_adding_prompt=audio_url)
# #             return
# #
# #         await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет около 5 минут...")
# #
# #         task_id = await suno_get_cover(audio_url, message.caption)
# #
# #         await send_result(message, session, task_id)
# #
# #
# #
# # @ai_func.message(AISelected.music_adding_prompt, F.text)
# # async def music_adding_prompt(message: types.Message, state: FSMContext, session: AsyncSession,):
# #     data = await state.get_data()
# #     audio_url = data['music_adding_prompt']
# #
# #     await message.answer("🧠 Обрабатываю, пожалуйста подождите.\nГенерация займет около 5 минут...")
# #
# #     task_id = await suno_get_cover(audio_url, message.caption)
# #
# #     await send_result(message, session, task_id)
#
#
#
#
#
#
#
# ######################################################################################################
#
#
# ################################## VIDEO #############################################################
#
# ratios = ['16:9','4:3','1:1','3:4','9:16','21:9','9:21']
#
# @ai_func.message(AISelected.video)
# async def video(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession, http_session: aiohttp.ClientSession):
#     user_id = message.from_user.id
#     model = 'video'
#     if await check_balance(session, user_id, 'video'):
#
#         ratio = '16:9'
#         long = False
#         image_data = None
#         image = None
#
#         if message.photo:
#             file_id = message.photo[-1].file_id
#             file_info = await bot.get_file(file_id)
#
#             file_path = file_info.file_path
#
#             file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
#             async with http_session.get(file_url) as response:
#                 if response.status != 200:
#                     # Обработка ошибок HTTP
#                     text = await response.text()
#                     raise Exception(f"HTTP error {response.status}: {text}")
#                 data = await response.content.read()
#
#                 image = f"files/image_for_video{user_id}.jpeg"
#                 with open(image, "wb") as f:
#                     f.write(data)
#                     print(f'saved to {image}')
#
#             image_data = await get_image_for_video(image)
#
#             if message.caption:
#                 prompt =message.caption
#             else:
#                 await state.update_data(video_adding_prompt=image_data)
#                 await state.set_state(AISelected.video_adding_prompt)
#                 await message.answer('Отлично! Теперь напиши, что сделать с этим фото...')
#                 return
#
#         elif message.text:
#             prompt = message.text
