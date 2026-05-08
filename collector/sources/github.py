import logging
from datetime import datetime, timezone, timedelta

import httpx

from config import settings
from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_SEARCH = "https://api.github.com/search/repositories"


class GitHubSource(BaseSource):
    source_name = "github"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        since = (datetime.now(tz=timezone.utc) - timedelta(days=settings.item_ttl_days)).strftime("%Y-%m-%d")
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        try:
            resp = await client.get(
                _SEARCH,
                params={"q": f"created:>{since}", "sort": "stars", "order": "desc", "per_page": 50},
                headers=headers,
                timeout=15.0,
            )
            resp.raise_for_status()
            repos = resp.json().get("items", [])
        except httpx.HTTPError as e:
            logger.error("GitHub search: %s", e)
            return []

        return [
            RawItem(
                source_name=self.source_name,
                external_id=str(r["id"]),
                title=r["full_name"],
                category="tech-infra",
                url=r["html_url"],
                description=r.get("description"),
                published_at=datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                if r.get("created_at") else None,
            )
            for r in repos
        ]
