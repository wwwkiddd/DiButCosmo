import asyncio
import importlib.util
import os
import shutil
import subprocess
import uuid

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

# Абсолютные пути, чтобы Supervisor не путался с CWD
PROJECT_ROOT = "/root/DiButCosmo"
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "app", "template_bot")
BOTS_ROOT = os.path.join(PROJECT_ROOT, "bots")
VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv", "bin", "python3")

from app.shared.subscription_db import upsert_subscription, get_subscription_by_id


def _supervisor(cmd: list[str]) -> subprocess.CompletedProcess:
    """Запуск supervisorctl с защитой от ошибок."""
    return subprocess.run(
        ["/usr/bin/supervisorctl", *cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _create_supervisor_conf(bot_id: str, bot_dir: str):
    """
    Создаёт конфиг /etc/supervisor/conf.d/bot_<id>.conf
    и включает автозапуск конкретного бота.
    """
    program = f"bot_{bot_id}"
    main_py = os.path.join(bot_dir, "app", "main.py")

    conf = f"""[program:{program}]
command={VENV_PYTHON} {main_py}
directory={bot_dir}
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/{program}_err.log
stdout_logfile=/var/log/{program}_out.log
environment=PYTHONUNBUFFERED="1"
"""
    conf_path = f"/etc/supervisor/conf.d/{program}.conf"
    _write(conf_path, conf)

    # Применяем новый конфиг и стартуем
    _supervisor(["reread"])
    _supervisor(["update"])
    _supervisor(["start", program])


async def _validate_token_and_get_username(bot_token: str) -> str:
    """Проверка токена и получение username бота."""
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        username = me.username  # без @
    except TelegramAPIError as e:
        raise Exception(f"Невалидный токен: {e}")
    finally:
        try:
            await bot.session.close()
        except Exception:
            pass
    return username


async def create_bot_instance(bot_data):
    """
    Создать нового “пользовательского” бота:
    - валидация токена,
    - копирование шаблона,
    - запись .env,
    - регистрация подписки (7-дневный trial),
    - создание supervisor-конфига и запуск.
    Возвращает {bot_id, username}.
    """
    bot_token = bot_data.bot_token
    admin_id = int(bot_data.admin_id)
    bot_id = str(uuid.uuid4())[:8]

    username = await _validate_token_and_get_username(bot_token)

    # Директория бота
    bot_dir = os.path.join(BOTS_ROOT, bot_id)
    if os.path.exists(bot_dir):
        shutil.rmtree(bot_dir)
    os.makedirs(bot_dir, exist_ok=True)

    # Копируем шаблон в bots/<id>/app
    shutil.copytree(TEMPLATE_PATH, os.path.join(bot_dir, "app"))

    # .env для шаблонного main.py (он читает BOT_TOKEN/ADMIN_IDS)
    env_content = (
        f"BOT_TOKEN={bot_token}\n"
        f"ADMIN_IDS={admin_id}\n"        # В шаблоне ожидается список, но один id тоже ок: split(',') даст 1 эл-т
        f"DB_PATH=bot_database.db\n"
        f"CONFIG_PATH=config.json\n"
    )
    _write(os.path.join(bot_dir, ".env"), env_content)

    # Создадим пустой config.json, если нужно
    _write(os.path.join(bot_dir, "config.json"), '{"schedule": {}, "services": [], "reviews_link": "", "faq": ""}\n')

    # Зарегистрируем ТРИАЛ 7 дней (active=1, warn_* сбросятся)
    await upsert_subscription(
        bot_id=bot_id,
        bot_token=bot_token,
        admin_ids=[admin_id],
        trial=True
    )

    # Настроим supervisor и стартанём бота
    _create_supervisor_conf(bot_id, bot_dir)

    return {"bot_id": bot_id, "username": username}


def restart_bot(bot_id: str):
    """Перезапускает конкретного бота через supervisor."""
    program = f"bot_{bot_id}"
    _supervisor(["stop", program])
    _supervisor(["start", program])


def start_bot(bot_id: str):
    program = f"bot_{bot_id}"
    _supervisor(["start", program])


def stop_bot(bot_id: str):
    program = f"bot_{bot_id}"
    _supervisor(["stop", program])
