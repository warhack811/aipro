"""
Mami AI - Semantic Router & Groq API Yöneticisi
===============================================

Bu modül, kullanıcı mesajlarını analiz edip uygun alt sisteme yönlendirir.

Sorumluluklar:
    - Mesaj niyetini belirleme (chat, image, internet, local)
    - Groq API çağrıları (çoklu anahtar rotasyonu)
    - Hafıza kayıt kararları
    - RAG depolama kararları

Alt Sistemler:
    - IMAGE: Görsel üretim (Flux/Forge)
    - INTERNET: Güncel bilgi araması
    - LOCAL_CHAT: Yerel model (Ollama/Bela)
    - GROQ_REPLY: Ana sohbet motoru (varsayılan)

Kullanım:
    from app.chat.decider import run_decider_async, call_groq_api_async
    
    # Mesaj yönlendirme kararı
    decision = await run_decider_async("Dolar kuru nedir?")
    # {"action": "INTERNET", "analysis": {...}}
    
    # Groq API çağrısı
    response = await call_groq_api_async(messages, model="llama-3.3-70b")
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional, List, AsyncGenerator

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
# HIZLI SINIFLANDIRMA (LLM'siz)
# =============================================================================

def quick_classify(message: str) -> Optional[Dict[str, Any]]:
    """
    LLM kullanmadan hızlı sınıflandırma yapar.
    
    Kesin anahtar kelimeler içeren mesajlar için token tasarrufu sağlar.
    
    Args:
        message: Kullanıcı mesajı
    
    Returns:
        Dict veya None: Eşleşme varsa karar, yoksa None
    """
    text = message.lower()

    # Görsel üretim
    if any(kw in text for kw in ['çiz', 'resim', 'görsel', 'draw', 'paint']):
        return {
            "analysis": {"intent": "image_generation"},
            "action": "IMAGE",
            "image": {"prompt": message},
        }
    
    # İnternet araması
    if any(kw in text for kw in ['dolar', 'kur', 'hava', 'haber', 'güncel', 'son']):
        return {
            "analysis": {"intent": "information_retrieval"},
            "action": "INTERNET",
            "internet": {"queries": [{"id": "q1", "query": message}]},
        }
    
    # Yerel model
    if 'bela' in text or 'sansürsüz' in text:
        return {
            "analysis": {"intent": "local"},
            "action": "LOCAL_CHAT",
        }
    
    return None


def run_decider_stub(message: str) -> Dict[str, Any]:
    """
    API çalışmazsa devreye giren basit kural tabanlı fallback.
    
    Args:
        message: Kullanıcı mesajı
    
    Returns:
        Dict: Varsayılan yönlendirme kararı
    """
    text = message.lower()

    if "çiz" in text or "resim" in text or "görsel" in text:
        return {
            "analysis": {"intent": "image", "needs_image": True},
            "action": "IMAGE",
            "image": {"prompt": message}
        }
    
    if "dolar" in text or "hava" in text or "haber" in text:
        return {
            "analysis": {"intent": "internet", "needs_internet": True},
            "action": "INTERNET",
            "internet": {"queries": [{"id": "q1", "query": message}]}
        }
    
    if "sansürsüz" in text or "bela" in text:
        return {
            "analysis": {"intent": "local", "needs_local_chat": True},
            "action": "LOCAL_CHAT"
        }

    return {"analysis": {"intent": "chat"}, "action": "GROQ_REPLY"}


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
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                )
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
                                logger.warning(f"[GROQ_STREAM] JSON parse error (line intact): {e} | Line: {line[:100]}")
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

DECIDER_SYSTEM_PROMPT = """
You are the **Semantic Router** for an advanced AI Assistant.
Your ONLY job is to analyze the user's input and output a JSON object determining the correct subsystem to handle the request.

### SUBSYSTEM DEFINITIONS (Strict Semantic Boundaries)

1. **IMAGE (Generative Art Engine)**
   - **Intent:** The user wants to *see* something new. Creating visual content.

2. **INTERNET (Real-Time Search Engine)**
   - **Intent:** The user needs *external* or *current* information not present in a static training set.

3. **LOCAL_CHAT (Uncensored/Raw Model)**
   - **Intent:** The user explicitly demands a raw, unfiltered, or "jailbreak" style interaction.

4. **GROQ_REPLY (Main Reasoning & Memory Engine) [DEFAULT]**
   - **Intent:** General conversation, coding, reasoning, and **Retrieval Augmented Generation (RAG)**.
   - **CRITICAL RULE:** Any query regarding the **User's Identity (Who am I?), Past Conversations, Uploaded Files, Personal Preferences, or Stored Memories** MUST be routed here.

### OUTPUT JSON FORMAT
{
  "analysis": {
    "intent": "chat | image_generation | information_retrieval | raw_mode",
    "requires_memory_access": true/false,
    "complexity": "medium"
  },
  "action": "GROQ_REPLY", // or IMAGE / INTERNET / LOCAL_CHAT
  "image": { "prompt": "..." },
  "internet": { "queries": [{"id": "q1", "query": "..."}] }
}
"""

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

RAG_DECIDER_SYSTEM_PROMPT = """
Sen bir BİLGİ ÖZETLEYİCİSİSİN. İnternetten gelen cevabın gelecekte tekrar kullanılmasına değer GENEL BİLGİ içerip içermediğine karar ver.
YALNIZCA Zamandan bağımsız, genel geçer bilgileri (tanım, rehber vb.) kaydet.
JSON Formatı: {"store": true/false}
"""

CONVERSATION_SUMMARY_SYSTEM = """
Sen bir SOHBET ÖZETLEYİCİSİSİN. Sohbetin ana noktalarını 3-6 cümlelik kısa bir PARAGRAF şeklinde özetle.
JSON Formatı: {"summary": "metin..."}
"""


# =============================================================================
# ANA KARAR FONKSİYONLARI
# =============================================================================

async def run_decider_async(message: str) -> Dict[str, Any]:
    """
    Mesaj için yönlendirme kararı üretir.
    
    İşlem Sırası:
    1. Hızlı sınıflandırma (anahtar kelime bazlı)
    2. LLM tabanlı semantik analiz
    3. Fallback (kural tabanlı)
    
    Args:
        message: Kullanıcı mesajı
    
    Returns:
        Dict: Yönlendirme kararı (action, analysis vb.)
    """
    # 1. Hızlı sınıflandırma
    quick_result = quick_classify(message)
    if quick_result:
        logger.info(f"[DECIDER] Quick classify: {quick_result['action']}")
        return quick_result

    # 2. LLM tabanlı karar
    messages = [
        {"role": "system", "content": DECIDER_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    content = await call_groq_api_async(messages, json_mode=True, temperature=0.2)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("[DECIDER] JSON parse hatası")

    # 3. Fallback
    return run_decider_stub(message)


async def decide_memory_storage_async(
    message: str,
    answer: str,
    existing_memories: Optional[List[Dict[str, Any]]] = None
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


async def decide_rag_storage_async(question: str, answer: str) -> Dict[str, Any]:
    """
    İnternet sonucunun RAG'a kaydedilip edilmeyeceğine karar verir.
    
    Args:
        question: Sorulan soru
        answer: Alınan yanıt
    
    Returns:
        Dict: {store: true/false}
    """
    user_content = f"Soru: {question}\nCevap: {answer}"
    messages = [
        {"role": "system", "content": RAG_DECIDER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    
    content = await call_groq_api_async(messages, json_mode=True, temperature=0.2)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
    
    return {"store": False}


async def summarize_conversation_for_rag_async(text: str) -> str:
    """
    Sohbet özetini çıkarır.
    
    Args:
        text: Özetlenecek sohbet metni
    
    Returns:
        str: Özet metin
    """
    messages = [
        {"role": "system", "content": CONVERSATION_SUMMARY_SYSTEM},
        {"role": "user", "content": text},
    ]
    
    content = await call_groq_api_async(messages, json_mode=True)
    if content:
        try:
            data = json.loads(content)
            return data.get("summary", "")
        except json.JSONDecodeError:
            pass
    
    return ""

