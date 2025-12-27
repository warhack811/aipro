from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

# Servisler
from app.auth import invite_manager
from app.auth import remember as remember_manager  # Beni Hatırla servisi
from app.auth import session as session_service
from app.auth import user_manager
from app.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["public"])

# Sabitler
SESSION_COOKIE_NAME = "session_token"
SESSION_MAX_AGE_LONG = 30 * 24 * 60 * 60  # 30 gün (Remember Me)
SESSION_MAX_AGE_SHORT = 24 * 60 * 60  # 1 gün (Standart)

# --- ŞEMALAR ---


class RegisterRequest(BaseModel):
    invite_code: str = Field(..., min_length=3, description="Sisteme kayıt için zorunlu davet kodu")
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=5, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=5, max_length=128)
    remember_me: bool = Field(default=False)


# --- ENDPOINTS ---


@router.get("/ping")
async def ping():
    """Sistem ayakta mı kontrolü."""
    return {"message": "pong", "system": "active"}


@router.post("/register_with_invite", status_code=status.HTTP_201_CREATED)
async def register_with_invite(payload: RegisterRequest):
    """Davet kodu ile yeni kullanıcı oluşturur."""
    # 1. Davet Kodu Kontrolü
    invite = invite_manager.find_valid_invite(payload.invite_code)
    if not invite:
        logger.warning(f"[AUTH] Geçersiz davet kodu denemesi: {payload.invite_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu davet kodu geçersiz veya daha önce kullanılmış.",
        )

    # 2. Kullanıcı Oluşturma (Argon2 ile hashleme)
    try:
        user = user_manager.create_user(username=payload.username, password=payload.password)
    except ValueError as ve:
        # Username çakışması vb.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"[AUTH] Kayıt sırasında hata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kaydetme sırasında sistemsel bir hata oluştu.",
        )

    # 3. Davet Kodunu İşaretle
    try:
        invite_manager.mark_invite_used(payload.invite_code, user.username)
    except Exception as e:
        logger.error(f"[AUTH] Davet kodu işaretleme hatası: {e}")
        # Kullanıcı oluştu ama invite düşmedi, kritik değil.

    logger.info(f"[AUTH] Yeni kullanıcı kayıt oldu: {user.username}")

    return {
        "ok": True,
        "message": f"Hoş geldin {payload.username}! Kaydın başarıyla oluşturuldu.",
    }


@router.post("/login")
async def login(payload: LoginRequest, response: Response, request: Request):
    """Kullanıcı girişi yapar ve HTTP-Only cookie set eder."""
    # 1. Kullanıcı Doğrulama (Argon2 ile şifre kontrolü)
    user = user_manager.get_user_by_username(payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı.",
        )

    if not user_manager.verify_password(user, payload.password):
        logger.warning(f"[AUTH] Başarısız giriş denemesi: {payload.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı.",
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız erişime kapatılmıştır.",
        )

    # 2. Oturum (Session) Oluşturma
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        session = session_service.create_session(user=user, user_agent=user_agent, ip_address=client_ip)
    except Exception as e:
        logger.error(f"[AUTH] Session oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Oturum açılırken bir hata oluştu.",
        )

    # 3. Cookie Ayarlama
    max_age = SESSION_MAX_AGE_LONG if payload.remember_me else SESSION_MAX_AGE_SHORT

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.id,  # Session Token (UUID/Hex)
        max_age=max_age,
        httponly=True,  # Javascript erişemez (XSS koruması)
        samesite="lax",  # CSRF koruması
        secure=False,  # Prod'da True olmalı
    )

    # 4. Beni Hatırla tokeni ayarla (opsiyonel)
    if payload.remember_me:
        token = remember_manager.create_remember_token(user.username)
        response.set_cookie(
            key=remember_manager.REMEMBER_COOKIE_NAME,
            value=token,
            max_age=SESSION_MAX_AGE_LONG,
            httponly=True,
            samesite="lax",
            secure=False,
        )

    logger.info(f"[AUTH] Giriş başarılı: {user.username} (Remember: {payload.remember_me})")

    return {"ok": True, "message": "Giriş başarılı.", "username": user.username, "role": user.role}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Oturumu sunucu tarafında sonlandırır ve cookie'yi temizler."""
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:
        session_service.invalidate_session(token)

    # Tarayıcı tarafında cookie'yi sil
    response.delete_cookie(key=SESSION_COOKIE_NAME, httponly=True, samesite="lax")

    # Beni Hatırla tokenini de sil
    remember_token = request.cookies.get(remember_manager.REMEMBER_COOKIE_NAME)
    if remember_token:
        remember_manager.invalidate_token(remember_token)
        response.delete_cookie(key=remember_manager.REMEMBER_COOKIE_NAME, httponly=True, samesite="lax")

    return {"ok": True, "message": "Çıkış yapıldı."}
