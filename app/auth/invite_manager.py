"""
Mami AI - Davet Kodu Yönetimi
=============================

Bu modül, yeni kullanıcı kaydı için davet kodu sistemini yönetir.

Kullanım:
    from app.auth.invite_manager import generate_invite, find_valid_invite

    # Yeni davet kodu oluştur
    invite = generate_invite(created_by="admin")
    print(invite.code)  # "A1B2C3D4E5"

    # Kodu doğrula
    valid = find_valid_invite("A1B2C3D4E5")
    if valid:
        mark_invite_used("A1B2C3D4E5", username="newuser")

Kod Formatı:
    - 10 karakter hex string (uppercase)
    - Örnek: "A1B2C3D4E5"
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime
from typing import List, Optional

from sqlmodel import select

# Modül logger'ı
logger = logging.getLogger(__name__)


# =============================================================================
# LAZY IMPORTS
# =============================================================================


def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    try:
        from app.core.database import get_session
        from app.core.models import Invite
    except ImportError:
        from app.core.database import get_session
        from app.core.models import Invite

    return get_session, Invite


# =============================================================================
# DAVET KODU İŞLEMLERİ
# =============================================================================


def generate_invite(created_by: str = "system"):
    """
    Yeni davet kodu üretir.

    Args:
        created_by: Kodu oluşturan kullanıcı adı

    Returns:
        Invite: Oluşturulan davet kaydı

    Example:
        >>> invite = generate_invite("admin")
        >>> print(invite.code)
        "A1B2C3D4E5"
    """
    get_session, Invite = _get_imports()

    code = secrets.token_hex(5).upper()  # 10 karakter hex

    with get_session() as session:
        invite = Invite(
            code=code,
            created_by=created_by,
            is_used=False,
            created_at=datetime.utcnow(),
        )
        session.add(invite)
        session.commit()
        session.refresh(invite)

        logger.info(f"[INVITE] Yeni davet kodu oluşturuldu: {code}")
        return invite


def find_valid_invite(code: str):
    """
    Kullanılmamış davet kodunu bulur.

    Args:
        code: Kontrol edilecek davet kodu

    Returns:
        Invite veya None: Geçerli ve kullanılmamış kod varsa
    """
    get_session, Invite = _get_imports()

    with get_session() as session:
        return session.exec(select(Invite).where(Invite.code == code.upper(), Invite.is_used == False)).first()


def mark_invite_used(code: str, username: str) -> None:
    """
    Davet kodunu kullanılmış olarak işaretler.

    Args:
        code: Kullanılan davet kodu
        username: Kodu kullanan kullanıcı adı
    """
    get_session, Invite = _get_imports()

    with get_session() as session:
        invite = session.exec(select(Invite).where(Invite.code == code.upper())).first()

        if invite:
            invite.is_used = True
            invite.used_at = datetime.utcnow()
            invite.used_by = username
            session.add(invite)
            session.commit()

            logger.info(f"[INVITE] Kod kullanıldı: {code} -> {username}")


def list_invites() -> List:
    """
    Tüm davet kodlarını listeler.

    Returns:
        List[Invite]: Davet kodları listesi
    """
    get_session, Invite = _get_imports()

    with get_session() as session:
        return list(session.exec(select(Invite)).all())


def delete_invite(code: str) -> bool:
    """
    Davet kodunu siler.

    Args:
        code: Silinecek davet kodu

    Returns:
        bool: Silme başarılı ise True
    """
    get_session, Invite = _get_imports()

    with get_session() as session:
        invite = session.exec(select(Invite).where(Invite.code == code.upper())).first()

        if not invite:
            return False

        session.delete(invite)
        session.commit()

        logger.info(f"[INVITE] Kod silindi: {code}")
        return True


def ensure_initial_invite():
    """
    Sistemde en az bir davet kodu olmasını garanti eder.

    İlk kurulumda otomatik olarak bir kod oluşturur.

    Returns:
        Invite: Mevcut veya yeni oluşturulan davet kodu
    """
    get_session, Invite = _get_imports()

    with get_session() as session:
        existing = session.exec(select(Invite)).first()
        if existing:
            return existing

    return generate_invite("system")
