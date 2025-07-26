# app/models.py
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    language TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    gender TEXT,
    birth_date TEXT,
    registered INTEGER DEFAULT 0
);
"""

CREATE_SLOTS_TABLE = """
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    available INTEGER DEFAULT 1
);
"""

CREATE_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""
