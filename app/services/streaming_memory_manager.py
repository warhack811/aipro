"""
Mami AI - Streaming Memory Manager
===================================

Streaming sırasında memory duplicate'i önlemek için lock mekanizması.
"""

import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StreamingMemoryManager:
    """
    Streaming memory kaydı için race condition önleme.
    
    Özellikler:
    - Message ID bazlı deduplication
    - Lock mekanizması
    - Timeout ile otomatik cleanup
    """
    
    def __init__(self):
        self._processing: Dict[str, datetime] = {}
        self._completed: Set[str] = set()
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def _cleanup_old_entries(self):
        """Eski entry'leri temizler (5 dakikadan eski)."""
        while True:
            try:
                await asyncio.sleep(60)  # Her dakika kontrol et
                
                async with self._lock:
                    now = datetime.utcnow()
                    timeout = timedelta(minutes=5)
                    
                    # Timeout olan processing'leri temizle
                    expired = [
                        msg_id for msg_id, start_time in self._processing.items()
                        if now - start_time > timeout
                    ]
                    
                    for msg_id in expired:
                        del self._processing[msg_id]
                        if msg_id in self._locks:
                            del self._locks[msg_id]
                        logger.warning(f"[STREAM_MEMORY] Timeout cleanup: {msg_id}")
                    
                    # Completed set'i sınırla (son 1000)
                    if len(self._completed) > 1000:
                        # En eski 500'ü temizle (set'te sıralama yok, hepsini temizle ve yeniden oluştur)
                        self._completed.clear()
                        
            except Exception as e:
                logger.error(f"[STREAM_MEMORY] Cleanup error: {e}")
    
    def start_cleanup_task(self):
        """Cleanup task'ı başlatır."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_old_entries())
    
    async def can_process_memory(self, message_id: str) -> bool:
        """
        Memory kaydının yapılıp yapılamayacağını kontrol eder.
        
        Args:
            message_id: Mesaj ID (conversation_id + timestamp kombinasyonu)
            
        Returns:
            bool: İşlenebilir ise True
        """
        async with self._lock:
            # Zaten tamamlanmış mı?
            if message_id in self._completed:
                logger.debug(f"[STREAM_MEMORY] Already completed: {message_id}")
                return False
            
            # Şu anda işleniyor mu?
            if message_id in self._processing:
                logger.debug(f"[STREAM_MEMORY] Already processing: {message_id}")
                return False
            
            # İşleme başla
            self._processing[message_id] = datetime.utcnow()
            
            # Lock oluştur
            if message_id not in self._locks:
                self._locks[message_id] = asyncio.Lock()
            
            return True
    
    async def mark_completed(self, message_id: str):
        """
        Memory kaydının tamamlandığını işaretle.
        
        Args:
            message_id: Mesaj ID
        """
        async with self._lock:
            if message_id in self._processing:
                del self._processing[message_id]
            
            self._completed.add(message_id)
            
            # Lock'u temizle
            if message_id in self._locks:
                del self._locks[message_id]
            
            logger.debug(f"[STREAM_MEMORY] Completed: {message_id}")
    
    async def get_lock(self, message_id: str) -> asyncio.Lock:
        """
        Message ID için lock döndürür.
        
        Args:
            message_id: Mesaj ID
            
        Returns:
            asyncio.Lock: Lock nesnesi
        """
        async with self._lock:
            if message_id not in self._locks:
                self._locks[message_id] = asyncio.Lock()
            return self._locks[message_id]
    
    def reset(self):
        """Tüm state'i temizler (test için)."""
        self._processing.clear()
        self._completed.clear()
        self._locks.clear()


# Global singleton
streaming_memory_manager = StreamingMemoryManager()

# Startup'ta cleanup task'ı başlat
streaming_memory_manager.start_cleanup_task()