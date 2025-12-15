# -*- coding: utf-8 -*-
"""
Mami AI - Image Router
======================

Bu modul, gorsel uretim isteklerini policy/izinlere gore routing yapar ve
uygun Flux checkpoint'ini secer.

Routing Kararlari:
    - NSFW icerik tespiti
    - Kullanici izinleri (censorship_level, can_use_image)
    - Checkpoint secimi (standard vs uncensored)
    - Policy enforcement (blocked/allowed)

Kullanim:
    from app.image.routing import decide_image_job
    
    spec = decide_image_job(
        prompt="a cute cat",
        user=user_obj,
    )
    
    if spec.blocked:
        raise PermissionError(spec.block_reason)
    
    # Forge'a spec.checkpoint_name ile istek at
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.core.models import User

logger = logging.getLogger(__name__)


# =============================================================================
# CHECKPOINT MAPPING
# =============================================================================

class FluxVariant(str, Enum):
    """Flux model varyantlari."""
    STANDARD = "flux_standard"
    UNCENSORED = "flux_uncensored"


# Checkpoint mapping - Config'ten alinir
def _get_checkpoints() -> Dict[FluxVariant, str]:
    """Config'ten checkpoint mapping'i dondurur."""
    try:
        from app.config import get_settings
        settings = get_settings()
        return {
            FluxVariant.STANDARD: settings.FLUX_STANDARD_CHECKPOINT,
            FluxVariant.UNCENSORED: settings.FLUX_NSFW_CHECKPOINT,
        }
    except Exception as e:
        logger.warning(f"[IMAGE_ROUTER] Config'ten checkpoint alinamadi: {e}")
        # Fallback - hardcoded defaults
        return {
            FluxVariant.STANDARD: "flux1-dev-bnb-nf4-v2.safetensors",
            FluxVariant.UNCENSORED: "fluxedUpFluxNSFW_51FP8.safetensors",
        }

# Module-level cache (startup'ta bir kez alinir)
CHECKPOINTS = _get_checkpoints()


# =============================================================================
# IMAGE JOB SPEC
# =============================================================================

@dataclass
class ImageJobSpec:
    """
    Gorsel uretim job'i icin routing karari.
    
    Attributes:
        variant: flux_standard veya flux_uncensored
        checkpoint_name: Forge'a gonderilecek .safetensors dosya adi
        prompt: Kullanilacak prompt
        negative_prompt: Negative prompt
        params: Generation parametreleri (steps, cfg_scale, vb.)
        flags: Ek flag'lar (nsfw_detected, policy_override, vb.)
        reasons: Karar nedenleri (log icin)
        blocked: Istek reddedildi mi
        block_reason: Reddetme nedeni
    """
    variant: FluxVariant
    checkpoint_name: str
    prompt: str
    negative_prompt: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict'e donustur (logging icin)."""
        return {
            "variant": self.variant.value,
            "checkpoint_name": self.checkpoint_name,
            "prompt": self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt,
            "negative_prompt": self.negative_prompt,
            "params": self.params,
            "flags": self.flags,
            "reasons": self.reasons,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
        }


# =============================================================================
# NSFW DETECTION
# =============================================================================

# NSFW tespit icin pattern'ler
NSFW_PATTERNS = [
    r"(?i)\b(ciplak|çıplak|nude|naked|nsfw)\b",
    r"(?i)\b(seksi|sexy|erotik|erotic)\b",
    r"(?i)\b(yetiskin|yetişkin|adult)\b",
    r"(?i)\b(porno|porn|xxx)\b",
    r"(?i)\b(soyunmus|soyunmuş|undressed)\b",
    r"(?i)18\s*\+",  # Word boundary kullanma, + ozel karakter
]

_nsfw_patterns_compiled = [re.compile(p) for p in NSFW_PATTERNS]


def _detect_nsfw_in_prompt(prompt: str) -> bool:
    """
    Prompt'ta NSFW icerik var mi kontrol eder.
    
    Args:
        prompt: Kontrol edilecek prompt
    
    Returns:
        bool: NSFW icerik tespit edildiyse True
    """
    for pattern in _nsfw_patterns_compiled:
        if pattern.search(prompt):
            return True
    return False


# =============================================================================
# PERMISSION HELPERS
# =============================================================================

def _get_censorship_level(user: Optional["User"]) -> int:
    """
    Kullanicinin censorship level'ini dondurur.
    
    Args:
        user: User nesnesi
    
    Returns:
        int: 0=unrestricted, 1=normal, 2=strict
    """
    if user is None:
        return 1  # default: normal
    
    try:
        from app.auth.permissions import get_censorship_level
        return get_censorship_level(user)
    except Exception as e:
        logger.warning(f"[IMAGE_ROUTER] Censorship level alinamadi: {e}")
        return 1  # default: normal


def _can_generate_nsfw(user: Optional["User"]) -> bool:
    """
    Kullanici NSFW gorsel uretebilir mi kontrol eder.
    
    Args:
        user: User nesnesi
    
    Returns:
        bool: NSFW gorsel uretebilir mi
    """
    if user is None:
        return False
    
    try:
        from app.auth.permissions import can_generate_nsfw_image
        return can_generate_nsfw_image(user)
    except Exception as e:
        logger.warning(f"[IMAGE_ROUTER] NSFW izni kontrol edilemedi: {e}")
        return False


def _can_use_image(user: Optional["User"]) -> bool:
    """
    Kullanici gorsel uretebilir mi kontrol eder.
    
    Args:
        user: User nesnesi
    
    Returns:
        bool: Gorsel uretebilir mi
    """
    if user is None:
        return False
    
    try:
        from app.auth.permissions import user_can_use_image
        return user_can_use_image(user)
    except Exception as e:
        logger.warning(f"[IMAGE_ROUTER] Image izni kontrol edilemedi: {e}")
        return False


# =============================================================================
# MAIN ROUTING LOGIC
# =============================================================================

def decide_image_job(
    prompt: str,
    user: Optional["User"] = None,
    negative_prompt: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    style_profile: Optional[Dict[str, Any]] = None,
) -> ImageJobSpec:
    """
    Gorsel uretim istegi icin routing karari verir.
    
    Karar Akisi:
        1. Kullanici gorsel uretebilir mi? (can_use_image)
        2. Prompt'ta NSFW icerik var mi? (pattern matching)
        3. NSFW icin izin var mi? (can_generate_nsfw_image)
        4. Checkpoint sec: NSFW -> uncensored, diger -> standard
        5. Policy enforcement: block veya allow
    
    Args:
        prompt: Kullanicinin istegi
        user: User nesnesi
        negative_prompt: Negative prompt (opsiyonel)
        params: Generation parametreleri (opsiyonel)
    
    Returns:
        ImageJobSpec: Routing karari
    
    Example:
        >>> spec = decide_image_job("a cute cat", user)
        >>> spec.variant  # FluxVariant.STANDARD
        >>> spec.checkpoint_name  # "flux1-dev-bnb-nf4-v2.safetensors"
        >>> spec.blocked  # False
    """
    reasons = []
    flags = {}
    
    # 1. Gorsel uretim izni kontrol
    if not _can_use_image(user):
        reasons.append("no_image_permission")
        return ImageJobSpec(
            variant=FluxVariant.STANDARD,
            checkpoint_name=CHECKPOINTS[FluxVariant.STANDARD],
            prompt=prompt,
            negative_prompt=negative_prompt,
            params=params or {},
            flags=flags,
            reasons=reasons,
            blocked=True,
            block_reason="[BLOCKED] Görsel üretim izniniz bulunmuyor.",
        )
    
    # 2. NSFW icerik tespiti
    nsfw_detected = _detect_nsfw_in_prompt(prompt)
    flags["nsfw_detected"] = nsfw_detected
    
    if nsfw_detected:
        reasons.append("nsfw_content_detected")
    
    # 3. Censorship level
    censorship_level = _get_censorship_level(user)
    flags["censorship_level"] = censorship_level
    
    # 4. NSFW izin kontrolu
    if nsfw_detected:
        can_nsfw = _can_generate_nsfw(user)
        
        if not can_nsfw:
            # NSFW reddedildi
            reasons.append("nsfw_blocked_no_permission")
            return ImageJobSpec(
                variant=FluxVariant.STANDARD,
                checkpoint_name=CHECKPOINTS[FluxVariant.STANDARD],
                prompt=prompt,
                negative_prompt=negative_prompt,
                params=params or {},
                flags=flags,
                reasons=reasons,
                blocked=True,
                block_reason="[BLOCKED] Bu tür görsel içerik üretim izniniz bulunmuyor.",
            )
        
        # NSFW izin var -> uncensored model
        reasons.append("nsfw_allowed_using_uncensored")
        variant = FluxVariant.UNCENSORED
    else:
        # Normal icerik -> standard model
        reasons.append("safe_content_using_standard")
        variant = FluxVariant.STANDARD
    
    # ============================================================================
    # TEMPORARY OVERRIDE: Her zaman NSFW modeli kullan (test için)
    # TODO: Bu satırları sil veya comment out et (eski haline dönmek için)
    # ============================================================================
    variant = FluxVariant.UNCENSORED
    reasons.append("TEMP_OVERRIDE_using_nsfw_model_for_all")
    # ============================================================================
    
    # 5. Checkpoint secimi
    checkpoint_name = CHECKPOINTS[variant]
    
    # 6. Parametreleri hazirla
    final_params = params or {}
    
    # Varsayılan çözünürlük: Kare (1024x1024)
    default_w, default_h = 1024, 1024
    
    # Kullanıcı tercihi varsa uygula
    if style_profile:
        ratio = style_profile.get("image_ratio", "square")
        if ratio == "portrait":
            default_w, default_h = 896, 1152
        elif ratio == "landscape":
            default_w, default_h = 1216, 832
        elif ratio == "cinematic":
            default_w, default_h = 1344, 768
            
    if "steps" not in final_params:
        final_params["steps"] = 20
    if "width" not in final_params:
        final_params["width"] = default_w
    if "height" not in final_params:
        final_params["height"] = default_h
    if "cfg_scale" not in final_params:
        final_params["cfg_scale"] = 1.0
    if "sampler_name" not in final_params:
        final_params["sampler_name"] = "Euler"
    if "scheduler" not in final_params:
        final_params["scheduler"] = "Simple"
    if "distilled_cfg_scale" not in final_params:
        final_params["distilled_cfg_scale"] = 3.5
    
    # 7. Spec olustur
    spec = ImageJobSpec(
        variant=variant,
        checkpoint_name=checkpoint_name,
        prompt=prompt,
        negative_prompt=negative_prompt,
        params=final_params,
        flags=flags,
        reasons=reasons,
        blocked=False,
        block_reason=None,
    )
    
    logger.info(
        f"[IMAGE_ROUTER] variant={variant.value}, checkpoint={checkpoint_name}, "
        f"nsfw={nsfw_detected}, censorship={censorship_level}, reasons={reasons}"
    )
    
    return spec


# =============================================================================
# CONFIG HELPER (ileride kullanilacak)
# =============================================================================

def get_checkpoint_from_config(variant: FluxVariant) -> str:
    """
    Config'ten checkpoint adini alir.
    
    Simdilik CHECKPOINTS dict'ten doner, ileride dynamic_config'e baglanir.
    
    Args:
        variant: Flux variant
    
    Returns:
        str: Checkpoint dosya adi
    """
    return CHECKPOINTS.get(variant, CHECKPOINTS[FluxVariant.STANDARD])

