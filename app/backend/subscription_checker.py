import os
import subprocess
import asyncio
from datetime import datetime

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.shared.subscription_db import get_all_subscriptions, deactivate_bot


async def notify_expired(bot_token, admin_ids):
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Продлить подписку", callback_data="renew")]
    ])
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, "⛔️ Подписка истекла. Бот был отключён.", reply_markup=markup)
        except Exception as e:
            print(f"Ошибка при отправке сообщения {admin_id}: {e}")
    await bot.session.close()


async def main():
    print("🔍 Проверка подписок...")
    subs = await get_all_subscriptions()
    for sub in subs:
        if sub["active"] and datetime.utcnow() > sub["end_date"]:
            bot_id = sub["bot_id"]
            print(f"⛔️ Отключаем бот {bot_id}...")
            subprocess.run(f"docker stop bot_{bot_id}", shell=True)
            subprocess.run(f"docker rm bot_{bot_id}", shell=True)
            await deactivate_bot(bot_id)
            await notify_expired(sub["bot_token"], sub["admin_ids"])


if __name__ == "__main__":
    asyncio.run(main())