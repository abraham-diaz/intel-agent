import logging
from datetime import datetime, timezone, timedelta

import httpx

from config import settings
from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://api.rawg.io/api"


class RAWGSource(BaseSource):
    source_name = "rawg"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        if not settings.rawg_api_key:
            logger.warning("RAWG_API_KEY not set, skipping")
            return []

        today = datetime.now(tz=timezone.utc)
        date_to = today.strftime("%Y-%m-%d")
        date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            resp = await client.get(
                f"{_BASE}/games",
                params={"key": settings.rawg_api_key, "dates": f"{date_from},{date_to}",
                        "ordering": "-added", "page_size": 20},
                timeout=15.0,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except httpx.HTTPError as e:
            logger.error("RAWG fetch: %s", e)
            return []

        return [
            RawItem(
                source_name=self.source_name,
                external_id=str(g["id"]),
                title=g["name"],
                url=f"https://rawg.io/games/{g.get('slug', g['id'])}",
                published_at=datetime.fromisoformat(g["released"]).replace(tzinfo=timezone.utc)
                if g.get("released") else None,
            )
            for g in results
            if g.get("name")
        ]
