import asyncio
import base64
import os

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.open_webapp_bot.AI.database.orm_query import orm_update_gpt_chat_history, orm_get_chat_history, \
    orm_update_gemini_chat_history

API = os.getenv('API_GPT')


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API,
)


async def deepseek(session: AsyncSession, user_id: int, prompt: str = None,):

    await orm_update_gemini_chat_history(session, [{
        "role": "user",
        "content": prompt},
    ], user_id)

    history = await orm_get_chat_history(session, user_id, 'gemini')
    print(history)
    try:

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="deepseek/deepseek-chat-v3.1:free",
            messages=history
        )

        print(response)
        ans = response.choices[0].message.content
        await orm_update_gemini_chat_history(session, [
            {"role": "assistant", "content": [
                {"type": "output_text", "text": ans}
            ]}
        ], user_id)


        return ans

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'
