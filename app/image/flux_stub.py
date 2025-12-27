# image/flux_stub.py
from __future__ import annotations

import asyncio
import base64
import time
from pathlib import Path
from typing import Optional

import aiohttp
import requests

from app.config import get_settings
from app.core.exceptions import ImageGenerationError
from app.core.logger import get_logger
from app.image.circuit_breaker import forge_circuit_breaker
from app.image.gpu_state import switch_to_flux, switch_to_gemma
from app.image.pending_state import update_pending_job
from app.websocket_sender import ImageJobStatus, send_image_progress

logger = get_logger(__name__)
settings = get_settings()

IMAGES_ROOT = Path("data") / "images"
IMAGES_ROOT.mkdir(parents=True, exist_ok=True)

# Placeholder image paths
PLACEHOLDER_IMAGES = {
    "error": "/images/placeholders/error.png",
    "timeout": "/images/placeholders/timeout.png",
    "maintenance": "/images/placeholders/maintenance.png",
}


def _build_forge_url() -> str:
    base = settings.FORGE_BASE_URL.rstrip("/")
    path = settings.FORGE_TXT2IMG_PATH
    if not path.startswith("/"):
        path = "/" + path
    return base + path


async def get_progress() -> int:
    """Forge’un anlık ilerleme yüzdesini döndür (0-100)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.FORGE_BASE_URL}/sdapi/v1/progress",
                timeout=2,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return int(data.get("progress", 0) * 100)
    except Exception as e:
        logger.debug(f"[FLUX] Progress okuma hatası: {e}")
    return 0


async def generate_image_via_forge(prompt: str, job, checkpoint_name: Optional[str] = None) -> str:
    """
    Stable Diffusion WebUI Forge üzerinden resim üretir.
    Circuit breaker ve retry mekanizması ile korunmuştur.

    Args:
        prompt: Görsel üretim prompt'u
        job: ImageJob nesnesi
        checkpoint_name: Kullanılacak checkpoint (.safetensors dosya adı)
                        None ise config'ten alınır

    Returns:
        str: Image URL veya placeholder image path
    """
    # Circuit breaker kontrolü
    if not forge_circuit_breaker.can_attempt():
        logger.warning("[FLUX] Circuit OPEN - placeholder image döndürülüyor")
        return PLACEHOLDER_IMAGES["maintenance"]

    # Retry with exponential backoff (3 deneme)
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await _generate_image_internal(prompt, job, checkpoint_name)

            # Başarılı - circuit breaker'a bildir
            forge_circuit_breaker.record_success()
            return result

        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning(f"[FLUX] Attempt {attempt+1}/{max_retries} - Timeout")

            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2**attempt
                logger.info(f"[FLUX] {delay}s bekleyip tekrar deneniyor...")
                await asyncio.sleep(delay)
            else:
                # Son deneme de başarısız
                forge_circuit_breaker.record_failure(e)
                return PLACEHOLDER_IMAGES["timeout"]

        except Exception as e:
            last_error = e
            logger.error(f"[FLUX] Attempt {attempt+1}/{max_retries} - Error: {e}")

            if attempt < max_retries - 1:
                delay = 2**attempt
                await asyncio.sleep(delay)
            else:
                # Tüm denemeler başarısız
                forge_circuit_breaker.record_failure(e)
                return PLACEHOLDER_IMAGES["error"]

    # Buraya ulaşılmamalı ama güvenlik için
    return PLACEHOLDER_IMAGES["error"]


async def _generate_image_internal(prompt: str, job, checkpoint_name: Optional[str] = None) -> str:
    """
    Internal image generation (retry loop tarafından çağrılır).
    """
    url = _build_forge_url()

    # Checkpoint adını belirle
    final_checkpoint = checkpoint_name or settings.FORGE_FLUX_CHECKPOINT

    logger.info(f"[FLUX] Forge txt2img endpoint: {url}")
    logger.info(f"[FLUX] Model checkpoint: {final_checkpoint}")

    # NOT: Warm-up request kaldırıldı - GPU çakışmasına neden oluyordu
    # Model değişikliği override_settings ile ana request'te yapılıyor

    # 2) Asıl generation payload
    payload = {
        "prompt": prompt,
        "steps": 20,
        "width": 1024,
        "height": 1024,
        "cfg_scale": 1.0,
        "sampler_name": "Euler",
        "scheduler": "Simple",
        "distilled_cfg_scale": 3.5,
        "override_settings": {"sd_model_checkpoint": final_checkpoint},
    }

    # GPU'yu Flux için hazırla
    switch_to_flux()

    logger.info(f"[FLUX] txt2img isteği başlatılıyor – prompt: {prompt[:50]}...")

    # 3) Senkron requests.post'u ayrı bir thread'de çalıştır
    def _do_txt2img_sync():
        # BU FONKSİYON ASYNC DEĞİL – to_thread için özellikle normal def
        return requests.post(url, json=payload, timeout=settings.FORGE_TIMEOUT)

    # Arka planda gerçek isteği başlat
    gen_task = asyncio.create_task(asyncio.to_thread(_do_txt2img_sync))

    # 4) İstek çalışırken progress poll et
    try:
        # Mesaj güncelleme için import
        from app.memory.conversation import update_message

        # İlk başta minimum bir progress gönder (frontend barı görebilsin)
        job.progress = 1
        update_pending_job(job.job_id, progress=job.progress)

        # Sadece metadata güncelle - içerik [IMAGE_PENDING] olarak kalmalı
        # Frontend WebSocket'ten progress alıyor, mesaj içeriğini değiştirmeye gerek yok
        if job.message_id:
            update_message(
                job.message_id, None, {"status": "processing", "progress": job.progress}  # İçerik değişmesin
            )

        await send_image_progress(
            username=job.username,
            conversation_id=job.conversation_id,
            job_id=job.job_id,
            status=ImageJobStatus.PROCESSING,
            progress=job.progress,
            queue_position=job.queue_pos,
            prompt=prompt,
            message_id=job.message_id,
        )

        while not gen_task.done():
            current = await get_progress()
            if current <= 0 and job.progress < 10:
                current = job.progress  # geriye düşmesin

            job.progress = current
            update_pending_job(job.job_id, progress=job.progress)

            # Her 10%'te bir metadata güncelle (içerik değişmesin)
            if job.message_id and job.progress % 10 == 0:
                update_message(
                    job.message_id, None, {"status": "processing", "progress": job.progress}  # İçerik değişmesin
                )

            await send_image_progress(
                username=job.username,
                conversation_id=job.conversation_id,
                job_id=job.job_id,
                status=ImageJobStatus.PROCESSING,
                progress=job.progress,
                queue_position=job.queue_pos,
                prompt=prompt,
                message_id=job.message_id,
            )
            await asyncio.sleep(1)

        # 5) txt2img sonucunu al
        resp = await gen_task  # to_thread içindeki requests.post sonucu

        try:
            resp.raise_for_status()
        except requests.Timeout:
            raise ImageGenerationError(f"Forge isteği zaman aşımına uğradı ({settings.FORGE_TIMEOUT}s).")
        except Exception as e:
            logger.error(f"[FLUX] Forge HTTP hatası: {e}")
            raise ImageGenerationError(f"Forge HTTP hatası: {e}")

    except Exception:
        if not gen_task.done():
            gen_task.cancel()
        raise

    # 6) Yanıtı işle: JSON → base64 → PNG
    try:
        data = resp.json()
    except Exception as e:
        raise ImageGenerationError(f"Forge yanıtı JSON değil: {e}")

    images = data.get("images") or []
    if not images:
        raise ImageGenerationError("Forge yanıtında resim verisi boş.")

    b64_str = images[0]
    if b64_str.startswith("data:"):
        b64_str = b64_str.split(",", 1)[-1]

    try:
        img_bytes = base64.b64decode(b64_str)
    except Exception as e:
        raise ImageGenerationError(f"Base64 decode hatası: {e}")

    ts = int(time.time())
    filename = f"flux_{ts}.png"
    out_path = IMAGES_ROOT / filename

    try:
        with out_path.open("wb") as f:
            f.write(img_bytes)
    except Exception as e:
        raise ImageGenerationError(f"Dosya yazma hatası: {e}")

    logger.info(f"[FLUX] Resim kaydedildi: {out_path}")

    image_url = f"/images/{filename}"

    # 7) Son durumda progress %100 + path ile WS'e gönder
    try:
        update_pending_job(job.job_id, progress=100)
        await send_image_progress(
            username=job.username,
            conversation_id=job.conversation_id,
            job_id=job.job_id,
            status=ImageJobStatus.COMPLETE,
            progress=100,
            queue_position=job.queue_pos,
            prompt=prompt,
            image_url=image_url,
        )
    except Exception as e:
        logger.error(f"[FLUX] Final progress gönderilirken hata: {e}")

    return image_url
