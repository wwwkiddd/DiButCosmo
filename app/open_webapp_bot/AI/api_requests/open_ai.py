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


async def gpt_5(session: AsyncSession, user_id: int, prompt: str | None = None, image = None,):
    if image:
        b64_image = base64.b64encode(image.read()).decode('utf-8')

    if image and prompt:
        await orm_update_gpt_chat_history(session, [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{b64_image}"
                }
            ],
        }], user_id)
    elif image:
        await orm_update_gpt_chat_history(session, [{
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{b64_image}"
                }
            ],
        }], user_id)
    else:
        await orm_update_gpt_chat_history(session, [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
            ],
        }], user_id)

    try:
        history = await orm_get_chat_history(session, user_id, 'gpt')

        # response = await asyncio.to_thread(
        #     client.responses.create,
        #     model="gpt-5",
        #     input=history  # список словарей с role и content
        # )

        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
            },
            extra_body={},
            model="openai/gpt-5-chat",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What is in this image?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                            }
                        }
                    ]
                }
            ]
        )

        ans = response.choices[0].message.content
        print(response)
        await orm_update_gpt_chat_history(session, [
            {"role": "assistant", "content": [
                {"type": "output_text", "text": ans}
            ]}
        ], user_id)


        return ans

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'
