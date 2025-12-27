"""
Auth Modülü
===========

Kimlik doğrulama ve yetkilendirme işlemlerini yönetir.

Alt Modüller:
    - dependencies: FastAPI dependency'leri (get_current_user vb.)
    - session: Oturum yönetimi ve token işlemleri
    - user_manager: Kullanıcı CRUD işlemleri
    - invite_manager: Davet kodu sistemi
    - remember: "Beni Hatırla" özelliği

Hızlı Kullanım:
    from app.auth.dependencies import get_current_user, get_current_admin_user
    from app.auth.user_manager import create_user, verify_password

    # Route'da kullanıcı kontrolü
    @router.get("/profile")
    async def profile(user: User = Depends(get_current_active_user)):
        return {"username": user.username}
"""

# Alt modülleri kolayca erişilebilir yap
from app.auth.dependencies import (
    SESSION_COOKIE_NAME,
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
)
from app.auth.invite_manager import (
    find_valid_invite,
    generate_invite,
    mark_invite_used,
)
from app.auth.remember import (
    REMEMBER_COOKIE_NAME,
    create_remember_token,
    get_username_from_token,
)
from app.auth.session import (
    create_session,
    get_username_from_request,
    invalidate_session,
)
from app.auth.user_manager import (
    create_user,
    get_user_by_id,
    get_user_by_username,
    verify_password,
)

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "SESSION_COOKIE_NAME",
    # User management
    "create_user",
    "verify_password",
    "get_user_by_username",
    "get_user_by_id",
    # Session
    "create_session",
    "invalidate_session",
    "get_username_from_request",
    # Invite
    "generate_invite",
    "find_valid_invite",
    "mark_invite_used",
    # Remember
    "create_remember_token",
    "get_username_from_token",
    "REMEMBER_COOKIE_NAME",
]
