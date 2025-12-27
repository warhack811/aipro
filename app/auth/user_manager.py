"""
Mami AI - Kullanıcı Yönetimi
============================

Bu modül, kullanıcı CRUD işlemlerini ve şifre yönetimini sağlar.

Özellikler:
    - Argon2 şifreleme (en güvenli standart)
    - Kullanıcı oluşturma, güncelleme, silme
    - Rol ve izin yönetimi
    - Varsayılan admin oluşturma

Güvenlik:
    - Şifreler Argon2 ile hash'lenir (bcrypt'ten daha güvenli)
    - Plain text şifreler asla saklanmaz
    - Limitsiz şifre uzunluğu desteği

Kullanım:
    from app.auth.user_manager import create_user, verify_password

    # Kullanıcı oluştur
    user = create_user("john", "securepassword123", role="user")

    # Şifre doğrula
    if verify_password(user, "securepassword123"):
        print("Giriş başarılı")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext
from sqlmodel import func, select

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# ŞİFRELEME YAPILANDIRMASI
# =============================================================================

# Argon2 - 2023 OWASP tarafından önerilen en güvenli şifreleme algoritması
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# =============================================================================
# LAZY IMPORTS
# =============================================================================


def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    try:
        from app.config import get_settings
        from app.core.database import get_session
        from app.core.models import User
    except ImportError:
        from app.config import get_settings
        from app.core.database import get_session
        from app.core.models import User

    return get_session, User, get_settings


# =============================================================================
# ŞİFRE İŞLEMLERİ
# =============================================================================


def _hash_password(password: str) -> str:
    """
    Şifreyi Argon2 ile hash'ler.

    Args:
        password: Plain text şifre

    Returns:
        str: Hash'lenmiş şifre
    """
    return pwd_context.hash(password)


def verify_password(user, password: str) -> bool:
    """
    Kullanıcı şifresini doğrular.

    Args:
        user: User nesnesi
        password: Kontrol edilecek plain text şifre

    Returns:
        bool: Şifre doğruysa True
    """
    if not user or not user.password_hash:
        return False
    return pwd_context.verify(password, user.password_hash)


# =============================================================================
# KULLANICI CRUD İŞLEMLERİ
# =============================================================================


def create_user(
    username: str,
    password: str,
    role: str = "user",
    limits: Optional[Dict[str, Any]] = None,
    permissions: Optional[Dict[str, Any]] = None,
):
    """
    Yeni kullanıcı oluşturur.

    Args:
        username: Kullanıcı adı (benzersiz olmalı)
        password: Plain text şifre (hash'lenerek saklanacak)
        role: Kullanıcı rolü (user, admin, vip)
        limits: Kullanım limitleri (opsiyonel)
        permissions: İzinler (opsiyonel)

    Returns:
        User: Oluşturulan kullanıcı

    Raises:
        ValueError: Kullanıcı adı boşsa veya zaten mevcutsa

    Example:
        >>> user = create_user("john", "pass123", role="user")
        >>> print(user.id)
        1
    """
    get_session, User, _ = _get_imports()

    if not username or not password:
        raise ValueError("Kullanıcı adı ve şifre boş olamaz.")

    # Varsayılan limitler
    if limits is None:
        limits = {"daily_internet": 50, "daily_image": 20}

    # Varsayılan izinler
    if permissions is None:
        permissions = {"can_use_internet": True, "censorship_level": 1}

    with get_session() as session:
        # Kullanıcı adı kontrolü
        existing_user = session.exec(select(User).where(User.username == username)).first()

        if existing_user:
            raise ValueError(f"Bu kullanıcı adı zaten alınmış: {username}")

        new_user = User(
            username=username,
            password_hash=_hash_password(password),
            role=role,
            is_banned=False,
            limits=limits,
            permissions=permissions,
        )

        try:
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            logger.info(f"[USER] Yeni kullanıcı oluşturuldu: {username}")
            return new_user
        except Exception as e:
            session.rollback()
            logger.error(f"[USER] Kullanıcı oluşturma hatası: {e}")
            raise


def get_user_by_username(username: str):
    """
    Kullanıcı adına göre kullanıcıyı bulur.

    Args:
        username: Aranacak kullanıcı adı

    Returns:
        User veya None
    """
    if not username:
        return None

    get_session, User, _ = _get_imports()

    with get_session() as session:
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()


def get_user_by_id(user_id: int):
    """
    ID'ye göre kullanıcıyı bulur.

    Args:
        user_id: Kullanıcı ID'si

    Returns:
        User veya None
    """
    get_session, User, _ = _get_imports()

    with get_session() as session:
        return session.get(User, user_id)


def list_users(limit: int = 100, offset: int = 0) -> List:
    """
    Kullanıcıları listeler.

    Args:
        limit: Maksimum kayıt sayısı
        offset: Başlangıç noktası (sayfalama için)

    Returns:
        List[User]: Kullanıcı listesi
    """
    get_session, User, _ = _get_imports()

    with get_session() as session:
        statement = select(User).offset(offset).limit(limit)
        return list(session.exec(statement).all())


def update_user(
    username: str,
    role: Optional[str] = None,
    censorship_level: Optional[int] = None,
    can_use_internet: Optional[bool] = None,
    can_use_image: Optional[bool] = None,
    can_use_local_chat: Optional[bool] = None,
    is_banned: Optional[bool] = None,
    daily_internet_limit: Optional[int] = None,
    daily_image_limit: Optional[int] = None,
):
    """
    Kullanıcı bilgilerini günceller.

    Args:
        username: Güncellenecek kullanıcı adı
        role: Yeni rol (opsiyonel)
        censorship_level: Sansür seviyesi (opsiyonel)
        can_use_internet: İnternet kullanım izni (opsiyonel)
        can_use_image: Görsel üretim izni (opsiyonel)
        can_use_local_chat: Yerel model izni (opsiyonel)
        is_banned: Ban durumu (opsiyonel)
        daily_internet_limit: Günlük internet limiti (opsiyonel)
        daily_image_limit: Günlük görsel limiti (opsiyonel)

    Returns:
        User veya None: Güncellenen kullanıcı
    """
    get_session, User, _ = _get_imports()

    with get_session() as session:
        user = session.exec(select(User).where(User.username == username)).first()

        if not user:
            return None

        # Temel alanları güncelle
        if role is not None:
            user.role = role
        if is_banned is not None:
            user.is_banned = is_banned

        # JSON alanlarını güncelle
        new_permissions = dict(user.permissions) if user.permissions else {}
        new_limits = dict(user.limits) if user.limits else {}

        if censorship_level is not None:
            new_permissions["censorship_level"] = censorship_level
        if can_use_internet is not None:
            new_permissions["can_use_internet"] = can_use_internet
        if can_use_image is not None:
            new_permissions["can_use_image"] = can_use_image
        if can_use_local_chat is not None:
            new_permissions["can_use_local_chat"] = can_use_local_chat
            new_permissions["allow_local_model"] = can_use_local_chat

        if daily_internet_limit is not None:
            new_limits["daily_internet"] = daily_internet_limit
        if daily_image_limit is not None:
            new_limits["daily_image"] = daily_image_limit

        user.permissions = new_permissions
        user.limits = new_limits

        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"[USER] Kullanıcı güncellendi: {username}")
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"[USER] Güncelleme hatası: {e}")
            return None


def get_user_limits_and_permissions(user) -> Dict[str, Any]:
    """
    Kullanıcının limit ve izinlerini döndürür.

    Args:
        user: User nesnesi

    Returns:
        Dict: limits, permissions, role ve ban durumu
    """
    limits = user.limits if isinstance(user.limits, dict) else {}
    permissions = user.permissions if isinstance(user.permissions, dict) else {}

    return {"limits": limits, "permissions": permissions, "role": user.role, "is_banned": user.is_banned}


# =============================================================================
# SİSTEM FONKSİYONLARI
# =============================================================================


def ensure_default_admin():
    """
    Sistemde hiç kullanıcı yoksa varsayılan admin oluşturur.

    DİKKAT: Bu fonksiyon sadece ilk kurulum için kullanılmalıdır.
    Production'da admin şifresini mutlaka değiştirin!

    Returns:
        User veya None: Oluşturulan admin kullanıcı
    """
    get_session, User, _ = _get_imports()

    # Hardcoded admin bilgileri (sadece ilk kurulum için)
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"

    with get_session() as session:
        # Kullanıcı sayısını kontrol et
        user_count = session.exec(select(func.count()).select_from(User)).one()

        if user_count == 0:
            logger.critical("[ADMIN_BOOTSTRAP] Kullanıcı tablosu boş. " "Varsayılan Admin oluşturuluyor...")

            try:
                admin_user = create_user(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, role="admin")
                logger.critical(
                    f"✅ ADMIN OLUŞTURULDU: "
                    f"Kullanıcı Adı: {ADMIN_USERNAME} | Şifre: {ADMIN_PASSWORD} "
                    f"(Bu hesabı hemen değiştirin!)"
                )
                return admin_user
            except Exception as e:
                logger.error(f"[ADMIN_BOOTSTRAP] Admin oluşturma hatası: {e}")
                return None

        return None
