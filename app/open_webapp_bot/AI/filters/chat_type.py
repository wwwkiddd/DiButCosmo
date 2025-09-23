from aiogram import types, Bot
from aiogram.filters import Filter

admins = [1191552984]

class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return message.from_user.id in admins
