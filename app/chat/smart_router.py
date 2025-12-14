"""
Mami AI - Akıllı Model Yönlendirici
===================================

Bu modül, kullanıcı mesajlarını en uygun modele yönlendirir.

Routing Öncelik Sırası:
    1. Tool Intent: IMAGE/INTERNET isteği → İlgili tool
    2. Explicit Local: requested_model="bela" veya force_local → LOCAL
    3. Persona Requirement: requires_uncensored → LOCAL
    4. Content Heuristic: Roleplay/erotik içerik → LOCAL
    5. Default: → GROQ

Kurallar:
    - LOCAL model çıktısı tool çağrısı yapamaz
    - censorship_level=2 ise otomatik local routing kapalı
    - censorship_level=2 ise NSFW image reddedilir

Kullanım:
    from app.chat.smart_router import SmartRouter, RoutingDecision
    
    router = SmartRouter()
    decision = router.route(
        message="Bana bir resim çiz",
        user=user_obj,
        persona_name="standard",
        requested_model=None,
        force_local=False,
    )
    
    print(decision.target)  # "IMAGE"
    print(decision.reason)  # "tool_intent_image"
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.core.models import User

logger = logging.getLogger(__name__)


# =============================================================================
# ENUM & DATA CLASSES
# =============================================================================

class RoutingTarget(str, Enum):
    """Yönlendirme hedefleri."""
    GROQ = "groq"
    LOCAL = "local"
    IMAGE = "image"
    INTERNET = "internet"


class ToolIntent(str, Enum):
    """Tool intent türleri."""
    NONE = "none"
    IMAGE = "image"
    INTERNET = "internet"


@dataclass
class RoutingDecision:
    """
    Routing kararı sonucu.
    
    Attributes:
        target: Hedef model/tool
        tool_intent: Tool isteği (none, image, internet)
        reason_codes: Karar nedenleri
        censorship_level: Kullanıcı sansür seviyesi
        blocked: İstek reddedildi mi
        block_reason: Reddetme nedeni
        persona_name: Aktif persona adı
        persona_requires_uncensored: Persona sansürsüz model gerektiriyor mu
        final_model: Final yanıtı yazacak model (groq veya local)
        metadata: Ek bilgiler
    """
    target: RoutingTarget
    tool_intent: ToolIntent = ToolIntent.NONE
    reason_codes: List[str] = field(default_factory=list)
    censorship_level: int = 1
    blocked: bool = False
    block_reason: Optional[str] = None
    persona_name: str = "standard"
    persona_requires_uncensored: bool = False
    final_model: str = "groq"  # "groq" veya "local"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict'e dönüştür (logging için)."""
        return {
            "target": self.target.value,
            "tool_intent": self.tool_intent.value,
            "reason_codes": self.reason_codes,
            "censorship_level": self.censorship_level,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "persona_name": self.persona_name,
            "final_model": self.final_model,
        }


# =============================================================================
# CONTENT PATTERNS
# =============================================================================

# Tool intent patterns
IMAGE_PATTERNS = [
    r"(?i)\b(ciz|çiz|resim|gorsel|görsel|draw|paint|illustrate)\b",
    r"(?i)\b(fotograf|fotoğraf|foto|image|picture)\s*(yap|olustur|oluştur|uret|üret)",
    r"(?i)\b(gorsel|görsel)\s*(olustur|oluştur|uret|üret)\b",
    r"^!{1,2}",  # ! veya !! ile başlayan mesajlar = raw image prompt
]

INTERNET_PATTERNS = [
    r"(?i)\b(dolar|euro|sterlin|kur|borsa)\s*(kac|kaç|ne\s*kadar|fiyat)",
    r"(?i)\b(hava\s*durumu|bugun\s*hava|bugün\s*hava|yarin\s*hava|yarın\s*hava)\b",
    r"(?i)\bhava\b.*(bugun|bugün|nasil|nasıl)",
    r"(?i)\b(haber|guncel|güncel|son\s*dakika)\b",
    r"(?i)\b(ara|arat|google|search|internette)\b",
    r"(?i)\b(bitcoin|btc|eth|kripto)\s*(kac|kaç|fiyat)",
]

# Local routing content patterns (explicit)
LOCAL_EXPLICIT_PATTERNS = [
    r"(?i)\b(bela|sansursuz|sansürsüz|filtresiz|uncensored)\b",
    r"(?i)\b(yerel\s*model|local\s*model)\b",
]

# Local routing content patterns (content-based)
LOCAL_CONTENT_PATTERNS = [
    r"(?i)\b(roleplay|rol\s*yap|canlandir|karakter)\b",
    r"(?i)\b(senaryo\s*yaz|hikaye\s*yaz)\b.*\b(yetiskin|erotik|18\+)\b",
    r"(?i)\b(erotik|seksuel|cinsel)\b",
]

# NSFW image patterns
NSFW_IMAGE_PATTERNS = [
    r"(?i)\b(ciplak|çıplak|nude|naked|nsfw)\b",
    r"(?i)\b(seksi|sexy|erotik|erotic)\b.*\b(ciz|çiz|resim|gorsel|görsel)\b",
    r"(?i)\b(yetiskin|yetişkin|adult|18\+)\b.*\b(ciz|çiz|resim|gorsel|görsel)\b",
]


# =============================================================================
# SMART ROUTER
# =============================================================================

class SmartRouter:
    """
    Akıllı model yönlendirici.
    
    Kullanıcı mesajını analiz ederek en uygun modele yönlendirir.
    """
    
    def __init__(self):
        """Router'ı başlatır."""
        # Compiled regex patterns for performance
        self._image_patterns = [re.compile(p) for p in IMAGE_PATTERNS]
        self._internet_patterns = [re.compile(p) for p in INTERNET_PATTERNS]
        self._local_explicit = [re.compile(p) for p in LOCAL_EXPLICIT_PATTERNS]
        self._local_content = [re.compile(p) for p in LOCAL_CONTENT_PATTERNS]
        self._nsfw_image = [re.compile(p) for p in NSFW_IMAGE_PATTERNS]
    
    # -------------------------------------------------------------------------
    # LAZY IMPORTS
    # -------------------------------------------------------------------------
    
    def _get_permission_helpers(self):
        """Permission helper'ları lazy import."""
        from app.auth.permissions import (
            user_can_use_local,
            user_can_use_internet,
            user_can_use_image,
            get_censorship_level,
            can_auto_route_to_local,
            can_generate_nsfw_image,
            is_censorship_strict,
        )
        return {
            'user_can_use_local': user_can_use_local,
            'user_can_use_internet': user_can_use_internet,
            'user_can_use_image': user_can_use_image,
            'get_censorship_level': get_censorship_level,
            'can_auto_route_to_local': can_auto_route_to_local,
            'can_generate_nsfw_image': can_generate_nsfw_image,
            'is_censorship_strict': is_censorship_strict,
        }
    
    def _get_config_service(self):
        """Config service lazy import."""
        try:
            from app.core.dynamic_config import config_service
            return config_service
        except ImportError:
            return None
    
    # -------------------------------------------------------------------------
    # PATTERN MATCHING
    # -------------------------------------------------------------------------
    
    def _matches_any(self, text: str, patterns: List[re.Pattern]) -> bool:
        """Herhangi bir pattern eşleşiyor mu?"""
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False
    
    def _detect_tool_intent(self, message: str) -> ToolIntent:
        """
        Mesajdaki tool intent'i algılar.
        
        Args:
            message: Kullanıcı mesajı
        
        Returns:
            ToolIntent: Algılanan intent
        """
        if self._matches_any(message, self._image_patterns):
            return ToolIntent.IMAGE
        
        if self._matches_any(message, self._internet_patterns):
            return ToolIntent.INTERNET
        
        return ToolIntent.NONE
    
    def _detect_local_explicit(self, message: str) -> bool:
        """Explicit local model isteği var mı?"""
        return self._matches_any(message, self._local_explicit)
    
    def _detect_local_content(self, message: str) -> bool:
        """İçerik bazlı local routing gerekiyor mu?"""
        return self._matches_any(message, self._local_content)
    
    def _detect_nsfw_image(self, message: str) -> bool:
        """NSFW görsel isteği var mı?"""
        return self._matches_any(message, self._nsfw_image)
    
    # -------------------------------------------------------------------------
    # PERSONA CHECK
    # -------------------------------------------------------------------------
    
    def _persona_requires_local(self, persona_name: Optional[str]) -> bool:
        """
        Persona local model gerektiriyor mu?
        
        Args:
            persona_name: Aktif persona adı
        
        Returns:
            bool: Local gerekli mi
        """
        if not persona_name:
            return False
        
        config_service = self._get_config_service()
        if not config_service:
            return False
        
        try:
            persona = config_service.get_persona(persona_name)
            if persona:
                return persona.get("requires_uncensored", False)
        except Exception as e:
            logger.warning(f"[ROUTER] Persona okuma hatası: {e}")
        
        return False
    
    # -------------------------------------------------------------------------
    # ANA ROUTING LOGIC
    # -------------------------------------------------------------------------
    
    def route(
        self,
        message: str,
        user: Optional["User"] = None,
        persona_name: Optional[str] = None,
        requested_model: Optional[str] = None,
        force_local: bool = False,
        semantic: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Mesajı en uygun modele yönlendirir.
        
        Öncelik Sırası:
            1. Tool Intent (IMAGE/INTERNET)
            2. Explicit Local (requested_model="bela" veya force_local)
            3. Persona Requirement (requires_uncensored)
            4. Content Heuristic (roleplay/erotik)
            5. Default (GROQ)
        
        Args:
            message: Kullanıcı mesajı
            user: User nesnesi
            persona_name: Aktif persona adı
            requested_model: İstenen model ("groq" veya "bela")
            force_local: Zorla local model kullan
            semantic: Semantic analiz sonucu (opsiyonel)
        
        Returns:
            RoutingDecision: Routing kararı
        """
        helpers = self._get_permission_helpers()
        reason_codes: List[str] = []
        
        # Kullanıcı izinlerini al
        can_use_local = helpers['user_can_use_local'](user)
        can_use_internet = helpers['user_can_use_internet'](user)
        can_use_image = helpers['user_can_use_image'](user)
        censorship_level = helpers['get_censorship_level'](user)
        can_auto_local = helpers['can_auto_route_to_local'](user)
        can_nsfw = helpers['can_generate_nsfw_image'](user)
        is_strict = helpers['is_censorship_strict'](user)
        
        # Kullanıcı tercihlerini kontrol et (web araması kapalı mı?)
        web_search_enabled = True
        try:
            from app.services import user_preferences
            if user and hasattr(user, 'id') and user.id:
                prefs = user_preferences.get_effective_preferences(user.id, category="features")
                web_search_enabled = prefs.get("web_search", "true").lower() in ("true", "1", "yes", "on")
        except Exception as e:
            logger.warning(f"[ROUTER] Kullanıcı tercihleri kontrol edilemedi: {e}")
        
        # Persona bilgilerini hesapla
        active_persona = persona_name or "standard"
        persona_uncensored = self._persona_requires_local(active_persona)
        
        # Final model: requires_uncensored + can_local → local, değilse groq
        final_model = "local" if (persona_uncensored and can_use_local) else "groq"
        
        # Tool intent algıla (web araması kapalıysa INTERNET intent'i yok sayılır)
        tool_intent = self._detect_tool_intent(message)
        if tool_intent == ToolIntent.INTERNET and not web_search_enabled:
            tool_intent = ToolIntent.NONE
            reason_codes.append("web_search_disabled_by_user_pref")
        
        # =====================================================================
        # PRIORITY 1: TOOL INTENT (IMAGE / INTERNET)
        # =====================================================================
        
        if tool_intent == ToolIntent.IMAGE:
            # Görsel izni var mı?
            if not can_use_image:
                return RoutingDecision(
                    target=RoutingTarget.GROQ,
                    tool_intent=ToolIntent.NONE,
                    reason_codes=["image_permission_denied"],
                    censorship_level=censorship_level,
                    blocked=True,
                    block_reason="Görsel üretim izniniz bulunmuyor.",
                    persona_name=active_persona,
                    persona_requires_uncensored=persona_uncensored,
                    final_model=final_model,
                )
            
            # NSFW kontrolü
            is_nsfw = self._detect_nsfw_image(message)
            if is_nsfw and not can_nsfw:
                return RoutingDecision(
                    target=RoutingTarget.GROQ,
                    tool_intent=ToolIntent.NONE,
                    reason_codes=["nsfw_image_blocked", f"censorship_level_{censorship_level}"],
                    censorship_level=censorship_level,
                    blocked=True,
                    block_reason="Bu tür görsel içerik üretim izniniz bulunmuyor.",
                    persona_name=active_persona,
                    persona_requires_uncensored=persona_uncensored,
                    final_model=final_model,
                )
            
            reason_codes.append("tool_intent_image")
            return RoutingDecision(
                target=RoutingTarget.IMAGE,
                tool_intent=ToolIntent.IMAGE,
                reason_codes=reason_codes,
                censorship_level=censorship_level,
                persona_name=active_persona,
                persona_requires_uncensored=persona_uncensored,
                final_model=final_model,
                metadata={"is_nsfw": is_nsfw},
            )
        
        if tool_intent == ToolIntent.INTERNET:
            if not can_use_internet:
                return RoutingDecision(
                    target=RoutingTarget.GROQ,
                    tool_intent=ToolIntent.NONE,
                    reason_codes=["internet_permission_denied"],
                    censorship_level=censorship_level,
                    blocked=True,
                    block_reason="İnternet araması izniniz bulunmuyor.",
                    persona_name=active_persona,
                    persona_requires_uncensored=persona_uncensored,
                    final_model=final_model,
                )
            
            reason_codes.append("tool_intent_internet")
            return RoutingDecision(
                target=RoutingTarget.INTERNET,
                tool_intent=ToolIntent.INTERNET,
                reason_codes=reason_codes,
                censorship_level=censorship_level,
                persona_name=active_persona,
                persona_requires_uncensored=persona_uncensored,
                final_model=final_model,
            )
        
        # =====================================================================
        # PRIORITY 2: EXPLICIT LOCAL
        # Bu kategoriye giren istekler kullanıcının BİLİNÇLİ tercihidir:
        # - requested_model="bela"
        # - force_local=True
        # - message'da explicit local trigger kelimesi
        # - PERSONA requires_uncensored (kullanıcı bilinçli mod seçti)
        # =====================================================================
        
        requested = (requested_model or "").lower()
        explicit_local_message = self._detect_local_explicit(message)
        persona_requires = persona_name and self._persona_requires_local(persona_name)
        
        # Explicit local isteği var mı?
        if force_local or requested == "bela" or explicit_local_message or persona_requires:
            if can_use_local:
                reason_codes.append("explicit_local_request")
                if force_local:
                    reason_codes.append("force_local_flag")
                if requested == "bela":
                    reason_codes.append("requested_model_bela")
                if explicit_local_message:
                    reason_codes.append("message_contains_local_trigger")
                if persona_requires:
                    reason_codes.append("persona_requires_uncensored")
                    reason_codes.append(f"persona_{persona_name}")
                
                return RoutingDecision(
                    target=RoutingTarget.LOCAL,
                    tool_intent=ToolIntent.NONE,  # Local model tool çağıramaz
                    reason_codes=reason_codes,
                    censorship_level=censorship_level,
                    persona_name=active_persona,
                    persona_requires_uncensored=bool(persona_requires),
                    final_model="local",  # Explicit local seçildi
                )
            else:
                # İzin yok, Groq'a yönlendir
                reason_codes.append("local_permission_denied")
                reason_codes.append("fallback_to_groq")
                return RoutingDecision(
                    target=RoutingTarget.GROQ,
                    tool_intent=ToolIntent.NONE,
                    reason_codes=reason_codes,
                    censorship_level=censorship_level,
                    persona_name=active_persona,
                    persona_requires_uncensored=bool(persona_requires),
                    final_model="groq",
                )
        
        # =====================================================================
        # PRIORITY 3: CONTENT HEURISTIC (sadece net sinyallerde - AUTO routing)
        # =====================================================================
        
        if can_auto_local and self._detect_local_content(message):
            reason_codes.append("content_heuristic_local")
            return RoutingDecision(
                target=RoutingTarget.LOCAL,
                tool_intent=ToolIntent.NONE,
                reason_codes=reason_codes,
                censorship_level=censorship_level,
                persona_name=active_persona,
                persona_requires_uncensored=persona_uncensored,
                final_model="local",
            )
        
        # Semantic analiz bazlı routing (opsiyonel, yavaş olabilir)
        if semantic and can_auto_local:
            domain = semantic.get("domain")
            sensitivity = set(semantic.get("sensitivity", []) or [])
            
            # SADECE net erotik/roleplay sinyallerde
            # politics/religion için otomatik local YAPMA (yanlış pozitif)
            if domain == "sex" or "sexual_content" in sensitivity:
                reason_codes.append("semantic_sexual_content")
                return RoutingDecision(
                    target=RoutingTarget.LOCAL,
                    tool_intent=ToolIntent.NONE,
                    reason_codes=reason_codes,
                    censorship_level=censorship_level,
                    persona_name=active_persona,
                    persona_requires_uncensored=persona_uncensored,
                    final_model="local",
                )
        
        # =====================================================================
        # PRIORITY 4: DEFAULT → GROQ
        # =====================================================================
        
        reason_codes.append("default_groq")
        return RoutingDecision(
            target=RoutingTarget.GROQ,
            tool_intent=ToolIntent.NONE,
            reason_codes=reason_codes,
            censorship_level=censorship_level,
            persona_name=active_persona,
            persona_requires_uncensored=persona_uncensored,
            final_model=final_model,
        )
    
    # -------------------------------------------------------------------------
    # LOGGING
    # -------------------------------------------------------------------------
    
    def log_decision(
        self,
        decision: RoutingDecision,
        request_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> None:
        """
        Routing kararını loglar.
        
        Args:
            decision: Routing kararı
            request_id: İstek ID'si
            username: Kullanıcı adı
        """
        log_data = {
            "request_id": request_id or "unknown",
            "username": username or "unknown",
            **decision.to_dict(),
        }
        
        if decision.blocked:
            logger.warning(f"[ROUTER] BLOCKED: {log_data}")
        else:
            logger.info(f"[ROUTER] Decision: {log_data}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global router instance
smart_router = SmartRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def route_message(
    message: str,
    user: Optional["User"] = None,
    persona_name: Optional[str] = None,
    requested_model: Optional[str] = None,
    force_local: bool = False,
    semantic: Optional[Dict[str, Any]] = None,
) -> RoutingDecision:
    """
    Kısayol fonksiyon - mesajı yönlendirir.
    
    Args:
        message: Kullanıcı mesajı
        user: User nesnesi
        persona_name: Aktif persona adı
        requested_model: İstenen model
        force_local: Zorla local
        semantic: Semantic analiz
    
    Returns:
        RoutingDecision: Routing kararı
    """
    return smart_router.route(
        message=message,
        user=user,
        persona_name=persona_name,
        requested_model=requested_model,
        force_local=force_local,
        semantic=semantic,
    )

