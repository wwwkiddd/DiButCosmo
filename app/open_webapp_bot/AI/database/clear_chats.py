import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from orm_query import orm_clear_user_histories


async def clear_history_periodically(session: AsyncSession):
    while True:
        # Ждём 90 дней в секундах (90*24*60*60)
        await asyncio.sleep(90 * 24 * 60 * 60)
        await orm_clear_user_histories(session)  # Ваша функция удаления данных

