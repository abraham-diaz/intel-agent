import json
import logging
from typing import Optional

import asyncpg

from config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.db_dsn, min_size=1, max_size=3, init=_init_conn)


async def close_pool() -> None:
    if _pool:
        await _pool.close()


def _p() -> asyncpg.Pool:
    assert _pool is not None
    return _pool


async def get_items_by_category(category: str, limit: int = 10) -> list[asyncpg.Record]:
    async with _p().acquire() as conn:
        return await conn.fetch(
            """
            SELECT title, url, summary, category, tags
            FROM items
            WHERE category = $1 AND processed = TRUE
            ORDER BY collected_at DESC
            LIMIT $2
            """,
            category, limit,
        )


async def get_today_items() -> list[asyncpg.Record]:
    async with _p().acquire() as conn:
        return await conn.fetch(
            """
            SELECT title, url, summary, category
            FROM items
            WHERE collected_at >= CURRENT_DATE AND processed = TRUE
            ORDER BY category, collected_at DESC
            """,
        )


async def search_items(query: str, limit: int = 10) -> list[asyncpg.Record]:
    async with _p().acquire() as conn:
        return await conn.fetch(
            """
            SELECT title, url, summary, category
            FROM items
            WHERE title ILIKE $1 AND processed = TRUE
            ORDER BY collected_at DESC
            LIMIT $2
            """,
            f"%{query}%", limit,
        )


async def get_source_status() -> list[asyncpg.Record]:
    async with _p().acquire() as conn:
        return await conn.fetch(
            "SELECT name, enabled, last_run FROM sources ORDER BY name",
        )
