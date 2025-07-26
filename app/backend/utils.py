import os
import shutil
from uuid import uuid4
from pathlib import Path
from dotenv import set_key

from app.backend.models import BotRequest

BOTS_DIR = os.getenv("BOTS_DIR", "app/bots_storage")
TEMPLATE_PATH = os.getenv("TEMPLATE_BOT_DIR", "app/template_bot")

async def create_bot_instance(bot_data: BotRequest) -> str:
    bot_id = str(uuid4())[:8]
    bot_path = Path(f"{BOTS_DIR}/{bot_id}")

    shutil.copytree(TEMPLATE_PATH, bot_path)
    env_path = bot_path / ".env"
    shutil.copy(bot_path / ".env.template", env_path)

    set_key(str(env_path), "BOT_TOKEN", bot_data.bot_token)
    set_key(str(env_path), "ADMIN_IDS", str(bot_data.admin_id))

    os.system(f"docker build -t bot_{bot_id} {bot_path}")
    os.system(f"docker run -d --env-file {env_path} --name bot_{bot_id} bot_{bot_id}")

    return bot_id
