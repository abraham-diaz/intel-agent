import logging
import re
from datetime import datetime
from xml.etree import ElementTree as ET

import httpx

from models import RawItem
from sources.base import BaseSource

logger = logging.getLogger(__name__)

_API = "http://export.arxiv.org/api/query"
_QUERY = "cat:cs.AI OR cat:cs.LG OR cat:cs.SE"
_NS = {"a": "http://www.w3.org/2005/Atom"}


class ArXivSource(BaseSource):
    source_name = "arxiv"

    async def fetch(self, client: httpx.AsyncClient) -> list[RawItem]:
        try:
            resp = await client.get(
                _API,
                params={"search_query": _QUERY, "start": 0, "max_results": 50,
                        "sortBy": "submittedDate", "sortOrder": "descending"},
                timeout=20.0,
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except (httpx.HTTPError, ET.ParseError) as e:
            logger.error("arXiv fetch: %s", e)
            return []

        items: list[RawItem] = []
        for entry in root.findall("a:entry", _NS):
            raw_id = entry.findtext("a:id", "", _NS)
            arxiv_id = raw_id.split("/abs/")[-1]
            title_el = entry.find("a:title", _NS)
            summary_el = entry.find("a:summary", _NS)
            published_el = entry.find("a:published", _NS)

            title = re.sub(r"\s+", " ", (title_el.text or "").strip()) if title_el is not None else ""
            summary = re.sub(r"\s+", " ", (summary_el.text or "").strip()) if summary_el is not None else ""

            if not arxiv_id or not title:
                continue

            published_at = None
            if published_el is not None and published_el.text:
                try:
                    published_at = datetime.fromisoformat(published_el.text.replace("Z", "+00:00"))
                except ValueError:
                    pass

            items.append(RawItem(
                source_name=self.source_name,
                external_id=arxiv_id,
                title=title,
                category="tech-ai",
                url=raw_id,
                description=summary[:500] if summary else None,
                published_at=published_at,
            ))
        return items
