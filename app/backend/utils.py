import asyncio
import importlib.util
import os
import shutil
import subprocess
import uuid
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from app.shared.subscription_db import set_subscription

TEMPLATE_PATH = "app/template_bot"
BOTS_ROOT = "bots"

async def create_bot_instance(bot_data):
    bot_token = bot_data.bot_token
    admin_id = bot_data.admin_id
    bot_id = str(uuid.uuid4())[:8]

    # Проверка токена
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        username = me.username
    except TelegramAPIError as e:
        raise Exception("Невалидный токен: " + str(e))

    # Создание директории
    bot_dir = os.path.join(BOTS_ROOT, bot_id)
    os.makedirs(bot_dir, exist_ok=True)
    shutil.copytree(TEMPLATE_PATH, os.path.join(bot_dir, "app"))

    # Создание .env внутри app/
    env_path = os.path.join(bot_dir, "app", ".env")
    with open(env_path, "w") as f:
        f.write(f"BOT_TOKEN={bot_token}\n")
        f.write(f"ADMIN_IDS={admin_id}\n")
        f.write(f"BOT_ID={bot_id}\n")

    # Запуск бота
    script_path = os.path.join(bot_dir, "app", "main.py")
    subprocess.Popen(
        ["python3", script_path],
        cwd=os.path.join(bot_dir, "app"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Активируем пробный период
    await set_subscription(bot_id=bot_id, months=1, trial=True)

    return {"bot_id": bot_id, "username": username}
