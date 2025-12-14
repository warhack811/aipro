"""
Celery Tasks - Async Image Generation
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Celery app
try:
    from celery import Celery

    from app.config import get_settings
    
    settings = get_settings()
    
    celery_app = Celery(
        'mami_async_image',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/1'
    )
    
    celery_app.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='Europe/Istanbul',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=600,  # 10 dakika max
        broker_connection_retry_on_startup=True,
    )
    
except ImportError:
    celery_app = None
    logger.warning("[ASYNC_IMAGE_TASKS] Celery not available")


if celery_app:
    @celery_app.task(bind=True, max_retries=2, name='async_image.generate')
    def generate_image_task(self, username: str, prompt: str, conversation_id: Optional[str] = None, user_id: Optional[int] = None):
        """
        Arka planda görsel üretir.
        
        Mevcut image_manager ve flux_stub'ı kullanır.
        """
        try:
            logger.info(f"[CELERY_TASK] Image generation started: {username} - {prompt[:50]}")
            
            # Mevcut image manager'ın flux_stub'ını kullan
            import asyncio
            import uuid
            from html import escape as html_escape

            from app.image.flux_stub import generate_image_via_forge
            from app.image.gpu_state import switch_to_flux, switch_to_gemma
            from app.image.job_queue import ImageJob
            from app.memory.conversation import append_message

            # GPU'yu Flux moduna geçir
            switch_to_flux()
            
            try:
                # Job objesi oluştur (progress tracking için)
                job_id = str(uuid.uuid4())
                image_result = None
                
                def on_done_callback(result):
                    nonlocal image_result
                    image_result = result
                
                job = ImageJob(
                    username=username,
                    prompt=prompt,
                    conversation_id=conversation_id,
                    on_done=on_done_callback,
                    job_id=job_id
                )
                
                # Async fonksiyonu senkron ortamda çalıştır
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Forge API çağrısı (30-60 saniye)
                    image_path = loop.run_until_complete(generate_image_via_forge(prompt, job))
                finally:
                    loop.close()
                
                if image_path.startswith("(IMAGE ERROR)"):
                    raise Exception(image_path)
                
                # Başarılı - Mesajı kaydet
                if conversation_id:
                    safe_prompt = html_escape(prompt, quote=True)
                    prompt_snippet = f'<span class="image-prompt" data-prompt="{safe_prompt}"></span>'
                    text = f"[IMAGE] Resminiz hazır.{prompt_snippet}\nIMAGE_PATH: {image_path}"
                    meta = {"engine": "image", "action": "IMAGE", "prompt": prompt, "async": True}
                    
                    append_message(
                        username=username,
                        conv_id=conversation_id,
                        role="bot",
                        text=text,
                        extra_metadata=meta
                    )
                
                # WebSocket bildirimi
                try:
                    import asyncio

                    from app.websocket_sender import send_to_user
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(send_to_user(username, {
                        "type": "image_complete",
                        "conversation_id": conversation_id,
                        "image_path": image_path
                    }))
                    loop.close()
                except Exception as ws_err:
                    logger.warning(f"[CELERY_TASK] WebSocket notification failed: {ws_err}")
                
                logger.info(f"[CELERY_TASK] Image generated successfully: {image_path}")
                return {"status": "success", "image_path": image_path}
                
            finally:
                # GPU'yu geri al
                switch_to_gemma()
            
        except Exception as exc:
            logger.error(f"[CELERY_TASK] Image generation error: {exc}")
            
            # Retry (2 kere daha dene)
            if self.request.retries < 2:
                logger.info(f"[CELERY_TASK] Retry {self.request.retries + 1}/2")
                raise self.retry(exc=exc, countdown=30)
            
            # Başarısız - Hata mesajı kaydet
            if conversation_id:
                from app.memory.conversation import append_message
                error_text = f"[IMAGE] Görsel oluşturulamadı: {str(exc)}"
                append_message(
                    username=username,
                    conv_id=conversation_id,
                    role="bot",
                    text=error_text
                )
            
            return {"status": "error", "error": str(exc)}