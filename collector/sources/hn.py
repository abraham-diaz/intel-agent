import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://hacker-news.firebaseio.com/v0"
_TOP_N = 50
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; intel-agent/1.0)"}
_SEMAPHORE = asyncio.Semaphore(10)


async def _fetch_item(story_id: int, client: httpx.AsyncClient) -> RawItem | None:
    async with _SEMAPHORE:
        try:
            r = await client.get(f"{_BASE}/item/{story_id}.json", timeout=10.0)
            r.raise_for_status()
            d = r.json()
            if not d or d.get("type") != "story" or not d.get("title"):
                return None
            return RawItem(
                source_name="hackernews",
                external_id=str(d["id"]),
                title=d["title"],
                category="tech-other",
                url=d.get("url"),
                description=d.get("text"),
                published_at=datetime.fromtimestamp(d["time"], tz=timezone.utc)
                if d.get("time") else None,
            )
        except httpx.HTTPError as e:
            logger.warning("HN item %d: %s", story_id, e)
            return None


async def _fetch_meta_desc(url: str, client: httpx.AsyncClient) -> str | None:
    async with _SEMAPHORE:
        try:
            r = await client.get(url, timeout=5.0, follow_redirects=True, headers=_HEADERS)
            soup = BeautifulSoup(r.text, "html.parser")
            tag = soup.find("meta", property="og:description") or \
                  soup.find("meta", attrs={"name": "description"})
            if tag and tag.get("content"):
                return tag["content"][:300].strip()
        except Exception:
            pass
        return None


class HNSource(BaseSource):
    source_name = "hackernews"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        try:
            resp = await client.get(f"{_BASE}/topstories.json", timeout=15.0)
            resp.raise_for_status()
            ids: list[int] = resp.json()[:_TOP_N]
        except httpx.HTTPError as e:
            logger.error("HN top stories: %s", e)
            return []

        results = await asyncio.gather(*[_fetch_item(sid, client) for sid in ids])
        items = [item for item in results if item is not None]

        items_with_url = [item for item in items if item.url and not item.description]
        if items_with_url:
            descs = await asyncio.gather(*[_fetch_meta_desc(item.url, client) for item in items_with_url])
            for item, desc in zip(items_with_url, descs):
                if desc:
                    item.description = desc

        return items
