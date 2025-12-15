"""
Mami AI - AI Kimlik Yönetimi
============================

Bu modül, AI asistanın kimlik bilgilerini ve marka tutarlılığını yönetir.

Özellikler:
    - Dinamik kimlik ayarları (veritabanından)
    - Sağlayıcı ismi gizleme (Google, OpenAI vb.)
    - Marka tutarlılığı enforcing

Kullanım:
    from app.ai.prompts.identity import get_ai_identity, enforce_model_identity
    
    # Kimlik bilgilerini al
    identity = get_ai_identity()
    print(identity.display_name)  # "Mami AI"
    
    # Yanıtta sağlayıcı isimlerini gizle
    clean_text = enforce_model_identity("groq", response_text)
"""

import logging
import re
from datetime import datetime
from typing import Optional

from sqlmodel import select

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# SABİTLER
# =============================================================================

# Modelin kendi kimliğini gizlemesi için anahtar kelimeler
PROVIDER_KEYWORDS = [
    "google", "google ai", "google deepmind", "openai", "meta", "microsoft",
    "anthropic", "mistral", "groq", "gemma", "gpt", "chatgpt", "bard", "llama",
    "dil modeli", "language model", "yapay zeka modeli", "ai model", "large language model"
]

IDENTITY_CONTEXT_WORDS = [
    "dil modeli", "yapay zeka", "model", "asistan", "assistant", "program", "bot"
]


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    try:
        from app.core.database import get_session
        from app.core.models import AIIdentityConfig
    except ImportError:
        from app.core.database import get_session
        from app.core.models import AIIdentityConfig
    return get_session, AIIdentityConfig


def _get_default_identity():
    """Varsayılan kimlik nesnesi oluşturur."""
    _, AIIdentityConfig = _get_imports()
    return AIIdentityConfig()


# =============================================================================
# KİMLİK FONKSİYONLARI
# =============================================================================

def get_ai_identity():
    """
    DB'den kimlik ayarlarını okur.
    
    Yoksa varsayılan kimliği oluşturur ve kaydeder.
    
    Returns:
        AIIdentityConfig: Kimlik yapılandırması
    """
    get_session, AIIdentityConfig = _get_imports()
    default_identity = _get_default_identity()
    
    with get_session() as session:
        try:
            config = session.get(AIIdentityConfig, 1)
            if not config:
                logger.info("[IDENTITY] Kimlik ayarları ilk kez oluşturuluyor...")
                session.add(default_identity)
                session.commit()
                session.refresh(default_identity)
                return default_identity
            return config
        except Exception as e:
            logger.error(f"[IDENTITY] Okuma hatası: {e}")
            return default_identity


def update_ai_identity(
    display_name: Optional[str] = None,
    developer_name: Optional[str] = None,
    product_family: Optional[str] = None,
    short_intro: Optional[str] = None,
    forbid_provider_mention: Optional[bool] = None,
):
    """
    AI kimlik ayarlarını günceller.
    
    Args:
        display_name: Görünen ad
        developer_name: Geliştirici adı
        product_family: Ürün ailesi
        short_intro: Kısa tanıtım
        forbid_provider_mention: Sağlayıcı ismini gizle
    
    Returns:
        AIIdentityConfig: Güncellenmiş kimlik
    """
    get_session, AIIdentityConfig = _get_imports()
    default_identity = _get_default_identity()
    
    with get_session() as session:
        config = session.get(AIIdentityConfig, 1)
        if not config:
            config = default_identity
            session.add(config)
        
        # Değerleri güncelle
        if display_name is not None:
            config.display_name = display_name
        if developer_name is not None:
            config.developer_name = developer_name
        if product_family is not None:
            config.product_family = product_family
        if short_intro is not None:
            config.short_intro = short_intro
        if forbid_provider_mention is not None:
            config.forbid_provider_mention = forbid_provider_mention
        
        config.updated_at = datetime.utcnow()

        session.add(config)
        session.commit()
        session.refresh(config)
        logger.info(f"[IDENTITY] Güncellendi: {config.display_name}")
        return config


def enforce_model_identity(_engine_key: str, text: str) -> str:
    """
    Model yanıtındaki sağlayıcı isimlerini projenin kimliğiyle değiştirir.
    
    Google, OpenAI, Meta vb. referansları temizler ve
    projenin kendi kimlik bilgileriyle değiştirir.
    
    Args:
        engine_key: Kullanılan motor (groq, local vb.)
        text: İşlenecek yanıt metni
    
    Returns:
        str: Temizlenmiş metin
    
    Example:
        >>> text = "Ben Google tarafından geliştirilen bir dil modeliyim."
        >>> clean = enforce_model_identity("groq", text)
        >>> # "Ben, bu sistemin geliştiricileri tarafından..."
    """
    identity = get_ai_identity()

    if not identity.forbid_provider_mention:
        return text

    # Yerine geçecek kimlik cümlesi
    identity_sentence = (
        f"Ben, {identity.developer_name} tarafından geliştirilen "
        f"{identity.product_family} parçası olan bir yapay zeka asistanıyım. "
        f"{identity.short_intro}"
    )

    lowered = text.lower()

    # Hızlı çıkış: Hiçbir sağlayıcı anahtar kelimesi geçmiyorsa
    if not any(k in lowered for k in PROVIDER_KEYWORDS):
        return text

    # Metni cümlelere böl
    raw_sentences = re.split(r"(?<=[\.\!\?])\s+|\n+", text)

    cleaned_sentences = []
    replaced_any = False

    for s in raw_sentences:
        s_strip = s.strip()
        if not s_strip:
            continue
        
        s_lower = s_strip.lower()

        has_provider = any(k in s_lower for k in PROVIDER_KEYWORDS)
        has_identity_context = any(w in s_lower for w in IDENTITY_CONTEXT_WORDS)

        # Hem sağlayıcı adı hem de kimlik bağlamı varsa değiştir
        if has_provider and has_identity_context:
            if not replaced_any:
                cleaned_sentences.append(identity_sentence)
                replaced_any = True
        else:
            cleaned_sentences.append(s_strip)

    if not replaced_any:
        return text

    return " ".join(cleaned_sentences)







