import logging
from datetime import datetime

import httpx

from config import settings
from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_BASE = "https://dev.to/api"


class DevToSource(BaseSource):
    source_name = "devto"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        headers = {"Accept": "application/vnd.forem.api-v1+json"}
        seen: set[str] = set()
        items: list[RawItem] = []

        if settings.devto_api_key:
            headers["api-key"] = settings.devto_api_key
            # Authenticated: fetch personalized feed (follows tags the user set on DEV.to)
            # plus the espanol tag for Spanish-specific content
            endpoints = [
                ("articles", {"per_page": 30}),
                ("articles", {"tag": "espanol", "per_page": 20}),
            ]
        else:
            endpoints = [
                ("articles", {"tag": "espanol", "per_page": 30}),
            ]

        for path, params in endpoints:
            try:
                resp = await client.get(
                    f"{_BASE}/{path}",
                    params=params,
                    headers=headers,
                    timeout=15.0,
                )
                resp.raise_for_status()
                articles = resp.json()
            except httpx.HTTPError as e:
                logger.error("DEV.to fetch (%s): %s", params, e)
                continue

            for a in articles:
                if not a.get("title") or str(a["id"]) in seen:
                    continue
                seen.add(str(a["id"]))
                items.append(RawItem(
                    source_name=self.source_name,
                    external_id=str(a["id"]),
                    title=a["title"],
                    category="tech-other",
                    url=a.get("url"),
                    description=a.get("description"),
                    published_at=datetime.fromisoformat(a["published_at"].replace("Z", "+00:00"))
                    if a.get("published_at") else None,
                ))

        return items
