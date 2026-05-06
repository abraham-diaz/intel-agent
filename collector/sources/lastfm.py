import logging

import httpx

from config import settings
from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://ws.audioscrobbler.com/2.0/"


class LastFMSource(BaseSource):
    source_name = "lastfm"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        if not settings.lastfm_api_key:
            logger.warning("LASTFM_API_KEY not set, skipping")
            return []

        try:
            resp = await client.get(
                _BASE,
                params={"method": "chart.gettoptracks", "api_key": settings.lastfm_api_key,
                        "format": "json", "limit": 30},
                timeout=15.0,
            )
            resp.raise_for_status()
            tracks = resp.json().get("tracks", {}).get("track", [])
        except httpx.HTTPError as e:
            logger.error("Last.fm fetch: %s", e)
            return []

        return [
            RawItem(
                source_name=self.source_name,
                external_id=f"{t.get('artist', {}).get('name', 'unknown')}-{t['name']}",
                title=f"{t['name']} — {t.get('artist', {}).get('name', '')}",
                url=t.get("url"),
            )
            for t in tracks
            if t.get("name")
        ]
