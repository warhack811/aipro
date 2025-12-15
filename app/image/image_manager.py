from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    from app.core.models import User

from app.core.logger import get_logger
from app.image.flux_stub import generate_image_via_forge
from app.image.gpu_state import switch_to_flux, switch_to_gemma
from app.image.job_queue import ImageJob, job_queue
from app.image.pending_state import (
    list_pending_jobs_for_user,
    register_pending_job,
    remove_pending_job,
)
from app.websocket_sender import send_progress

logger = get_logger(__name__)

# Basit image kuyruğu istatistikleri (Admin paneli için)
_image_stats: Dict[str, Any] = {
    "total_jobs": 0,        
    "pending_jobs": 0,      
    "last_username": None,  
    "last_prompt": None,    
}


def _on_job_added(username: str, prompt: str) -> None:
    """Yeni iş eklendiğinde istatistikleri günceller."""
    _image_stats["total_jobs"] += 1
    _image_stats["pending_jobs"] += 1
    _image_stats["last_username"] = username
    # Prompt çok uzun olmasın
    _image_stats["last_prompt"] = (prompt[:120] + "…") if len(prompt) > 120 else prompt


def _on_job_finished(job_id: Optional[str] = None) -> None:
    """İş bittiğinde pending sayısını azaltır."""
    if _image_stats["pending_jobs"] > 0:
        _image_stats["pending_jobs"] -= 1
    if job_id:
        remove_pending_job(job_id)


def get_image_queue_stats() -> Dict[str, Any]:
    """Admin paneli için image kuyruğu istatistiklerini döndürür."""
    return dict(_image_stats)


def request_image_generation(
    username: str,
    prompt: str,
    message_id: int,  # Güncellenecek mesaj ID'si
    job_id: str,      # ← YENİ: Önceden oluşturulmuş job_id
    conversation_id: Optional[str] = None,
    user: Optional[Any] = None,
) -> Optional[str]:
    """
    Kullanicidan gelen resim istegini kuyruk sistemine gonderir.
    
    YENİ YAKLAŞIM:
        - message_id ZORUNLU - mesaj önceden oluşturulmuş olmalı
        - job_id ZORUNLU - processor.py'de önceden oluşturulmuş olmalı
        - İş tamamlandığında mesaj içeriği güncellenir
    
    Args:
        username: Kullanici adi
        prompt: Gorsel prompt'u
        message_id: Güncellenecek mesaj ID'si (veritabanında mevcut olmalı)
        job_id: Önceden oluşturulmuş job ID'si
        conversation_id: Sohbet ID'si
        user: User nesnesi (routing icin)
    
    Returns:
        job_id: Aynı job_id (başarılı ise) veya None (hata ise)
    """
    from html import escape as html_escape

    from app.image.routing import decide_image_job
    from app.memory.conversation import update_message
    from app.services.user_preferences import get_effective_preferences

    # Kullanıcı tercihlerini al
    style_prefs = {}
    if user and hasattr(user, 'id'):
        try:
            # Hem response style hem formatting preferences birleştir
            style_prefs = get_effective_preferences(user_id=user.id, category="style")
        except Exception as e:
            logger.warning(f"[IMAGE_MANAGER] Tercihler alınamadı: {e}")

    # ImageRouter ile routing karari al
    try:
        spec = decide_image_job(prompt, user, style_profile=style_prefs)
        
        # Blocked ise mesajı hata ile güncelle
        if spec.blocked:
            logger.warning(f"[IMAGE_MANAGER] Request blocked: {spec.block_reason}")
            update_message(message_id, f"❌ {spec.block_reason}", {"status": "error"})
            return None
        
        # Routing kararini logla
        logger.info(
            f"[IMAGE_MANAGER] Routing: variant={spec.variant.value}, "
            f"checkpoint={spec.checkpoint_name}, nsfw={spec.flags.get('nsfw_detected', False)}"
        )
        
    except Exception as e:
        logger.error(f"[IMAGE_MANAGER] Routing hatasi: {e}")
        from app.image.routing import CHECKPOINTS, FluxVariant
        spec = None
        checkpoint_name = CHECKPOINTS[FluxVariant.STANDARD]
    
    _on_job_added(username, prompt)

    # İş tamamlandığında mesajı güncelle
    def on_complete(result: str) -> None:
        _on_job_finished(job.job_id)
        
        try:
            if result.startswith("(IMAGE ERROR)"):
                # Hata durumu
                update_message(
                    message_id,
                    f"❌ Görsel üretilemedi: {result.replace('(IMAGE ERROR)', '').strip()}",
                    {"status": "error", "type": "image"}
                )
            else:
                # Başarılı - resim URL'i ile güncelle
                safe_prompt = html_escape(prompt, quote=True)
                prompt_snippet = f'<span class="image-prompt" data-prompt="{safe_prompt}"></span>'
                update_message(
                    message_id,
                    f"[IMAGE] Resminiz hazır.{prompt_snippet}\nIMAGE_PATH: {result}",
                    {"status": "complete", "type": "image", "image_url": result}
                )
            logger.info(f"[IMAGE_MANAGER] Mesaj güncellendi: {message_id}")
        except Exception as e:
            logger.error(f"[IMAGE_MANAGER] Mesaj güncelleme hatası: {e}")

    # Job oluştur (job_id processor.py'den geliyor, yeni oluşturma!)
    job = ImageJob(
        username,
        prompt,
        conversation_id,
        on_done=on_complete,
        job_id=job_id,  # ← processor.py'den gelen job_id kullanılıyor
        checkpoint_name=spec.checkpoint_name if spec else None,
        message_id=message_id,
    )
    
    queue_pos = job_queue.add_job(job)
    register_pending_job(job.job_id, username, conversation_id, queue_pos)
    
    # İlk durumu mesaja yaz - [IMAGE_PENDING] marker ZORUNLU (frontend buna bakıyor)
    estimated_seconds = queue_pos * 30
    update_message(
        message_id,
        f"[IMAGE_PENDING] Görsel isteğiniz kuyruğa alındı...",
        {
            "status": "queued", 
            "type": "image", 
            "job_id": job.job_id, 
            "queue_pos": queue_pos,
            "prompt": prompt[:200],  # Frontend'in göstermesi için
        }
    )
    
    # WebSocket ile progress gönder
    asyncio.create_task(send_progress(
        username,
        conversation_id,
        0,
        queue_pos,
        job_id=job.job_id,
        message_id=message_id,
    ))
    
    return job.job_id

    
async def generate_image_sync(username: str, prompt: str) -> str:
    """
    ASYNC görsel üretim (Çok nadiren kullanılır, genellikle test amaçlı).
    GPU state'i Flux'a çevirir, Forge'a istek gönderir ve Gemma'ya geri döner.
    """
    _on_job_added(username, prompt)
    
    # Geçici job nesnesi oluştur
    temp_job = ImageJob(
        username=username,
        prompt=prompt,
        conversation_id=None,
        on_done=lambda x: None,
    )
    
    try:
        switch_to_flux()
        image_url = await generate_image_via_forge(prompt, temp_job)
        
        if image_url.startswith("(IMAGE ERROR)"):
            return f"[IMAGE] {image_url}"
        
        return f"[IMAGE] Resminiz oluşturuldu.\nIMAGE_PATH: {image_url}"
    except Exception as e:
        logger.error(f"[IMAGE_MANAGER] generate_image_sync hata: {e}")
        return f"[IMAGE] Resim üretilirken bir hata oluştu: {e}"
    finally:
        try:
            switch_to_gemma()
        finally:
            _on_job_finished()
