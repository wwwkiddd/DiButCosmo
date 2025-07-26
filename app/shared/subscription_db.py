import aiosqlite
from datetime import datetime, timedelta
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "subscriptions.db")

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                bot_id TEXT PRIMARY KEY,
                bot_token TEXT,
                admin_ids TEXT,
                start_date TEXT,
                end_date TEXT,
                active INTEGER
            )
        ''')
        await db.commit()

async def set_subscription(bot_id, bot_token, admin_ids, months: int):
    await init_db()
    now = datetime.utcnow()
    end_date = now + timedelta(days=30 * months)
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            INSERT OR REPLACE INTO subscriptions
            (bot_id, bot_token, admin_ids, start_date, end_date, active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (bot_id, bot_token, ",".join(map(str, admin_ids)), now.isoformat(), end_date.isoformat(), 1))
        await db.commit()

async def get_all_subscriptions():
    await init_db()
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute('SELECT * FROM subscriptions') as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "bot_id": row[0],
                    "bot_token": row[1],
                    "admin_ids": row[2].split(","),
                    "start_date": datetime.fromisoformat(row[3]),
                    "end_date": datetime.fromisoformat(row[4]),
                    "active": bool(row[5])
                }
                for row in rows
            ]

async def get_expired_bots():
    async with aiosqlite.connect(DB_FILE) as db:
        now = datetime.utcnow().isoformat()
        async with db.execute('SELECT bot_id FROM subscriptions WHERE end_date < ?', (now,)) as cursor:
            return await cursor.fetchall()

async def deactivate_bot(bot_id):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('UPDATE subscriptions SET active = 0 WHERE bot_id = ?', (bot_id,))
        await db.commit()

async def prolong_subscription(bot_id: str, months: int):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute('SELECT end_date FROM subscriptions WHERE bot_id = ?', (bot_id,)) as cursor:
            row = await cursor.fetchone()

        now = datetime.utcnow()
        if row:
            current_end = datetime.fromisoformat(row[0])
            new_end = current_end + timedelta(days=30 * months) if current_end > now else now + timedelta(days=30 * months)

            await db.execute('''
                UPDATE subscriptions SET end_date = ?, active = 1 WHERE bot_id = ?
            ''', (new_end.isoformat(), bot_id))
            await db.commit()
