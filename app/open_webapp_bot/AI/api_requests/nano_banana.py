import asyncio
import base64
import os

from openai import OpenAI


API = os.getenv('API_GPT')


client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=API,
)


async def nano_banana(prompt: str, images: list = None,):
    if images:
        content = [
        {
          "type": "text",
          "text": prompt
        },]
        for image in images:
            b64_image = base64.b64encode(image.read()).decode('utf-8')
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_image}"
                    }
                }
            )

            print('yes')

        request = [{
            "role": "user",
            "content": content},
        ]

    else:
        request = [{
            "role": "user",
            "content": prompt},
        ]


    try:



        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="google/gemini-2.5-flash-image-preview",
            messages=request
        )


        image_out = response.choices[0].message.images[0]['image_url']['url']
        base64_str = image_out.split(",")[1]
        image_bytes = base64.b64decode(base64_str)


        return image_bytes

    except Exception as e:
        print(e)
        return 'К сожалению, произошла ошибка. Пожалуйста, повторите попытку\nЕсли ошибка продолжает возникать, дайте нам знать @aitb_support'
