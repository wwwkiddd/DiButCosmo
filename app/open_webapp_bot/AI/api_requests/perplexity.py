import asyncio
import base64
import os

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.open_webapp_bot.AI.database.orm_query import orm_update_gpt_chat_history, orm_get_chat_history, \
    orm_update_perplexity_chat_history

API = os.getenv('API_GPT')


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API,
)


async def perp_send_request(session: AsyncSession, user_id: int, prompt: str = None, image = None):
    print('to perplexity')
    if image:
        print('its_image')
        b64_image = base64.b64encode(image.read()).decode('utf-8')
        print('yes')

    if image and prompt:
        await orm_update_perplexity_chat_history(session, [{
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
        }], user_id)
        print('image and text added to history')
    elif image:
        print('working on histiry')
        await orm_update_perplexity_chat_history(session, [{
            "role": "user",
            "content": [
        {
          "type": "text",
          "text": ''
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{b64_image}"
          }
        }
      ],
        }], user_id)

        print('image added to history')
    else:
        print('no image')
        await orm_update_perplexity_chat_history(session, [{
            "role": "user",
            "content": prompt},
        ], user_id)
        print('udated')

    history = await orm_get_chat_history(session, user_id, 'perplexity')
    print(history)
    try:

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="perplexity/sonar-pro",
            messages=history
        )

        print(response)
        ans = response.choices[0].message.content
        await orm_update_perplexity_chat_history(session, [
            {"role": "assistant", "content": [
                {"type": "output_text", "text": ans}
            ]}
        ], user_id)

        print(response.citations)
        return ans, response.citations

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'
