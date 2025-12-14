from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from app.ai.prompts.identity import get_ai_identity, update_ai_identity
from app.auth import invite_manager, user_manager
from app.auth.dependencies import get_current_admin_user  # Admin Yetkisi ve BYPASS buradan gelir

# Core Servisler
from app.auth.session import get_username_from_request
from app.core.database import get_session
from app.core.feedback_store import list_all_feedback
from app.core.logger import get_logger
from app.core.models import AIIdentityConfig, Conversation, ConversationSummarySettings, Message, User
from app.core.summary_config import get_summary_settings, update_summary_settings
from app.image.gpu_state import get_state as get_gpu_state
from app.image.image_manager import get_image_queue_stats

logger = get_logger(__name__)

router = APIRouter(tags=["admin"])


# -------------------------------------------------------------------
# ŞEMALAR
# -------------------------------------------------------------------
class AdminUserOut(BaseModel):
    username: str
    role: str
    censorship_level: int
    can_use_internet: bool
    can_use_image: bool
    can_use_local_chat: bool
    is_banned: bool
    daily_internet_limit: int
    daily_image_limit: int

    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    role: Optional[str] = Field(None, description="user / vip / admin")
    censorship_level: Optional[int] = Field(None, ge=0, le=2)
    can_use_internet: Optional[bool] = None
    can_use_image: Optional[bool] = None
    can_use_local_chat: Optional[bool] = None
    is_banned: Optional[bool] = None
    daily_internet_limit: Optional[int] = Field(None, ge=0, le=10000)
    daily_image_limit: Optional[int] = Field(None, ge=0, le=10000)


class AdminSummaryOut(BaseModel):
    total_users: int
    total_admins: int
    total_invites: int
    used_invites: int
    unused_invites: int


class AdminInviteOut(BaseModel):
    code: str
    created_at: datetime
    created_by: str
    used: bool = Field(default=False, alias="is_used")
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AdminCreateInvite(BaseModel):
    note: Optional[str] = Field(
        None,
        description="Şimdilik sadece log için."
    )
class IdentityUpdate(BaseModel):
    display_name: Optional[str] = None
    developer_name: Optional[str] = None
    product_family: Optional[str] = None
    short_intro: Optional[str] = None
    forbid_provider_mention: Optional[bool] = None

class AdminMessageLogItem(BaseModel):
    username: str
    conversation_id: str
    role: str
    content_preview: str
    engine: str
    action: str
    mode: str
    persona_applied: bool
    created_at: datetime


class SummarySettingsUpdate(BaseModel):
    summary_enabled: Optional[bool] = None
    summary_first_threshold: Optional[int] = Field(None, ge=1, le=1000)
    summary_update_step: Optional[int] = Field(None, ge=1, le=1000)
    summary_max_messages: Optional[int] = Field(None, ge=5, le=200)


# ESKİ _require_admin FONKSİYONU KALDIRILDI.
# ARTIK HER YERDE get_current_admin_user KULLANILIYOR.

# -------------------------------------------------------------------
# 1) Admin Bilgisi
# -------------------------------------------------------------------
@router.get("/me")
async def admin_me(
    current_admin: User = Depends(get_current_admin_user),
):
    """Admin panelini açan kullanıcıyı ve rolünü döner."""
    return {"ok": True, "username": current_admin.username, "role": current_admin.role}


# -------------------------------------------------------------------
# 2) Kullanıcılar
# -------------------------------------------------------------------
@router.get("/users", response_model=List[AdminUserOut])
async def admin_list_users(
    current_admin: User = Depends(get_current_admin_user),
):
    """Sistemdeki tüm kullanıcıları ve yetkilerini listeler."""
    users = user_manager.list_users()
    return [
        AdminUserOut(
            username=u.username,
            role=getattr(u, "role", "user"),
            censorship_level=getattr(u, "permissions", {}).get("censorship_level", 0),
            can_use_internet=getattr(u, "permissions", {}).get("can_use_internet", True),
            can_use_image=getattr(u, "permissions", {}).get("can_use_image", True),
            can_use_local_chat=getattr(u, "permissions", {}).get("can_use_local_chat", True),
            is_banned=getattr(u, "is_banned", False),
            daily_internet_limit=getattr(u, "limits", {}).get("daily_internet", 50),
            daily_image_limit=getattr(u, "limits", {}).get("daily_image", 20),
        )
        for u in users
    ]


@router.put("/users/{username}", response_model=AdminUserOut)
async def admin_update_user(
    username: str,
    payload: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin_user),
):
    """Tek bir kullanıcının yetki ve limitlerini günceller."""
    updated = user_manager.update_user(
        username,
        role=payload.role,
        censorship_level=payload.censorship_level,
        can_use_internet=payload.can_use_internet,
        can_use_image=payload.can_use_image,
        can_use_local_chat=payload.can_use_local_chat,
        is_banned=payload.is_banned,
        daily_internet_limit=payload.daily_internet_limit,
        daily_image_limit=payload.daily_image_limit,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    return AdminUserOut(
        username=updated.username,
        role=getattr(updated, "role", "user"),
        censorship_level=getattr(updated, "permissions", {}).get("censorship_level", 0),
        can_use_internet=getattr(updated, "permissions", {}).get("can_use_internet", True),
        can_use_image=getattr(updated, "permissions", {}).get("can_use_image", True),
        can_use_local_chat=getattr(updated, "permissions", {}).get("can_use_local_chat", True),
        is_banned=getattr(updated, "is_banned", False),
        daily_internet_limit=getattr(updated, "limits", {}).get("daily_internet", 50),
        daily_image_limit=getattr(updated, "limits", {}).get("daily_image", 20),
    )


# -------------------------------------------------------------------
# 3) Davet Kodları
# -------------------------------------------------------------------
@router.get("/invites", response_model=List[AdminInviteOut])
async def admin_list_invites(
    current_admin: User = Depends(get_current_admin_user),
):
    """Tüm davet kodlarını listeler."""
    invites = invite_manager.list_invites()
    return [AdminInviteOut.model_validate(inv) for inv in invites]


@router.post("/invites", response_model=AdminInviteOut)
async def admin_create_invite(
    payload: AdminCreateInvite,
    current_admin: User = Depends(get_current_admin_user),
):
    """Yeni bir davet kodu oluşturur."""
    inv = invite_manager.generate_invite(current_admin.username)
    logger.info(f"[ADMIN] {current_admin.username} yeni davet kodu üretti: {inv.code}")
    return AdminInviteOut.model_validate(inv)


@router.delete("/invites/{code}")
async def admin_delete_invite(
    code: str,
    current_admin: User = Depends(get_current_admin_user),
):
    """Davet kodunu siler."""
    ok = invite_manager.delete_invite(code)
    if not ok:
        raise HTTPException(status_code=404, detail="Davet kodu bulunamadı.")
    return {"ok": True}


# -------------------------------------------------------------------
# 4) Özet / İstatistik
# -------------------------------------------------------------------
@router.get("/summary", response_model=AdminSummaryOut)
async def admin_summary(
    current_admin: User = Depends(get_current_admin_user),
):
    """Toplam kullanıcı, admin ve davet kodu istatistiklerini döner."""
    users = user_manager.list_users()
    invites = invite_manager.list_invites()

    total_users = len(users)
    total_admins = sum(1 for u in users if getattr(u, "role", "user") == "admin")
    total_invites = len(invites)
    used_invites = sum(1 for i in invites if getattr(i, "is_used", False))
    unused_invites = total_invites - used_invites

    return AdminSummaryOut(
        total_users=total_users,
        total_admins=total_admins,
        total_invites=total_invites,
        used_invites=used_invites,
        unused_invites=unused_invites,
    )

@router.get("/summary-settings", response_model=ConversationSummarySettings)
async def admin_get_summary_settings(
    current_admin: User = Depends(get_current_admin_user), # Dependency eklendi
):
    """Sohbet özeti sistemi için geçerli global ayarları döner."""
    return get_summary_settings()


@router.put("/summary-settings", response_model=ConversationSummarySettings)
async def admin_update_summary_settings(
    body: SummarySettingsUpdate,
    current_admin: User = Depends(get_current_admin_user), # Dependency eklendi
):
    """Sohbet özeti ayarlarını günceller."""
    updated = update_summary_settings(
        enabled=body.summary_enabled,
        first_threshold=body.summary_first_threshold,
        update_step=body.summary_update_step,
        max_messages=body.summary_max_messages,
    )
    return updated

# -------------------------------------------------------------------
# 5) Loglar ve Mesaj Geçmişi
# -------------------------------------------------------------------
LOG_FILE = Path("logs") / "mami.log" # logger.py'daki dosya adıyla eşleşmeli

@router.get("/logs/tail")
async def admin_logs_tail(
    lines: int = Query(200, ge=10, le=1000),
    current_admin: User = Depends(get_current_admin_user),
):
    """Log dosyasının son X satırını okur (Hata takibi için)."""
    if not LOG_FILE.exists():
        # Fallback: belki app.log'dur
        fallback_log = Path("logs") / "app.log"
        if fallback_log.exists():
            try:
                content = fallback_log.read_text(encoding="utf-8", errors="ignore").splitlines()
                return {"ok": True, "lines": content[-lines:]}
            except: pass
        return {"ok": True, "lines": ["Log dosyası henüz oluşmadı."]}

    try:
        content = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = content[-lines:]
    except Exception as e:
        logger.error(f"[ADMIN] Log okunamadı: {e}")
        return {"ok": False, "lines": [f"Log okuma hatası: {e}"]}

    return {"ok": True, "lines": tail}


# -------------------------------------------------------------------
# 6) Feedback Listesi (Like / Dislike)
# -------------------------------------------------------------------
class AdminFeedbackOut(BaseModel):
    username: str
    conversation_id: str
    message: str
    feedback: str
    created_at: str


@router.get("/feedback", response_model=List[AdminFeedbackOut])
async def admin_list_feedback(
    limit_per_user: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin_user),
):
    """Tüm kullanıcıların feedback kayıtlarını listeler."""
    items = list_all_feedback(limit_per_user=limit_per_user)
    return [
        AdminFeedbackOut(
            username=it["username"], # Dict dönüyor
            conversation_id=it["conversation_id"],
            message=it["message"],
            feedback=it["feedback"],
            created_at=it["created_at"],
        )
        for it in items
    ]

@router.get("/usage/messages", response_model=List[AdminMessageLogItem])
async def admin_list_messages(
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin_user),
) -> List[AdminMessageLogItem]:
    """Son bot mesajlarını ve metadata bilgilerini listeler."""
    from sqlmodel import col, desc
    
    with get_session() as session:
        stmt = (
            select(Message, Conversation, User)
            .join(Conversation, col(Message.conversation_id) == col(Conversation.id))
            .join(User, col(Conversation.user_id) == col(User.id))
            .where(col(Message.role) == "bot")
            .order_by(desc(Message.created_at))
            .limit(limit)
        )

        results = session.exec(stmt).all()
        items: List[AdminMessageLogItem] = []

        for msg, conv, user in results:
            meta: Dict[str, Any] = msg.extra_metadata or {}
            items.append(
                AdminMessageLogItem(
                    username=user.username,
                    conversation_id=conv.id,
                    role=msg.role,
                    content_preview=msg.content[:200],
                    engine=meta.get("engine", "unknown"),
                    action=meta.get("action", "UNKNOWN"),
                    mode=meta.get("mode", "normal"),
                    persona_applied=bool(meta.get("persona_applied", False)),
                    created_at=msg.created_at,
                )
            )

        return items

@router.get("/ai-identity", response_model=AIIdentityConfig)
async def admin_get_ai_identity(
    current_admin: User = Depends(get_current_admin_user), # Dependency eklendi
):
    """Mevcut AI kimlik ayarlarını döner."""
    return get_ai_identity()


@router.put("/ai-identity", response_model=AIIdentityConfig)
async def admin_update_ai_identity(
    body: IdentityUpdate,
    current_admin: User = Depends(get_current_admin_user), # Dependency eklendi
):
    """AI kimlik ayarlarını günceller."""
    updated = update_ai_identity(
        display_name=body.display_name,
        developer_name=body.developer_name,
        product_family=body.product_family,
        short_intro=body.short_intro,
        forbid_provider_mention=body.forbid_provider_mention,
    )
    return updated