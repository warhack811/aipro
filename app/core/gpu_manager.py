import asyncio
import logging
import time
from enum import Enum
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelState(str, Enum):
    GEMMA = "gemma"
    FLUX = "flux"
    UNKNOWN = "unknown"

class GPUManager:
    """
    Tekil (Singleton) GPU Kaynak Yöneticisi.
    Görevi: Chat ve Image servisleri arasındaki geçişi koordine etmek.
    Race Condition'ı önlemek için 'Async Lock' kullanır.
    """
    _instance = None
    _lock = asyncio.Lock()
    _current_state = ModelState.GEMMA
    _last_activity = time.time()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPUManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_state(cls) -> ModelState:
        return cls._current_state

    @classmethod
    async def request_gemma_access(cls):
        """
        Chat servisi tarafından çağrılır.
        Eğer GPU Flux modundaysa, Gemma'ya geçişi zorlar.
        """
        async with cls._lock:
            if cls._current_state == ModelState.GEMMA:
                cls._last_activity = time.time()
                return

            logger.warning("[GPU_WARDEN] Chat isteği geldi, Flux -> Gemma geçişi başlatılıyor...")
            
            # 1. Flux/Forge ile işimiz bitti mi? (Şimdilik sert geçiş yapıyoruz)
            # İleride buraya 'Kuyruk boş mu?' kontrolü eklenebilir.
            
            # 2. Gemma'yı Yükle (Ollama'ya boş istek atarak warm-up yap)
            try:
                # Basit bir keep-alive isteği
                await cls._trigger_ollama_load()
                cls._current_state = ModelState.GEMMA
                logger.info("[GPU_WARDEN] Geçiş tamamlandı: GEMMA modundayız.")
            except Exception as e:
                logger.error(f"[GPU_WARDEN] Gemma yüklenirken hata: {e}")
                # Hata olsa bile state'i güncellemeyi deneyelim
                cls._current_state = ModelState.GEMMA

    @classmethod
    async def request_flux_access(cls):
        """
        Image servisi tarafından çağrılır.
        Gemma'yı VRAM'den atar (unload) ve Flux moduna geçer.
        """
        async with cls._lock:
            if cls._current_state == ModelState.FLUX:
                return

            logger.warning("[GPU_WARDEN] Resim isteği geldi, Gemma -> Flux geçişi başlatılıyor...")
            
            # 1. Gemma'yı Unload Et
            await cls._unload_ollama()
            
            # 2. State güncelle
            cls._current_state = ModelState.FLUX
            logger.info("[GPU_WARDEN] Geçiş tamamlandı: FLUX modundayız.")

    @staticmethod
    async def _unload_ollama():
        """Ollama API'sine keep_alive=0 göndererek VRAM'i boşaltır."""
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {"model": settings.OLLAMA_GEMMA_MODEL, "keep_alive": 0}
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(url, json=payload)
            logger.info("[GPU_WARDEN] Ollama VRAM boşaltma sinyali gönderildi.")
        except Exception as e:
            logger.warning(f"[GPU_WARDEN] Ollama unload hatası (Ollama kapalı olabilir): {e}")

    @staticmethod
    async def _trigger_ollama_load():
        """Ollama'ya çok kısa bir istek atarak modeli VRAM'e yüklemesini sağlar."""
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        # Cevap üretmesine gerek yok, sadece yüklesin diye boş prompt
        payload = {"model": settings.OLLAMA_GEMMA_MODEL, "prompt": "", "keep_alive": "5m"} 
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=payload)
        except Exception:
            pass # Hata beklenir (boş prompt), önemli olan modelin yüklenmesi