"""
Mami AI - FastAPI Auth Dependencies
===================================

Bu modül, route'larda kullanılacak kimlik doğrulama dependency'lerini tanımlar.

Kullanım:
    from app.auth.dependencies import get_current_user, get_current_admin_user

    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_active_user)):
        return {"message": f"Merhaba {user.username}"}

    @router.get("/admin-only")
    async def admin_route(user: User = Depends(get_current_admin_user)):
        return {"message": "Admin paneli"}

Dependency Zinciri:
    get_current_user
        └── get_current_active_user (ban kontrolü)
                └── get_current_admin_user (rol kontrolü)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import Depends, HTTPException, Request, status

if TYPE_CHECKING:
    from app.core.models import User

# =============================================================================
# SABİTLER
# =============================================================================

SESSION_COOKIE_NAME = "session_token"
"""Cookie'de saklanan oturum token'ı için anahtar adı."""


# =============================================================================
# LAZY IMPORTS
# =============================================================================


def _get_imports():
    """
    Import döngüsünü önlemek için lazy import.

    Bu fonksiyon ilk çağrıda gerekli modülleri import eder.
    """
    try:
        from app.auth import session as session_service
        from app.auth.user_manager import get_user_by_username
        from app.config import get_settings
        from app.core.logger import get_logger
        from app.core.models import User
    except ImportError:
        # Eski import yolu (geçiş dönemi)
        from app.auth.user_manager import get_user_by_username
        from app.config import get_settings
        from app.core.logger import get_logger
        from app.core.models import User
        from auth import session as session_service

    return get_logger, User, get_settings, session_service, get_user_by_username


# =============================================================================
# DEPENDENCY FONKSİYONLARI
# =============================================================================


async def get_current_user(request: Request) -> "User":
    """
    İstekten oturum açmış kullanıcıyı getirir.

    İşlem Adımları:
    1. DEBUG modunda: Otomatik admin erişimi sağlar (geliştirme kolaylığı)
    2. Production'da: Session token kontrolü yapar

    Args:
        request: FastAPI Request nesnesi

    Returns:
        User: Oturum açmış kullanıcı

    Raises:
        HTTPException 401: Oturum token'ı yoksa veya geçersizse

    Note:
        DEBUG=True durumunda login gerektirmez.
    """
    get_logger, User, get_settings, session_service, get_user_by_username = _get_imports()

    logger = get_logger(__name__)
    settings = get_settings()

    # --- DEBUG MODU BYPASS ---
    # Geliştirme sırasında login olmadan test için
    if settings.DEBUG:
        # 1. Önce DB'den gerçek admin'i dene
        try:
            admin_user = get_user_by_username("admin")
            if admin_user:
                return admin_user
        except Exception:
            pass

        # 2. DB'de yoksa sanal admin döndür
        logger.warning("[AUTH] Debug modu aktif: Sanal Admin ile giriş yapılıyor.")
        return User(
            id=1,
            username="admin",
            role="admin",
            password_hash="dummy",
            is_banned=False,
            limits={"daily_internet": 1000, "daily_image": 1000},
            permissions={"can_use_internet": True, "censorship_level": 0},
        )
    # --- DEBUG MODU SONU ---

    # Production: Session token kontrolü
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Oturum açmanız gerekiyor.")

    # Token ile kullanıcıyı getir
    user = session_service.get_user_from_session_token(token)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Oturum geçersiz veya süresi dolmuş.")

    # Session süresini uzat (keep-alive)
    session_service.touch_session(token)

    return user


async def get_current_active_user(current_user: "User" = Depends(get_current_user)) -> "User":
    """
    Aktif (banlı olmayan) kullanıcıyı getirir.

    Args:
        current_user: get_current_user dependency'sinden gelen kullanıcı

    Returns:
        User: Aktif kullanıcı

    Raises:
        HTTPException 403: Kullanıcı banlıysa
    """
    get_logger, _, _, _, _ = _get_imports()
    logger = get_logger(__name__)

    if current_user.is_banned:
        logger.warning(f"[AUTH] Banlı kullanıcı erişim denemesi: {current_user.username}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hesabınız erişime kapatılmıştır.")

    return current_user


async def get_current_admin_user(current_user: "User" = Depends(get_current_active_user)) -> "User":
    """
    Admin rolündeki kullanıcıyı getirir.

    Args:
        current_user: get_current_active_user dependency'sinden gelen kullanıcı

    Returns:
        User: Admin kullanıcı

    Raises:
        HTTPException 403: Kullanıcı admin değilse
    """
    get_logger, _, _, _, _ = _get_imports()
    logger = get_logger(__name__)

    if current_user.role != "admin":
        logger.warning(f"[AUTH] Yetkisiz admin paneli erişimi: {current_user.username}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem için yönetici yetkisi gerekiyor.")

    return current_user


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================


def get_optional_user(request: Request) -> Optional["User"]:
    """
    Opsiyonel kullanıcı bilgisi - hata fırlatmaz.

    Oturum açılmışsa kullanıcıyı döndürür, açılmamışsa None.
    Public endpoint'lerde kullanıcı bilgisi gerektiğinde kullanılır.

    Args:
        request: FastAPI Request nesnesi

    Returns:
        User veya None: Oturum açıksa kullanıcı, değilse None
    """
    _, _, _, session_service, _ = _get_imports()

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    return session_service.get_user_from_session_token(token)
