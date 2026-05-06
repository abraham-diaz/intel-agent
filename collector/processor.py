import json
import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "tech-ai", "tech-frontend", "tech-infra", "tech-other",
    "gaming", "music", "film-tv",
}

_PROMPT = """\
Dado el siguiente contenido, devuelve SOLO un JSON con esta estructura:
{{
  "summary": ["bullet 1", "bullet 2", "bullet 3"],
  "category": "<una de: tech-ai, tech-frontend, tech-infra, tech-other, gaming, music, film-tv>",
  "tags": ["tag1", "tag2", "tag3"]
}}

Contenido: {title} — {description}"""


async def process_item(
    item_id: int,
    title: str,
    description: str | None,
    client: httpx.AsyncClient,
) -> dict | None:
    prompt = _PROMPT.format(title=title, description=description or "")
    try:
        resp = await client.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = json.loads(resp.json()["response"])
        if data.get("category") not in VALID_CATEGORIES:
            data["category"] = "tech-other"
        return data
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        logger.warning("LLM failed for item %d: %s", item_id, e)
        return None
