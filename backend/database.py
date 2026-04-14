import aiosqlite
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "pokeme.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                image_hash      TEXT UNIQUE NOT NULL,
                photo_path      TEXT,
                number          TEXT,
                name            TEXT NOT NULL,
                scientific_name TEXT,
                category        TEXT,
                height          TEXT,
                weight          TEXT,
                habitat         TEXT,
                diet            TEXT,
                predator        TEXT,
                conservation    TEXT,
                description     TEXT,
                rarity          TEXT DEFAULT '普通',
                attributes      TEXT,
                narration       TEXT,
                raw_json        TEXT,
                scanned_at      DATETIME DEFAULT (datetime('now', 'localtime'))
            )
        """)
        # 兼容旧数据库：如果 narration 列不存在则添加
        try:
            await db.execute("ALTER TABLE entries ADD COLUMN narration TEXT")
        except Exception:
            pass  # 列已存在，忽略
        await db.execute("CREATE INDEX IF NOT EXISTS idx_category   ON entries(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_rarity     ON entries(rarity)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_scanned_at ON entries(scanned_at DESC)")
        await db.commit()


async def get_by_hash(image_hash: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM entries WHERE image_hash = ?", (image_hash,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return _row_to_dict(row)
    return None


async def insert_entry(
    image_hash: str,
    photo_path: str,
    data: dict,
    raw_json: str,
) -> dict:
    attributes_json = json.dumps(data.get("attributes", []), ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            INSERT INTO entries
                (image_hash, photo_path, number, name, scientific_name, category,
                 height, weight, habitat, diet, predator, conservation,
                 description, rarity, attributes, narration, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                image_hash,
                photo_path,
                data.get("number"),
                data.get("name"),
                data.get("scientific_name"),
                data.get("category"),
                data.get("height"),
                data.get("weight"),
                data.get("habitat"),
                data.get("diet"),
                data.get("predator"),
                data.get("conservation"),
                data.get("description"),
                data.get("rarity", "普通"),
                attributes_json,
                data.get("narration"),
                raw_json,
            ),
        )
        await db.commit()
        row_id = cursor.lastrowid

        async with db.execute("SELECT * FROM entries WHERE id = ?", (row_id,)) as c:
            row = await c.fetchone()
            return _row_to_dict(row)


async def get_collection(category: Optional[str], limit: int, offset: int) -> tuple[int, list[dict]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        where = "WHERE category = ?" if category else ""
        params_count = (category,) if category else ()
        params_list = (category, limit, offset) if category else (limit, offset)

        async with db.execute(f"SELECT COUNT(*) FROM entries {where}", params_count) as c:
            total = (await c.fetchone())[0]

        async with db.execute(
            f"""SELECT id, number, name, category, rarity, photo_path, scanned_at
                FROM entries {where}
                ORDER BY scanned_at DESC
                LIMIT ? OFFSET ?""",
            params_list,
        ) as c:
            rows = await c.fetchall()
            entries = [_row_to_dict(row) for row in rows]

    return total, entries


async def get_entry_by_id(entry_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)) as c:
            row = await c.fetchone()
            if row:
                return _row_to_dict(row)
    return None


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT COUNT(*) FROM entries") as c:
            total = (await c.fetchone())[0]

        async with db.execute(
            "SELECT rarity, COUNT(*) as count FROM entries GROUP BY rarity"
        ) as c:
            by_rarity = {row["rarity"]: row["count"] for row in await c.fetchall()}

        async with db.execute(
            "SELECT category, COUNT(*) as count FROM entries GROUP BY category ORDER BY count DESC"
        ) as c:
            by_category = {row["category"]: row["count"] for row in await c.fetchall()}

        async with db.execute(
            "SELECT scanned_at FROM entries ORDER BY scanned_at DESC LIMIT 1"
        ) as c:
            row = await c.fetchone()
            latest = row["scanned_at"] if row else None

    return {
        "total": total,
        "by_rarity": by_rarity,
        "by_category": by_category,
        "latest_scanned_at": latest,
    }


def _row_to_dict(row) -> dict:
    d = dict(row)
    if d.get("attributes"):
        try:
            d["attributes"] = json.loads(d["attributes"])
        except Exception:
            d["attributes"] = []
    else:
        d["attributes"] = []
    if d.get("photo_path"):
        d["photo_url"] = f"/static/photos/{os.path.basename(d['photo_path'])}"
    else:
        d["photo_url"] = None
    return d
