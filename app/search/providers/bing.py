from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class BingResult:
    title: str
    url: str
    snippet: str


async def bing_search_async(
    query: str,
    max_results: int = 5,
    client: Optional[httpx.AsyncClient] = None,
    timeout: float = 3.0,
) -> List[BingResult]:
    """
    Bing Web Search API üzerinden arama yapar (async).
    Kısa timeout + iki deneme ile çalışır.
    """
    api_key = settings.BING_API_KEY
    endpoint = settings.BING_ENDPOINT

    if not api_key:
        logger.info("[BING] API key ayarlı değil, bu provider devre dışı.")
        return []

    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
    }

    params = {
        "q": query,
        "count": max_results,
        "mkt": "tr-TR",
        "responseFilter": "Webpages",
    }

    async def _do_request(ac: httpx.AsyncClient) -> List[BingResult]:
        resp = await ac.get(endpoint, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        web = data.get("webPages", {}).get("value", [])
        results: List[BingResult] = []
        for item in web:
            title = item.get("name") or ""
            url = item.get("url") or ""
            snippet = item.get("snippet") or item.get("description") or ""
            if not title and not snippet:
                continue
            results.append(BingResult(title=title, url=url, snippet=snippet))
        return results

    for attempt in range(2):
        try:
            if client is not None:
                results = await _do_request(client)
            else:
                async with httpx.AsyncClient() as ac:
                    results = await _do_request(ac)
            logger.info(f"[BING] '{query}' için {len(results)} sonuç döndü.")
            return results
        except Exception as e:
            logger.warning(f"[BING] Arama sorunu (deneme {attempt+1}/2): {e}")
            if attempt == 0:
                continue
    return []
