import asyncio
import base64
import os

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.open_webapp_bot.AI.database.orm_query import orm_get_chat_history, orm_update_gemini_chat_history


async def part_to_dict(part):
    return {
        "mime_type": part.inline_data.mime_type,
        "data": base64.b64encode(part.inline_data.data).decode('utf-8'),
        # другие нужные поля
    }


# async def gem_send_request(session: AsyncSession, content: list, user_id: int, add_info: list):
#     this_chat = []

    # if add_info:
    #     add_part = types.Part.from_bytes(
    #         data=add_info[0],
    #         mime_type=add_info[1]
    #     )
    #     # print(add_part)
    #     part_dict = await part_to_dict(add_part)
    #
    #     print(content)
    #     this_chat.append({'role': 'user', 'parts': [part_dict, {'text': content[-1]}]})
    #
    #     content.append(add_part)

    # else:
    #     this_chat.append({'role': 'user', 'parts': [{'text': content[-1]}]})
    # # print(this_chat)
    #
    # chat_history = await orm_get_chat_history(session, user_id, 'gemini')
    # history = []
    #
    # for message in chat_history:
    #     added = message['parts']
    #     if len(added) > 1:
    #         added = [types.Part.from_bytes(
    #         data=added[0]['data'],
    #         mime_type=added[0]['mime_type']
    #     ), added[-1]]
    #         history.append({'role': 'user', 'parts': added})
    #     else:
    #         history.append(message)
    #
    #
    # # print(chat_history)
    #
    # chat = await asyncio.to_thread(client.chats.create, model="gemini-2.5-flash", history=history)
    #
    # response = await asyncio.to_thread(chat.send_message, content)
    # # print(response.text)
    # this_chat.append({'role': 'model', 'parts': [{'text': response.text}]})
    # # print(this_chat)
    # await orm_update_gemini_chat_history(session, this_chat, user_id)
    #
    # # print(response.text)
    # return response.text


API = os.getenv('API_GPT')


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API,
)


async def gem_send_request(session: AsyncSession, user_id: int, prompt: str = None, add_info = None):
    print('to gemini')
    if add_info and add_info[-1] == 'image/jpeg':
        print('its_image')
        b64_image = base64.b64encode(add_info[0].read()).decode('utf-8')
        print('yes')

        if prompt:
            await orm_update_gemini_chat_history(session, [{
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
        else:
            print('working on history')
            await orm_update_gemini_chat_history(session, [{
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
        await orm_update_gemini_chat_history(session, [{
            "role": "user",
            "content": prompt},
        ], user_id)
        print('udated')

    history = await orm_get_chat_history(session, user_id, 'gemini')
    print(history)
    try:

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="google/gemini-2.5-flash",
            messages=history
        )

        print(response)
        ans = response.choices[0].message.content
        await orm_update_gemini_chat_history(session, [
            {"role": "assistant", "content":  ans}
        ], user_id)


        return ans

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'



async def gem_receipt(prompt: str, add_info: tuple = None):
    print('in process')
    content = [prompt]
    # if add_info:
    #     add_part = types.Part.from_bytes(client.chat.completions.create,
    #         data=add_info[0],
    #         mime_type=add_info[1]
    #     )
    #     content.append(add_part)

    response = await asyncio.to_thread(client.chat.completions.create,
        model="gemini-2.5-flash",
        contents=content
    )

    return response.text