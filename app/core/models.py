"""
Mami AI - Veritabanı Modelleri
==============================

Bu modül, SQLModel kullanarak veritabanı tablolarını tanımlar.

Model Kategorileri:
    - Kullanıcı: User, UserPreference, ModelPreset
    - Sohbet: Conversation, Message, ConversationSummary
    - Önbellek: AnswerCache
    - Kullanım: UsageCounter
    - Kimlik Doğrulama: Session, Invite
    - Geri Bildirim: Feedback
    - Yapılandırma: AIIdentityConfig, ConversationSummarySettings

Kullanım:
    from app.core.models import User, Conversation, Message
    from app.core.database import get_session
    
    with get_session() as session:
        user = session.get(User, user_id)

İlişkiler:
    User 1--N Conversation 1--N Message
    User 1--N UserPreference
    User 1--N Session
    Conversation 1--1 ConversationSummary
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, Relationship, SQLModel

# =============================================================================
# KULLANICI MODELLERİ
# =============================================================================

class User(SQLModel, table=True):
    """
    Kullanıcı ana tablosu.
    
    Attributes:
        id: Benzersiz kullanıcı ID'si (auto-increment)
        username: Kullanıcı adı (benzersiz, giriş için kullanılır)
        password_hash: Şifrelenmiş parola (Argon2)
        role: Kullanıcı rolü (admin, user, vip)
        is_banned: Kullanıcı yasaklı mı
        selected_model: Varsayılan model tercihi (groq, bela)
        bela_unlocked: Yerel model erişimi var mı
    """
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    password_hash: str
    
    # Rol ve izinler
    role: str = Field(default="user")  # admin, user, vip
    is_banned: bool = Field(default=False)
    
    # Model tercihleri
    selected_model: str = Field(default="groq", max_length=16)  # groq | bela
    bela_unlocked: bool = Field(default=False)
    
    # Aktif persona/mod (kalıcı - DB'de tutulur)
    active_persona: str = Field(default="standard", max_length=64)
    
    # Ek yapılandırma (JSON)
    limits: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    permissions: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Zaman damgası
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # İlişkiler
    preferences: List["UserPreference"] = Relationship(back_populates="user")
    conversations: List["Conversation"] = Relationship(back_populates="user")
    sessions: List["Session"] = Relationship(back_populates="user")
    presets: List["ModelPreset"] = Relationship(back_populates="owner")


class UserPreference(SQLModel, table=True):
    """
    Kullanıcı tercihleri ve persona ayarları.
    
    EAV (Entity-Attribute-Value) yapısı kullanılır:
    - key: Tercih anahtarı (ör: "theme", "language")
    - value: Tercih değeri
    - category: Kategori (system, behavior, personal)
    - source: Kaynak (explicit: kullanıcı belirledi, inferred: model çıkardı)
    """
    __tablename__ = "user_preferences"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    key: str = Field(index=True, max_length=64)
    value: str = Field(sa_column=Column(Text))  # Uzun metin olabilir
    
    category: str = Field(default="system", index=True)  # system, behavior, personal
    source: str = Field(default="explicit")  # explicit, inferred
   
    is_active: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # İlişki
    user: Optional[User] = Relationship(back_populates="preferences")


class ModelPreset(SQLModel, table=True):
    """
    Model kişilik şablonları.
    
    Farklı "modlar" veya "kişilikler" için ayar şablonları tanımlar.
    Örnek: "Profesyonel", "Arkadaş Canlısı", "Teknik Uzman"
    """
    __tablename__ = "model_presets"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    
    # Prompt Mühendisliği
    system_prompt_template: str = Field(sa_column=Column(Text))
    
    # Model Parametreleri
    temperature: float = Field(default=0.7)
    max_tokens: Optional[int] = Field(default=None)
    model_name: Optional[str] = Field(default=None)  # Model override
    
    # Erişim
    is_global: bool = Field(default=False)  # Herkese açık mı
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # İlişkiler
    owner: Optional[User] = Relationship(back_populates="presets")
    conversations: List["Conversation"] = Relationship(back_populates="preset")


# =============================================================================
# SOHBET MODELLERİ
# =============================================================================

class Conversation(SQLModel, table=True):
    """
    Sohbet ana kaydı.
    
    Her sohbet bir kullanıcıya aittir ve birden fazla mesaj içerir.
    """
    __tablename__ = "conversations"  # type: ignore[assignment]

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: Optional[str] = Field(default="Yeni Sohbet")
    
    preset_id: Optional[int] = Field(default=None, foreign_key="model_presets.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # İlişkiler
    user: Optional[User] = Relationship(back_populates="conversations")
    preset: Optional[ModelPreset] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    summary: Optional["ConversationSummary"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Message(SQLModel, table=True):
    """
    Sohbet mesajları.
    
    Attributes:
        role: Mesaj rolü (user, bot, system)
        content: Mesaj içeriği
        extra_metadata: Ek bilgiler (token sayısı, latency vb.)
    """
    __tablename__ = "messages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    
    role: str = Field(index=True)  # user, bot, system
    content: str = Field(sa_column=Column(Text))
    
    # Ek metadata (JSON)
    extra_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # İlişki
    conversation: Optional[Conversation] = Relationship(back_populates="messages")


class ConversationSummary(SQLModel, table=True):
    """
    Sohbet özeti.
    
    Uzun sohbetler için otomatik oluşturulan kısa özet.
    Her sohbet için tek bir özet kaydı bulunur.
    """
    __tablename__ = "conversation_summaries"  # type: ignore[assignment]

    conversation_id: str = Field(
        primary_key=True,
        foreign_key="conversations.id",
        index=True
    )
    summary: str = Field(sa_column=Column(Text))
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Özet güncellendiğindeki mesaj sayısı
    message_count_at_update: int = Field(default=0)
    
    # Son özetlenen mesajın ID'si (incremental update için)
    last_message_id: Optional[int] = Field(default=None)

    # İlişki
    conversation: Optional["Conversation"] = Relationship(back_populates="summary")


# =============================================================================
# ÖNBELLEK MODELLERİ
# =============================================================================

class AnswerCache(SQLModel, table=True):
    """
    AI yanıt önbelleği.
    
    Aynı/benzer sorulara hızlı yanıt vermek için kullanılır.
    """
    __tablename__ = "answer_cache"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    cache_key: str = Field(index=True, max_length=128)  # Lookup anahtarı
    question: str = Field(sa_column=Column(Text))
    answer: str = Field(sa_column=Column(Text))

    engine: str = Field(max_length=32)  # groq, local

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, index=True)

    user: Optional["User"] = Relationship()


# =============================================================================
# KULLANIM TAKİBİ
# =============================================================================

class UsageCounter(SQLModel, table=True):
    """
    Günlük kullanım sayacı.
    
    Her kullanıcı için her gün ayrı bir kayıt oluşturulur.
    Rate limiting ve kota yönetimi için kullanılır.
    """
    __tablename__ = "usage_counters"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    usage_date: date = Field(index=True)  # Hangi günün sayacı (UTC)

    groq_count: int = Field(default=0)       # Groq API çağrı sayısı
    local_count: int = Field(default=0)      # Yerel model çağrı sayısı
    total_chat_count: int = Field(default=0) # Toplam mesaj sayısı

    user: Optional["User"] = Relationship()


# =============================================================================
# KİMLİK DOĞRULAMA
# =============================================================================

class Session(SQLModel, table=True):
    """
    Kullanıcı oturumları.
    
    Cookie tabanlı oturum yönetimi için kullanılır.
    """
    __tablename__ = "sessions"  # type: ignore[assignment]

    id: str = Field(primary_key=True)  # Cookie'deki token
    user_id: int = Field(foreign_key="users.id", index=True)
    
    type: str = Field(default="active_session")  # active_session, remember_token
    expires_at: datetime = Field(index=True)
    user_agent: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="sessions")


class Invite(SQLModel, table=True):
    """
    Davet kodları.
    
    Yeni kullanıcı kaydı için davet kodu sistemi.
    """
    __tablename__ = "invites"  # type: ignore[assignment]

    code: str = Field(primary_key=True)
    created_by: str = Field(max_length=64)  # Oluşturan kullanıcı adı
    
    is_used: bool = Field(default=False, index=True)
    used_by: Optional[str] = Field(default=None, max_length=64)
    used_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# GERİ BİLDİRİM
# =============================================================================

class Feedback(SQLModel, table=True):
    """
    Kullanıcı geri bildirimleri.
    
    Mesajlara verilen like/dislike geri bildirimleri.
    """
    __tablename__ = "feedback"  # type: ignore[assignment]
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    conversation_id: Optional[str] = Field(default=None, foreign_key="conversations.id")
    
    message_content: str = Field(sa_column=Column(Text))
    feedback_type: str = Field(max_length=10)  # like, dislike
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional["User"] = Relationship()
    conversation: Optional["Conversation"] = Relationship()


# =============================================================================
# SİSTEM YAPILANDIRMASI
# =============================================================================

class AIIdentityConfig(SQLModel, table=True):
    """
    AI kimlik yapılandırması (Singleton).
    
    Yapay zekanın adı, kişiliği ve davranış kuralları.
    """
    __tablename__ = "ai_identity_config"  # type: ignore[assignment]

    id: int = Field(default=1, primary_key=True)
    
    display_name: str = Field(default="Akıllı Asistan")
    developer_name: str = Field(default="bu sistemin geliştiricileri")
    product_family: str = Field(default="bu sohbet sistemi")
    
    short_intro: str = Field(
        sa_column=Column(Text),
        default=(
            "Ben kullanıcıların sorularına yanıt vermek ve yardımcı olmak için "
            "tasarlanmış bir yapay zeka asistanıyım."
        )
    )
    
    # Sağlayıcı ismini (Google, OpenAI vb.) gizle
    forbid_provider_mention: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationSummarySettings(SQLModel, table=True):
    """
    Sohbet özeti sistemi ayarları (Singleton).
    
    Özetleme davranışını kontrol eden parametreler.
    """
    __tablename__ = "conversation_summary_settings"  # type: ignore[assignment]

    id: int = Field(default=1, primary_key=True)

    summary_enabled: bool = Field(default=True)
    summary_first_threshold: int = Field(default=12, ge=1)  # İlk özet kaç mesajda
    summary_update_step: int = Field(default=10, ge=1)      # Kaç mesajda güncelle
    summary_max_messages: int = Field(default=40, ge=5)     # Maksimum mesaj

    updated_at: datetime = Field(default_factory=datetime.utcnow)

