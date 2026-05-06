import json
import logging
from typing import Optional

import asyncpg

from config import settings
from models import RawItem

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.db_dsn, min_size=1, max_size=5, init=_init_conn)
    logger.info("DB pool ready")


async def close_pool() -> None:
    if _pool:
        await _pool.close()


def _pool_ref() -> asyncpg.Pool:
    assert _pool is not None, "Pool not initialized — call init_pool() first"
    return _pool


async def ensure_source(name: str) -> int:
    pool = _pool_ref()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sources (name) VALUES ($1) ON CONFLICT (name) DO NOTHING",
            name,
        )
        row = await conn.fetchrow("SELECT id FROM sources WHERE name = $1", name)
        return row["id"]


async def save_items(items: list[RawItem]) -> int:
    if not items:
        return 0
    pool = _pool_ref()
    saved = 0
    async with pool.acquire() as conn:
        for item in items:
            source_id = await ensure_source(item.source_name)
            result = await conn.execute(
                """
                INSERT INTO items (source_id, external_id, title, url, description, published_at, category)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (source_id, external_id) DO UPDATE
                SET description = EXCLUDED.description
                WHERE items.description IS NULL
                """,
                source_id,
                item.external_id,
                item.title,
                item.url,
                item.description,
                item.published_at,
                item.category,
            )
            if result == "INSERT 0 1":
                saved += 1
    return saved


async def cleanup_old_items(ttl_days: int) -> int:
    pool = _pool_ref()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM items WHERE collected_at < NOW() - ($1 || ' days')::interval",
            str(ttl_days),
        )
        deleted = int(result.split()[-1])
        if deleted:
            logger.info("Cleaned up %d items older than %d days", deleted, ttl_days)
        return deleted


async def mark_source_run(name: str) -> None:
    pool = _pool_ref()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sources SET last_run = NOW() WHERE name = $1",
            name,
        )
