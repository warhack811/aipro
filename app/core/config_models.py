"""
Mami AI - Dinamik Yapılandırma Modelleri
========================================

Bu modül, admin panelden yönetilebilen dinamik yapılandırma
tablolarını tanımlar.

Tablolar:
    - SystemConfig: Genel key-value ayarlar
    - ModelConfig: LLM model yapılandırmaları
    - APIConfig: Harici API ayarları (endpoint, timeout vb., KEY'LER DEĞİL!)
    - ThemeConfig: UI tema tanımları
    - PersonaConfig: AI kişilik modları

Kullanım:
    from app.core.config_models import SystemConfig, ModelConfig
    from app.core.database import get_session
    
    with get_session() as session:
        config = session.exec(
            select(SystemConfig).where(SystemConfig.key == "app.name")
        ).first()

Güvenlik Notu:
    API KEY'LER BU TABLOLARDA SAKLANMAZ!
    Hassas bilgiler .env dosyasında kalmalıdır.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Text, UniqueConstraint


# =============================================================================
# ENUM TANIMLARI
# =============================================================================

class ConfigValueType(str, Enum):
    """Yapılandırma değer tipleri."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"  # Dict veya List için


class ConfigCategory(str, Enum):
    """Yapılandırma kategorileri (namespace)."""
    SYSTEM = "system"       # Genel sistem ayarları
    MODELS = "models"       # Model yapılandırması
    UI = "ui"               # Arayüz ayarları
    FEATURES = "features"   # Özellik bayrakları
    AI = "ai"               # AI davranış ayarları
    IMAGE = "image"         # Görsel üretim ayarları
    SEARCH = "search"       # Arama ayarları


class ModelProvider(str, Enum):
    """Model sağlayıcıları."""
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class PersonaModeType(str, Enum):
    """Persona mod tipleri."""
    STANDARD = "standard"
    RESEARCHER = "researcher"
    FRIEND = "friend"
    ROMANTIC = "romantic"
    ARTIST = "artist"
    WRITER = "writer"
    ROLEPLAY = "roleplay"
    BUSINESS = "business"
    CODER = "coder"
    CUSTOM = "custom"


# =============================================================================
# SYSTEM CONFIG (Key-Value Store)
# =============================================================================

class SystemConfig(SQLModel, table=True):
    """
    Genel sistem yapılandırması (Key-Value).
    
    EAV (Entity-Attribute-Value) yapısı ile esnek config yönetimi.
    Admin panelden değiştirilebilen tüm ayarlar burada saklanır.
    
    Attributes:
        key: Benzersiz yapılandırma anahtarı (ör: "system.app_name")
        value: Değer (string olarak saklanır, tip dönüşümü runtime'da)
        value_type: Değer tipi (string, integer, float, boolean, json)
        category: Kategori/namespace
        description: Admin panel için açıklama
        is_secret: Gizli mi (UI'da maskelenir)
        is_editable: Admin panelden düzenlenebilir mi
        default_value: Varsayılan değer (.env'den veya hardcode)
    
    Example:
        >>> config = SystemConfig(
        ...     key="system.app_name",
        ...     value="Mami AI Pro",
        ...     value_type=ConfigValueType.STRING,
        ...     category=ConfigCategory.SYSTEM,
        ...     description="Uygulama adı"
        ... )
    """
    __tablename__ = "system_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("key", name="uq_system_config_key"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Anahtar ve Değer
    key: str = Field(index=True, max_length=128)
    value: str = Field(sa_column=Column(Text))
    
    # Tip Bilgisi
    value_type: str = Field(default=ConfigValueType.STRING.value, max_length=16)
    category: str = Field(default=ConfigCategory.SYSTEM.value, index=True, max_length=32)
    
    # Meta Bilgiler
    description: Optional[str] = Field(default=None, max_length=512)
    is_secret: bool = Field(default=False)  # UI'da maskelenir
    is_editable: bool = Field(default=True)  # Admin'den değiştirilebilir mi
    
    # Varsayılan (reset için)
    default_value: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Zaman Damgaları
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = Field(default=None, max_length=64)  # Admin username


# =============================================================================
# MODEL CONFIG
# =============================================================================

class ModelConfig(SQLModel, table=True):
    """
    LLM Model yapılandırması.
    
    Her model için ayrı kayıt: Groq modelleri, Ollama modelleri vb.
    Admin panelden model ekleme/düzenleme/aktif-pasif yapma.
    
    Attributes:
        name: Benzersiz model tanımlayıcı (ör: "groq_main", "ollama_qwen")
        display_name: UI'da gösterilecek isim
        provider: Sağlayıcı (groq, ollama, openai)
        model_id: Sağlayıcıdaki model adı (ör: "llama-3.3-70b-versatile")
        purpose: Kullanım amacı (answer, decider, semantic, fast)
        is_active: Aktif mi
        is_default: Bu amaç için varsayılan mı
        parameters: Model parametreleri (temperature, max_tokens vb.)
        capabilities: Model yetenekleri (streaming, json_mode vb.)
    """
    __tablename__ = "model_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("name", name="uq_model_config_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tanımlama
    name: str = Field(index=True, max_length=64)  # Internal identifier
    display_name: str = Field(max_length=128)      # UI display name
    
    # Sağlayıcı Bilgileri
    provider: str = Field(index=True, max_length=32)  # groq, ollama, openai
    model_id: str = Field(max_length=128)              # Actual model name at provider
    
    # Kullanım Amacı
    purpose: str = Field(index=True, max_length=32)  # answer, decider, semantic, fast, uncensored
    
    # Durum
    is_active: bool = Field(default=True, index=True)
    is_default: bool = Field(default=False)  # Bu purpose için varsayılan mı
    priority: int = Field(default=0)         # Fallback sırası (yüksek = önce)
    
    # Model Parametreleri (JSON)
    parameters: Dict[str, Any] = Field(
        default={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9,
        },
        sa_column=Column(JSON)
    )
    
    # Model Yetenekleri (JSON)
    capabilities: Dict[str, bool] = Field(
        default={
            "streaming": True,
            "json_mode": True,
            "function_calling": False,
            "vision": False,
        },
        sa_column=Column(JSON)
    )
    
    # Açıklama
    description: Optional[str] = Field(default=None, max_length=512)
    
    # Zaman Damgaları
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# API CONFIG (Endpoint & Settings - NOT KEYS!)
# =============================================================================

class APIConfig(SQLModel, table=True):
    """
    Harici API yapılandırması.
    
    DİKKAT: API KEY'LER BURADA SAKLANMAZ!
    Sadece endpoint URL'leri, timeout'lar ve diğer ayarlar.
    
    Attributes:
        name: API tanımlayıcı (ör: "groq", "bing_search", "forge")
        display_name: UI'da gösterilecek isim
        base_url: Ana endpoint URL
        is_active: Aktif mi
        timeout: İstek zaman aşımı (saniye)
        rate_limit: Dakikadaki maksimum istek
        settings: Ek ayarlar (JSON)
    """
    __tablename__ = "api_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("name", name="uq_api_config_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tanımlama
    name: str = Field(index=True, max_length=64)
    display_name: str = Field(max_length=128)
    
    # Endpoint
    base_url: str = Field(max_length=512)
    
    # Durum
    is_active: bool = Field(default=True, index=True)
    
    # Ayarlar
    timeout: int = Field(default=30)       # Saniye
    rate_limit: int = Field(default=60)    # İstek/dakika (0 = sınırsız)
    retry_count: int = Field(default=3)    # Yeniden deneme sayısı
    
    # Ek Ayarlar (JSON)
    settings: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Açıklama
    description: Optional[str] = Field(default=None, max_length=512)
    
    # Zaman Damgaları
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# THEME CONFIG
# =============================================================================

class ThemeConfig(SQLModel, table=True):
    """
    UI tema yapılandırması.
    
    Admin panelden tema ekleme/düzenleme. Kod değişikliği gerektirmez.
    
    Attributes:
        name: Tema tanımlayıcı (ör: "dark", "ocean", "sunset")
        display_name: UI'da gösterilecek isim
        is_active: Kullanılabilir mi
        is_default: Varsayılan tema mı
        colors: Renk paleti (JSON)
        fonts: Font ayarları (JSON)
        custom_css: Özel CSS (opsiyonel)
    """
    __tablename__ = "theme_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("name", name="uq_theme_config_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tanımlama
    name: str = Field(index=True, max_length=32)
    display_name: str = Field(max_length=64)
    
    # Durum
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    sort_order: int = Field(default=0)
    
    # Renk Paleti (JSON)
    colors: Dict[str, str] = Field(
        default={
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
        sa_column=Column(JSON)
    )
    
    # Font Ayarları (JSON)
    fonts: Dict[str, str] = Field(
        default={
            "primary": "Inter, sans-serif",
            "mono": "JetBrains Mono, monospace",
            "size_base": "16px",
        },
        sa_column=Column(JSON)
    )
    
    # Özel CSS (opsiyonel)
    custom_css: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Zaman Damgaları
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PERSONA CONFIG (Mod Sistemi)
# =============================================================================

class PersonaConfig(SQLModel, table=True):
    """
    AI kişilik/mod yapılandırması.
    
    Her mod için ayrı davranış kuralları, system prompt, ton ayarları.
    Admin panelden mod ekleme/düzenleme.
    
    Attributes:
        name: Mod tanımlayıcı (ör: "standard", "friend", "romantic")
        display_name: UI'da gösterilecek isim
        mode_type: Mod tipi enum
        description: Kullanıcıya gösterilecek açıklama
        system_prompt: Ana system prompt
        personality_traits: Kişilik özellikleri (JSON)
        behavior_rules: Davranış kuralları (JSON)
        allowed_for: Hangi model'ler için geçerli (JSON array)
        requires_uncensored: Sansürsüz model gerektirir mi
    """
    __tablename__ = "persona_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("name", name="uq_persona_config_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tanımlama
    name: str = Field(index=True, max_length=32)
    display_name: str = Field(max_length=64)
    mode_type: str = Field(default=PersonaModeType.STANDARD.value, max_length=32)
    
    # Açıklama (kullanıcıya gösterilir)
    description: Optional[str] = Field(default=None, max_length=512)
    icon: Optional[str] = Field(default="💬", max_length=8)  # Emoji veya icon adı
    
    # Durum
    is_active: bool = Field(default=True, index=True)
    is_default: bool = Field(default=False)
    sort_order: int = Field(default=0)
    
    # Ana System Prompt
    system_prompt: str = Field(sa_column=Column(Text))
    
    # Kişilik Özellikleri (JSON)
    personality_traits: Dict[str, Any] = Field(
        default={
            "tone": "friendly",           # formal, friendly, casual, romantic
            "emoji_usage": "moderate",    # none, minimal, moderate, heavy
            "verbosity": "balanced",      # brief, balanced, detailed
            "humor": "light",             # none, light, moderate, heavy
            "formality": 0.5,             # 0.0 (casual) - 1.0 (formal)
        },
        sa_column=Column(JSON)
    )
    
    # Davranış Kuralları (JSON)
    behavior_rules: Dict[str, Any] = Field(
        default={
            "stay_in_character": True,
            "allow_roleplay": False,
            "allow_nsfw": False,
            "proactive_suggestions": True,
            "remember_context": True,
            "use_user_name": True,
        },
        sa_column=Column(JSON)
    )
    
    # Model Kısıtlamaları
    allowed_providers: List[str] = Field(
        default=["groq", "ollama"],
        sa_column=Column(JSON)
    )
    requires_uncensored: bool = Field(default=False)
    preferred_model_purpose: Optional[str] = Field(default=None, max_length=32)
    
    # Kullanıcı Tercih Override Davranışı
    # hard: Kullanıcı tercihi tam uygulanır, soft: Mod ruhu korunur
    preference_override_mode: str = Field(default="soft", max_length=8)
    
    # Örnek Diyaloglar (Few-shot için)
    example_dialogues: List[Dict[str, str]] = Field(
        default=[],
        sa_column=Column(JSON)
    )
    
    # Zaman Damgaları
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# IMAGE GENERATION CONFIG
# =============================================================================

class ImageGenConfig(SQLModel, table=True):
    """
    Görsel üretim yapılandırması.
    
    Forge/SD WebUI için model, LoRA ve üretim ayarları.
    Admin panelden yönetilebilir.
    
    Attributes:
        name: Yapılandırma adı (ör: "default", "anime", "realistic")
        checkpoint: Ana model dosyası
        loras: LoRA listesi ve ağırlıkları
        default_params: Varsayılan üretim parametreleri
    """
    __tablename__ = "image_gen_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("name", name="uq_image_gen_config_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tanımlama
    name: str = Field(index=True, max_length=64)
    display_name: str = Field(max_length=128)
    
    # Durum
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    
    # Model Ayarları
    checkpoint: str = Field(max_length=256)  # Checkpoint dosya adı
    vae: Optional[str] = Field(default=None, max_length=256)
    
    # LoRA Listesi (JSON)
    loras: List[Dict[str, Any]] = Field(
        default=[],
        sa_column=Column(JSON)
    )  # [{"name": "detail_lora", "weight": 0.8}, ...]
    
    # Varsayılan Parametreler (JSON)
    default_params: Dict[str, Any] = Field(
        default={
            "width": 1024,
            "height": 1024,
            "steps": 25,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "seed": -1,
            "clip_skip": 2,
        },
        sa_column=Column(JSON)
    )
    
    # Negatif Prompt Şablonu
    negative_prompt_template: str = Field(
        default="low quality, blurry, distorted",
        sa_column=Column(Text)
    )
    
    # Açıklama
    description: Optional[str] = Field(default=None, max_length=512)
    
    # Zaman Damgaları
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# UI TEXT CONFIG (Dinamik Metinler)
# =============================================================================

class UITextConfig(SQLModel, table=True):
    """
    UI metin yapılandırması.
    
    Tüm kullanıcıya gösterilen metinler (hoşgeldin, hata mesajları vb.)
    Admin panelden değiştirilebilir.
    
    Attributes:
        key: Metin anahtarı (ör: "welcome_message", "error.api_failed")
        value: Metin içeriği
        locale: Dil kodu (tr, en)
    """
    __tablename__ = "ui_text_configs"  # type: ignore[assignment]
    __table_args__ = (
        UniqueConstraint("key", "locale", name="uq_ui_text_key_locale"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Anahtar ve Değer
    key: str = Field(index=True, max_length=128)
    value: str = Field(sa_column=Column(Text))
    
    # Dil
    locale: str = Field(default="tr", index=True, max_length=8)
    
    # Kategori
    category: str = Field(default="general", index=True, max_length=32)
    
    # Meta
    description: Optional[str] = Field(default=None, max_length=256)
    
    # Zaman Damgaları
    updated_at: datetime = Field(default_factory=datetime.utcnow)







