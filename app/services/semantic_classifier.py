from __future__ import annotations

import json
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.chat.decider import call_groq_api_safe_async
from app.config import get_settings

settings = get_settings()


class SemanticAnalysis(BaseModel):
    domain: str = Field(default="general")
    risk_level: str = Field(default="low")
    intent_type: str = Field(default="informational")
    sensitivity: List[str] = Field(default_factory=list)
    advice_type: str = Field(default="none")
    answer_mode: Literal["strict_structured", "web_factual", "free_opinion"] = Field(default="web_factual")
    data_freshness_needed: Literal["low", "medium", "high"] = Field(default="medium")
    is_structured_request: bool = Field(default=False)
    expected_data_format: Optional[Literal["text", "list", "table", "mixed"]] = None
    force_no_hallucination: Optional[bool] = None
    should_use_internet: bool = Field(default=False)
    user_requests_search: bool = Field(default=False)
    user_forbids_search: bool = Field(default=False)

    # YENİ ALANLAR - Cevap Kalitesi İyileştirmesi
    complexity: Literal["low", "medium", "high"] = Field(default="medium")
    creativity_level: Literal["low", "medium", "high"] = Field(default="medium")
    preferred_response_length: Literal["brief", "medium", "detailed"] = Field(default="medium")
    requires_step_by_step: bool = Field(default=False)


SEMANTIC_SYSTEM_PROMPT = r"""
Analyze the user message and return STRICT JSON with these fields:
- domain: ["health","finance","legal","sex","politics","religion","violence","tech","code","personal","relationships","mental_health","weather","sports","creative","general"]
- risk_level: "low" | "medium" | "high"
- intent_type: "informational" | "opinion" | "advice_low_risk" | "advice_high_risk" | "explicit_instruction" | "chat" | "emotional_support" | "story"
- sensitivity: ["sexual_content","swearing","hate_speech","insult","dark_humor","none", ...] (list; empty => ["none"])
- advice_type: "none" | "general_guidance" | "strong_guidance" | "high_risk_personal_decision"
- answer_mode: "strict_structured" | "web_factual" | "free_opinion"
- data_freshness_needed: "low" | "medium" | "high"
- is_structured_request: true/false
- expected_data_format: "text" | "list" | "table" | "mixed" | null
- force_no_hallucination: true/false/null
- user_requests_search: true/false (e.g., "internette ara", "google'da bak", "haberleri getir")
- user_forbids_search: true/false (e.g., "arama yapma", "internete bakma", "sadece sen konuş")
- should_use_internet: true/false (your overall judgment)
- complexity: "low" | "medium" | "high" (how complex is the question?)
- creativity_level: "low" | "medium" | "high" (does the answer need creativity?)
- preferred_response_length: "brief" | "medium" | "detailed"
- requires_step_by_step: true/false (does the question need step-by-step explanation?)

Rules for complexity:
- low: simple greetings, yes/no questions, basic facts
- medium: explanations, comparisons, general advice
- high: multi-step reasoning, technical deep-dives, complex analysis

Rules for creativity_level:
- low: factual queries, data lookups, technical questions (temperature ~0.2-0.4)
- medium: general chat, advice, explanations (temperature ~0.5-0.7)
- high: creative writing, stories, jokes, roleplay (temperature ~0.7-0.9)

Rules for preferred_response_length:
- brief: simple questions, greetings, confirmations (1-3 sentences)
- medium: most questions (1-3 paragraphs)
- detailed: "explain in detail", "tell me everything", complex topics

Rules for answer_mode:
- strict_structured: clear data/lookup requests (weather, currency/fx/coin price, fixtures/scores/standings, stock/market quotes, tabular/list info). Set is_structured_request=true, data_freshness_needed="high", force_no_hallucination=true.
- web_factual: general external facts/news/companies/events; freshness may be medium/high; structured request optional.
- free_opinion: chat/opinion/advice/relationships/emotional/creative writing/roleplay; usually data_freshness_needed="low", is_structured_request=false, force_no_hallucination=false.

TURKISH SPECIAL RULES (force strict_structured):
- If the message contains any of: "hava", "hava durumu", "bugün hava", "yarın hava", "sıcaklık", "derece":
  * domain="weather"
  * answer_mode="strict_structured"
  * is_structured_request=true
  * data_freshness_needed="high"
- If the message contains any of: "dolar kaç", "dolar şu an", "euro kaç", "euro şu an", "altın kaç", "gram altın", "bitcoin kaç", "btc kaç", "kur kaç", "ne kadar":
  * domain="finance"
  * answer_mode="strict_structured"
  * is_structured_request=true
  * data_freshness_needed="high"
- If the message contains any of: "fikstür", "fikstürü", "maç fikstürü", "maç programı", "maç takvimi", "puan durumu", "puan tablosu" AND a team name (e.g., "Galatasaray", "Fenerbahçe", "Beşiktaş", "GS", "FB", "BJK"):
  * domain="sports"
  * answer_mode="strict_structured"
  * is_structured_request=true
  * data_freshness_needed="high"
- In these cases, DO NOT choose web_factual or free_opinion; answer_mode must be strict_structured.

Always return valid JSON only; no explanations.
"""


def _derive_should_use_internet(raw: dict, message: str) -> bool:
    domain = raw.get("domain") or "general"
    risk = raw.get("risk_level") or "low"
    intent = (raw.get("intent_type") or "").lower()
    sensitivity = set(raw.get("sensitivity") or [])
    answer_mode = raw.get("answer_mode") or "web_factual"
    req = raw.get("user_requests_search") is True
    forbid = raw.get("user_forbids_search") is True

    if forbid:
        return False

    lowered = (message or "").lower()
    web_patterns = [
        "hava durumu",
        "bugün hava",
        "düzce hava",
        "dolar kaç",
        "euro kaç",
        "altın fiyat",
        "kur kaç",
        "haberler",
        "son seçim",
        "btc fiyat",
    ]
    if any(pat in lowered for pat in web_patterns):
        return True

    if answer_mode == "strict_structured":
        return True

    if domain in {"personal", "relationships", "mental_health"}:
        return True if req else False
    if intent in {"chat", "emotional_support", "story"}:
        return True if req else False

    if answer_mode == "free_opinion":
        return True if req else False

    if req:
        return True

    return raw.get("should_use_internet") is True


def _post_process_overrides(raw: dict, message: str) -> dict:
    lowered = message.lower()
    # Weather
    if any(kw in lowered for kw in ["hava durumu", "bugün hava", "yarın hava", "hava ", "sıcaklık", "derece"]):
        raw["domain"] = "weather"
        raw["answer_mode"] = "strict_structured"
        raw["is_structured_request"] = True
        raw["data_freshness_needed"] = "high"
        raw["force_no_hallucination"] = True
    # Finance / currency
    finance_patterns = [
        "dolar kaç",
        "dolar şu an",
        "euro kaç",
        "euro şu an",
        "altın kaç",
        "gram altın",
        "bitcoin kaç",
        "btc kaç",
        "kur kaç",
        "ne kadar",
    ]
    if any(pat in lowered for pat in finance_patterns):
        raw["domain"] = "finance"
        raw["answer_mode"] = "strict_structured"
        raw["is_structured_request"] = True
        raw["data_freshness_needed"] = "high"
        raw["force_no_hallucination"] = True
    # Sports fixtures/standings
    team_keywords = ["galatasaray", "fenerbahçe", "fenerbahce", "beşiktaş", "besiktas", "gs", "fb", "bjk"]
    if any(
        kw in lowered
        for kw in ["fikstür", "fikstürü", "maç fikstürü", "maç programı", "maç takvimi", "puan durumu", "puan tablosu"]
    ) and any(t in lowered for t in team_keywords):
        raw["domain"] = "sports"
        raw["answer_mode"] = "strict_structured"
        raw["is_structured_request"] = True
        raw["data_freshness_needed"] = "high"
        raw["force_no_hallucination"] = True
    # Additional direct overrides (broader patterns)
    if "hava" in lowered and "durumu" in lowered:
        raw["domain"] = "weather"
        raw["answer_mode"] = "strict_structured"
        raw["is_structured_request"] = True
        raw["data_freshness_needed"] = "high"
        raw["force_no_hallucination"] = True
    if any(tok in lowered for tok in ["dolar", "euro", "altın", "bitcoin", "btc"]) and any(
        tok in lowered for tok in ["kaç", "ne kadar"]
    ):
        raw["domain"] = "finance"
        raw["answer_mode"] = "strict_structured"
        raw["is_structured_request"] = True
        raw["data_freshness_needed"] = "high"
        raw["force_no_hallucination"] = True
    if any(tok in lowered for tok in ["fikstür", "fikstürü", "puan durumu", "puan tablosu"]) and any(
        t in lowered for t in team_keywords
    ):
        raw["domain"] = "sports"
        raw["answer_mode"] = "strict_structured"
        raw["is_structured_request"] = True
        raw["data_freshness_needed"] = "high"
        raw["force_no_hallucination"] = True
    return raw


async def analyze_message_semantics(message: str, now_iso: Optional[str] = None) -> SemanticAnalysis:
    """
    Groq üzerinden semantic etiket çıkarır.
    Hızlı model kullanarak performansı artırır.
    Hata durumunda güvenli varsayılan döner.
    """
    payload = [
        {"role": "system", "content": SEMANTIC_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    # Hızlı model kullan (semantic analiz için büyük model gereksiz)
    semantic_model = getattr(
        settings, "GROQ_SEMANTIC_MODEL", getattr(settings, "GROQ_FAST_MODEL", settings.GROQ_DECIDER_MODEL)
    )

    content, _ = await call_groq_api_safe_async(
        messages=payload,
        model=semantic_model,
        json_mode=True,
        temperature=0.0,
        timeout=10.0,
        max_retries=2,
    )
    if not content:
        return SemanticAnalysis()

    try:
        data = json.loads(content)
        data.setdefault("answer_mode", "web_factual")
        data.setdefault("data_freshness_needed", "medium")
        data.setdefault("is_structured_request", False)
        data = _post_process_overrides(data, message)
        data["should_use_internet"] = _derive_should_use_internet(data, message)
        return SemanticAnalysis(**data)
    except Exception:
        data = {}
        data["answer_mode"] = "web_factual"
        data["data_freshness_needed"] = "medium"
        data["is_structured_request"] = False
        data["should_use_internet"] = _derive_should_use_internet(data, message)
        return SemanticAnalysis(**data)
