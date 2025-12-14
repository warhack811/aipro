"""
Mami AI - Model Router (Legacy Wrapper)
=======================================

Bu modül, geriye uyumluluk için eski choose_model_for_request fonksiyonunu
sağlar. Yeni kod smart_router.py kullanmalıdır.

Yeni Kullanım:
    from app.chat.smart_router import route_message, RoutingDecision
    
    decision = route_message(message, user, persona_name)
    if decision.target == RoutingTarget.LOCAL:
        # Local model kullan

Eski Kullanım (hala çalışır):
    from app.services.model_router import choose_model_for_request
    
    provider = choose_model_for_request(user, requested_model, force_local)
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.models import User

logger = logging.getLogger(__name__)


def choose_model_for_request(
    user: "User",
    requested_model: Optional[str] = None,
    force_local: bool = False,
    semantic: Optional[object] = None,
) -> str:
    """
    Kullanıcının yetkisine ve talebine göre model seçer.
    
    Bu fonksiyon geriye uyumluluk için korunmuştur.
    Yeni SmartRouter'a delege eder.
    
    Args:
        user: User nesnesi
        requested_model: İstenen model ("groq" veya "bela")
        force_local: Zorla local model kullan
        semantic: Semantic analiz sonucu
    
    Returns:
        str: "groq" veya "bela"
    """
    try:
        from app.chat.smart_router import route_message, RoutingTarget
        
        # Semantic'i dict'e çevir
        semantic_dict = None
        if semantic:
            semantic_dict = {
                "domain": getattr(semantic, "domain", None),
                "sensitivity": getattr(semantic, "sensitivity", []),
            }
        
        # Smart router'a delege et
        decision = route_message(
            message="",  # Boş mesaj (sadece user/model bazlı karar)
            user=user,
            persona_name=None,
            requested_model=requested_model,
            force_local=force_local,
            semantic=semantic_dict,
        )
        
        # RoutingTarget'ı eski formata çevir
        if decision.target == RoutingTarget.LOCAL:
            return "bela"
        else:
            return "groq"
        
    except ImportError:
        # Fallback: Eski mantık
        logger.warning("[MODEL_ROUTER] SmartRouter yüklenemedi, fallback kullanılıyor")
        return _legacy_choose_model(user, requested_model, force_local, semantic)


def _legacy_choose_model(
    user: "User",
    requested_model: Optional[str] = None,
    force_local: bool = False,
    semantic: Optional[object] = None,
) -> str:
    """
    Eski routing mantığı (fallback).
    
    DEPRECATED: Sadece SmartRouter yüklenemezse kullanılır.
    """
    from app.auth.permissions import user_can_use_local
    
    can_local = user_can_use_local(user)
    preferred = (requested_model or getattr(user, "selected_model", None) or "groq").lower()

    # Explicit bela isteği
    if preferred == "bela":
        return "bela" if can_local else "groq"

    # Force local
    if force_local and can_local:
        return "bela"

    # Semantic bazlı (sadece explicit sinyallerde)
    if semantic and can_local:
        domain = getattr(semantic, "domain", None)
        if domain == "sex":
            return "bela"

    return "groq"
