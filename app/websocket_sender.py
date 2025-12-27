# websocket_sender.py
"""
WebSocket İletişim Modülü
=========================

Bu modül, gerçek zamanlı bildirimler için WebSocket mesajlarını yönetir.

Desteklenen Mesaj Tipleri:
    - image_progress: Görsel üretim ilerleme durumu
    - image_complete: Görsel üretim tamamlandı
    - image_error: Görsel üretim hatası
    - notification: Genel bildirimler
"""

import logging
from enum import Enum
from typing import Any, Dict, Literal, Optional

logger = logging.getLogger(__name__)

# WebSocket bağlantıları: {ws: username} mapping
connected: Dict[Any, str] = {}


class ImageJobStatus(str, Enum):
    """Görsel üretim iş durumları."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


async def send_image_progress(
    username: str,
    conversation_id: Optional[str],
    job_id: str,
    status: ImageJobStatus,
    progress: int = 0,
    queue_position: int = 1,
    prompt: Optional[str] = None,
    image_url: Optional[str] = None,
    error: Optional[str] = None,
    estimated_seconds: Optional[int] = None,
    message_id: Optional[int] = None,
) -> int:
    """
    Görsel üretim ilerlemesini WebSocket üzerinden gönderir.

    Args:
        username: Kullanıcı adı
        conversation_id: Sohbet ID'si
        job_id: İş ID'si (benzersiz)
        status: İş durumu (queued, processing, complete, error)
        progress: İlerleme yüzdesi (0-100)
        queue_position: Kuyruk pozisyonu
        prompt: Görsel prompt'u (kısa versiyon)
        image_url: Tamamlanmış görsel URL'i
        error: Hata mesajı (error durumunda)
        estimated_seconds: Tahmini kalan süre (saniye)

    Returns:
        int: Gönderilen istemci sayısı
    """
    # Payload oluştur
    payload: Dict[str, Any] = {
        "type": "image_progress",
        "job_id": job_id,
        "conversation_id": conversation_id,
        "status": status.value,
        "progress": min(max(progress, 0), 100),
        "queue_position": queue_position,
        "username": username,
    }

    # Message ID (frontend mesaj güncelleme için)
    if message_id is not None:
        payload["message_id"] = message_id

    # Opsiyonel alanlar
    if prompt:
        # Prompt'u kısalt (max 100 karakter)
        payload["prompt"] = prompt[:100] + "..." if len(prompt) > 100 else prompt

    if image_url:
        payload["image_url"] = image_url

    if error:
        payload["error"] = error

    if estimated_seconds is not None:
        payload["estimated_seconds"] = estimated_seconds

    # Tüm bağlı kullanıcılara gönder
    sent_count = 0
    for ws in list(connected.keys()):
        try:
            await ws.send_json(payload)
            sent_count += 1
        except Exception as e:
            logger.debug(f"[WS_SENDER] Failed to send: {e}")

    # Loglama
    log_msg = f"[WS_SENDER] Job {job_id[:8]} | {status.value} | {progress}%"
    if sent_count > 0:
        logger.info(f"{log_msg} → {sent_count} clients")
    else:
        logger.warning(f"{log_msg} → No clients connected!")

    return sent_count


# ═══════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY - Eski fonksiyon (deprecated)
# ═══════════════════════════════════════════════════════════════════════════


async def send_progress(
    username: str,
    conv_id: Optional[str],
    prog: int,
    pos: int,
    path: Optional[str] = None,
    job_id: Optional[str] = None,
    prompt: Optional[str] = None,
    message_id: Optional[int] = None,
) -> None:
    """
    DEPRECATED: Eski format için backward compatibility.
    Yeni kod send_image_progress() kullanmalı.
    """
    # Durumu belirle
    if path is not None:
        status = ImageJobStatus.COMPLETE
    elif prog > 0:
        status = ImageJobStatus.PROCESSING
    else:
        status = ImageJobStatus.QUEUED

    await send_image_progress(
        username=username,
        conversation_id=conv_id,
        job_id=job_id or "unknown",
        status=status,
        progress=prog,
        queue_position=pos,
        prompt=prompt,
        image_url=path,
        message_id=message_id,
    )


# ═══════════════════════════════════════════════════════════════════════════
# GENEL BİLDİRİMLER
# ═══════════════════════════════════════════════════════════════════════════


async def send_to_user(username: str, message: Dict[str, Any]) -> int:
    """
    Belirli bir kullanıcıya WebSocket mesajı gönderir.

    Args:
        username: Hedef kullanıcı adı
        message: Gönderilecek JSON mesajı

    Returns:
        int: Gönderilen mesaj sayısı
    """
    sent_count = 0
    for ws, ws_username in list(connected.items()):
        if ws_username == username:
            try:
                await ws.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.debug(f"[WS] Failed to send message to user: {e}")

    return sent_count


async def send_notification(
    username: str,
    title: str,
    message: str,
    notification_type: Literal["info", "success", "warning", "error"] = "info",
) -> int:
    """
    Kullanıcıya bildirim gönderir.

    Args:
        username: Hedef kullanıcı adı
        title: Bildirim başlığı
        message: Bildirim mesajı
        notification_type: Bildirim tipi

    Returns:
        int: Gönderilen mesaj sayısı
    """
    payload = {
        "type": "notification",
        "data": {
            "type": notification_type,
            "title": title,
            "message": message,
        },
    }

    return await send_to_user(username, payload)


async def broadcast(message: Dict[str, Any]) -> int:
    """
    Tüm bağlı kullanıcılara mesaj gönderir.

    Args:
        message: Gönderilecek JSON mesajı

    Returns:
        int: Gönderilen mesaj sayısı
    """
    sent_count = 0
    for ws in list(connected.keys()):
        try:
            await ws.send_json(message)
            sent_count += 1
        except Exception as e:
            logger.debug(f"[WS] Failed to broadcast: {e}")

    return sent_count
