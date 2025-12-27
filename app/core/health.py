import time

from fastapi import APIRouter

from app.config import get_settings
from app.core.feature_flags import feature_enabled

router = APIRouter()


@router.get("/health")
async def health():
    """Basit sağlık endpoint'i."""
    settings = get_settings()
    now = time.time()

    return {
        "ok": True,
        "app": settings.APP_NAME,
        "env": "dev" if settings.DEBUG else "prod",
        "timestamp": now,
        "features": {
            "chat": feature_enabled("chat", True),
            "image_generation": feature_enabled("image_generation", True),
            "file_upload": feature_enabled("file_upload", True),
            "internet": feature_enabled("internet", True),
            "bela_mode": feature_enabled("bela_mode", True),
            "groq_enabled": feature_enabled("groq_enabled", True),
        },
    }
