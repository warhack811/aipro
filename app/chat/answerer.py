"""
Mami AI - Yanıt Üretici (Groq Answerer)
=======================================

Bu modül, Groq API kullanarak yüksek kaliteli yanıtlar üretir.

Özellikler:
    - Dinamik temperature (domain/risk bazlı)
    - Chain-of-Thought desteği (karmaşık sorular için)
    - Context injection (RAG, hafıza)
    - Streaming desteği
    - Thinking block filtreleme

Kullanım:
    from app.chat.answerer import generate_answer, generate_answer_stream
    
    # Tek seferlik yanıt
    answer = await generate_answer(
        message="Python'da liste nasıl oluşturulur?",
        context="Kullanıcı yeni başlayan bir geliştirici"
    )
    
    # Streaming yanıt
    async for chunk in generate_answer_stream(message, context):
        print(chunk, end="")
"""

from __future__ import annotations

import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, cast

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# NOT: SYSTEM_PROMPT_UNIVERSAL silindi.
# Sistem promptları artık compiler.py üzerinden build_system_prompt() ile üretiliyor.
# =============================================================================



# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    from app.ai.prompts.identity import enforce_model_identity, get_ai_identity
    from app.chat.decider import call_groq_api_async, call_groq_api_stream_async
    from app.config import get_settings
    from app.services.response_processor import full_post_process
    
    return get_settings, get_ai_identity, enforce_model_identity, call_groq_api_async, call_groq_api_stream_async, full_post_process


# =============================================================================
# DİNAMİK TEMPERATURE HESAPLAMA
# =============================================================================

def get_dynamic_temperature(
    analysis: Optional[Dict[str, Any]] = None,
    style_profile: Optional[Dict[str, Any]] = None
) -> float:
    """
    Domain, risk seviyesi ve KULLANICI TERCİHLERİNE göre dinamik temperature hesaplar.
    
    Temperature Seviyeleri:
        - Düşük (0.1-0.3): Deterministik, doğruluk kritik
        - Orta (0.4-0.6): Dengeli
        - Yüksek (0.7-1.0): Yaratıcı
    
    Args:
        analysis: Semantic analiz sonuçları
        style_profile: Kullanıcı stil tercihleri (tone, creativity vb.)
    
    Returns:
        float: Hesaplanan temperature değeri (0.0-1.0)
    """
    if not analysis and not style_profile:
        return 0.6  # Varsayılan dengeli
    
    # Domain bazlı base temperature
    domain = analysis.get("domain", "general")
    domain_temps = {
        # Kritik doğruluk gerektiren alanlar
        "finance": 0.2,
        "health": 0.2,
        "legal": 0.2,
        "weather": 0.1,
        "sports": 0.3,
        # Teknik alanlar
        "code": 0.4,
        "tech": 0.4,
        # Sosyal/kişisel alanlar
        "personal": 0.6,
        "relationships": 0.6,
        "mental_health": 0.5,
        # Yaratıcı alanlar
        "creative": 0.8,
        "story": 0.85,
        # Hassas ama özgür tartışma
        "politics": 0.5,
        "religion": 0.5,
        "sex": 0.6,
        # Genel
        "general": 0.6,
    }
    base_temp = domain_temps.get(domain, 0.6)
    
    # Risk seviyesine göre düşür
    risk_level = analysis.get("risk_level", "low")
    if risk_level == "high":
        base_temp = min(base_temp, 0.3)
    elif risk_level == "medium":
        base_temp = min(base_temp, 0.5)
    
    # Intent tipine göre ayarla
    intent_type = analysis.get("intent_type", "")
    if intent_type in ("explicit_instruction", "advice_high_risk"):
        base_temp = min(base_temp, 0.3)
    elif intent_type in ("story", "emotional_support"):
        base_temp = max(base_temp, 0.6)
    
    # Creativity override
    creativity = analysis.get("creativity_level", "")
    if creativity == "high":
        base_temp = max(base_temp, 0.75)
    elif creativity == "low":
        base_temp = min(base_temp, 0.35)
    
    return round(base_temp, 2)

    # -------------------------------------------------------------------------
    # STİL BAZLI MODİFİKASYONLAR (Kullanıcı Tercihleri)
    # -------------------------------------------------------------------------
    if style_profile:
        # 1. Ton Bazlı Değişim
        tone = style_profile.get("tone", "neutral")
        if tone == "friendly":
            base_temp += 0.05
        elif tone == "humorous":
            base_temp += 0.15
        elif tone == "serious":
            base_temp -= 0.10
        elif tone == "empathetic":
            base_temp += 0.05

        # 2. Formality Bazlı Değişim
        formality = style_profile.get("formality", "medium")
        if formality == "low":  # Samimi
            base_temp += 0.05
        elif formality == "high":  # Resmi
            base_temp -= 0.05

        # 3. Yaratıcı Mod Kontrolü 
        # (Eğer kullanıcı özellikle 'creative' bir mod seçtiyse)
        # NOT: Kullanıcı "Emniyet kemeri yok" dediği için burada
        # riskli domain olsa bile artışa izin veriyoruz (kısmi).
        
    # Sonuç sınırlandırma (0.0 - 1.0 arası)
    final_temp = max(0.0, min(1.0, base_temp))
    
    return round(final_temp, 2)


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def _clean_thinking_block(text: str, *, strip: bool = True) -> str:
    """
    Modelin <thinking> bloklarını temizler.
    
    Args:
        text: Temizlenecek metin
        strip: Baş/son boşlukları temizle
    
    Returns:
        str: Temizlenmiş metin
    """
    if not text:
        return ""
    cleaned = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
    return cleaned.strip() if strip else cleaned


def _build_user_content(message: str, context: Optional[str]) -> str:
    """
    Context ve kullanıcı mesajını birleştirir.
    
    Args:
        message: Kullanıcı mesajı
        context: RAG/hafıza bağlamı
    
    Returns:
        str: Birleştirilmiş içerik
    """
    if context:
        return (
            "--- BAĞLAM BÖLÜMÜ BAŞLANGICI ---\n"
            f"{context}\n"
            "--- BAĞLAM BÖLÜMÜ SONU ---\n\n"
            f"KULLANICI SORUSU:\n{message}"
        )
    return message


def _append_history(messages: List[Dict[str, str]], history: Optional[List[Dict[str, str]]]) -> None:
    """
    Sohbet geçmişini mesaj listesine ekler.
    
    Args:
        messages: Hedef mesaj listesi
        history: Eklenecek geçmiş
    """
    if not history:
        return
    for m in history:
        role = m.get("role")
        content = m.get("content")
        if role == "bot":
            role = "assistant"
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})


async def _thinking_filter_async(
    source: AsyncGenerator[str, None],
) -> AsyncGenerator[str, None]:
    """
    Streaming yanıttan <thinking> bloklarını filtreler.
    
    Memory-safe implementation using StreamingBuffer.
    
    Args:
        source: Kaynak stream
    
    Yields:
        str: Filtrelenmiş içerik parçaları
    """
    from app.chat.streaming_buffer import StreamingBuffer
    
    open_tag = "<thinking>"
    close_tag = "</thinking>"
    buffer_obj = StreamingBuffer(max_chunks=100)  # Small buffer for filter
    thinking_mode = False

    try:
        async for chunk in source:
            if not chunk:
                continue
            
            buffer_obj.append(chunk)
            buffer_str = "".join(buffer_obj.chunks)  # Get current content without finalizing
            
            while True:
                if thinking_mode:
                    end_idx = buffer_str.find(close_tag)
                    if end_idx == -1:
                        break
                    buffer_str = buffer_str[end_idx + len(close_tag):]
                    buffer_obj.clear()
                    buffer_obj.append(buffer_str)
                    thinking_mode = False
                    continue

                start_idx = buffer_str.find(open_tag)
                if start_idx == -1:
                    if buffer_str:
                        cleaned = _clean_thinking_block(buffer_str, strip=False)
                        if cleaned:
                            yield cleaned
                    buffer_obj.clear()
                    break

                if start_idx > 0:
                    segment = buffer_str[:start_idx]
                    cleaned = _clean_thinking_block(segment, strip=False)
                    if cleaned:
                        yield cleaned

                buffer_str = buffer_str[start_idx + len(open_tag):]
                buffer_obj.clear()
                buffer_obj.append(buffer_str)
                thinking_mode = True

        # Final cleanup
        buffer_str = "".join(buffer_obj.chunks)
        if buffer_str and not thinking_mode:
            cleaned = _clean_thinking_block(buffer_str, strip=False)
            if cleaned:
                yield cleaned
    
    finally:
        buffer_obj.clear()  # Cleanup


# =============================================================================
# ANA YANIT FONKSİYONLARI
# =============================================================================

async def generate_answer(
    message: str,
    analysis: Optional[Dict[str, Any]] = None,
    context: Optional[str] = None,
    system_prompt: Optional[str] = None,
    source: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    style_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Groq API ile tek seferlik yanıt üretir.
    
    Args:
        message: Kullanıcı mesajı
        analysis: Semantic analiz sonuçları
        context: RAG/hafıza bağlamı
        system_prompt: Özel sistem prompt'u
        source: Yanıt kaynağı (loglama için)
        history: Sohbet geçmişi
    
    Returns:
        str: Üretilen yanıt
    """
    get_settings, get_ai_identity, enforce_model_identity, call_groq_api_async, _, full_post_process = _get_imports()
    settings = get_settings()
    
    # Dinamik temperature (Style profile ile)
    temperature = get_dynamic_temperature(analysis, style_profile)
    logger.debug(f"[ANSWERER] Temperature: {temperature}")

    # AI kimliği
    identity = get_ai_identity()
    identity_block = (
        f"KİMLİK: Adın {identity.display_name}. {identity.short_intro}\n"
        "GİZLİLİK: Sağlayıcı isimlerini (Google, Groq, Llama vb.) asla söyleme.\n"
    )
    
    # Sistem prompt
    base_system = system_prompt or SYSTEM_PROMPT_UNIVERSAL
    
    # Semantic analiz bazlı ek talimatlar
    extra_instructions = []
    
    if analysis:
        complexity = analysis.get("complexity", "medium")
        requires_step = analysis.get("requires_step_by_step", False)
        
        if complexity == "high" or requires_step:
            extra_instructions.append(
                "🧠 DÜŞÜNME TALİMATI: Bu karmaşık bir soru. "
                "Cevaplamadan önce problemi parçalara ayır ve adım adım çöz."
            )
        
        response_length = analysis.get("preferred_response_length", "medium")
        if response_length == "brief":
            extra_instructions.append("📏 UZUNLUK: Kısa ve öz cevap ver (1-3 cümle).")
        elif response_length == "detailed":
            extra_instructions.append("📏 UZUNLUK: Detaylı ve kapsamlı cevap ver.")
        
        if analysis.get("is_structured_request"):
            extra_instructions.append("📊 FORMAT: Yapılandırılmış veri isteniyor. Tablo veya liste formatı kullan.")
        
        if analysis.get("force_no_hallucination"):
            extra_instructions.append("⚠️ DOĞRULUK: Sadece kesin bildiğin verileri paylaş. Tahmin yapma.")

    # NOT: Stil enjeksiyonu artik processor.py tarafindan build_system_prompt() ile yapiliyor.
    # Burada tekrar eklemeye gerek yok.
    
    extra_block = "\n".join(extra_instructions) if extra_instructions else ""
    
    final_system = f"{base_system}\n\n{identity_block}"
    if extra_block:
        final_system += f"\n\n{extra_block}"

    messages: List[Dict[str, str]] = [{"role": "system", "content": final_system}]
    
    # History ekle
    _append_history(messages, history)
    
    # Kullanıcı mesajı
    user_content = _build_user_content(message, context)
    messages.append({"role": "user", "content": user_content})

    try:
        answer_model = getattr(settings, 'GROQ_ANSWER_MODEL', settings.GROQ_DECIDER_MODEL)
        raw_answer = await call_groq_api_async(
            messages=messages,
            temperature=temperature,
            model=answer_model,
        )

        if not raw_answer:
            return "😔 (Sistem) Yanıt üretilemedi. Lütfen tekrar dene."

        # Post-processing
        cleaned = _clean_thinking_block(raw_answer, strip=False)
        
        # Context for answer shaping
        shaper_context = {"user_message": message}
        if analysis and 'persona' in analysis:
            shaper_context['persona'] = analysis['persona']
        
        try:
            processed = full_post_process(cleaned, context=shaper_context)
        except Exception as e:
            logger.warning(f"[ANSWERER] full_post_process failed: {e}")
            processed = cleaned  # Fallback to unprocessed
        
        final = enforce_model_identity("groq", processed)
        
        return final

    except Exception as e:
        logger.error(f"[ANSWERER] Hata: {e}")
        return "⚠️ Bir hata oluştu. Lütfen daha sonra tekrar dene."


async def generate_answer_stream(
    message: str,
    analysis: Optional[Dict[str, Any]] = None,
    context: Optional[str] = None,
    system_prompt: Optional[str] = None,
    source: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    style_profile: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[str, None]:
    """
    Groq API ile streaming yanıt üretir.
    
    Hibrit yaklaşım: Tüm cevap alınıp formatlanır, 
    sonra kelime bazlı hızlı stream edilir.
    
    Args:
        message: Kullanıcı mesajı
        analysis: Semantic analiz sonuçları
        context: RAG/hafıza bağlamı
        system_prompt: Özel sistem prompt'u
        source: Yanıt kaynağı
        history: Sohbet geçmişi
    
    Yields:
        str: Yanıt parçaları
    """
    get_settings, get_ai_identity, enforce_model_identity, _, call_groq_api_stream_async, full_post_process = _get_imports()
    settings = get_settings()
    
    temperature = get_dynamic_temperature(analysis, style_profile)
    logger.debug(f"[ANSWERER_STREAM] Temperature: {temperature}")

    identity = get_ai_identity()
    identity_block = (
        f"KİMLİK: Adın {identity.display_name}. {identity.short_intro}\n"
        "GİZLİLİK: Sağlayıcı isimlerini (Google, Groq, Llama vb.) asla söyleme.\n"
    )
    
    base_system = system_prompt or SYSTEM_PROMPT_UNIVERSAL
    
    extra_instructions = []
    if analysis:
        complexity = analysis.get("complexity", "medium")
        if complexity == "high" or analysis.get("requires_step_by_step", False):
            extra_instructions.append(
                "🧠 DÜŞÜNME TALİMATI: Bu karmaşık bir soru. "
                "Cevaplamadan önce problemi parçalara ayır ve adım adım çöz."
            )
    
    extra_block = "\n".join(extra_instructions) if extra_instructions else ""
    
    final_system = f"{base_system}\n\n{identity_block}"
    if extra_block:
        final_system += f"\n\n{extra_block}"

    messages: List[Dict[str, str]] = [{"role": "system", "content": final_system}]
    _append_history(messages, history)
    
    user_content = _build_user_content(message, context)
    messages.append({"role": "user", "content": user_content})

    try:
        from app.chat.streaming_buffer import StreamingBuffer
        
        answer_model = getattr(settings, 'GROQ_ANSWER_MODEL', settings.GROQ_DECIDER_MODEL)
        chunk_source = cast(
            AsyncGenerator[str, None],
            call_groq_api_stream_async(
                messages=messages,
                temperature=temperature,
                model=answer_model,
            ),
        )

        # 1. Tüm cevabı topla (memory-safe buffer ile)
        buffer = StreamingBuffer(max_chunks=1000)  # ~100KB max
        
        try:
            async for chunk in _thinking_filter_async(chunk_source):
                buffer.append(chunk)
            
            # Finalize buffer (memory cleared automatically)
            full_response = buffer.finalize()
        finally:
            buffer.clear()  # Ensure cleanup
        
        # 2. Post-processing
        # Context for answer shaping
        shaper_context = {"user_message": message}
        if analysis and 'persona' in analysis:
            shaper_context['persona'] = analysis['persona']
        
        processed_response = full_post_process(full_response, context=shaper_context)
        final_response = enforce_model_identity("groq", processed_response)
        
        # 3. Kelime bazlı stream
        words = final_response.split(' ')
        for i, word in enumerate(words):
            if i < len(words) - 1:
                yield word + ' '
            else:
                yield word

    except Exception as e:
        logger.error(f"[ANSWERER_STREAM] Hata: {e}")
        yield "⚠️ Bir hata oluştu. Lütfen daha sonra tekrar dene."



