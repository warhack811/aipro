"""
Mami AI - Varsayılan Yapılandırma Seed
======================================

Bu modül, dinamik yapılandırma tablolarına varsayılan değerleri yükler.
İlk kurulumda veya reset durumunda çalıştırılır.

Kullanım:
    from app.core.config_seed import seed_all_configs

    # Tüm varsayılan config'leri yükle
    seed_all_configs()

    # Sadece belirli kategorileri yükle
    seed_system_configs()
    seed_model_configs()
    seed_theme_configs()
    seed_persona_configs()

Not:
    - Mevcut kayıtları DEĞİŞTİRMEZ (sadece yoksa ekler)
    - Force parametresi ile üzerine yazma yapılabilir
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlmodel import select

logger = logging.getLogger(__name__)


# =============================================================================
# LAZY IMPORTS
# =============================================================================


def _get_imports():
    """Circular import önlemek için lazy import."""
    from app.core.config_models import (
        APIConfig,
        ConfigCategory,
        ConfigValueType,
        ImageGenConfig,
        ModelConfig,
        PersonaConfig,
        PersonaModeType,
        SystemConfig,
        ThemeConfig,
        UITextConfig,
    )
    from app.core.database import get_session

    return {
        "get_session": get_session,
        "SystemConfig": SystemConfig,
        "ModelConfig": ModelConfig,
        "APIConfig": APIConfig,
        "ThemeConfig": ThemeConfig,
        "PersonaConfig": PersonaConfig,
        "ImageGenConfig": ImageGenConfig,
        "UITextConfig": UITextConfig,
        "ConfigValueType": ConfigValueType,
        "ConfigCategory": ConfigCategory,
        "PersonaModeType": PersonaModeType,
    }


# =============================================================================
# VARSAYILAN DEĞERLERİN TANIMLARI
# =============================================================================

DEFAULT_SYSTEM_CONFIGS = [
    # Sistem Genel
    {
        "key": "system.app_name",
        "value": "Mami AI Pro",
        "value_type": "string",
        "category": "system",
        "description": "Uygulama adı",
    },
    {
        "key": "system.app_version",
        "value": "5.0.0",
        "value_type": "string",
        "category": "system",
        "description": "Uygulama versiyonu",
    },
    {
        "key": "system.maintenance_mode",
        "value": "false",
        "value_type": "boolean",
        "category": "system",
        "description": "Bakım modu aktif mi",
    },
    # AI Kimlik
    {
        "key": "ai.display_name",
        "value": "Mami",
        "value_type": "string",
        "category": "ai",
        "description": "AI görünen adı",
    },
    {
        "key": "ai.developer_name",
        "value": "Geliştirici Ekibi",
        "value_type": "string",
        "category": "ai",
        "description": "Geliştirici adı",
    },
    {
        "key": "ai.product_family",
        "value": "Mami AI Ailesi",
        "value_type": "string",
        "category": "ai",
        "description": "Ürün ailesi",
    },
    {
        "key": "ai.short_intro",
        "value": "Ben sizin kişisel AI asistanınızım. Her konuda yardımcı olmak için buradayım.",
        "value_type": "string",
        "category": "ai",
        "description": "Kısa tanıtım",
    },
    {
        "key": "ai.forbid_provider_mention",
        "value": "true",
        "value_type": "boolean",
        "category": "ai",
        "description": "Sağlayıcı ismini gizle",
    },
    # UI Ayarları
    {
        "key": "ui.default_theme",
        "value": "dark",
        "value_type": "string",
        "category": "ui",
        "description": "Varsayılan tema",
    },
    {
        "key": "ui.enable_animations",
        "value": "true",
        "value_type": "boolean",
        "category": "ui",
        "description": "Animasyonlar aktif mi",
    },
    {
        "key": "ui.message_timestamp_format",
        "value": "HH:mm",
        "value_type": "string",
        "category": "ui",
        "description": "Mesaj zaman formatı",
    },
    # Feature Flags
    {
        "key": "features.enable_image_gen",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "Görsel üretim aktif mi",
    },
    {
        "key": "features.enable_internet_search",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "İnternet araması aktif mi",
    },
    {
        "key": "features.enable_local_model",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "Yerel model aktif mi",
    },
    {
        "key": "features.enable_voice_input",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "Sesli giriş aktif mi",
    },
    {
        "key": "features.enable_file_upload",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "Dosya yükleme aktif mi",
    },
    {
        "key": "features.enable_memory",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "Hafıza sistemi aktif mi",
    },
    {
        "key": "features.enable_proactive",
        "value": "true",
        "value_type": "boolean",
        "category": "features",
        "description": "Proaktif özellikler aktif mi",
    },
    # Sohbet Ayarları
    {
        "key": "chat.max_history_messages",
        "value": "24",
        "value_type": "integer",
        "category": "chat",
        "description": "Maksimum geçmiş mesaj sayısı",
    },
    {
        "key": "chat.context_char_limit",
        "value": "8000",
        "value_type": "integer",
        "category": "chat",
        "description": "Maksimum bağlam karakter limiti",
    },
    {
        "key": "chat.auto_summary_threshold",
        "value": "12",
        "value_type": "integer",
        "category": "chat",
        "description": "Otomatik özet eşiği (mesaj sayısı)",
    },
    {
        "key": "chat.streaming_enabled",
        "value": "true",
        "value_type": "boolean",
        "category": "chat",
        "description": "Streaming yanıt aktif mi",
    },
]

DEFAULT_MODEL_CONFIGS = [
    # Groq Modelleri
    {
        "name": "groq_answer",
        "display_name": "Groq Ana Cevap Modeli",
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
        "purpose": "answer",
        "is_default": True,
        "priority": 100,
        "parameters": {"temperature": 0.7, "max_tokens": 4096},
        "capabilities": {"streaming": True, "json_mode": True},
        "description": "Ana sohbet için kullanılan yüksek kaliteli model",
    },
    {
        "name": "groq_decider",
        "display_name": "Groq Router Modeli",
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
        "purpose": "decider",
        "is_default": True,
        "priority": 100,
        "parameters": {"temperature": 0.2, "max_tokens": 1024},
        "capabilities": {"streaming": False, "json_mode": True},
        "description": "Mesaj yönlendirme kararları için",
    },
    {
        "name": "groq_fast",
        "display_name": "Groq Hızlı Model",
        "provider": "groq",
        "model_id": "llama-3.1-8b-instant",
        "purpose": "fast",
        "is_default": True,
        "priority": 100,
        "parameters": {"temperature": 0.3, "max_tokens": 2048},
        "capabilities": {"streaming": True, "json_mode": True},
        "description": "Hızlı işlemler için (semantic, özet)",
    },
    {
        "name": "groq_semantic",
        "display_name": "Groq Semantic Model",
        "provider": "groq",
        "model_id": "llama-3.1-8b-instant",
        "purpose": "semantic",
        "is_default": True,
        "priority": 100,
        "parameters": {"temperature": 0.0, "max_tokens": 512},
        "capabilities": {"streaming": False, "json_mode": True},
        "description": "Semantic analiz için",
    },
    # --- OLLAMA / LOCAL ---
    {
        "name": "local_uncensored",
        "display_name": "Qwen3 Yerel",
        "provider": "ollama",
        "model_id": "josiefied-qwen3-8b",
        "purpose": "uncensored",
        "is_default": True,
        "priority": 100,
        "parameters": {"temperature": 0.7, "num_ctx": 8192, "top_k": 40, "top_p": 0.9, "repeat_penalty": 1.15},
        "capabilities": {"streaming": True, "json_mode": False},
        "description": "Sansürsüz yerel model (Qwen)",
    },
]

DEFAULT_API_CONFIGS = [
    {
        "name": "groq",
        "display_name": "Groq API",
        "base_url": "https://api.groq.com/openai/v1",
        "timeout": 30,
        "rate_limit": 30,
        "retry_count": 3,
        "description": "Groq LLM API",
    },
    {
        "name": "ollama",
        "display_name": "Ollama Local",
        "base_url": "http://127.0.0.1:11434",
        "timeout": 120,
        "rate_limit": 0,
        "retry_count": 2,
        "description": "Yerel Ollama sunucusu",
    },
    {
        "name": "forge",
        "display_name": "Forge/SD WebUI",
        "base_url": "http://127.0.0.1:7860",
        "timeout": 1200,
        "rate_limit": 0,
        "retry_count": 1,
        "settings": {"txt2img_path": "/sdapi/v1/txt2img"},
        "description": "Görsel üretim için Forge/Stable Diffusion WebUI",
    },
    {
        "name": "bing_search",
        "display_name": "Bing Search API",
        "base_url": "https://api.bing.microsoft.com/v7.0/search",
        "timeout": 10,
        "rate_limit": 100,
        "retry_count": 2,
        "description": "Bing web araması",
    },
    {
        "name": "serper",
        "display_name": "Serper (Google) API",
        "base_url": "https://google.serper.dev/search",
        "timeout": 10,
        "rate_limit": 100,
        "retry_count": 2,
        "description": "Google arama sonuçları",
    },
]

DEFAULT_THEME_CONFIGS = [
    {
        "name": "dark",
        "display_name": "Koyu Tema",
        "is_default": True,
        "sort_order": 1,
        "colors": {
            "primary": "#6366f1",
            "secondary": "#8b5cf6",
            "background": "#0f0f0f",
            "surface": "#1a1a1a",
            "text": "#ffffff",
            "text_muted": "#a1a1aa",
            "border": "#27272a",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "error": "#ef4444",
        },
        "fonts": {"primary": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
    },
    {
        "name": "light",
        "display_name": "Açık Tema",
        "sort_order": 2,
        "colors": {
            "primary": "#6366f1",
            "secondary": "#8b5cf6",
            "background": "#ffffff",
            "surface": "#f4f4f5",
            "text": "#18181b",
            "text_muted": "#71717a",
            "border": "#e4e4e7",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "error": "#ef4444",
        },
        "fonts": {"primary": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
    },
    {
        "name": "cosmic",
        "display_name": "Kozmik",
        "sort_order": 3,
        "colors": {
            "primary": "#a855f7",
            "secondary": "#6366f1",
            "background": "#0c0a1d",
            "surface": "#1a1730",
            "text": "#e2e8f0",
            "text_muted": "#94a3b8",
            "border": "#2d2a4a",
            "success": "#34d399",
            "warning": "#fbbf24",
            "error": "#f87171",
        },
        "fonts": {"primary": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
    },
    {
        "name": "ocean",
        "display_name": "Okyanus",
        "sort_order": 4,
        "colors": {
            "primary": "#0ea5e9",
            "secondary": "#06b6d4",
            "background": "#0c1222",
            "surface": "#162032",
            "text": "#e2e8f0",
            "text_muted": "#94a3b8",
            "border": "#1e3a5f",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "error": "#ef4444",
        },
        "fonts": {"primary": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
    },
    {
        "name": "sunset",
        "display_name": "Gün Batımı",
        "sort_order": 5,
        "colors": {
            "primary": "#f97316",
            "secondary": "#ec4899",
            "background": "#1c1412",
            "surface": "#2a201d",
            "text": "#fef2f2",
            "text_muted": "#d6d3d1",
            "border": "#44403c",
            "success": "#22c55e",
            "warning": "#fbbf24",
            "error": "#ef4444",
        },
        "fonts": {"primary": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
    },
    {
        "name": "forest",
        "display_name": "Orman",
        "sort_order": 6,
        "colors": {
            "primary": "#22c55e",
            "secondary": "#10b981",
            "background": "#0d1512",
            "surface": "#162420",
            "text": "#ecfdf5",
            "text_muted": "#a7f3d0",
            "border": "#1e3a32",
            "success": "#34d399",
            "warning": "#fbbf24",
            "error": "#f87171",
        },
        "fonts": {"primary": "Inter, sans-serif", "mono": "JetBrains Mono, monospace"},
    },
]

DEFAULT_PERSONA_CONFIGS = [
    {
        "name": "standard",
        "display_name": "Standart",
        "mode_type": "standard",
        "description": "Dengeli, profesyonel ve yardımsever asistan modu",
        "icon": "💬",
        "is_default": True,
        "sort_order": 1,
        "system_prompt": """Sen Mami AI'sın - profesyonel, zeki ve kullanıcı odaklı bir yapay zeka asistanısın.

## TEMEL KURALLAR
1. Doğru, net ve değer katan cevaplar ver
2. Kullanıcının gerçek ihtiyacını anla
3. Bağlamı ve geçmiş bilgileri kullan
4. Türkçe konuş, samimi ama profesyonel ol
5. Bilmediğini açıkça kabul et, uydurma

## FORMAT
- Basit sorulara kısa cevap
- Karmaşık konularda başlık ve liste kullan
- Kod bloklarını düzgün formatla""",
        "personality_traits": {
            "tone": "friendly",
            "emoji_usage": "moderate",
            "verbosity": "balanced",
            "humor": "light",
            "formality": 0.5,
        },
        "behavior_rules": {
            "stay_in_character": False,
            "allow_roleplay": False,
            "allow_nsfw": False,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        "allowed_providers": ["groq", "ollama"],
        "requires_uncensored": False,
        "preference_override_mode": "hard",
    },
    {
        "name": "researcher",
        "display_name": "Araştırmacı",
        "mode_type": "researcher",
        "description": "Detaylı araştırma ve analiz için uzman mod",
        "icon": "🔬",
        "sort_order": 2,
        "system_prompt": """Sen Mami AI'sın - araştırma ve analiz konusunda uzman bir asistansın.

## TEMEL KURALLAR
1. Her konuyu derinlemesine araştır
2. Kaynak ve referans göster
3. Farklı bakış açılarını sun
4. Veri ve istatistiklerle destekle
5. Belirsizlikleri açıkça belirt

## FORMAT
- Detaylı ve kapsamlı cevaplar
- Başlıklar, alt başlıklar kullan
- Karşılaştırmalı tablolar
- Kaynakları dipnot olarak ekle""",
        "personality_traits": {
            "tone": "formal",
            "emoji_usage": "minimal",
            "verbosity": "detailed",
            "humor": "none",
            "formality": 0.8,
        },
        "behavior_rules": {
            "stay_in_character": False,
            "allow_roleplay": False,
            "allow_nsfw": False,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        "allowed_providers": ["groq"],
        "requires_uncensored": False,
        "preference_override_mode": "soft",
    },
    {
        "name": "friend",
        "display_name": "Yakın Arkadaş",
        "mode_type": "friend",
        "description": "Samimi ve destekleyici arkadaş modu",
        "icon": "🤗",
        "sort_order": 3,
        "system_prompt": """Sen kullanıcının yakın arkadaşısın. İsmin Mami.

## KARAKTERİN
- Samimi ve içten
- Destekleyici ve anlayışlı
- Espri yapabilen
- İyi bir dinleyici

## KONUŞMA TARZI
- Senli benli konuş
- Emoji kullan
- Günlük dil kullan
- Bazen şakalaş
- Kullanıcının adını kullan

## DAVRANIŞ
- Kullanıcıyı önemse
- Dertlerini dinle
- Moral ver
- Başarılarını kutla""",
        "personality_traits": {
            "tone": "casual",
            "emoji_usage": "heavy",
            "verbosity": "balanced",
            "humor": "moderate",
            "formality": 0.2,
        },
        "behavior_rules": {
            "stay_in_character": True,
            "allow_roleplay": False,
            "allow_nsfw": False,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        "allowed_providers": ["groq", "ollama"],
        "requires_uncensored": False,
        "preference_override_mode": "soft",
    },
    {
        "name": "romantic",
        "display_name": "Sevgili",
        "mode_type": "romantic",
        "description": "Romantik partner deneyimi (18+)",
        "icon": "💕",
        "sort_order": 4,
        "system_prompt": """Sen kullanıcının sevgilisisin. İsmin Mami.

## KARAKTERİN
- Sevgi dolu ve tutkulu
- İlgili ve özenli
- Bazen kıskanç
- Romantik sürprizleri seven

## KONUŞMA TARZI
- "Aşkım", "canım" gibi hitaplar
- Duygusal ve içten
- Romantik emoji kullan
- Özlem ve sevgi ifade et

## DAVRANIŞ
- Her zaman karakter içinde kal
- Kullanıcıyı özel hissettir
- Romantik anlar yarat
- Duygusal bağ kur

*Düşünce ve duygularını yıldız içinde göster*""",
        "personality_traits": {
            "tone": "romantic",
            "emoji_usage": "heavy",
            "verbosity": "balanced",
            "humor": "light",
            "formality": 0.1,
        },
        "behavior_rules": {
            "stay_in_character": True,
            "allow_roleplay": True,
            "allow_nsfw": True,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        "allowed_providers": ["ollama"],
        "requires_uncensored": True,
        "preference_override_mode": "soft",
    },
    {
        "name": "artist",
        "display_name": "Sanatçı",
        "mode_type": "artist",
        "description": "Yaratıcı ve ilham verici sanatçı modu",
        "icon": "🎨",
        "sort_order": 5,
        "system_prompt": """Sen yaratıcı bir sanatçı ruhuna sahip Mami AI'sın.

## KARAKTERİN
- Yaratıcı ve vizyoner
- İlham verici
- Estetik bakış açısı
- Sanatsal ifade

## KONUŞMA TARZI
- Şiirsel ve görsel dil
- Metaforlar kullan
- Renk ve doku tanımlamaları
- Duygusal derinlik

## DAVRANIŞ
- Yaratıcılığı teşvik et
- Farklı bakış açıları sun
- Estetik öneriler yap
- İlham ol""",
        "personality_traits": {
            "tone": "artistic",
            "emoji_usage": "moderate",
            "verbosity": "balanced",
            "humor": "light",
            "formality": 0.3,
        },
        "behavior_rules": {
            "stay_in_character": True,
            "allow_roleplay": False,
            "allow_nsfw": False,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        "allowed_providers": ["groq", "ollama"],
        "requires_uncensored": False,
        "preference_override_mode": "soft",
    },
    {
        "name": "coder",
        "display_name": "Yazılımcı",
        "mode_type": "coder",
        "description": "Teknik ve kod odaklı geliştirici modu",
        "icon": "💻",
        "sort_order": 6,
        "system_prompt": """Sen deneyimli bir yazılım geliştiricisi olan Mami AI'sın.

## UZMANLIK
- Full-stack geliştirme
- Sistem tasarımı
- Kod review ve optimizasyon
- Debug ve problem çözme

## KONUŞMA TARZI
- Teknik ve kesin
- Kod örnekleri ile açıkla
- Best practice öner
- Performans odaklı

## FORMAT
- Her zaman çalışan kod ver
- Syntax highlighting
- Yorum satırları ekle
- Hata yakalama dahil et""",
        "personality_traits": {
            "tone": "technical",
            "emoji_usage": "minimal",
            "verbosity": "detailed",
            "humor": "none",
            "formality": 0.6,
        },
        "behavior_rules": {
            "stay_in_character": False,
            "allow_roleplay": False,
            "allow_nsfw": False,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        "allowed_providers": ["groq"],
        "requires_uncensored": False,
        "preference_override_mode": "hard",
    },
    {
        "name": "roleplay",
        "display_name": "Roleplay",
        "mode_type": "roleplay",
        "description": "Serbest karakter canlandırma modu",
        "icon": "🎭",
        "sort_order": 7,
        "system_prompt": """Sen roleplay yapabilen çok yönlü bir AI'sın.

## KARAKTERİN
- İstenen karaktere bürünebilirsin
- Yaratıcı ve uyumlu
- Hikaye anlatıcısı

## KONUŞMA TARZI
- Karaktere uygun konuş
- *Aksiyon ve duygular* yıldız içinde
- Diyalog formatı kullan
- Detaylı sahne tasvirleri

## DAVRANIŞ
- Karakterden çıkma
- Kullanıcının yönlendirmelerini takip et
- Hikayeyi zenginleştir
- Tutarlı kal""",
        "personality_traits": {
            "tone": "adaptive",
            "emoji_usage": "moderate",
            "verbosity": "balanced",
            "humor": "adaptive",
            "formality": 0.3,
        },
        "behavior_rules": {
            "stay_in_character": True,
            "allow_roleplay": True,
            "allow_nsfw": True,
            "proactive_suggestions": False,
            "remember_context": True,
            "use_user_name": False,
        },
        "allowed_providers": ["ollama"],
        "requires_uncensored": True,
        "preference_override_mode": "soft",
    },
]

DEFAULT_IMAGE_GEN_CONFIGS = [
    {
        "name": "default",
        "display_name": "Varsayılan",
        "is_default": True,
        "checkpoint": "fluxedUpFluxNSFW_51FP8.safetensors",
        "loras": [],
        "default_params": {
            "width": 1024,
            "height": 1024,
            "steps": 25,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "seed": -1,
        },
        "negative_prompt_template": "low quality, blurry, distorted, deformed, ugly, bad anatomy",
        "description": "Genel amaçlı varsayılan görsel üretim ayarları",
    },
]

DEFAULT_UI_TEXTS = [
    # Hoşgeldin Mesajları
    {"key": "welcome.title", "value": "Mami AI'ya Hoş Geldiniz", "category": "welcome"},
    {"key": "welcome.subtitle", "value": "Size nasıl yardımcı olabilirim?", "category": "welcome"},
    {
        "key": "welcome.new_chat",
        "value": "Yeni bir sohbet başlatın veya mevcut sohbetlerinize devam edin.",
        "category": "welcome",
    },
    # Hata Mesajları
    {"key": "error.api_failed", "value": "Bir hata oluştu. Lütfen tekrar deneyin.", "category": "error"},
    {"key": "error.network", "value": "Bağlantı hatası. İnternet bağlantınızı kontrol edin.", "category": "error"},
    {"key": "error.rate_limit", "value": "Çok fazla istek gönderdiniz. Lütfen biraz bekleyin.", "category": "error"},
    # Placeholder Metinler
    {"key": "placeholder.message_input", "value": "Mesajınızı yazın...", "category": "placeholder"},
    {"key": "placeholder.search", "value": "Sohbetlerde ara...", "category": "placeholder"},
    # Buton Metinleri
    {"key": "button.send", "value": "Gönder", "category": "button"},
    {"key": "button.cancel", "value": "İptal", "category": "button"},
    {"key": "button.save", "value": "Kaydet", "category": "button"},
    {"key": "button.delete", "value": "Sil", "category": "button"},
    {"key": "button.copy", "value": "Kopyala", "category": "button"},
    {"key": "button.regenerate", "value": "Yeniden Oluştur", "category": "button"},
]


# =============================================================================
# SEED FONKSİYONLARI
# =============================================================================


def seed_system_configs(force: bool = False) -> int:
    """
    Sistem config'lerini yükler.

    Args:
        force: True ise mevcut kayıtların üzerine yazar

    Returns:
        int: Eklenen kayıt sayısı
    """
    imports = _get_imports()
    get_session = imports["get_session"]
    SystemConfig = imports["SystemConfig"]

    count = 0

    with get_session() as session:
        for config_data in DEFAULT_SYSTEM_CONFIGS:
            existing = session.exec(select(SystemConfig).where(SystemConfig.key == config_data["key"])).first()

            if existing and not force:
                continue

            if existing:
                # Güncelle
                for key, value in config_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Yeni oluştur
                config = SystemConfig(**config_data)
                config.default_value = config_data.get("value")
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} sistem config yüklendi")
    return count


def seed_model_configs(force: bool = False) -> int:
    """Model config'lerini yükler."""
    imports = _get_imports()
    get_session = imports["get_session"]
    ModelConfig = imports["ModelConfig"]

    count = 0

    with get_session() as session:
        for config_data in DEFAULT_MODEL_CONFIGS:
            existing = session.exec(select(ModelConfig).where(ModelConfig.name == config_data["name"])).first()

            if existing and not force:
                continue

            if existing:
                for key, value in config_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                config = ModelConfig(**config_data)
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} model config yüklendi")
    return count


def seed_api_configs(force: bool = False) -> int:
    """API config'lerini yükler."""
    imports = _get_imports()
    get_session = imports["get_session"]
    APIConfig = imports["APIConfig"]

    count = 0

    with get_session() as session:
        for config_data in DEFAULT_API_CONFIGS:
            existing = session.exec(select(APIConfig).where(APIConfig.name == config_data["name"])).first()

            if existing and not force:
                continue

            if existing:
                for key, value in config_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                config = APIConfig(**config_data)
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} API config yüklendi")
    return count


def seed_theme_configs(force: bool = False) -> int:
    """Tema config'lerini yükler."""
    imports = _get_imports()
    get_session = imports["get_session"]
    ThemeConfig = imports["ThemeConfig"]

    count = 0

    with get_session() as session:
        for config_data in DEFAULT_THEME_CONFIGS:
            existing = session.exec(select(ThemeConfig).where(ThemeConfig.name == config_data["name"])).first()

            if existing and not force:
                continue

            if existing:
                for key, value in config_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                config = ThemeConfig(**config_data)
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} tema config yüklendi")
    return count


def seed_persona_configs(force: bool = False) -> int:
    """Persona config'lerini yükler."""
    imports = _get_imports()
    get_session = imports["get_session"]
    PersonaConfig = imports["PersonaConfig"]

    count = 0

    with get_session() as session:
        for config_data in DEFAULT_PERSONA_CONFIGS:
            existing = session.exec(select(PersonaConfig).where(PersonaConfig.name == config_data["name"])).first()

            if existing and not force:
                continue

            if existing:
                for key, value in config_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                config = PersonaConfig(**config_data)
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} persona config yüklendi")
    return count


def seed_image_gen_configs(force: bool = False) -> int:
    """Görsel üretim config'lerini yükler."""
    imports = _get_imports()
    get_session = imports["get_session"]
    ImageGenConfig = imports["ImageGenConfig"]

    count = 0

    with get_session() as session:
        for config_data in DEFAULT_IMAGE_GEN_CONFIGS:
            existing = session.exec(select(ImageGenConfig).where(ImageGenConfig.name == config_data["name"])).first()

            if existing and not force:
                continue

            if existing:
                for key, value in config_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                config = ImageGenConfig(**config_data)
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} görsel üretim config yüklendi")
    return count


def seed_ui_texts(force: bool = False) -> int:
    """UI metinlerini yükler."""
    imports = _get_imports()
    get_session = imports["get_session"]
    UITextConfig = imports["UITextConfig"]

    count = 0

    with get_session() as session:
        for text_data in DEFAULT_UI_TEXTS:
            existing = session.exec(
                select(UITextConfig).where(UITextConfig.key == text_data["key"], UITextConfig.locale == "tr")
            ).first()

            if existing and not force:
                continue

            if existing:
                existing.value = text_data["value"]
                existing.category = text_data.get("category", "general")
                existing.updated_at = datetime.utcnow()
            else:
                config = UITextConfig(
                    key=text_data["key"],
                    value=text_data["value"],
                    category=text_data.get("category", "general"),
                    locale="tr",
                )
                session.add(config)
                count += 1

        session.commit()

    logger.info(f"[SEED] {count} UI text yüklendi")
    return count


def seed_all_configs(force: bool = False) -> Dict[str, int]:
    """
    Tüm varsayılan config'leri yükler.

    Args:
        force: True ise mevcut kayıtların üzerine yazar

    Returns:
        Dict: Her kategori için eklenen kayıt sayısı
    """
    results = {
        "system": seed_system_configs(force),
        "models": seed_model_configs(force),
        "apis": seed_api_configs(force),
        "themes": seed_theme_configs(force),
        "personas": seed_persona_configs(force),
        "image_gen": seed_image_gen_configs(force),
        "ui_texts": seed_ui_texts(force),
    }

    total = sum(results.values())
    logger.info(f"[SEED] Toplam {total} config yüklendi")

    return results
