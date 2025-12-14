"""
Mami AI - Ana Uygulama Giriş Noktası
====================================

Bu modül, FastAPI uygulamasını başlatır ve yapılandırır.

Başlatma:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

veya eski yol (hala çalışır):
    uvicorn main:app --reload

Özellikler:
    - CORS middleware
    - Session middleware
    - Statik dosya sunumu (UI, images)
    - API route'ları
    - WebSocket desteği
    - Otomatik veritabanı başlatma
"""

import sys
import os
from pathlib import Path

# Proje kök dizinini Python path'e ekle
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Yapılandırma
from app.config import get_settings

# Core modüller
from app.core.logger import get_logger
from app.core.database import init_database_with_defaults
from app.core.exceptions import MamiException

# Auth
from app.auth.user_manager import ensure_default_admin
from app.auth.invite_manager import ensure_initial_invite
from app.auth.session import get_username_from_request

# Resolvers
from app.auth.user_manager import get_user_by_username
from app.memory.store import set_user_resolver as set_memory_user_resolver
from app.memory.conversation import set_user_resolver as set_conv_user_resolver

# =============================================================================
# YAPILANDIRMA
# =============================================================================

settings = get_settings()
logger = get_logger(__name__)

# =============================================================================
# USER RESOLVER
# =============================================================================

def _resolve_user_id(username: str):
    """Username -> user_id çözmek için ortak resolver."""
    user = get_user_by_username(username)
    return user.id if user else None

# Resolver'ları ayarla
set_memory_user_resolver(_resolve_user_id)
set_conv_user_resolver(_resolve_user_id)

# =============================================================================
# FASTAPI UYGULAMASI
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Mami AI - Gelişmiş AI Asistan",
    version="4.2.0",
    debug=settings.DEBUG,
)

# =============================================================================
# MIDDLEWARE
# =============================================================================

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# STATİK DOSYALAR
# =============================================================================

BASE_DIR = project_root
UI_DIR = BASE_DIR / "ui"
IMAGES_DIR = BASE_DIR / "data" / "images"

# Dizinleri oluştur
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/ui", StaticFiles(directory=str(UI_DIR)), name="ui")
app.mount("/pwa", StaticFiles(directory=str(UI_DIR)), name="pwa")
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(MamiException)
async def mami_exception_handler(request: Request, exc: MamiException):
    """MamiException türündeki hataları yakalar."""
    logger.error(f"[EXCEPTION] {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": True,
            "message": exc.user_message,
            "detail": exc.message if settings.DEBUG else None
        }
    )

# =============================================================================
# LIFECYCLE EVENTS
# =============================================================================

@app.on_event("startup")
async def on_startup():
    """Uygulama başlangıcında çalışır."""
    logger.info("=" * 50)
    logger.info("Mami AI v5.0 başlatılıyor...")
    logger.info("=" * 50)
    
    # 1. Veritabanı ve varsayılan config'leri yükle
    init_database_with_defaults()
    
    # 2. Varsayılan admin oluştur
    ensure_default_admin()
    
    # 3. İlk davet kodunu oluştur
    invite = ensure_initial_invite()
    logger.info(f"Test için davet kodu: {invite.code}")
    
    # 4. Bakım görevlerini başlat
    try:
        from app.core.maintenance import start_maintenance_scheduler
        start_maintenance_scheduler()
        logger.info("Günlük bakım görevi aktif")
    except ImportError:
        logger.warning("Bakım modülü yüklenemedi")
    
    # 5. Dynamic config cache'i ısıt (opsiyonel, performans için)
    try:
        from app.core.dynamic_config import config_service
        # Kritik config'leri preload et
        config_service.get_category("system")
        config_service.get_category("features")
        logger.info("Dinamik config sistemi aktif")
    except Exception as e:
        logger.warning(f"Config preload hatası: {e}")

    logger.info("Mami AI hazır!")


@app.on_event("shutdown")
async def on_shutdown():
    """Uygulama kapanırken çalışır."""
    logger.info("Mami AI kapatılıyor...")

# =============================================================================
# TEMEL ENDPOINT'LER
# =============================================================================

@app.get("/health")
async def health_check():
    """Sağlık kontrolü endpoint'i."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/favicon.ico")
async def favicon():
    """Favicon için boş yanıt döndür (404 hatasını önlemek için)."""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/pwa/icon-192.png")
@app.get("/pwa/icon-512.png")
async def pwa_icon():
    """PWA icon dosyaları için boş yanıt döndür (404 hatasını önlemek için)."""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Ana sayfa.
    
    Giriş yapmışsa sohbete, yapmamışsa login'e yönlendirir.
    """
    username = get_username_from_request(request)
    
    if username:
        return RedirectResponse(url="/ui/chat.html")

    login_html_path = UI_DIR / "login.html"
    if login_html_path.exists():
        return HTMLResponse(content=login_html_path.read_text(encoding="utf-8"))
    
    return HTMLResponse("<h1>Mami AI</h1><p>login.html bulunamadı.</p>")


# =============================================================================
# YENİ FRONTEND (React)
# =============================================================================

UI_NEW_DIR = BASE_DIR / "ui-new" / "dist"

@app.get("/new-ui/{path:path}", response_class=HTMLResponse)
async def new_ui(request: Request, path: str = ""):
    """
    Yeni React frontend'i sunar.
    
    - Giriş yapmamış kullanıcıları login'e yönlendirir
    - SPA routing için index.html fallback
    - Static assets (.js, .css, etc.) direkt sunulur
    """
    username = get_username_from_request(request)
    
    # Auth kontrolü
    if not username:
        # API isteği mi? (AJAX)
        if request.headers.get("accept", "").startswith("application/json"):
            return JSONResponse(
                status_code=401,
                content={"ok": False, "error": "Unauthorized", "redirect": "/"}
            )
        return RedirectResponse(url="/")
    
    # Static asset ise direkt sun
    file_path = UI_NEW_DIR / path
    if path and file_path.exists() and file_path.is_file():
        content_type = "text/html"
        if path.endswith(".js"):
            content_type = "application/javascript"
        elif path.endswith(".css"):
            content_type = "text/css"
        elif path.endswith(".svg"):
            content_type = "image/svg+xml"
        elif path.endswith(".png"):
            content_type = "image/png"
        elif path.endswith(".woff2"):
            content_type = "font/woff2"
        
        from fastapi.responses import Response
        return Response(
            content=file_path.read_bytes(),
            media_type=content_type
        )
    
    # SPA fallback - index.html
    index_path = UI_NEW_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    
    return HTMLResponse("<h1>Yeni UI bulunamadı</h1><p>ui-new/dist klasörü mevcut değil.</p>")

# =============================================================================
# WEBSOCKET
# =============================================================================

# WebSocket bağlantıları - websocket_sender.py ile aynı isim olmalı!
from app.websocket_sender import connected
from app.auth.dependencies import SESSION_COOKIE_NAME
from app.auth.session import get_user_from_session_token
from http.cookies import SimpleCookie

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket bağlantı endpoint'i - username ile kayıt yapar."""
    await ws.accept()
    
    # Cookie'den session token al ve kullanıcı bul
    username = "anonymous"
    try:
        # WebSocket'te cookies'e scope üzerinden erişim
        cookies = {}
        for header_name, header_value in ws.scope.get("headers", []):
            if header_name == b"cookie":
                cookie = SimpleCookie()
                cookie.load(header_value.decode("utf-8"))
                for key, morsel in cookie.items():
                    cookies[key] = morsel.value
                break
        
        token = cookies.get(SESSION_COOKIE_NAME)
        logger.info(f"[WEBSOCKET] Cookie token: {token[:20] if token else 'None'}...")
        
        if token:
            user = get_user_from_session_token(token)
            if user:
                username = user.username
                logger.info(f"[WEBSOCKET] User resolved: {username}")
    except Exception as e:
        logger.error(f"[WEBSOCKET] Username alınamadı: {e}")
    
    # Dict olarak kaydet: {ws: username}
    connected[ws] = username
    logger.info(f"[WEBSOCKET] Yeni bağlantı: {username}, toplam: {len(connected)}, all_users: {list(connected.values())}")
    
    try:
        while True:
            await ws.receive_text()
    except Exception as e:
        logger.debug(f"[WEBSOCKET] Bağlantı kapandı ({username}): {e}")
    finally:
        if ws in connected:
            del connected[ws]
        logger.info(f"[WEBSOCKET] Bağlantı kaldırıldı: {username}, kalan: {len(connected)}")

# =============================================================================
# API ROUTE'LARI
# =============================================================================

from app.api import public_routes, user_routes, admin_routes, system_routes, auth_routes

# API v1 (Yeni standart yol)
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["v1-auth"])
app.include_router(public_routes.router, prefix="/api/v1/public", tags=["v1-public"])
app.include_router(user_routes.router, prefix="/api/v1/user", tags=["v1-user"])
app.include_router(admin_routes.router, prefix="/api/v1/admin", tags=["v1-admin"])
app.include_router(system_routes.router, prefix="/api/v1/system", tags=["v1-system"])

# Backward Compatibility (Eski yollar da çalışır)
app.include_router(public_routes.router, prefix="/api/public", include_in_schema=False)
app.include_router(user_routes.router, prefix="/api/user", include_in_schema=False)
app.include_router(admin_routes.router, prefix="/api/admin", include_in_schema=False)
app.include_router(system_routes.router, prefix="/api/system", include_in_schema=False)

logger.info("API route'ları yüklendi (v1 + backward compat)")

