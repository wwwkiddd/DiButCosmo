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


async def gpt_5(session: AsyncSession, user_id: int, prompt: str = None, image = None,):
    if image:
        b64_image = base64.b64encode(image.read()).decode('utf-8')

    if image and prompt:
        await orm_update_gpt_chat_history(session, [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "input_image",
                    "image_uri": f"data:image/jpeg;base64,{b64_image}"
                }
            ],
        }], user_id)
        print('image and text added to history')
    elif image:

        await orm_update_gpt_chat_history(session, [{
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_uri": f"data:image/jpeg;base64,{b64_image}"
                }
            ],
        }], user_id)

        print('image added to history')
    else:
        await orm_update_gpt_chat_history(session, [{
            "role": "user",
            "content": prompt},
        ], user_id)
    history = await orm_get_chat_history(session, user_id, 'gpt')
    print(history)
    try:



        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="openai/gpt-5",
            messages=history
        )

        print(response)
        ans = response.choices[0].message.content
        await orm_update_gpt_chat_history(session, [
            {"role": "assistant", "content": [
                {"type": "output_text", "text": ans}
            ]}
        ], user_id)


        return ans

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'
