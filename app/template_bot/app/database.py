# app/database.py
import aiosqlite
from models import CREATE_USERS_TABLE, CREATE_SLOTS_TABLE, CREATE_CONFIG_TABLE

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute(CREATE_USERS_TABLE)
        await self.conn.execute(CREATE_SLOTS_TABLE)
        await self.conn.execute(CREATE_CONFIG_TABLE)
        await self.conn.commit()

    async def set_config(self, key: str, value: str):
        await self.conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
        await self.conn.commit()

    async def get_config(self, key: str) -> str:
        cursor = await self.conn.execute(
            "SELECT value FROM config WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else ""
