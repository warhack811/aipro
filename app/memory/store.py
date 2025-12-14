"""
Mami AI - Hafıza Deposu
=======================

Bu modül, kullanıcı hafızalarını (uzun vadeli bilgiler) yönetir.

Özellikler:
    - Semantik arama (ChromaDB)
    - Importance bazlı sıralama
    - Soft delete desteği
    - User ID resolver pattern

Kullanım:
    from app.memory.store import add_memory, search_memories
    
    # Hafıza ekle
    item = await add_memory("john", "Kedimin adı Pamuk", importance=0.8)
    
    # Hafıza ara
    memories = await search_memories("john", "kedim ne?", max_items=5)

Mimari:
    MemoryStore (bu modül) -> MemoryService -> ChromaDB
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

# Modül logger'ı
logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASS
# =============================================================================

@dataclass
class MemoryItem:
    """
    Hafıza kaydı veri sınıfı.
    
    Attributes:
        id: Benzersiz hafıza ID'si (UUID)
        text: Hafıza içeriği
        created_at: Oluşturulma zamanı
        importance: Önem skoru (0.0-1.0)
        tags: Etiketler listesi
        topic: Konu kategorisi
        score: Arama relevance skoru
    """
    text: str
    created_at: str
    id: Optional[str] = None
    importance: float = 0.5
    tags: Optional[List[str]] = None
    topic: Optional[str] = "general"
    score: float = 0.0


# =============================================================================
# USER RESOLVER
# =============================================================================

def _default_user_resolver(username: str) -> Optional[int]:
    """Varsayılan user resolver (hata verir)."""
    logger.error("[MEMORY_STORE] User ID resolver henüz set edilmedi!")
    return None


_user_id_resolver: Callable[[str], Optional[int]] = _default_user_resolver


def set_user_resolver(resolver_func: Callable[[str], Optional[int]]) -> None:
    """
    Username -> user_id çözümleyici fonksiyonunu ayarlar.
    
    Args:
        resolver_func: Username alıp user_id döndüren fonksiyon
    
    Example:
        >>> def resolve(username):
        ...     user = get_user_by_username(username)
        ...     return user.id if user else None
        >>> set_user_resolver(resolve)
    """
    global _user_id_resolver
    _user_id_resolver = resolver_func
    logger.info("[MEMORY_STORE] User ID resolver ayarlandı")


def _resolve_user_id(username: str) -> int:
    """Username'i user_id'ye çözer."""
    user_id = _user_id_resolver(username)
    if user_id is None:
        raise ValueError(f"Kullanıcı bulunamadı: {username}")
    return user_id


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_memory_service():
    """MemoryService lazy import."""
    try:
        from app.services.memory_service import MemoryRecord, MemoryService
    except ImportError:
        from app.services.memory_service import MemoryRecord, MemoryService
    return MemoryService, MemoryRecord


def _record_to_item(record) -> MemoryItem:
    """MemoryRecord'u MemoryItem'a dönüştürür."""
    tags_list = []
    if record.topic:
        tags_list.append(record.topic)
    
    return MemoryItem(
        id=record.id,
        text=record.text,
        created_at=record.created_at,
        importance=record.importance,
        tags=tags_list or None,
        topic=record.topic,
        score=record.score or 0.0,
    )


# =============================================================================
# PUBLIC API
# =============================================================================

async def add_memory(
    username: str,
    text: str,
    importance: float = 0.5,
    tags: Optional[List[str]] = None
) -> MemoryItem:
    """
    Yeni hafıza kaydı ekler.
    
    Args:
        username: Kullanıcı adı
        text: Hafıza içeriği
        importance: Önem skoru (0.0-1.0)
        tags: Etiketler
    
    Returns:
        MemoryItem: Oluşturulan hafıza kaydı
    
    Raises:
        ValueError: Kullanıcı bulunamazsa
    """
    MemoryService, _ = _get_memory_service()
    user_id = _resolve_user_id(username)
    topic = tags[0] if tags and len(tags) > 0 else "general"
    
    try:
        record = await MemoryService.add_memory(
            user_id=user_id,
            text=text,
            importance=importance,
            topic=topic
        )
        logger.info(f"[MEMORY] Eklendi: {text[:50]}...")
        return _record_to_item(record)
    except Exception as e:
        logger.error(f"[MEMORY] Ekleme hatası: {e}")
        raise


async def search_memories(
    username: str,
    query: str,
    max_items: int = 5
) -> List[MemoryItem]:
    """
    Hafızalarda semantik arama yapar.
    
    Args:
        username: Kullanıcı adı
        query: Arama sorgusu
        max_items: Maksimum sonuç sayısı
    
    Returns:
        List[MemoryItem]: Eşleşen hafızalar (relevance sıralı)
    """
    MemoryService, _ = _get_memory_service()
    user_id = _resolve_user_id(username)
    
    try:
        records = await MemoryService.retrieve_relevant_memories(
            user_id=user_id,
            query=query,
            limit=max_items
        )
        return [_record_to_item(rec) for rec in records]
    except Exception as e:
        logger.error(f"[MEMORY] Arama hatası: {e}")
        return []


async def list_memories(username: str) -> List[MemoryItem]:
    """
    Kullanıcının tüm hafızalarını listeler.
    
    Args:
        username: Kullanıcı adı
    
    Returns:
        List[MemoryItem]: Tüm hafıza kayıtları
    """
    MemoryService, _ = _get_memory_service()
    user_id = _resolve_user_id(username)
    
    try:
        records = await MemoryService.retrieve_relevant_memories(
            user_id=user_id,
            query="everything about me",
            limit=100,
            min_relevance=0.0
        )
        return [_record_to_item(rec) for rec in records]
    except Exception as e:
        logger.error(f"[MEMORY] Listeleme hatası: {e}")
        return []


async def delete_memory(username: str, memory_id: str) -> bool:
    """
    Hafıza kaydını siler (soft delete).
    
    Args:
        username: Kullanıcı adı
        memory_id: Silinecek hafıza ID'si
    
    Returns:
        bool: Silme başarılı ise True
    """
    MemoryService, _ = _get_memory_service()
    user_id = _resolve_user_id(username)
    
    try:
        result = await MemoryService.soft_delete_memory(user_id, memory_id)
        if result:
            logger.info(f"[MEMORY] Silindi: {memory_id}")
        return result
    except Exception as e:
        logger.error(f"[MEMORY] Silme hatası: {e}")
        return False


async def update_memory(
    username: str,
    memory_id: str,
    text: str,
    importance: Optional[float] = None
) -> Optional[MemoryItem]:
    """
    Mevcut hafıza kaydını günceller.
    
    Args:
        username: Kullanıcı adı
        memory_id: Güncellenecek hafıza ID'si
        text: Yeni içerik
        importance: Yeni önem skoru (opsiyonel)
    
    Returns:
        MemoryItem veya None: Güncellenen kayıt
    """
    MemoryService, _ = _get_memory_service()
    user_id = _resolve_user_id(username)
    
    try:
        record = await MemoryService.update_memory(
            user_id=user_id,
            memory_id=memory_id,
            text=text,
            importance=importance,
        )
        if not record:
            return None
        logger.info(f"[MEMORY] Güncellendi: {memory_id}")
        return _record_to_item(record)
    except Exception as e:
        logger.error(f"[MEMORY] Güncelleme hatası: {e}")
        return None


async def cleanup_old_memories(username: str) -> int:
    """
    Eski/düşük önemli hafızaları temizler.
    
    Returns:
        int: Temizlenen kayıt sayısı
    """
    # TODO: Implement cleanup logic
    return 0







