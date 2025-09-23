import asyncio
import base64
import os

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.open_webapp_bot.AI.database.orm_query import orm_update_gpt_chat_history, orm_get_chat_history

API = os.getenv('API_GPT')


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API,
)

async def grok_for_receipt(prompt: str = None, image = None,):
    print('grok')
    if image:
        print('its_image')
        b64_image = base64.b64encode(image.read()).decode('utf-8')
        print('yes')

    if image and prompt:
        request = [{
            "role": "user",
            "content": [
        {
          "type": "text",
          "text": prompt
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{b64_image}"
          }
        }
      ]
        }]

        print('image and text')

    else:
        request = [{
            "role": "user",
            "content": prompt},
        ]


    try:



        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="openai/gpt-5",
            messages=request
        )

        print(response)
        ans = response.choices[0].message.content


        return ans

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'
