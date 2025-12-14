"""
Mami AI - Kullanıcı İzin Yardımcıları
=====================================

Bu modül, kullanıcı izinlerini kontrol eden tek doğruluk kaynağı
fonksiyonları sağlar. Tüm izin kontrolleri bu fonksiyonlar üzerinden
yapılmalıdır.

Kullanım:
    from app.auth.permissions import (
        user_can_use_local,
        user_can_use_internet,
        user_can_use_image,
        get_censorship_level,
    )

    if user_can_use_local(user):
        # Yerel model kullanılabilir
        pass

Tasarım Kararları:
    - bela_unlocked ve can_use_local_chat birleştirildi
    - censorship_level varsayılan 1 (normal)
    - Tüm kontroller defensive programming ile yapılır
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from app.core.models import User

logger = logging.getLogger(__name__)


# =============================================================================
# SABİTLER
# =============================================================================

# Sansür seviyeleri
CENSORSHIP_UNRESTRICTED = 0  # Sansürsüz - her şeye izin
CENSORSHIP_NORMAL = 1        # Normal - varsayılan
CENSORSHIP_STRICT = 2        # Sıkı - NSFW yasak, otomatik local kapalı

# Varsayılan değerler
DEFAULT_CENSORSHIP_LEVEL = CENSORSHIP_NORMAL
DEFAULT_CAN_USE_INTERNET = True
DEFAULT_CAN_USE_IMAGE = True
DEFAULT_CAN_USE_LOCAL = False  # Güvenli varsayılan


# =============================================================================
# HELPER FONKSİYONLAR
# =============================================================================

def _get_permissions(user: Optional["User"]) -> Dict[str, Any]:
    """
    Kullanıcının permissions dict'ini güvenli şekilde döndürür.

    Args:
        user: User nesnesi

    Returns:
        Dict: permissions veya boş dict
    """
    if user is None:
        return {}

    perms = getattr(user, "permissions", None)
    if perms is None:
        return {}
    if not isinstance(perms, dict):
        return {}

    return perms


def _get_bool_permission(user: Optional["User"], key: str, default: bool) -> bool:
    """
    Boolean izin değerini güvenli şekilde okur.

    Args:
        user: User nesnesi
        key: İzin anahtarı
        default: Varsayılan değer

    Returns:
        bool: İzin değeri
    """
    perms = _get_permissions(user)
    value = perms.get(key)

    if value is None:
        return default

    # String "true"/"false" desteği
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")

    return bool(value)


# =============================================================================
# ANA İZİN FONKSİYONLARI
# =============================================================================

def user_can_use_local(user: Optional["User"]) -> bool:
    """
    Kullanıcının yerel model (Ollama/Qwen) kullanma iznini kontrol eder.

    Tek doğruluk kaynağı: bela_unlocked + permissions birleşik kontrol.

    Kontrol sırası:
    1. User None ise → False
    2. is_banned ise → False
    3. Admin ise → True
    4. bela_unlocked True ise → True
    5. permissions["can_use_local_chat"] True ise → True
    6. permissions["allow_local_model"] True ise → True
    7. Varsayılan → False

    Args:
        user: User nesnesi

    Returns:
        bool: Yerel model kullanabilir mi

    Example:
        >>> if user_can_use_local(user):
        ...     route_to_ollama()
    """
    if user is None:
        return False

    # Yasaklı kullanıcı hiçbir şey kullanamaz
    if getattr(user, "is_banned", False):
        return False

    # Admin kullanıcılar tam yetkiye sahip
    if getattr(user, "role", None) == "admin":
        return True

    # 1. bela_unlocked kontrolü (eski alan, hala destekleniyor)
    if getattr(user, "bela_unlocked", False):
        return True

    # 2. permissions kontrolü
    perms = _get_permissions(user)

    # can_use_local_chat veya allow_local_model
    if perms.get("can_use_local_chat") is True:
        return True
    if perms.get("allow_local_model") is True:
        return True

    return DEFAULT_CAN_USE_LOCAL


def user_can_use_internet(user: Optional["User"]) -> bool:
    """
    Kullanıcının internet araması yapma iznini kontrol eder.

    Args:
        user: User nesnesi

    Returns:
        bool: İnternet araması yapabilir mi
    """
    if user is None:
        return DEFAULT_CAN_USE_INTERNET

    if getattr(user, "is_banned", False):
        return False

    return _get_bool_permission(user, "can_use_internet", DEFAULT_CAN_USE_INTERNET)


def user_can_use_image(user: Optional["User"]) -> bool:
    """
    Kullanıcının görsel üretme iznini kontrol eder.

    Args:
        user: User nesnesi

    Returns:
        bool: Görsel üretebilir mi
    """
    if user is None:
        return DEFAULT_CAN_USE_IMAGE

    if getattr(user, "is_banned", False):
        return False

    # Admin kullanıcılar tam yetkiye sahip
    if getattr(user, "role", None) == "admin":
        return True

    return _get_bool_permission(user, "can_use_image", DEFAULT_CAN_USE_IMAGE)


def get_censorship_level(user: Optional["User"]) -> int:
    """
    Kullanıcının sansür seviyesini döndürür.

    Seviyeler:
        0 = UNRESTRICTED: Sansürsüz, her şeye izin
        1 = NORMAL: Varsayılan davranış
        2 = STRICT: Sıkı sansür, NSFW yasak, otomatik local kapalı

    Args:
        user: User nesnesi

    Returns:
        int: Sansür seviyesi (0, 1, veya 2)
    """
    if user is None:
        return DEFAULT_CENSORSHIP_LEVEL

    perms = _get_permissions(user)
    level = perms.get("censorship_level")

    if level is None:
        return DEFAULT_CENSORSHIP_LEVEL

    # String desteği
    if isinstance(level, str):
        try:
            level = int(level)
        except ValueError:
            return DEFAULT_CENSORSHIP_LEVEL

    # Geçerli aralıkta mı?
    if isinstance(level, int) and 0 <= level <= 2:
        return level

    return DEFAULT_CENSORSHIP_LEVEL


def is_censorship_strict(user: Optional["User"]) -> bool:
    """
    Sıkı sansür modunda mı kontrol eder.

    Args:
        user: User nesnesi

    Returns:
        bool: Sıkı sansür aktif mi
    """
    return get_censorship_level(user) == CENSORSHIP_STRICT


def is_censorship_unrestricted(user: Optional["User"]) -> bool:
    """
    Sansürsüz modda mı kontrol eder.

    Args:
        user: User nesnesi

    Returns:
        bool: Sansürsüz mod aktif mi
    """
    return get_censorship_level(user) == CENSORSHIP_UNRESTRICTED


# =============================================================================
# NSFW POLİCY
# =============================================================================

def can_generate_nsfw_image(user: Optional["User"]) -> bool:
    """
    Kullanıcının NSFW görsel üretebilme iznini kontrol eder.

    Kurallar:
        - Admin kullanıcılar için her zaman True (tam yetki)
        - can_use_image False ise → False
        - censorship_level == 2 (STRICT) ise → False
        - censorship_level == 0 (UNRESTRICTED) + can_use_image ise → True
        - censorship_level == 1 (NORMAL) → Sistem ayarına bağlı (varsayılan False)

    Args:
        user: User nesnesi

    Returns:
        bool: NSFW görsel üretebilir mi
    """
    if user is None:
        return False

    # Admin kullanıcılar tam yetkiye sahip
    if getattr(user, "role", None) == "admin":
        return user_can_use_image(user)

    if not user_can_use_image(user):
        return False

    level = get_censorship_level(user)

    if level == CENSORSHIP_STRICT:
        return False

    if level == CENSORSHIP_UNRESTRICTED:
        return True

    # NORMAL seviyede varsayılan olarak kapalı
    # İleride sistem ayarından okunabilir
    return False


def can_auto_route_to_local(user: Optional["User"]) -> bool:
    """
    Otomatik local routing yapılabilir mi kontrol eder.

    Sıkı sansür modunda otomatik local routing kapalıdır.
    Kullanıcı explicit olarak seçebilir ama sistem otomatik yönlendirmez.

    Args:
        user: User nesnesi

    Returns:
        bool: Otomatik local routing yapılabilir mi
    """
    if not user_can_use_local(user):
        return False

    # Sıkı sansür modunda otomatik routing kapalı
    if is_censorship_strict(user):
        return False

    return True


# =============================================================================
# ÖZET BİLGİ
# =============================================================================

def get_user_permission_summary(user: Optional["User"]) -> Dict[str, Any]:
    """
    Kullanıcının tüm izin bilgilerini özet olarak döndürür.

    Args:
        user: User nesnesi

    Returns:
        Dict: İzin özeti

    Example:
        >>> summary = get_user_permission_summary(user)
        >>> print(summary)
        {
            "can_use_local": True,
            "can_use_internet": True,
            "can_use_image": True,
            "censorship_level": 1,
            "can_generate_nsfw": False,
            "can_auto_route_local": True,
        }
    """
    return {
        "can_use_local": user_can_use_local(user),
        "can_use_internet": user_can_use_internet(user),
        "can_use_image": user_can_use_image(user),
        "censorship_level": get_censorship_level(user),
        "censorship_strict": is_censorship_strict(user),
        "censorship_unrestricted": is_censorship_unrestricted(user),
        "can_generate_nsfw": can_generate_nsfw_image(user),
        "can_auto_route_local": can_auto_route_to_local(user),
    }

