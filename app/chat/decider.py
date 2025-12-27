"""
Mami AI - Groq API & Query Builder
==================================

Bu modül Groq API çağrıları ve arama sorgusu üretimi yapar.

Sorumluluklar:
    - Groq API çağrıları (çoklu anahtar rotasyonu)
    - INTERNET için arama sorgusu üretimi
    - Hafıza kayıt kararları

Kullanım:
    from app.chat.decider import call_groq_api_async, build_search_queries_async

    # Groq API çağrısı
    response = await call_groq_api_async(messages, model="llama-3.3-70b")

    # İnternet araması için sorgu üretimi
    queries = await build_search_queries_async("Dolar kuru nedir?")
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# YAPILANDIRMA
# =============================================================================

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
"""Groq API endpoint URL'si."""

DEFAULT_GROQ_TIMEOUT = 15.0
"""Varsayılan API zaman aşımı (saniye)."""


# =============================================================================
# LAZY IMPORTS & API KEY YÖNETİMİ
# =============================================================================


def _get_settings():
    """Ayarları lazy import ile yükler."""
    from app.config import get_settings

    return get_settings()


def _get_available_keys() -> List[str]:
    """
    Tüm geçerli Groq API anahtarlarını döndürür.

    Boş olmayan anahtarlar rotasyon için sırayla denenir.
    """
    settings = _get_settings()
    keys = [
        settings.GROQ_API_KEY,
        settings.GROQ_API_KEY_BACKUP,
        settings.GROQ_API_KEY_4,
        getattr(settings, "GROQ_API_KEY_3", None),
    ]
    return [k for k in keys if k]


# =============================================================================
# GROQ API FONKSİYONLARI
# =============================================================================


async def call_groq_api_async(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    json_mode: bool = False,
    temperature: float = 0.7,
    timeout: float = DEFAULT_GROQ_TIMEOUT,
) -> Optional[str]:
    """
    Groq Chat API çağrısı (async, anahtar rotasyonlu).

    Tüm anahtarlar sırayla denenir. 429 (rate limit) durumunda
    otomatik olarak sonraki anahtara geçilir.

    Args:
        messages: OpenAI formatında mesaj listesi
        model: Kullanılacak model (varsayılan: GROQ_DECIDER_MODEL)
        json_mode: JSON çıktı modu
        temperature: Yaratıcılık seviyesi (0.0-1.0)
        timeout: İstek zaman aşımı

    Returns:
        str veya None: API yanıtı veya hata durumunda None
    """
    settings = _get_settings()
    available_keys = _get_available_keys()

    if not available_keys:
        logger.error("[GROQ] Hiçbir API anahtarı tanımlı değil!")
        return None

    model = model or settings.GROQ_DECIDER_MODEL

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    for index, api_key in enumerate(available_keys):
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if content:
                    logger.info(f"[GROQ] Anahtar {index+1} başarılı")
                    return content

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                logger.warning(f"[GROQ] Anahtar {index+1} kotası doldu, sıradakine geçiliyor...")
                continue
            # 400 hatası detayını göster
            try:
                error_detail = exc.response.json()
                logger.error(f"[GROQ] Anahtar {index+1} HTTP hatası: {status} - {error_detail}")
            except Exception:
                logger.error(f"[GROQ] Anahtar {index+1} HTTP hatası: {status} - {exc.response.text[:200]}")
            continue
        except Exception as exc:
            logger.error(f"[GROQ] Anahtar {index+1} beklenmeyen hata: {exc}")
            continue

    logger.critical("[GROQ] TÜM ANAHTARLAR TÜKENDİ VEYA HATA VERDİ!")
    return None


async def call_groq_api_safe_async(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    json_mode: bool = False,
    temperature: float = 0.7,
    timeout: float = DEFAULT_GROQ_TIMEOUT,
    max_retries: int = 2,
) -> tuple[Optional[str], Optional[str]]:
    """
    Retry mekanizmalı güvenli Groq API çağrısı.

    Args:
        messages: Mesaj listesi
        model: Model adı
        json_mode: JSON modu
        temperature: Sıcaklık
        timeout: Zaman aşımı
        max_retries: Maksimum deneme sayısı

    Returns:
        tuple: (content, error_str) - İkisinden biri None olur
    """
    settings = _get_settings()
    model = model or settings.GROQ_DECIDER_MODEL

    last_error: Optional[str] = None
    for attempt in range(max_retries):
        content = await call_groq_api_async(
            messages=messages,
            model=model,
            json_mode=json_mode,
            temperature=temperature,
            timeout=timeout,
        )
        if content:
            return content, None
        last_error = "empty_response"

    return None, last_error


async def call_groq_api_stream_async(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    timeout: float = DEFAULT_GROQ_TIMEOUT,
) -> AsyncGenerator[str, None]:
    """
    Streaming Groq API çağrısı.

    Args:
        messages: Mesaj listesi
        model: Model adı
        temperature: Sıcaklık
        timeout: Zaman aşımı

    Yields:
        str: Yanıt parçaları
    """
    settings = _get_settings()
    available_keys = _get_available_keys()
    model = model or settings.GROQ_DECIDER_MODEL

    if not available_keys:
        logger.error("[GROQ_STREAM] Hiçbir API anahtarı tanımlı değil!")
        yield "[ERROR] No API keys available."
        return

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }

    key_exhausted = False
    for index, api_key in enumerate(available_keys):
        headers = {"Authorization": f"Bearer {api_key}"}
        key_exhausted = False
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", GROQ_API_URL, headers=headers, json=payload) as resp:
                    if resp.status_code == 429:
                        logger.warning(f"[GROQ_STREAM] Anahtar {index+1} kotası doldu")
                        key_exhausted = True
                        continue

                    resp.raise_for_status()
                    logger.info(f"[GROQ_STREAM] Anahtar {index+1} başarılı")

                    # ✅ FIX: Use aiter_lines() to respect UTF-8 and line boundaries
                    async for line in resp.aiter_lines():
                        if not line:
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]  # len("data: ") = 6
                            if data_str == "[DONE]":
                                return

                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                            except json.JSONDecodeError as e:
                                # Log but don't drop - should never happen with aiter_lines()
                                logger.warning(
                                    f"[GROQ_STREAM] JSON parse error (line intact): {e} | Line: {line[:100]}"
                                )
                                continue
                    return

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                key_exhausted = True
            else:
                logger.error(f"[GROQ_STREAM] HTTP hatası: {exc.response.status_code}")
            continue
        except Exception as exc:
            logger.error(f"[GROQ_STREAM] Beklenmeyen hata: {exc}")
            continue

    logger.critical("[GROQ_STREAM] TÜM ANAHTARLAR TÜKENDİ!")
    yield " [ERROR] Tüm API anahtarları tükendi. "


# =============================================================================
# SİSTEM PROMPTLARI
# =============================================================================

# DECIDER_SYSTEM_PROMPT silindi - SmartRouter artık action belirliyor

MEMORY_DECIDER_SYSTEM_PROMPT = """
Sen bir KİŞİSEL BİLGİ FİLTRESİSİN. Görevin: SADECE kullanıcının KENDİSİNE AİT kişisel bilgileri tespit etmek.

## 🔴 KRİTİK KURAL: SADECE KİŞİSEL BİLGİLERİ KAYDET

### ✅ SADECE BUNLARI KAYDET (store: true):
1. **Kimlik Bilgileri**: "Benim adım...", "Ben 25 yaşındayım", "Erkek/Kadınım"
2. **Konum**: "İstanbul'da yaşıyorum", "Ankara'dan yazıyorum"
3. **Meslek/İş**: "Yazılımcıyım", "Öğrenciyim", "Doktorum"
4. **Aile/İlişki**: "Evliyim", "2 çocuğum var", "Annemin adı..."
5. **Evcil Hayvan**: "Kedim var, adı Pamuk", "Köpeğim Max"
6. **Hobiler**: "Futbol severim", "Piyano çalıyorum", "Kitap okumayı severim"
7. **Tercihler**: "React kullanıyorum", "Kahve sevmem", "Vejeteryanım"
8. **Hedefler**: "İngilizce öğreniyorum", "Yazılım öğrenmek istiyorum"

### ❌ ASLA BUNLARI KAYDETME (store: false):
1. **Genel Bilgi**: "Türkiye'nin başkenti Ankara", "Dünya yuvarlak"
2. **Tanımlar**: "Python bir programlama dili", "AI yapay zeka demek"
3. **Matematik**: "2+2=4", "Pi sayısı 3.14"
4. **Tarihsel Gerçekler**: "Atatürk 1881'de doğdu", "İstanbul 1453'te fethedildi"
5. **Güncel Olaylar**: "Dolar 34 TL", "Bugün hava güneşli"
6. **Geçici Durumlar**: "Şu an mutluyum", "Bugün yorgunum"
7. **Sohbet Konuları**: "Bana bir şaka anlat", "Kod yaz", "Çeviri yap"

## KARAR VERİRKEN KENDİNE SOR:
"Bu bilgi bu KULLANICIYA mı özgü, yoksa HERKES için geçerli mi?"
- Kullanıcıya özgü → store: true
- Herkes için geçerli → store: false

## KATEGORİLER (sadece store: true ise):
- identity: İsim, yaş, cinsiyet
- location: Şehir, ülke
- profession: Meslek, iş
- family: Aile, ilişki
- preferences: Tercihler, hobiler
- goals: Hedefler

## CONFLICT CHECK:
Eğer yeni bilgi mevcut bir hafıza ile çelişiyorsa (örn: "Artık Ankara'da yaşıyorum" vs mevcut "İstanbul'da yaşıyor"), eski hafızayı `invalidate` listesine ekle.

## ÖNEMLİ ÖRNEKLER:

Kullanıcı: "Türkiye'nin başkenti neresi?"
Asistan: "Türkiye'nin başkenti Ankara'dır."
→ {"store": false} (Genel bilgi, kişisel değil)

Kullanıcı: "Benim adım Mehmet"
Asistan: "Memnun oldum Mehmet!"
→ {"store": true, "memory": "Kullanıcının adı Mehmet", "importance": 0.9, "category": "identity", "invalidate": []}

Kullanıcı: "Python nedir?"
Asistan: "Python bir programlama dilidir..."
→ {"store": false} (Tanım, kişisel değil)

Kullanıcı: "Python öğreniyorum"
Asistan: "Harika! Python öğrenmek güzel bir hedef."
→ {"store": true, "memory": "Kullanıcı Python öğreniyor", "importance": 0.6, "category": "goals", "invalidate": []}

JSON Format: {"store": true/false, "memory": "...", "importance": 0.0-1.0, "category": "...", "invalidate": ["id1"...]}
""".strip()

# RAG_DECIDER_SYSTEM_PROMPT ve CONVERSATION_SUMMARY_SYSTEM silindi - Kullanılmıyordu


# run_decider_async silindi - SmartRouter artık action belirliyor
# build_search_queries_async kullanılmalı

# -----------------------------------------------------------------------------
# QUERY BUILDER (Secenek B - Yeni Sistem)
# -----------------------------------------------------------------------------

QUERY_BUILDER_PROMPT = """
You are a search query generator. Given a user's question, create 1-3 optimized web search queries.

Guidelines:
- For finance (dolar, euro, altın): Add "kuru bugün güncel" to make it time-specific
- For weather: Add city name if mentioned + "hava durumu"
- For sports: Add team name + "son maç skor"
- For news: Add "son dakika" or "güncel haber"
- Keep queries in Turkish

Output JSON: {"queries": [{"id": "q1", "query": "..."}, {"id": "q2", "query": "..."}]}
"""


async def build_search_queries_async(message: str, semantic: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    INTERNET akışı için arama sorguları üretir.

    Özellikler:
    - SmartRouter'dan bağımsız çalışır
    - Sadece sorgu oluşturmaya odaklanır
    - Semantic analiz sonuçlarını kullanabilir

    Args:
        message: Kullanıcı mesajı
        semantic: Semantic analiz sonuçları (opsiyonel)

    Returns:
        List[Dict]: [{"id": "q1", "query": "..."}]
    """
    # Domain bazlı basit kontrol
    domain = semantic.get("domain", "general") if semantic else "general"
    text_lower = message.lower()

    # 1. Hızlı template kontrolü (LLM çağrısı gerekmez)
    if domain == "finance" or any(kw in text_lower for kw in ["dolar", "euro", "altın", "kur"]):
        for currency in ["dolar", "euro", "altın", "sterlin"]:
            if currency in text_lower:
                return [{"id": "q1", "query": f"{currency} TL kuru bugün güncel"}]

    if domain == "weather" or "hava" in text_lower:
        # Şehir çıkarımı
        cities = ["istanbul", "ankara", "izmir", "bursa", "antalya", "trabzon", "adana"]
        city = next((c for c in cities if c in text_lower), "türkiye")
        return [{"id": "q1", "query": f"{city} hava durumu"}]

    # 2. LLM ile akıllı sorgu üretimi
    llm_messages = [
        {"role": "system", "content": QUERY_BUILDER_PROMPT},
        {"role": "user", "content": message},
    ]

    content = await call_groq_api_async(llm_messages, json_mode=True, temperature=0.2)
    if content:
        try:
            data = json.loads(content)
            queries = data.get("queries", [])
            if queries:
                logger.info(f"[QUERY_BUILDER] LLM generated {len(queries)} queries")
                return queries
        except json.JSONDecodeError:
            logger.warning("[QUERY_BUILDER] JSON parse hatası, fallback'e geçiliyor")

    # 3. Fallback: Ham mesajı sorgu olarak kullan
    return [{"id": "q1", "query": message}]


async def decide_memory_storage_async(
    message: str, answer: str, existing_memories: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Hafıza kayıt kararını LLM'e sorar.

    Conflict detection: Mevcut hafızalarla çelişki varsa
    eski kayıtları invalidate eder.

    Args:
        message: Kullanıcı mesajı
        answer: Asistan yanıtı
        existing_memories: Mevcut ilgili hafızalar

    Returns:
        Dict: {store, memory, importance, category, invalidate}
    """
    existing_memories = existing_memories if existing_memories is not None else []

    # Mevcut hafızaları context olarak ekle
    memory_context = ""
    if existing_memories:
        memory_context = "\n\n## MEVCUT İLGİLİ HAFIZALAR:\n"
        for m in existing_memories:
            mid = m.get("id", "unknown")
            mtext = m.get("text", "")
            memory_context += f"- ID: {mid} | Text: {mtext}\n"

    user_content = f"Kullanıcı: {message}\nAsistan: {answer}{memory_context}"

    messages = [
        {"role": "system", "content": MEMORY_DECIDER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    content = await call_groq_api_async(messages, json_mode=True, temperature=0.2)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    return {"store": False}


# decide_rag_storage_async ve summarize_conversation_for_rag_async silindi - Hiç çağrılmıyordu
