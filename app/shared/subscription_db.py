import aiosqlite
from datetime import datetime, timedelta
import os
from typing import List, Optional, Tuple

DB_FILE = os.path.join(os.path.dirname(__file__), "subscriptions.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS subscriptions (
    bot_id TEXT PRIMARY KEY,
    bot_token TEXT,
    admin_ids TEXT,           -- "123,456"
    start_date TEXT,
    end_date TEXT,
    active INTEGER DEFAULT 1, -- 1=включен, 0=выключен
    warn_24h INTEGER DEFAULT 0,
    warn_12h INTEGER DEFAULT 0,
    warn_6h  INTEGER DEFAULT 0
);
"""

async def _ensure_columns(conn: aiosqlite.Connection):
    # Миграция старой таблицы -> добавить недостающие колонки
    await conn.execute(CREATE_TABLE_SQL)
    await conn.commit()

    async with conn.execute("PRAGMA table_info(subscriptions)") as cur:
        cols = {row[1] for row in await cur.fetchall()}

    async def add(name: str, decl: str):
        if name not in cols:
            try:
                await conn.execute(f"ALTER TABLE subscriptions ADD COLUMN {decl}")
                await conn.commit()
            except Exception:
                pass

    await add("bot_token", "bot_token TEXT")
    await add("admin_ids", "admin_ids TEXT")
    await add("active", "active INTEGER DEFAULT 1")
    await add("warn_24h", "warn_24h INTEGER DEFAULT 0")
    await add("warn_12h", "warn_12h INTEGER DEFAULT 0")
    await add("warn_6h",  "warn_6h  INTEGER DEFAULT 0")

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await _ensure_columns(db)

async def upsert_subscription(
    bot_id: str,
    bot_token: str,
    admin_ids: List[int],
    months: Optional[int] = None,
    trial: bool = False
):
    """
    Создать/обновить подписку. Если trial=True — 7 дней, иначе months * 30 дней.
    Сбрасывает флаги предупреждений, active=1.
    """
    await init_db()
    async with aiosqlite.connect(DB_FILE) as db:
        start = datetime.utcnow()
        if trial:
            end = start + timedelta(days=7)
        else:
            if not months:
                months = 1
            end = start + timedelta(days=30 * months)

        await db.execute("""
            INSERT INTO subscriptions (bot_id, bot_token, admin_ids, start_date, end_date, active, warn_24h, warn_12h, warn_6h)
            VALUES (?, ?, ?, ?, ?, 1, 0, 0, 0)
            ON CONFLICT(bot_id) DO UPDATE SET
                bot_token=excluded.bot_token,
                admin_ids=excluded.admin_ids,
                start_date=excluded.start_date,
                end_date=excluded.end_date,
                active=1,
                warn_24h=0,
                warn_12h=0,
                warn_6h=0
        """, (bot_id, bot_token, ",".join(map(str, admin_ids)), start.isoformat(), end.isoformat()))
        await db.commit()

async def get_all_subscriptions():
    await init_db()
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT bot_id, bot_token, admin_ids, start_date, end_date, active, warn_24h, warn_12h, warn_6h FROM subscriptions") as cur:
            rows = await cur.fetchall()
    result = []
    for r in rows:
        result.append({
            "bot_id": r[0],
            "bot_token": r[1],
            "admin_ids": [int(x) for x in r[2].split(",")] if r[2] else [],
            "start_date": datetime.fromisoformat(r[3]) if r[3] else None,
            "end_date": datetime.fromisoformat(r[4]) if r[4] else None,
            "active": bool(r[5]),
            "warn_24h": bool(r[6]),
            "warn_12h": bool(r[7]),
            "warn_6h":  bool(r[8]),
        })
    return result

async def mark_warned(bot_id: str, hours: int):
    col = {24: "warn_24h", 12: "warn_12h", 6: "warn_6h"}.get(hours)
    if not col:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(f"UPDATE subscriptions SET {col}=1 WHERE bot_id=?", (bot_id,))
        await db.commit()

async def deactivate_bot(bot_id: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE subscriptions SET active=0 WHERE bot_id=?", (bot_id,))
        await db.commit()

async def get_expired_active_bots() -> List[str]:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT bot_id FROM subscriptions WHERE active=1 AND end_date < ?", (now,)) as cur:
            return [row[0] for row in await cur.fetchall()]

async def get_due_warnings() -> List[Tuple[str, str, List[int]]]:
    """
    Список [(bot_id, end_date_iso, [нужные предупреждения из {24,12,6}])], для которых ещё не отправляли.
    """
    subs = await get_all_subscriptions()
    now = datetime.utcnow()
    due = []
    for s in subs:
        if not s["active"] or not s["end_date"]:
            continue
        left = s["end_date"] - now
        hrs = left.total_seconds() / 3600.0
        need = []
        if 0 < hrs <= 24 and not s["warn_24h"]:
            need.append(24)
        if 0 < hrs <= 12 and not s["warn_12h"]:
            need.append(12)
        if 0 < hrs <= 6 and not s["warn_6h"]:
            need.append(6)
        if need:
            due.append((s["bot_id"], s["end_date"].isoformat(), need))
    return due

async def get_subscription_by_id(bot_id: str):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT bot_id, bot_token, admin_ids, end_date, active, warn_24h, warn_12h, warn_6h FROM subscriptions WHERE bot_id=?", (bot_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return {
                "bot_id": row[0],
                "bot_token": row[1],
                "admin_ids": [int(x) for x in row[2].split(",")] if row[2] else [],
                "end_date": datetime.fromisoformat(row[3]) if row[3] else None,
                "active": bool(row[4]),
                "warn_24h": bool(row[5]),
                "warn_12h": bool(row[6]),
                "warn_6h":  bool(row[7]),
            }
