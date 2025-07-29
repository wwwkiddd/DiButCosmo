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
SUPERVISOR_CONFIG_DIR = "/etc/supervisor/conf.d"  # Убедитесь, что у вас есть доступ
SUPERVISOR_PROGRAM_PREFIX = "bot_"

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

    # Создание .env
    env_path = os.path.join(bot_dir, ".env")
    with open(env_path, "w") as f:
        f.write(f"BOT_TOKEN={bot_token}\n")
        f.write(f"ADMIN_IDS={admin_id}\n")
        f.write(f"BOT_ID={bot_id}\n")

    # Создание supervisor-конфига
    supervisor_conf_path = os.path.join(SUPERVISOR_CONFIG_DIR, f"{SUPERVISOR_PROGRAM_PREFIX}{bot_id}.conf")
    with open(supervisor_conf_path, "w") as f:
        f.write(f"""[program:{SUPERVISOR_PROGRAM_PREFIX}{bot_id}]
command=python3 {os.path.abspath(os.path.join(bot_dir, "app", "main.py"))}
directory={os.path.abspath(bot_dir)}
autostart=true
autorestart=true
stderr_logfile=/var/log/{SUPERVISOR_PROGRAM_PREFIX}{bot_id}_err.log
stdout_logfile=/var/log/{SUPERVISOR_PROGRAM_PREFIX}{bot_id}_out.log
environment=BOT_TOKEN="{bot_token}",ADMIN_IDS="{admin_id}",BOT_ID="{bot_id}"
""")

    # Перезапуск supervisor
    subprocess.run(["supervisorctl", "update"])

    # Активируем пробный период
    await set_subscription(bot_id=bot_id, months=1, trial=True)

    return {"bot_id": bot_id, "username": username}
