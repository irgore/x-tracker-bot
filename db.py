"""SQLite storage for tracked X accounts + per-account state."""
import aiosqlite
from config import DB_PATH

_db: aiosqlite.Connection | None = None

async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(str(DB_PATH))
        _db.row_factory = aiosqlite.Row
        await _db.executescript("""
            CREATE TABLE IF NOT EXISTS tracked (
                id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                added_at TEXT DEFAULT (datetime('now')),
                UNIQUE(guild_id, username)
            );
            CREATE TABLE IF NOT EXISTS user_state (
                username TEXT PRIMARY KEY,
                following_json TEXT DEFAULT '{}',
                first_seen_at TEXT,
                last_check_at TEXT
            );
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                default_channel_id INTEGER
            );
        """)
        await _db.commit()
    return _db


async def add_tracking(guild_id: int, channel_id: int, username: str) -> bool:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO tracked (guild_id, channel_id, username) VALUES (?, ?, ?)",
            (guild_id, channel_id, username.lower()),
        )
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def remove_tracking(guild_id: int, username: str) -> bool:
    db = await get_db()
    cur = await db.execute(
        "DELETE FROM tracked WHERE guild_id = ? AND username = ?",
        (guild_id, username.lower()),
    )
    await db.commit()
    return cur.rowcount > 0


async def get_tracked(guild_id: int) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT username, channel_id, added_at FROM tracked WHERE guild_id = ? ORDER BY added_at",
        (guild_id,),
    )
    return [dict(r) for r in await cur.fetchall()]


async def get_all_tracked() -> list[dict]:
    db = await get_db()
    cur = await db.execute("SELECT username, guild_id, channel_id FROM tracked")
    return [dict(r) for r in await cur.fetchall()]


async def get_state(username: str) -> dict:
    db = await get_db()
    cur = await db.execute(
        "SELECT following_json, first_seen_at, last_check_at FROM user_state WHERE username = ?",
        (username.lower(),),
    )
    row = await cur.fetchone()
    if row:
        import json
        return {
            "following": json.loads(row["following_json"]),
            "first_seen_at": row["first_seen_at"],
            "last_check_at": row["last_check_at"],
        }
    return {"following": {}, "first_seen_at": None, "last_check_at": None}


async def set_default_channel(guild_id: int, channel_id: int):
    db = await get_db()
    await db.execute(
        """INSERT INTO guild_settings (guild_id, default_channel_id)
           VALUES (?, ?)
           ON CONFLICT(guild_id) DO UPDATE SET default_channel_id = excluded.default_channel_id""",
        (guild_id, channel_id),
    )
    await db.commit()


async def get_default_channel(guild_id: int) -> int | None:
    db = await get_db()
    cur = await db.execute(
        "SELECT default_channel_id FROM guild_settings WHERE guild_id = ?",
        (guild_id,),
    )
    row = await cur.fetchone()
    return row["default_channel_id"] if row else None


async def save_state(username: str, following: dict, first_seen_at: str = None):
    db = await get_db()
    import json
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO user_state (username, following_json, first_seen_at, last_check_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(username) DO UPDATE SET
             following_json = excluded.following_json,
             last_check_at = excluded.last_check_at""",
        (username.lower(), json.dumps(following), first_seen_at or now, now),
    )
    await db.commit()
