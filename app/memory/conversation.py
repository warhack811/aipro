"""
Mami AI - Sohbet Geçmişi Yönetimi
=================================

Bu modül, sohbet ve mesaj kayıtlarını yönetir.

Özellikler:
    - Sohbet oluşturma ve listeleme
    - Mesaj ekleme ve yükleme
    - Özet yönetimi
    - Sahiplik kontrolü

Kullanım:
    from app.memory.conversation import create_conversation, append_message
    
    # Yeni sohbet
    conv = create_conversation("john", first_message="Merhaba")
    
    # Mesaj ekle
    append_message("john", conv.id, "user", "Nasılsın?")
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlmodel import col, select

# Modül logger'ı
logger = logging.getLogger(__name__)


# =============================================================================
# USER RESOLVER
# =============================================================================

def _default_user_resolver(username: str) -> Optional[int]:
    """Varsayılan user resolver (hata verir)."""
    logger.error("[CONV_STORE] User ID resolver henüz set edilmedi!")
    return None


_user_id_resolver: Callable[[str], Optional[int]] = _default_user_resolver


def set_user_resolver(resolver_func: Callable[[str], Optional[int]]) -> None:
    """Username -> user_id resolver'ı ayarlar."""
    global _user_id_resolver
    _user_id_resolver = resolver_func
    logger.info("[CONV_STORE] User ID resolver ayarlandı")


def _resolve_user_id(username: str) -> int:
    """Username'i user_id'ye çözer."""
    user_id = _user_id_resolver(username)
    if user_id is None:
        raise ValueError(f"Kullanıcı bulunamadı: {username}")
    return user_id


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    try:
        from app.core.database import get_session
        from app.core.models import Conversation, Message
    except ImportError:
        from app.core.database import get_session
        from app.core.models import Conversation, Message
    return get_session, Conversation, Message


# =============================================================================
# SOHBET İŞLEMLERİ
# =============================================================================

def create_conversation(
    username: str,
    first_message: Optional[str] = None,
    title: Optional[str] = None,
    preset_id: Optional[int] = None
):
    """
    Yeni sohbet oluşturur.
    
    Args:
        username: Kullanıcı adı
        first_message: İlk mesaj (başlık için kullanılır)
        title: Özel başlık
        preset_id: Kullanılacak preset ID'si
    
    Returns:
        Conversation: Oluşturulan sohbet
    """
    get_session, Conversation, _ = _get_imports()
    user_id = _resolve_user_id(username)
    
    # Otomatik başlık
    if not title:
        if first_message:
            title = first_message[:50] + ("..." if len(first_message) > 50 else "")
        else:
            title = "Yeni Sohbet"

    with get_session() as session:
        new_conv = Conversation(
            user_id=user_id,
            title=title,
            preset_id=preset_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        try:
            session.add(new_conv)
            session.commit()
            session.refresh(new_conv)
            logger.info(f"[CONV] Yeni sohbet: {new_conv.id}")
            return new_conv
        except Exception as e:
            session.rollback()
            logger.error(f"[CONV] Oluşturma hatası: {e}")
            raise


def list_conversations(username: str, limit: int = 50) -> List:
    """
    Kullanıcının sohbetlerini listeler.
    
    Args:
        username: Kullanıcı adı
        limit: Maksimum sonuç
    
    Returns:
        List[Conversation]: Sohbet listesi (en yeni üstte)
    """
    get_session, Conversation, _ = _get_imports()
    user_id = _resolve_user_id(username)
    
    with get_session() as session:
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(col(Conversation.updated_at).desc())
            .limit(limit)
        )
        return list(session.exec(statement).all())


def load_messages(username: str, conv_id: str) -> List:
    """
    Sohbetteki mesajları yükler.
    
    Args:
        username: Kullanıcı adı
        conv_id: Sohbet ID'si
    
    Returns:
        List[Message]: Mesaj listesi (kronolojik)
    """
    get_session, Conversation, Message = _get_imports()
    user_id = _resolve_user_id(username)
    
    with get_session() as session:
        # Sahiplik kontrolü
        conv = session.get(Conversation, conv_id)
        if not conv or conv.user_id != user_id:
            logger.warning(f"[CONV] Yetkisiz erişim: {username} -> {conv_id}")
            return []
        
        from sqlmodel import asc
        
        statement = (
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(asc(Message.created_at))
        )
        return list(session.exec(statement).all())


def append_message(
    username: str,
    conv_id: str,
    role: str,
    text: str,
    extra_metadata: Optional[Dict[str, Any]] = None
):
    """
    Sohbete mesaj ekler.
    
    Args:
        username: Kullanıcı adı
        conv_id: Sohbet ID'si
        role: Mesaj rolü (user, bot, system)
        text: Mesaj içeriği
        extra_metadata: Ek bilgiler
    
    Returns:
        Message: Eklenen mesaj
    """
    get_session, Conversation, Message = _get_imports()
    user_id = _resolve_user_id(username)

    with get_session() as session:
        # Sahiplik kontrolü
        conv = session.get(Conversation, conv_id)
        if not conv or conv.user_id != user_id:
            raise ValueError(f"Sohbet bulunamadı veya yetki yok: {conv_id}")

        new_msg = Message(
            conversation_id=conv_id,
            role=role,
            content=text,
            extra_metadata=extra_metadata or {},
            created_at=datetime.utcnow()
        )

        # Sohbet güncelleme zamanını da güncelle
        conv.updated_at = datetime.utcnow()

        try:
            session.add(new_msg)
            session.add(conv)
            session.commit()
            session.refresh(new_msg)
            return new_msg
        except Exception as e:
            session.rollback()
            logger.error(f"[CONV] Mesaj ekleme hatası: {e}")
            raise


def update_message(
    message_id: int,
    new_content: Optional[str] = None,
    new_metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Mevcut mesajı günceller.
    
    Args:
        message_id: Güncellenecek mesaj ID'si
        new_content: Yeni içerik (None ise değişmez)
        new_metadata: Yeni metadata (None ise değişmez, dict ise merge edilir)
    
    Returns:
        bool: Güncelleme başarılı ise True
    """
    get_session, _, Message = _get_imports()

    with get_session() as session:
        msg = session.get(Message, message_id)
        if not msg:
            logger.warning(f"[CONV] Mesaj bulunamadı: {message_id}")
            return False

        if new_content is not None:
            msg.content = new_content

        if new_metadata is not None:
            # Mevcut metadata ile merge et
            existing = msg.extra_metadata or {}
            existing.update(new_metadata)
            msg.extra_metadata = existing

        try:
            session.add(msg)
            session.commit()
            logger.info(f"[CONV] Mesaj güncellendi: {message_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"[CONV] Mesaj güncelleme hatası: {e}")
            return False


def delete_conversation(username: str, conv_id: str) -> bool:
    """
    Sohbeti ve mesajlarını siler.
    
    Args:
        username: Kullanıcı adı
        conv_id: Silinecek sohbet ID'si
    
    Returns:
        bool: Silme başarılı ise True
    """
    get_session, Conversation, _ = _get_imports()
    user_id = _resolve_user_id(username)

    with get_session() as session:
        conv = session.get(Conversation, conv_id)
        if not conv or conv.user_id != user_id:
            return False

        try:
            session.delete(conv)  # Cascade ile mesajlar da silinir
            session.commit()
            logger.info(f"[CONV] Silindi: {conv_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"[CONV] Silme hatası: {e}")
            return False


def get_conversation_summary_text(conv_id: str) -> Optional[str]:
    """
    Sohbet özetini döndürür.
    
    Args:
        conv_id: Sohbet ID'si
    
    Returns:
        str veya None: Özet metni
    """
    try:
        from app.core.models import ConversationSummary
    except ImportError:
        from app.core.models import ConversationSummary
    
    get_session, _, _ = _get_imports()
    
    with get_session() as session:
        summary = session.get(ConversationSummary, conv_id)
        return summary.summary if summary else None


def get_recent_context(username: str, conv_id: str, max_messages: int = 4) -> Optional[str]:
    """
    Son mesajları string olarak döndürür.
    
    Args:
        username: Kullanıcı adı
        conv_id: Sohbet ID'si
        max_messages: Maksimum mesaj sayısı
    
    Returns:
        str veya None: Son mesajlar formatlanmış string
    """
    messages = load_messages(username, conv_id)
    if not messages:
        return None
    
    # Son N mesajı al
    recent = messages[-max_messages:] if len(messages) > max_messages else messages
    
    # Formatla
    lines = []
    for msg in recent:
        role = getattr(msg, "role", "user")
        content = getattr(msg, "content", getattr(msg, "text", ""))
        if content:
            prefix = "Kullanıcı" if role == "user" else "Asistan"
            lines.append(f"{prefix}: {content[:200]}")
    
    return "\n".join(lines) if lines else None

