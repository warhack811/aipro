from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.search.manager import SearchSnippet


def parse_weather_result(snippets: List[SearchSnippet]) -> Optional[Dict]:
    """Best-effort weather extractor from snippets."""
    if not snippets:
        return None

    temp_re = re.compile(r"(-?\d+(?:[.,]\d+)?)\s*°?\s*C", re.IGNORECASE)
    humidity_re = re.compile(r"humidity[:\s]+(\d+%?)", re.IGNORECASE)
    wind_re = re.compile(r"wind[:\s]+([\w\s/]+)", re.IGNORECASE)

    for sn in snippets:
        temp_match = temp_re.search(sn.snippet or "")
        if temp_match:
            temp = temp_match.group(1).replace(",", ".") + "°C"
            humidity = None
            wind = None
            hum_m = humidity_re.search(sn.snippet or "")
            if hum_m:
                humidity = hum_m.group(1)
            wind_m = wind_re.search(sn.snippet or "")
            if wind_m:
                wind = wind_m.group(1).strip()
            return {
                "type": "weather",
                "location": sn.title or "",
                "current_temp": temp,
                "condition": "",  # condition parsing zayıf kaldı; snippet kısa olabilir
                "humidity": humidity,
                "wind": wind,
                "source_url": sn.url,
            }
    return None


def parse_exchange_rate_result(snippets: List[SearchSnippet], base: str, quote: str) -> Optional[Dict]:
    """Best-effort döviz kuru çıkarıcı."""
    if not snippets:
        return None
    rate_re = re.compile(r"(\d+(?:[.,]\d+))")
    for sn in snippets:
        if base.lower() in (sn.title or "").lower() or base.lower() in (sn.snippet or "").lower():
            m = rate_re.search(sn.snippet or "")
            if m:
                rate = m.group(1).replace(",", ".")
                return {
                    "type": "exchange_rate",
                    "base": base.upper(),
                    "quote": quote.upper(),
                    "rate": rate,
                    "source_url": sn.url,
                }
    return None


def parse_sports_fixture_result(snippets: List[SearchSnippet], team_name: str) -> Optional[Dict]:
    """Best-effort fikstür çıkarıcı; organik snippetlerden tarih ve rakip arar."""
    if not snippets:
        return None

    date_re = re.compile(r"(\d{1,2}\s*[A-Za-zÇÖŞİĞÜçöşığü]+|\d{4}-\d{2}-\d{2})")
    matches: List[Dict] = []

    for sn in snippets:
        text = (sn.snippet or "") + " " + (sn.title or "")
        if team_name.lower() not in text.lower():
            continue
        date_m = date_re.search(text)
        date_val = date_m.group(1) if date_m else None
        # Rakip takım ve konum için basit heuristik
        opponent = None
        vs_m = re.search(rf"{team_name}\s*[-–]\s*([A-Za-zÇÖŞİĞÜçöşığü\s]+)", text, re.IGNORECASE)
        if not vs_m:
            vs_m = re.search(rf"([A-Za-zÇÖŞİĞÜçöşığü\s]+)\s*[-–]\s*{team_name}", text, re.IGNORECASE)
        if vs_m:
            opponent = vs_m.group(1).strip()

        matches.append(
            {
                "date": date_val,
                "home": team_name if vs_m and vs_m.start() < vs_m.end() else None,
                "away": opponent,
                "source_url": sn.url,
            }
        )

    return {"type": "sports_fixture", "team": team_name, "matches": matches or []}


def parse_standings_result(snippets: List[SearchSnippet], league_name: str) -> Optional[Dict]:
    """Basit puan durumu iskeleti; şu an boş/deneme."""
    return {"type": "standings", "league": league_name, "table": []}
