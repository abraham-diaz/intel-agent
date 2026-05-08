import logging

import httpx

from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://www.reddit.com"
_USER_AGENT = "intel-agent/1.0 (personal aggregator)"

_SUBREDDITS = [
    ("programacion", "tech-other"),
    ("linuxes", "tech-infra"),
]


class RedditSource(BaseSource):
    source_name = "reddit"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        items: list[RawItem] = []

        for subreddit, category in _SUBREDDITS:
            try:
                resp = await client.get(
                    f"{_BASE}/r/{subreddit}/hot.json",
                    params={"limit": 25},
                    headers={"User-Agent": _USER_AGENT},
                    timeout=15.0,
                )
                resp.raise_for_status()
                posts = resp.json().get("data", {}).get("children", [])
            except httpx.HTTPError as e:
                logger.error("Reddit r/%s: %s", subreddit, e)
                continue

            for post in posts:
                d = post.get("data", {})
                if d.get("stickied") or not d.get("title"):
                    continue
                selftext = d.get("selftext", "")
                description = (
                    selftext[:500]
                    if selftext and selftext not in ("[removed]", "[deleted]")
                    else None
                )
                items.append(RawItem(
                    source_name=self.source_name,
                    external_id=d["id"],
                    title=d["title"],
                    category=category,
                    url=d.get("url") or f"https://www.reddit.com{d.get('permalink', '')}",
                    description=description,
                ))

        return items
