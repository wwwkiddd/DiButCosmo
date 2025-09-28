import asyncio
import os

from aiogram.client.session import aiohttp

API = os.getenv('API_VIDEO')

async def veo_text_to_video(http_session: aiohttp.ClientSession, prompt: str, ratio: str, image, long: bool | None = None):
    # url_veo3 = "https://api.aimlapi.com/v2/generate/video/google/generation"
    url_bytedance = "https://api.aimlapi.com/v2/generate/video/bytedance/generation"
    if long:
        duration = '10'
    else:
        duration = '5'

    if image:


        payload = {
            "model": f"bytedance/seedance-1-0-lite-i2v",
            'image_url': image,
            "prompt": prompt,
            "duration": duration,
        }
    else:

        payload = {
            "model": f"bytedance/seedance-1-0-lite-t2v",
            "prompt": prompt,
            "aspect_ratio": ratio,
            "duration": duration,
        }

    headers = {"Authorization": f"Bearer {API}", "Content-Type": "application/json"}

    async with http_session.post(url_bytedance, json=payload, headers=headers) as response:
        data = await response.json()
        print(data)
        generation_id = data['id']

    while True:
        params = {"generation_id": generation_id}
        async with http_session.get(url_bytedance, headers=headers, params=params) as response:
            if response.status != 200:
                # Обработка ошибок HTTP
                text = await response.text()
                raise Exception(f"HTTP error {response.status}: {text}")
            data = await response.json()
        status = data.get('status')
        print("Текущий статус:", status)
        if status in ["waiting", "active", "queued", "generating"]:
            print("Видео еще генерируется, ждем 10 секунд...")
            await asyncio.sleep(10)

        elif status == "completed":
            video_url = data.get("video", {}).get("url")
            print(data)
            print("Видео готово! Ссылка:", video_url)
            return video_url

        else:
            print("Получен неожиданный статус или ошибка:", data)
            return





