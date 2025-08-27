import asyncio
import subprocess
from datetime import datetime
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.shared.subscription_db import (
    init_db, get_all_subscriptions, get_due_warnings,
    mark_warned, get_expired_active_bots, deactivate_bot
)

async def _notify(bot_token: str, admin_ids, text: str):
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        for uid in admin_ids:
            try:
                await bot.send_message(uid, text)
            except Exception as e:
                print(f"Notify error to {uid}: {e}")
    finally:
        await bot.session.close()

def _stop_bot_process(bot_id: str):
    """
    Пытаемся корректно остановить бота, запущенного под supervisor как [program:bot_<id>].
    Если такого нет — можно добавить свои варианты (docker, pkill и т.д.).
    """
    prog = f"bot_{bot_id}"
    try:
        subprocess.run(["/usr/bin/supervisorctl", "stop", prog], check=False)
    except Exception as e:
        print(f"supervisorctl stop {prog} failed: {e}")

async def process_warnings():
    """
    Шлём предупреждения за 24/12/6 часов до конца.
    """
    subs = await get_all_subscriptions()
    due = await get_due_warnings()

    for bot_id, end_iso, hours_list in due:
        sub = next((s for s in subs if s["bot_id"] == bot_id), None)
        if not sub:
            continue

        left = (datetime.fromisoformat(end_iso) - datetime.utcnow()).total_seconds() / 3600.0
        for h in sorted(hours_list, reverse=True):
            text = (
                f"⏰ Напоминание: срок действия подписки бота <b>{bot_id}</b> "
                f"закончится примерно через <b>{int(left)}</b> часов.\n\n"
                f"Пожалуйста, продлите подписку."
            )
            await _notify(sub["bot_token"], sub["admin_ids"], text)
            await mark_warned(bot_id, h)

async def process_expired():
    """
    Отключаем ботов с истёкшей подпиской и шлём уведомление.
    """
    expired = await get_expired_active_bots()
    if not expired:
        return

    subs = await get_all_subscriptions()
    for bot_id in expired:
        sub = next((s for s in subs if s["bot_id"] == bot_id), None)
        await deactivate_bot(bot_id)
        _stop_bot_process(bot_id)

        if sub:
            text = (
                f"⛔️ Подписка бота <b>{bot_id}</b> истекла. Бот остановлен.\n"
                f"Продлите подписку, чтобы снова включить бота."
            )
            await _notify(sub["bot_token"], sub["admin_ids"], text)

async def main():
    await init_db()
    await process_warnings()
    await process_expired()

if __name__ == "__main__":
    asyncio.run(main())
