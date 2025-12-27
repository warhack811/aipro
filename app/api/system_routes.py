from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.core.feature_flags import feature_enabled, set_feature_flag
from app.core.health import router as health_router  # Health check endpoint'i
from app.image.gpu_state import get_state as get_gpu_state
from app.image.image_manager import get_image_queue_stats

# Admin tarafındaki sistem / proje sağlığı endpoint'leri için router.
router = APIRouter(tags=["system"])

# /health endpoint'ini buraya da bağlıyoruz: /api/system/health
router.include_router(health_router)


class FeatureToggleRequest(BaseModel):
    """Admin panelinden bir özelliği açıp kapatma isteği için şema."""

    key: str
    enabled: bool


@router.get("/features")
async def list_features():
    """Önemli feature flag'lerin mevcut durumunu döner."""
    keys = [
        "chat",
        "image_generation",
        "file_upload",
        "internet",
        "bela_mode",
        "groq_enabled",
    ]
    return {"features": {k: feature_enabled(k, True) for k in keys}}


@router.post("/features/toggle")
async def toggle_feature(body: FeatureToggleRequest):
    """Tek bir feature flag'i açar veya kapatır."""
    set_feature_flag(body.key, body.enabled)
    return {
        "ok": True,
        "key": body.key,
        "enabled": feature_enabled(body.key),
    }


@router.get("/overview")
async def system_overview():
    """Admin proje sağlığı ekranı için genel sistem durumunu döner."""
    settings = get_settings()

    # GPU durumu (Gemma / Flux)
    gpu_state = get_gpu_state()

    # Image kuyruğu istatistikleri
    queue_stats = get_image_queue_stats()

    # Önemli feature'ların durumu
    feature_keys = [
        "chat",
        "image_generation",
        "file_upload",
        "internet",
        "bela_mode",
        "groq_enabled",
    ]
    features = {k: feature_enabled(k, True) for k in feature_keys}

    return {
        "ok": True,
        "app": settings.APP_NAME,
        "env": "dev" if settings.DEBUG else "prod",
        "host": settings.API_HOST,
        "port": settings.API_PORT,
        "gpu_state": str(gpu_state.value) if hasattr(gpu_state, "value") else str(gpu_state),
        "image_queue": queue_stats,
        "features": features,
    }
