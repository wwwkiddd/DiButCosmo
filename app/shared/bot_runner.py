import asyncio
import os
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

async def run_bot_instance(bot_id):
    user_bot_path = Path(__file__).parent.parent / "user_bots" / bot_id
    env_path = user_bot_path / ".env"
    if not env_path.exists():
        print(f".env не найден для бота {bot_id}")
        return

    # Загрузить .env
    load_dotenv(dotenv_path=env_path)

    # Запуск main.py ?
    main_path = user_bot_path / "main.py"
    spec = importlib.util.spec_from_file_location("main", main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    await module.main()
