# -*- coding: utf-8 -*-
"""
Tool Output Formatter
=====================

Web araması ve diğer tool çıktılarını standart formatta sunar.
"Özet + Detaylar + Kaynaklar" yapısı ile ChatGPT benzeri görünüm.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """URL'den domain çıkarır."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # www. prefix'ini kaldır
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def format_web_result(
    answer_text: str,
    sources: Optional[List[Dict[str, Any]]] = None,
    max_sources: int = 5,
) -> str:
    """
    Web araması sonuçlarını standart formatta sunar.

    Args:
        answer_text: Model tarafından üretilen cevap metni
        sources: Kaynak listesi [{"title": str, "url": str, "snippet": str, "date": str?}]
        max_sources: Maksimum kaynak sayısı

    Returns:
        Formatlanmış çıktı (Özet + Detaylar + Kaynaklar)
    """
    if not answer_text:
        return ""

    parts = []

    # 1. Ana cevap (zaten model tarafından üretilmiş)
    parts.append(answer_text.strip())

    # 2. Kaynaklar bölümü (varsa)
    if sources and len(sources) > 0:
        sources_section = _format_sources_section(sources[:max_sources])
        if sources_section:
            parts.append("")  # Boş satır
            parts.append(sources_section)

    result = "\n".join(parts)

    # Log
    source_count = len(sources) if sources else 0
    logger.info(f"[TOOLFMT] kind=web sources={source_count}")

    return result


def _format_sources_section(sources: List[Dict[str, Any]]) -> str:
    """Kaynaklar bölümünü formatlar."""
    if not sources:
        return ""

    lines = ["### Kaynaklar"]

    for source in sources:
        title = source.get("title", "").strip()
        url = source.get("url", "")
        date = source.get("date", "")

        if not title and not url:
            continue

        domain = extract_domain(url) if url else ""

        # Format: - **Başlık** — domain.com (tarih)
        if title:
            line = f"- **{title}**"
            if domain:
                line += f" — {domain}"
            if date:
                line += f" ({date})"
        else:
            line = f"- {domain}"
            if date:
                line += f" ({date})"

        lines.append(line)

    return "\n".join(lines)


def format_search_summary(
    query: str,
    answer: str,
    sources: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Arama sonucu için tam özet formatı.

    Args:
        query: Arama sorgusu
        answer: Model cevabı
        sources: Kaynak listesi

    Returns:
        Formatlanmış tam çıktı
    """
    # Ana cevabı formatla
    formatted = format_web_result(answer, sources)

    return formatted


def format_image_result(
    image_url: str,
    prompt: str,
    model: str = "unknown",
) -> str:
    """
    Görsel üretim sonucunu formatlar.

    Args:
        image_url: Üretilen görsel URL'i
        prompt: Kullanılan prompt
        model: Kullanılan model

    Returns:
        Formatlanmış çıktı
    """
    parts = []

    # Görsel referansı (markdown image)
    parts.append(f"![Üretilen Görsel]({image_url})")

    # Kullanılan prompt (kısa, gri)
    if prompt:
        short_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
        parts.append(f"\n*Prompt: {short_prompt}*")

    logger.info(f"[TOOLFMT] kind=image model={model}")

    return "\n".join(parts)
