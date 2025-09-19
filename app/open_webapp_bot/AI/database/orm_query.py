from asyncio import Lock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, delete


from models import User, PromoCode


async def orm_add_user(session: AsyncSession, data: dict):
    user = User(
        user_id=data['user_id'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        tokens=data['tokens'],
        username=data['username'],
        gemini_chat_history=[],
        perplexity_chat_history=[
            {
                "role": "system",
                "content": (
                    "You are an artificial intelligence assistant and you need to "
                    "engage in a helpful, detailed, polite conversation with a user."
                ),
            },
        ],
        deep_research_chat_history=[]
    )
    session.add(user)
    await session.commit()



async def orm_get_users(session:AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_user(session:AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_clear_user_histories(session: AsyncSession):
    query = update(User).values(gemini_chat_history=[],
        perplexity_chat_history=[
            {
                "role": "system",
                "content": (
                    "You are an artificial intelligence assistant and you need to "
                    "engage in a helpful, detailed, polite conversation with a user."
                ),
            },
        ],
        deep_research_chat_history=[]
    )
    await session.execute(query)
    await session.commit()


async def orm_get_balance(session: AsyncSession, user_id: int):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)

    if result:
        return result.scalar().tokens


async def orm_update_balance(session: AsyncSession, user_id: int, tokens: int):
    query = update(User).where(User.user_id == user_id).values(tokens=User.tokens + tokens)
    await session.execute(query)
    await session.commit()

async def orm_update_first_name(session: AsyncSession, user_id: int, first_name: str):
    query = update(User).where(User.user_id == user_id).values(first_name=first_name)
    await session.execute(query)
    await session.commit()

async def orm_update_last_name(session: AsyncSession, user_id: int, last_name: str):
    query = update(User).where(User.user_id == user_id).values(last_name=last_name)
    await session.execute(query)
    await session.commit()

async def orm_update_user_name(session: AsyncSession, user_id: int, user_name: str):
    query = update(User).where(User.user_id == user_id).values(username=user_name)
    await session.execute(query)
    await session.commit()


async def orm_get_user_id(session: AsyncSession, user_name: str,):
    query = select(User).where(User.username == user_name)
    result = await session.execute(query)
    ret = result.scalar()
    if ret:
        return ret.user_id


async def orm_get_chat_history(session: AsyncSession, user_id: int, model: str):
    res = None
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)

    if model == 'gemini':
        res = result.scalar().gemini_chat_history
    elif model == 'perplexity':
        res = result.scalar().perplexity_chat_history
    elif model == 'sonar_deep':
        res = result.scalar().deep_research_chat_history
    elif model == 'gpt':
        res = result.scalar().gpt_chat_history

    return res

########### gemini ###########

gem_locks = {}

async def get_gem_lock(user_id: int) -> Lock:
    if user_id not in perp_locks:
        perp_locks[user_id] = Lock()
    return perp_locks[user_id]

async def orm_update_gemini_chat_history(session: AsyncSession, chat, user_id: int):
    query = update(User).where(User.user_id == user_id).values(gemini_chat_history=User.gemini_chat_history + chat)
    await session.execute(query)
    await session.commit()

async def orm_delete_gemini_chat_history(session: AsyncSession, user_id: int):
    query = update(User).where(User.user_id == user_id).values(gemini_chat_history=[])
    await session.execute(query)
    await session.commit()

########### perplexity ###########

# Глобальный словарь замков
perp_locks = {}

async def get_perp_lock(user_id: int) -> Lock:
    if user_id not in perp_locks:
        perp_locks[user_id] = Lock()
    return perp_locks[user_id]

async def orm_update_perplexity_chat_history(session: AsyncSession, chat, user_id: int):
    lock = await get_perp_lock(user_id)
    async with lock:
        query = update(User).where(User.user_id == user_id).values(perplexity_chat_history=User.perplexity_chat_history + chat)
        await session.execute(query)
        await session.commit()

async def orm_delete_perplexity_chat_history(session: AsyncSession, user_id: int):
    lock = await get_perp_lock(user_id)
    async with lock:
        query = update(User).where(User.user_id == user_id).values(perplexity_chat_history=[])
        await session.execute(query)
        await session.commit()

########### sonar deep ###########

# Глобальный словарь замков
deep_locks = {}

async def get_deep_lock(user_id: int) -> Lock:
    if user_id not in deep_locks:
        deep_locks[user_id] = Lock()
    return deep_locks[user_id]

# Пример обёртки обновления истории с блокировкой
async def orm_update_sonar_deep_chat_history(session: AsyncSession, chat, user_id: int):
    lock = await get_deep_lock(user_id)
    async with lock:
        query = update(User).where(User.user_id == user_id).values(
            deep_research_chat_history=User.deep_research_chat_history + chat
        )
        await session.execute(query)
        await session.commit()

async def orm_delete_sonar_deep_chat_history(session: AsyncSession, user_id: int):
    lock = await get_deep_lock(user_id)
    async with lock:
        query = update(User).where(User.user_id == user_id).values(
            deep_research_chat_history=[]
        )
        await session.execute(query)
        await session.commit()

########### gpt-5 ###########


# Глобальный словарь замков
gpt_locks = {}

async def get_gpt_lock(user_id: int) -> Lock:
    if user_id not in gpt_locks:
        gpt_locks[user_id] = Lock()
    return gpt_locks[user_id]

# Пример обёртки обновления истории с блокировкой
async def orm_update_gpt_chat_history(session: AsyncSession, chat, user_id: int):
    lock = await get_deep_lock(user_id)
    async with lock:
        query = update(User).where(User.user_id == user_id).values(
            gpt_chat_history=User.gpt_chat_history + chat
        )
        await session.execute(query)
        await session.commit()

async def orm_delete_gpt_chat_history(session: AsyncSession, user_id: int):
    lock = await get_deep_lock(user_id)
    async with lock:
        query = update(User).where(User.user_id == user_id).values(
            gpt_chat_history=[]
        )
        await session.execute(query)
        await session.commit()

###################################

async def orm_add_promo_code(session: AsyncSession, data: dict):
    code = PromoCode(code=data['code'],
                     value=data['value'],
                     used_by=[],
                     date_end=data['date'])
    session.add(code)
    await session.commit()

async def orm_get_promo_codes(session: AsyncSession):
    query = select(PromoCode)
    result = await session.execute(query)

    return result.scalars().all()

async def orm_get_promo_code(session: AsyncSession, code: str):
    query = select(PromoCode).where(PromoCode.code == code)
    result = await session.execute(query)

    return result.scalar()

async def orm_use_promo_code(session: AsyncSession, code: str, user_id: int):
    query = update(PromoCode).where(PromoCode.code == code).values(used_by=PromoCode.used_by + [user_id])
    await session.execute(query)
    await session.commit()

async def orm_delete_promo_code(session: AsyncSession, code: str):
    query = delete(PromoCode).where(PromoCode.code == code)
    await session.execute(query)
    await session.commit()





