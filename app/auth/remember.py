"""
Mami AI - "Beni Hatırla" Token Yönetimi
=======================================

Bu modül, uzun süreli oturum (remember me) token'larını yönetir.

Özellikler:
    - 30 günlük token süresi (varsayılan)
    - Session tablosunda type="remember_token" olarak saklanır
    - Normal session'dan bağımsız çalışır

Kullanım:
    from app.auth.remember import create_remember_token, get_username_from_token
    
    # Token oluştur
    token = create_remember_token("john")
    response.set_cookie("mami_remember", token, max_age=30*24*3600)
    
    # Token'dan kullanıcı al
    username = get_username_from_token(token)

Güvenlik:
    - secrets.token_urlsafe(32) ile 256-bit entropi
    - Süre dolmuş tokenlar otomatik reddedilir
"""

from __future__ import annotations

import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import select

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# SABİTLER
# =============================================================================

REMEMBER_COOKIE_NAME = "mami_remember"
"""Cookie adı."""

REMEMBER_TTL_DAYS = 30
"""Token geçerlilik süresi (gün)."""


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    try:
        from app.core.database import get_session
        from app.core.models import Session
    except ImportError:
        from app.core.database import get_session
        from app.core.models import Session
    
    return get_session, Session


# =============================================================================
# TOKEN İŞLEMLERİ
# =============================================================================

def create_remember_token(username: str, days: int = REMEMBER_TTL_DAYS) -> str:
    """
    Remember me token'ı oluşturur.
    
    Args:
        username: Kullanıcı adı
        days: Token geçerlilik süresi (gün)
    
    Returns:
        str: Oluşturulan token
    
    Raises:
        ValueError: Kullanıcı bulunamazsa
    
    Example:
        >>> token = create_remember_token("john")
        >>> print(len(token))  # ~43 karakter
    """
    # Lazy import - döngüsel bağımlılığı önlemek için
    try:
        from app.auth.user_manager import get_user_by_username
    except ImportError:
        from app.auth.user_manager import get_user_by_username
    
    get_session, Session = _get_imports()
    
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"Kullanıcı bulunamadı: {username}")
    
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=days)
    
    with get_session() as session:
        remember_session = Session(
            id=token,
            user_id=user.id,
            type="remember_token",
            expires_at=expires,
            created_at=datetime.utcnow(),
        )
        session.add(remember_session)
        session.commit()
        
        logger.info(f"[REMEMBER] Token oluşturuldu: {username}")
        return token


def get_username_from_token(token: str) -> Optional[str]:
    """
    Token'dan kullanıcı adını döndürür.
    
    Args:
        token: Remember me token'ı
    
    Returns:
        str veya None: Geçerli token ise kullanıcı adı
    """
    if not token:
        return None
    
    get_session, Session = _get_imports()
    
    # Lazy import
    try:
        from app.auth.user_manager import get_user_by_id
    except ImportError:
        from app.auth.user_manager import get_user_by_id
    
    with get_session() as session:
        stmt = select(Session).where(
            Session.id == token,
            Session.type == "remember_token",
            Session.expires_at > datetime.utcnow()
        )
        session_obj = session.exec(stmt).first()
        
        if not session_obj:
            return None
        
        user = get_user_by_id(session_obj.user_id)
        return user.username if user else None


def invalidate_token(token: str) -> None:
    """
    Remember token'ı iptal eder.
    
    Args:
        token: İptal edilecek token
    """
    if not token:
        return
    
    get_session, Session = _get_imports()
    
    with get_session() as session:
        session_obj = session.get(Session, token)
        if session_obj:
            session.delete(session_obj)
            session.commit()
            logger.info("[REMEMBER] Token iptal edildi")


def cleanup_expired_tokens() -> int:
    """
    Süresi dolmuş remember token'ları temizler.
    
    Returns:
        int: Temizlenen token sayısı
    """
    get_session, Session = _get_imports()
    
    now = datetime.utcnow()
    removed = 0
    
    with get_session() as session:
        stmt = select(Session).where(
            Session.type == "remember_token",
            Session.expires_at <= now
        )
        expired = session.exec(stmt).all()
        
        for sess in expired:
            session.delete(sess)
            removed += 1
        
        if removed > 0:
            session.commit()
            logger.info(f"[REMEMBER] {removed} adet süresi dolmuş token temizlendi")
    
    return removed







