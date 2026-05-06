import asyncio
import logging

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import get_unprocessed_items, mark_source_run, save_items, update_item_llm
from processor import process_item
from sources.arxiv import ArXivSource
from sources.base import BaseSource
from sources.github import GitHubSource
from sources.hn import HNSource
from sources.lastfm import LastFMSource
from sources.rawg import RAWGSource
from sources.tmdb import TMDBSource

logger = logging.getLogger(__name__)


async def collect(source: BaseSource) -> None:
    async with httpx.AsyncClient() as client:
        logger.info("Collecting %s…", source.source_name)
        items = await source.fetch(client)
        saved = await save_items(items)
        await mark_source_run(source.source_name)
        logger.info("%s: %d new / %d fetched", source.source_name, saved, len(items))


async def process_pending() -> None:
    rows = await get_unprocessed_items(limit=20)
    if not rows:
        return
    logger.info("Processing %d pending items…", len(rows))
    async with httpx.AsyncClient() as client:
        for row in rows:
            result = await process_item(row["id"], row["title"], row["description"], client)
            if result:
                await update_item_llm(
                    row["id"],
                    result.get("summary", []),
                    result.get("category", "tech-other"),
                    result.get("tags", []),
                )
            await asyncio.sleep(1)  # no saturar la raspi entre llamadas LLM


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(collect, "interval", hours=2,   args=[HNSource()],     id="collect_hn")
    scheduler.add_job(collect, "interval", hours=6,   args=[GitHubSource()], id="collect_github")
    scheduler.add_job(collect, "interval", hours=12,  args=[ArXivSource()],  id="collect_arxiv")
    scheduler.add_job(collect, "interval", hours=24,  args=[TMDBSource()],   id="collect_tmdb")
    scheduler.add_job(collect, "interval", hours=24,  args=[RAWGSource()],   id="collect_rawg")
    scheduler.add_job(collect, "interval", hours=6,   args=[LastFMSource()], id="collect_lastfm")
    scheduler.add_job(process_pending, "interval", minutes=30, id="process_pending")

    return scheduler
