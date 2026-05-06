import logging

import httpx

from config import settings
from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://api.themoviedb.org/3"


class TMDBSource(BaseSource):
    source_name = "tmdb"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        if not settings.tmdb_api_key:
            logger.warning("TMDB_API_KEY not set, skipping")
            return []

        items: list[RawItem] = []
        for media_type in ("movie", "tv"):
            try:
                resp = await client.get(
                    f"{_BASE}/trending/{media_type}/week",
                    params={"api_key": settings.tmdb_api_key, "language": "en-US"},
                    timeout=15.0,
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
            except httpx.HTTPError as e:
                logger.error("TMDB %s fetch: %s", media_type, e)
                continue

            for r in results:
                title = r.get("title") or r.get("name", "")
                if not title:
                    continue
                items.append(RawItem(
                    source_name=self.source_name,
                    external_id=f"{media_type}-{r['id']}",
                    title=title,
                    category="film-tv",
                    url=f"https://www.themoviedb.org/{media_type}/{r['id']}",
                    description=r.get("overview") or None,
                ))

        return items
