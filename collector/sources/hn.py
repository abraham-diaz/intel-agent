import logging
from datetime import datetime, timezone

import httpx

from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://hacker-news.firebaseio.com/v0"
_TOP_N = 30


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

        items: list[RawItem] = []
        for story_id in ids:
            try:
                r = await client.get(f"{_BASE}/item/{story_id}.json", timeout=10.0)
                r.raise_for_status()
                d = r.json()
                if not d or d.get("type") != "story" or not d.get("title"):
                    continue
                items.append(RawItem(
                    source_name=self.source_name,
                    external_id=str(d["id"]),
                    title=d["title"],
                    url=d.get("url"),
                    description=d.get("text"),
                    published_at=datetime.fromtimestamp(d["time"], tz=timezone.utc)
                    if d.get("time") else None,
                ))
            except httpx.HTTPError as e:
                logger.warning("HN item %d: %s", story_id, e)
        return items
