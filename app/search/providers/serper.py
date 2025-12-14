from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class SerperResult:
    title: str
    url: str
    snippet: str


async def serper_search_async(
    query: str,
    max_results: int = 5,
    client: Optional[httpx.AsyncClient] = None,
    timeout: float = 6.0,
) -> List[SerperResult]:
    """
    Serper.dev üzerinden Google araması yapar (async).
    Basit iki denemeli retry içerir.
    """
    api_key = settings.SERPER_API_KEY
    endpoint = settings.SERPER_ENDPOINT

    if not api_key:
        logger.info("[SERPER] API key ayarlı değil, bu provider devre dışı.")
        return []

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "gl": "tr",
        "hl": "tr",
        "num": max_results,
    }

    async def _do_request(ac: httpx.AsyncClient) -> List[SerperResult]:
        resp = await ac.post(endpoint, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        organic = data.get("organic", [])
        results: List[SerperResult] = []
        for item in organic[:max_results]:
            title = item.get("title") or ""
            url = item.get("link") or item.get("url") or ""
            snippet = item.get("snippet") or item.get("description") or ""
            if not title and not snippet:
                continue
            results.append(SerperResult(title=title, url=url, snippet=snippet))
        return results

    # İki deneme: ilkinde hata olursa kısa bekleme ile tekrar dene.
    for attempt in range(2):
        try:
            if client is not None:
                results = await _do_request(client)
            else:
                async with httpx.AsyncClient() as ac:
                    results = await _do_request(ac)
            logger.info(f"[SERPER] '{query}' için {len(results)} sonuç döndü.")
            return results
        except Exception as e:
            logger.warning(f"[SERPER] Arama sorunu (deneme {attempt+1}/2): {e}")
            if attempt == 0:
                continue
    return []
