"""
Async Image Plugin - Ana Sınıf
"""

import logging
from typing import Any, Callable, Optional

from app.plugins import BasePlugin

logger = logging.getLogger(__name__)


class AsyncImagePlugin(BasePlugin):
    """
    Celery ile asenkron görsel üretimi plugin'i.
    
    Mevcut image_manager.request_image_generation() fonksiyonunu
    override etmeden, alternatif bir yol sunar.
    """
    
    name = "async_image"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.celery_app = None
        self.has_celery = False
    
    def initialize(self) -> bool:
        """
        Plugin devre dışı - Celery/Redis karmaşıklığı yerine
        basit job_queue.py sistemi kullanılıyor.
        """
        logger.info("[ASYNC_IMAGE_PLUGIN] Plugin disabled - using job_queue fallback")
        return False
    
    def generate_async(
        self,
        username: str,
        prompt: str,
        conversation_id: Optional[str] = None,
        user: Optional[Any] = None,
    ) -> dict:
        """
        Asenkron görsel üretimi başlat.
        
        Args:
            username: Kullanıcı adı
            prompt: Görsel prompt'u
            conversation_id: Sohbet ID
            user: User nesnesi
        
        Returns:
            dict: {"status": "processing", "task_id": "..."}
        """
        if not self.is_enabled() or not self.has_celery:
            raise RuntimeError("Async Image plugin is not available")
        
        from app.plugins.async_image.tasks import generate_image_task
        
        user_id = user.id if user else None
        
        # Celery task başlat
        task = generate_image_task.delay(
            username=username,
            prompt=prompt,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        logger.info(f"[ASYNC_IMAGE_PLUGIN] Task started: {task.id}")
        
        return {
            "status": "processing",
            "task_id": str(task.id),
            "message": "Görsel arka planda oluşturuluyor..."
        }