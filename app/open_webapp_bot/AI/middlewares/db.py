from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.client.session import aiohttp
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data['session'] = session
            return await handler(event, data)

class HTTPSessionMiddleware(BaseMiddleware):
    def __init__(self, http_session: aiohttp.ClientSession):
        self.http_session = http_session
        super().__init__()

    async def __call__(self, handler, event, data):
        data["http_session"] = self.http_session  # добавляем параметр
        return await handler(event, data)



# class BanCheckMiddleware(BaseMiddleware):
#     def __init__(self, banned_user_ids: set):
#         self.banned_user_ids = banned_user_ids
#
#     async def __call__(
#         self,
#         handler: Callable[[Message, Dict[str, Any]], Any],
#         event: Message,
#         data: Dict[str, Any]
#     ) -> Any:
#         user_id = event.from_user.id
#
#         # Check if the user is banned (adjust the logic for your DB/check function)
#         if user_id not in self.banned_user_ids:
#             await event.answer("⛔ You are banned.")
#             return  # Stops event processing
#
#         return await handler(event, data)
