from __future__ import annotations

import time
from enum import Enum

import requests

from app.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ModelState(str, Enum):
    GEMMA = "gemma"
    FLUX = "flux"


current_state = ModelState.GEMMA


def _unload_ollama():
    """Ollama'ya yüklü modeli VRAM'den boşaltması için sinyal gönderir (keep_alive=0)."""
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {"model": settings.OLLAMA_GEMMA_MODEL, "keep_alive": 0}
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            logger.info("[GPU_STATE] Ollama (Gemma) VRAM'den boşaltıldı.")
        else:
            logger.warning(f"[GPU_STATE] Ollama unload başarısız: {resp.status_code}")
    except Exception as e:
        logger.error(f"[GPU_STATE] Ollama bağlantı hatası: {e}")


def switch_to_flux():
    """Görsel üretimine geçmeden önce Chat modelini (Gemma) VRAM'den atar."""
    global current_state
    if current_state != ModelState.FLUX:
        logger.info("[GPU_STATE] Flux moduna geçiliyor... Gemma VRAM'den atılıyor.")
        _unload_ollama()
        time.sleep(2)  # Ollama'nın VRAM'i boşaltması için kısa bir bekleme
        current_state = ModelState.FLUX


def switch_to_gemma():
    """Sistemi sohbet (Gemma) moduna geri döndürür (state güncellenir)."""
    global current_state
    if current_state != ModelState.GEMMA:
        logger.info("[GPU_STATE] Gemma moduna (Chat) geri dönüldü.")
        current_state = ModelState.GEMMA


def get_state() -> ModelState:
    """GPU'nun anlık hangi model tarafından kullanıldığını döndürür."""
    return current_state
