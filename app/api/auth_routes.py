"""
Auth Routes - Kimlik doğrulama endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Request

from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["auth"])


@router.get("/me")
async def get_current_user_info(request: Request):
    """Oturum açmış kullanıcının bilgilerini döner."""
    from app.auth.dependencies import get_current_user

    try:
        user = await get_current_user(request)

        return {
            "id": str(user.id),
            "username": user.username,
            "displayName": user.username,
            "role": user.role,
            "preferences": {
                "theme": "warmDark",
                "language": "tr",
                "fontSize": "md",
                "reducedMotion": False,
                "soundEnabled": True,
                "notificationsEnabled": True,
                "activePersona": getattr(user, "active_persona", None),
            },
            "permissions": {
                "canUseInternet": user.permissions.get("can_use_internet", True),
                "canUseImage": True,
                "canUseLocalChat": True,
                "dailyInternetLimit": user.limits.get("daily_internet", 100),
                "dailyImageLimit": user.limits.get("daily_image", 50),
                "censorshipLevel": user.permissions.get("censorship_level", 0),
                "isBanned": user.is_banned,
            },
            "createdAt": user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None,
        }
    except HTTPException:
        # Oturum yoksa 401 döndür
        raise
