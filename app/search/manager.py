from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List

import httpx

from app.config import get_settings
from app.core.logger import get_logger
from app.search.providers.bing import BingResult, bing_search_async  # Bing
from app.search.providers.serper import SerperResult, serper_search_async  # Google

# DuckDuckGo entegrasyonu eklenirse buraya import edilir.

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class SearchQuery:
    id: str
    query: str


@dataclass
class SearchSnippet:
    """LLM'e gönderilecek standardize edilmiş arama sonucu."""

    title: str
    url: str
    snippet: str


def _convert_serper_results(results: List[SerperResult]) -> List[SearchSnippet]:
    return [SearchSnippet(title=r.title, url=r.url, snippet=r.snippet) for r in results]


def _convert_bing_results(results: List[BingResult]) -> List[SearchSnippet]:
    return [SearchSnippet(title=r.title, url=r.url, snippet=r.snippet) for r in results]


async def search_queries_async(query_items: List[Dict[str, str]]) -> Dict[str, List[SearchSnippet]]:
    """
    Decider'dan gelen sorguları asenkron işler.
    Provider sırası: 1) Serper (Google) -> 2) Bing -> 3) (opsiyonel) Duck.
    """
    queries: List[SearchQuery] = []
    for idx, q in enumerate(query_items):
        queries.append(
            SearchQuery(
                id=q.get("id", f"q{idx+1}"),
                query=q.get("query", ""),
            )
        )

    results: Dict[str, List[SearchSnippet]] = {}

    # Tek bir async client ile yeniden kullanım
    timeout = httpx.Timeout(6.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for q in queries:
            if not q.query:
                results[q.id] = []
                continue

            logger.info(f"[SEARCH] query_id={q.id} query={q.query!r}")

            snippets: List[SearchSnippet] = []

            # 1) Serper (ana kaynak)
            serper_results: List[SerperResult] = await serper_search_async(q.query, max_results=5, client=client)
            if serper_results:
                snippets = _convert_serper_results(serper_results)
            else:
                # 2) Bing fallback
                bing_results: List[BingResult] = await bing_search_async(q.query, max_results=5, client=client)
                if bing_results:
                    snippets = _convert_bing_results(bing_results)
                else:
                    logger.warning("[SEARCH] Serper ve Bing başarısız. Duck entegrasyonu pasif/eksik.")
                    # Duck entegrasyonu eklenirse burada devreye alınır.

            results[q.id] = snippets

    return results
