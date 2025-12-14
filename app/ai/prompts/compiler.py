# -*- coding: utf-8 -*-
"""
Mami AI - System Prompt Compiler
================================

Bu modul, yanit ureten model icin system prompt'u tek yerden uretir.

Prompt Katmanlari:
    1. CORE_PROMPT: Sabit kurallar (dogruluk, guvenlik, logging)
    2. PERSONA_PROMPT: DB PersonaConfig'ten system_prompt_template
    3. USER_PREFS: Kullanici tercihleri (ton, emoji, uzunluk)
    4. TOGGLE_CONTEXT: Web/Image toggle durumu ve izinler
    5. SAFETY_CONTEXT: Censorship level ve guvenlik kurallari

Kurallar:
    - Persona prompt ASLA image/web prompt uretimine karismaZ
    - Image/Web prompt uretimi mode'dan bagimsiz ve minimal kalir
    - initial_message sadece yeni sohbet baslarken gosterilir

Kullanim:
    from app.ai.prompts.compiler import build_system_prompt
    
    prompt = build_system_prompt(
        user=user_obj,
        persona_name="romantic",
        toggles={"web": True, "image": False},
    )
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from app.core.models import User

logger = logging.getLogger(__name__)


# =============================================================================
# CORE PROMPT - Sabit Kurallar
# =============================================================================

CORE_PROMPT = """Sen Mami AI, kullanicilara yardimci olan bir yapay zeka asistanisin.

TEMEL KURALLAR:
- Dogru ve guvenilir bilgi ver
- Emin olmadigin konularda belirt
- Kullaniciya saygi goster
- Turkce konusmalarada Turkce yanitla
- Kodlari aciklamali ve anlasilir yaz

TURKCE KALITESI KURALLARI (KRITIK!):
- TAM CUMLELER KUR: Her cumle mutlaka tamamlanmali, yarim kalmamali
- DILBILGISI: Turkce dilbilgisi kurallarina uy (ekler, cogul, zamanlar)
- DOGAL TURKCE: Robotik kalip ifadelerden kacin, dogal konus
- KOD ACİKLAMALARI: Kod ornekleri verirken aciklamalari TAM ve ANLASILIR Turkce yaz
- NOKTALAMA: Noktalama isaretlerini dogru kullan (nokta, virgul, soru isareti)
- KELIME SECIMI: Uygun Turkce kelimeler kullan, gereksiz Ingilizce kelime kullanma
- CUMLE YAPISI: Basit ve anlasilir cumleler kur, cok uzun ve karmasik cumlelerden kacin

ORNEK IYI TURKCE:
✅ "Bu kodun calismasi icin, bilgisayarinizda Python yuklu olmasi gerekir. Kodu calistirdiginizda, ekranda 'Merhaba, Dunya!' yazisi gorunecektir."

ORNEK KOTU TURKCE (YAPMA!):
❌ "print("Mera, Dunya!")`Bu kodun calismasi icin, bilgisayarinizda Python)yuklu olması. Kodu calistirdiginizda, ekranda "Merhaba, Dunya!" yazisi gorunecektir.```**Aciklama:**"

CUMLE TAMAMLAMA KURALLARI:
- Her cumle mutlaka bir nokta, soru isareti veya unlem ile bitmeli
- Yarim kalan cumleler olmamali
- Kod bloklarindan sonra mutlaka tam bir aciklama cumlesi yaz
- Liste maddeleri de tam cumle olmali

KOD BLOKLARI FORMATI (KRITIK!):
- Kod ornegi verirken MUTLAKA 3 backtick (```) kullan
- Format: ```dil\nkod\n```
- ASLA [CODE_BLOCK_{}] gibi placeholder formatlari kullanma
- ASLA "Kod:" veya "*** Kod:" gibi formatlar kullanma
- Direkt ``` ile basla ve ``` ile bitir

YASAKLAR:
- Yanlis bilgi uretme
- Zararli icerik olusturma
- Kisisel veri paylaslma
- Yarim kalan cumleler
- Dilbilgisi hatalari
- Robotik kalip ifadeler
"""

# =============================================================================
# OUTPUT CONTRACT - Profesyonel Cevap Formati (ChatGPT Kalitesi)
# =============================================================================

OUTPUT_CONTRACT_PROFESSIONAL = """
YAPIT FORMATI KURALLARI (PROFESYONEL STANDART):

1. GEREKSIZ SUSLEME YOK:
   - Emoji kullanma (kullanici tercihi yoksa)
   - Asiri vurgulama yapma
   - Her yanita baslik zorunlu DEGIL

2. BASLIK KULLANIMI:
   - Uzun aciklamalarda ## ve ### kullan
   - Kisa yanitlarda baslik KULLANMA
   - Tek cumleligin basligi olmaz

3. YAPILANDIRILMIS YANITLAR:
   - Teknik/plan sorularinda: 3-7 maddelik adim listesi
   - Karsilastirmalarda: Artilari ve Eksileri ayri listele
   - Aciklama gerektiren sorularda: Once ozet, sonra detay

4. KOD ORNEKLERI FORMATI:
   - Oncelikle 1-2 cumle aciklama yaz
   - Sonra ```dil\\nkod\\n``` blogu
   - Ardindan 2-4 maddelik aciklama notlari ekle
   - ASLA kod aciklamasiz brakma

5. VURGULAMA:
   - Onemli noktalar icin **bold** kullan
   - Tek yanotta maksimum 3-5 vurgu
   - Her cumleyi vurgulama

6. WEB ARAMA SONUCLARI:
   - Sonuclari "Kaynaklar" bolumunde listele
   - Format: - [Baslik] - kaynak.com
   - Kaynak yoksa bu bolumu yazma

7. UZUNLUK DENGESI:
   - Soru kisaysa yanit da kisa olsun
   - Detay istemediyse uzatma
   - Noktayi koy ve bitir
"""

# =============================================================================
# TOGGLE CONTEXT TEMPLATES
# =============================================================================

TOGGLE_WEB_ENABLED = """
WEB ARAMA: Aktif
- Kullanici guncel bilgi istediginde web aramasini kullanabilirsin
- Hava durumu, doviz kuru, haberler icin web aramasindan faydalanabilirsin
"""

TOGGLE_WEB_DISABLED = """
WEB ARAMA: Devre Disi
- Web aramasina erisiimin yok
- Guncel bilgi isteklerinde bunu belirt
"""

TOGGLE_IMAGE_ENABLED = """
GORSEL URETIM: Aktif
- Kullanici gorsel istediginde gorsel uretebilirsin
- Gorsel promptlari kisa ve net tut
"""

TOGGLE_IMAGE_DISABLED = """
GORSEL URETIM: Devre Disi
- Gorsel uretim ozelligin yok
- Gorsel isteklerinde bunu belirt
"""

# =============================================================================
# SAFETY CONTEXT TEMPLATES
# =============================================================================

SAFETY_STRICT = """
GUVENLIK: Siki Mod
- NSFW icerik uretme
- Yetiskin icerikten kacin
- Uygunsuz istekleri kibarca reddet
"""

SAFETY_NORMAL = """
GUVENLIK: Normal Mod
- Genel kurallara uy
- Uygunsuz istekleri reddet
"""

SAFETY_UNRESTRICTED = """
GUVENLIK: Serbest Mod
- Kullanici yetiskin ve izinli
- Yaratici ozgurluk var
- Yine de etik sinirlara dikkat et
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_persona_prompt(persona_name: str) -> str:
    """
    DB'den persona system_prompt_template'ini alir.
    
    Args:
        persona_name: Persona adi
    
    Returns:
        str: Persona prompt veya bos string
    """
    try:
        from app.core.dynamic_config import config_service
        
        persona = config_service.get_persona(persona_name)
        if persona:
            template = persona.get("system_prompt_template", "")
            if template:
                return f"\nPERSONA ({persona.get('display_name', persona_name)}):\n{template}\n"
    except Exception as e:
        logger.warning(f"[PROMPT_COMPILER] Persona prompt alinamadi: {e}")
    
    return ""


def _get_user_prefs_prompt(user: Optional["User"]) -> str:
    """
    Kullanici tercihlerinden prompt olusturur.
    
    Args:
        user: User nesnesi
    
    Returns:
        str: User prefs prompt
    """
    if not user:
        return ""
    
    prefs_parts = []
    
    # Permissions'dan tercihleri oku
    perms = getattr(user, "permissions", {}) or {}
    
    # Ton tercihi
    tone = perms.get("preferred_tone")
    if tone:
        prefs_parts.append(f"- Tercih edilen ton: {tone}")
    
    # Emoji tercihi
    emoji_pref = perms.get("use_emoji")
    if emoji_pref is not None:
        if emoji_pref:
            prefs_parts.append("- Emoji kullanabilirsin")
        else:
            prefs_parts.append("- Emoji kullanma")
    
    # Uzunluk tercihi
    length_pref = perms.get("response_length")
    if length_pref:
        prefs_parts.append(f"- Yanit uzunlugu: {length_pref}")
    
    if prefs_parts:
        return "\nKULLANICI TERCIHLERI:\n" + "\n".join(prefs_parts) + "\n"
    
    return ""


def _get_toggle_context(toggles: Optional[Dict[str, bool]]) -> str:
    """
    Toggle durumlarindan context olusturur.
    
    Args:
        toggles: {"web": bool, "image": bool}
    
    Returns:
        str: Toggle context
    """
    if not toggles:
        return ""
    
    parts = []
    
    if toggles.get("web", True):
        parts.append(TOGGLE_WEB_ENABLED.strip())
    else:
        parts.append(TOGGLE_WEB_DISABLED.strip())
    
    if toggles.get("image", True):
        parts.append(TOGGLE_IMAGE_ENABLED.strip())
    else:
        parts.append(TOGGLE_IMAGE_DISABLED.strip())
    
    return "\n" + "\n".join(parts) + "\n"


def _get_safety_context(user: Optional["User"]) -> str:
    """
    Censorship level'a gore safety context olusturur.
    
    Args:
        user: User nesnesi
    
    Returns:
        str: Safety context
    """
    from app.auth.permissions import get_censorship_level
    
    level = get_censorship_level(user)
    
    if level == 0:  # UNRESTRICTED
        return SAFETY_UNRESTRICTED.strip()
    elif level == 2:  # STRICT
        return SAFETY_STRICT.strip()
    else:  # NORMAL (default)
        return SAFETY_NORMAL.strip()


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def build_system_prompt(
    user: Optional["User"] = None,
    persona_name: str = "standard",
    toggles: Optional[Dict[str, bool]] = None,
) -> str:
    """
    Yanitlama modeli icin system prompt'u derler.
    
    5 Katman:
        1. CORE_PROMPT - Sabit kurallar
        2. PERSONA_PROMPT - DB'den persona template
        3. USER_PREFS - Kullanici tercihleri
        4. TOGGLE_CONTEXT - Web/Image durumu
        5. SAFETY_CONTEXT - Guvenlik kurallari
    
    Args:
        user: User nesnesi
        persona_name: Aktif persona adi
        toggles: {"web": bool, "image": bool}
    
    Returns:
        str: Derlenmiş system prompt
    
    Example:
        >>> prompt = build_system_prompt(
        ...     user=user_obj,
        ...     persona_name="romantic",
        ...     toggles={"web": True, "image": False},
        ... )
    """
    parts = []
    
    # 1. Core Prompt (sabit)
    parts.append(CORE_PROMPT.strip())
    
    # 1.5 Output Contract (profesyonel format kuralları - CORE'dan hemen sonra)
    parts.append(OUTPUT_CONTRACT_PROFESSIONAL.strip())
    
    # 2. Persona Prompt (DB'den)
    persona_prompt = _get_persona_prompt(persona_name)
    if persona_prompt:
        parts.append(persona_prompt.strip())
    
    # 3. User Prefs
    user_prefs = _get_user_prefs_prompt(user)
    if user_prefs:
        parts.append(user_prefs.strip())
    
    # 4. Toggle Context
    toggle_ctx = _get_toggle_context(toggles)
    if toggle_ctx:
        parts.append(toggle_ctx.strip())
    
    # 5. Safety Context
    safety_ctx = _get_safety_context(user)
    if safety_ctx:
        parts.append(safety_ctx.strip())
    
    final_prompt = "\n\n".join(parts)
    
    logger.debug(f"[PROMPT_COMPILER] Prompt derlendi: persona={persona_name}, len={len(final_prompt)}")
    
    return final_prompt


def get_persona_initial_message(persona_name: str) -> Optional[str]:
    """
    Persona'nin initial_message'ini dondurur.
    
    NOT: Bu sadece YENi sohbet baslarken kullanilmali!
    
    Args:
        persona_name: Persona adi
    
    Returns:
        str veya None: Ilk mesaj
    """
    try:
        from app.core.dynamic_config import config_service
        
        persona = config_service.get_persona(persona_name)
        if persona:
            return persona.get("initial_message")
    except Exception as e:
        logger.warning(f"[PROMPT_COMPILER] Initial message alinamadi: {e}")
    
    return None



