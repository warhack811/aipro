# -*- coding: utf-8 -*-
"""
Mami AI - Image Prompt Guard
============================

Bu modul, gorsel uretim promptlarindan izinsiz style tokenlarini temizler.

Kural:
    Kullanici prompt'unda gecmeyen style tokenlar eklenmez.
    
Forbidden Tokens (kullanici istemediginde eklenmeyecekler):
    - anime, manga, cartoon
    - neon, cinematic, dramatic lighting
    - unreal engine, octane render, unity
    - 8k, 4k, hdr, ultra hd
    - masterpiece, best quality, highly detailed
    - photorealistic, hyperrealistic
    - professional, studio lighting
    - award winning, trending on artstation
    - digital art, concept art
    - volumetric lighting, ray tracing
    - bokeh, depth of field
    - sharp focus, intricate details

Kullanim:
    from app.ai.prompts.image_guard import sanitize_image_prompt, FORBIDDEN_STYLE_TOKENS
    
    clean_prompt = sanitize_image_prompt(
        generated_prompt="A cute cat, 8k, masterpiece, photorealistic",
        user_original="kedi ciz"
    )
    # Result: "A cute cat" (8k, masterpiece, photorealistic kaldirilir)
"""

import re
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


# =============================================================================
# FORBIDDEN STYLE TOKENS
# =============================================================================

FORBIDDEN_STYLE_TOKENS: List[str] = [
    # Quality buzzwords
    "masterpiece",
    "best quality",
    "highly detailed",
    "ultra detailed",
    "extremely detailed",
    "intricate details",
    "sharp focus",
    "professional",
    "award winning",
    "award-winning",
    
    # Resolution
    "8k",
    "4k",
    "hdr",
    "ultra hd",
    "high resolution",
    "hi-res",
    
    # Art style (unless asked)
    "anime",
    "manga",
    "cartoon",
    "digital art",
    "concept art",
    "oil painting",
    "watercolor",
    
    # Render engines
    "unreal engine",
    "octane render",
    "unity",
    "blender",
    "vray",
    "ray tracing",
    
    # Photography jargon
    "cinematic",
    "cinematic lighting",
    "dramatic lighting",
    "studio lighting",
    "volumetric lighting",
    "bokeh",
    "depth of field",
    "dof",
    "lens flare",
    
    # Realism
    "photorealistic",
    "photo realistic",
    "hyperrealistic",
    "hyper realistic",
    "realistic",
    
    # Platform mentions
    "trending on artstation",
    "artstation",
    "deviantart",
    "pixiv",
    
    # Style words
    "neon",
    "vibrant",
    "vivid colors",
    "ethereal",
    "majestic",
    "epic",
    "stunning",
    "breathtaking",
    "gorgeous",
    "beautiful",
    "amazing",
    
    # Generic enhancers
    "perfect",
    "flawless",
    "exquisite",
    "elegant",
    "refined",
]

# Daha hızlı arama için set'e çevir (lowercase)
_FORBIDDEN_SET: Set[str] = {t.lower() for t in FORBIDDEN_STYLE_TOKENS}


# =============================================================================
# SANITIZATION FUNCTIONS
# =============================================================================

def _normalize_for_search(text: str) -> str:
    """Araştırma için metni normalize et."""
    return text.lower().strip()


def _token_in_text(token: str, text: str) -> bool:
    """Token'in metinde (kelime sınırlarıyla) geçip geçmediğini kontrol et."""
    # Kelime sınırı ile ara (örn: "art" "artstation"u tetiklemesin)
    pattern = r'\b' + re.escape(token) + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))


def get_forbidden_tokens_in_prompt(prompt: str) -> List[str]:
    """
    Bir prompt'ta bulunan forbidden token'lari dondurur.
    
    Args:
        prompt: Kontrol edilecek prompt
    
    Returns:
        List[str]: Bulunan forbidden tokenlar
    """
    found = []
    for token in FORBIDDEN_STYLE_TOKENS:
        if _token_in_text(token, prompt):
            found.append(token)
    return found


def sanitize_image_prompt(
    generated_prompt: str,
    user_original: str,
) -> str:
    """
    Uretilen image prompt'tan kullanicinin istemedigi style tokenlarini kaldirir.
    
    Args:
        generated_prompt: Groq'un urettigi/zenginlestirdigi prompt
        user_original: Kullanicinin orijinal mesaji
    
    Returns:
        str: Temizlenmis prompt
    
    Example:
        >>> sanitize_image_prompt(
        ...     "A cute fluffy cat, 8k, masterpiece, photorealistic, cinematic",
        ...     "kedi çiz"
        ... )
        'A cute fluffy cat'
    """
    if not generated_prompt:
        return generated_prompt
    
    user_lower = _normalize_for_search(user_original)
    result = generated_prompt
    removed_tokens = []
    
    for token in FORBIDDEN_STYLE_TOKENS:
        # Token kullanicinin orijinal mesajinda var mi?
        if _token_in_text(token, user_lower):
            # Kullanici istedi, birak
            continue
        
        # Token uretilen prompt'ta var mi?
        if _token_in_text(token, result):
            # Kaldir
            # Pattern: token'i ve ondan onceki virgul/and'i temizle
            patterns = [
                # ", token" veya "; token"
                r',\s*\b' + re.escape(token) + r'\b',
                r';\s*\b' + re.escape(token) + r'\b',
                # "token," veya "token;"
                r'\b' + re.escape(token) + r'\b\s*[,;]',
                # Sadece token (kelime siniri ile)
                r'\b' + re.escape(token) + r'\b',
            ]
            
            for pattern in patterns:
                new_result = re.sub(pattern, '', result, flags=re.IGNORECASE)
                if new_result != result:
                    result = new_result
                    removed_tokens.append(token)
                    break
    
    # Cift bosluk ve gereksiz virgulleri temizle
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r',\s*,', ',', result)
    result = re.sub(r'^\s*,\s*', '', result)
    result = re.sub(r'\s*,\s*$', '', result)
    result = result.strip()
    
    if removed_tokens:
        unique_removed = list(set(removed_tokens))
        logger.info(f"[IMAGE_GUARD] Kaldirilan tokenlar: {unique_removed}")
        logger.debug(f"[IMAGE_GUARD] '{generated_prompt}' -> '{result}'")
    
    return result


def validate_prompt_minimal(prompt: str) -> bool:
    """
    Prompt'un minimal (gereksiz style token yok) olup olmadigini kontrol eder.
    
    Test icin kullanilir.
    
    Args:
        prompt: Kontrol edilecek prompt
    
    Returns:
        bool: True = minimal/temiz, False = forbidden token var
    """
    found = get_forbidden_tokens_in_prompt(prompt)
    return len(found) == 0







