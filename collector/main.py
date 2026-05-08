import asyncio
import logging

from config import settings
from db import close_pool, init_pool
from scheduler import build_scheduler, collect
from sources.arxiv import ArXivSource
from sources.devto import DevToSource
from sources.github import GitHubSource
from sources.hn import HNSource
from sources.lastfm import LastFMSource
from sources.rawg import RAWGSource
from sources.reddit import RedditSource
from sources.tmdb import TMDBSource

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_ALL_SOURCES = [
    HNSource(),
    GitHubSource(),
    ArXivSource(),
    TMDBSource(),
    RAWGSource(),
    LastFMSource(),
    DevToSource(),
    RedditSource(),
]


async def main() -> None:
    await init_pool()

    logger.info("Initial collection run…")
    for source in _ALL_SOURCES:
        await collect(source)

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler running — Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
        await close_pool()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
