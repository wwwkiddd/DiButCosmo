import asyncio
import base64
import os

from aiogram import Bot
from aiogram.client.session import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_update_balance, orm_get_balance

BOT_TOKEN = os.getenv('TOKEN')

rate = {
    'gemini': 2,
    'perplexity': 8,
    'sonar-deep-research': 160,
    'img2txt': 40,
    'img2img': 70,
    'video': 105,
    'video_long': 200,
    'receipt': 15,
    'suno_song': 30,
    'gpt_5': 10

}

async def send_long_text(text):
    chunks = []
    MESS_MAX_LENGTH = 4096
    start = 0
    text_length = len(text)

    while start < text_length:
        # берем срез текста с позиции start
        end = start + MESS_MAX_LENGTH

        # Если нужно, чтобы не разрезать слова — ищем последний пробел перед end
        if end < text_length:
            # Попробуем найти пробел для разбиения в пределах start:end
            space_pos = text.rfind(' ', start, end)
            newline_pos = text.rfind('\n', start, end)
            split_pos = max(space_pos, newline_pos)
            if split_pos != -1 and split_pos > start:
                end = split_pos
            # Если нет подходящего пробела, то режем на ровно 4096 символов

        # Берем текстовый фрагмент
        chunk = text[start:end]
        chunks.append(chunk)
        # Продвигаемся дальше
        start = end if end > start else start + MESS_MAX_LENGTH

    return chunks

async def get_image_for_video(image: str):

    with open(image, 'rb') as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
    mime_type = 'image/jpeg'  # или image/png
    data_uri = f'data:{mime_type};base64,{b64_string}'
    return data_uri

async def get_image_for_gpt(bot: Bot, http_session: aiohttp.ClientSession, user_id: int, photo_id: str | None = None,  photo_bytes = None, ):
    # files = []
    if photo_id:
        file_id = photo_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        async with http_session.get(file_url) as response:
            if response.status != 200:
                # Обработка ошибок HTTP
                text = await response.text()
                raise Exception(f"HTTP error {response.status}: {text}")
            bytes = await response.content.read()
    elif photo_bytes:
        bytes = photo_bytes


    file = f"./files/image_for_gpt{user_id}.jpeg"

    with open(file, "wb") as f:
        f.write(bytes)

    return open(file, "rb"), file

async def send_typing_action(bot: Bot, chat_id: int, stop_event: asyncio.Event, delay: float = 4.0):
    while not stop_event.is_set():
        try:
            await bot.send_chat_action(chat_id=chat_id, action='typing')
        except Exception as e:
            print(f"Ошибка при отправке typing: {e}")
        await asyncio.sleep(delay)

async def check_balance(session: AsyncSession, user_id: int, model: str):
    payment = rate[model]
    balance = await orm_get_balance(session, user_id)
    if balance >= payment:
        return True
    else:
        return False

async def use_model(session: AsyncSession, user_id: int, model: str):
    payment = -rate[model]
    await orm_update_balance(session, user_id, payment)
