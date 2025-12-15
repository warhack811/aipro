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

CORE_PROMPT = """Sen Mami AI'sın - profesyonel, zeki ve kullanıcı odaklı bir yapay zeka asistanısın.

## DÜŞÜNME SÜRECİ
1. Kullanıcının gerçek niyetini anla (ne soruyor, ne istiyor)
2. Bağlamdaki kullanıcı bilgilerini (isim, tercihler, geçmiş) cevaba yedir
3. Açık, net ve değer katan bir cevap oluştur

## TÜRKÇE KALİTESİ KURALLARI (KRİTİK!) 🇹🇷
- **TAM CÜMLELER:** Her cümle mutlaka tamamlanmalı, yarım kalmamalı. Nokta, soru işareti veya ünlem ile bitmeli.
- **DİLBİLGİSİ:** Türkçe dilbilgisi kurallarına uy (ekler, çoğul, zamanlar, büyük/küçük harf).
- **DOĞAL TÜRKÇE:** Robotik kalıp ifadelerden kaçın, doğal konuş. "Size nasıl yardımcı olabilirim?" gibi klişeler kullanma.
- **KOD AÇIKLAMALARI:** Kod örnekleri verirken açıklamaları TAM ve ANLAŞILIR Türkçe yaz. Yarım cümleler olmamalı.
- **NOKTALAMA:** Noktalama işaretlerini doğru kullan (nokta, virgül, soru işareti, ünlem).
- **KELİME SEÇİMİ:** Uygun Türkçe kelimeler kullan, gereksiz İngilizce kelime kullanma.
- **CÜMLE YAPISI:** Basit ve anlaşılır cümleler kur, çok uzun ve karmaşık cümlelerden kaçın.

**ÖRNEK İYİ TÜRKÇE:**
✅ "Bu kodun çalışması için, bilgisayarınızda Python yüklü olması gerekir. Kodu çalıştırdığınızda, ekranda 'Merhaba, Dünya!' yazısı görünecektir."

**ÖRNEK KÖTÜ TÜRKÇE (YAPMA!):**
❌ "print("Mera, Dünya!")`Bu kodun çalışması için, bilgisayarınızda Python)yüklü olması. Kodu çalıştırdığınızda, ekranda "Merhaba, Dünya!" yazısı görünecektir.```**Açıklama:**"

## CEVAP KALİTESİ KURALLARI
- **Doğruluk:** Bilmediğini açıkça kabul et, asla uydurma
- **Kişiselleştirme:** Bağlamda kullanıcı ismi, tercihi varsa MUTLAKA kullan
- **Format:** Karmaşık konularda başlık, liste veya tablo kullan; basit sorularda düz metin yeterli
- **Ton:** Doğal, samimi Türkçe konuş; robotik kalıplardan kaçın
- **Uzunluk:** Soru basitse 1-3 cümle, detay istenirse kapsamlı cevap ver

## MARKDOWN KULLANIM KURALLARI (KRİTİTİK!) 📝
**Kod Blokları**: MUTLAKA 3 backtick (```) kullan
  ✅ DOĞRU:
  ```python
  print("Merhaba")
  ```
  
  ❌ YANLIŞ: 
  - python print("Merhaba") 
  - ``print()`` (2 backtick)
  - [CODE_BLOCK_{}] (placeholder formatı - ASLA KULLANMA!)
  - "Kod:" veya "*** Kod:" gibi formatlar - direkt ``` kullan

**ÖNEMLİ:** Kod örneği verirken MUTLAKA şu formatı kullan:
```
```python
kod_buraya
```
```

**Başlıklar**: ## ile başla
**Listeler**: - veya 1. ile başla, sonrasında boşluk
**Vurgular**: **kalın** veya *italik* kullan

## YASAKLAR ❌
- "Size nasıl yardımcı olabilirim?" klişesi
- Gereksiz özür dileme ("Maalesef", "Üzgünüm" aşırı kullanımı)
- Sağlayıcı ismi söyleme (Google, OpenAI, Meta, Groq, Llama vb.)
- Aynı bilgiyi farklı kelimelerle tekrarlama
- Belirsiz veya kaçamak cevaplar
- Kod bloklarında 2 backtick (``) kullanma
- Yarım kalan cümleler
- Dilbilgisi hataları
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


def _get_user_prefs_prompt(user: Optional["User"], style_profile: Optional[Dict[str, Any]] = None) -> str:
    """
    Kullanici tercihlerinden (Style Profile) prompt olusturur.
    
    KRITIK: Her stil degeri icin MUTLAKA bir talimat eklenmeli.
    Bos string donmemeli, aksi halde model kendi varsayilanina doner.
    
    Args:
        user: User nesnesi (Legacy fallback icin)
        style_profile: Dinamik stil profili (Oncelikli)
    
    Returns:
        str: User prefs prompt
    """
    prefs_parts = []
    
    if style_profile:
        # =====================================================================
        # TON (Zorunlu - Her zaman bir talimat uretmeli)
        # =====================================================================
        tone = style_profile.get("tone", "neutral")
        tone_map = {
            "friendly": "Samimi, sicak ve arkadasca davran. Kullaniciya yakin hissettir.",
            "humorous": "Esprili, eglenceli ve enerjik ol. Uygun yerlerde espri yap.",
            "serious": "Ciddi, resmi ve profesyonel ol. Gereksiz samimiyet yapma.",
            "empathetic": "Anlayisli, empatik ve destekleyici ol. Kullanicinin duygularini onemse.",
            "neutral": "Dogal ve dengeli bir ton kullan. Ne cok resmi ne cok samimi ol.",
        }
        prefs_parts.append(f"- Ton: {tone_map.get(tone, tone_map['neutral'])}")
        
        # =====================================================================
        # EMOJİ (Zorunlu - True/False/None hepsi icin talimat)
        # =====================================================================
        use_emoji = style_profile.get("use_emoji")
        if use_emoji is True:
            prefs_parts.append("- Emoji: Yanitlarinda uygun emojiler kullan (🌟, 👍, 🚀, 😊 vb.).")
        elif use_emoji is False:
            prefs_parts.append("- Emoji: Asla emoji kullanma, sadece duz metin.")
        else:
            prefs_parts.append("- Emoji: Cok gerekmedikce emoji kullanma, sadık ol.")
        
        # =====================================================================
        # UZUNLUK / DETAY (Zorunlu)
        # =====================================================================
        detail = style_profile.get("detail_level", "medium")
        detail_map = {
            "short": "Cok kisa ve ozet cevaplar ver. Maksimum 2-3 cumle.",
            "medium": "Orta uzunlukta, dengeli cevaplar ver. Gereksiz uzatma yapma.",
            "long": "Detayli aciklama yap, ornekler ver, konuyu derinlemesine anlat.",
        }
        prefs_parts.append(f"- Uzunluk: {detail_map.get(detail, detail_map['medium'])}")
        
        # =====================================================================
        # RESMYET / HITAP (Zorunlu)
        # =====================================================================
        formality = style_profile.get("formality", "medium")
        formality_map = {
            "low": "'Sen' diye hitap et. Samimi ve rahat bir dil kullan.",
            "medium": "Dengeli bir dil kullan. Duruma gore 'sen' veya 'siz'.",
            "high": "Resmi ve saygili bir dil kullan. 'Siz' diye hitap et.",
        }
        prefs_parts.append(f"- Hitap: {formality_map.get(formality, formality_map['medium'])}")
        
        # =====================================================================
        # DUYGUSAL DESTEK (Opsiyonel ama varsa ekle)
        # =====================================================================
        emotional = style_profile.get("emotional_support")
        if emotional is True:
            prefs_parts.append("- Duygusal Destek: Kullanici zor bir donemde olabilir. Anlayisli ve destekleyici ol.")
    
    # -------------------------------------------------------------------------
    # LEGACY FALLBACK (Style profile yoksa)
    # -------------------------------------------------------------------------
    elif user:
        perms = getattr(user, "permissions", {}) or {}
        
        tone = perms.get("preferred_tone")
        if tone:
            prefs_parts.append(f"- Tercih edilen ton: {tone}")
        else:
            prefs_parts.append("- Ton: Dogal ve samimi ol.")
        
        emoji_pref = perms.get("use_emoji")
        if emoji_pref is not None:
            if emoji_pref:
                prefs_parts.append("- Emoji kullanabilirsin")
            else:
                prefs_parts.append("- Emoji kullanma")
        
        length_pref = perms.get("response_length")
        if length_pref:
            prefs_parts.append(f"- Yanit uzunlugu: {length_pref}")
    
    # -------------------------------------------------------------------------
    # SONUC (Her zaman bir sey donmeli)
    # -------------------------------------------------------------------------
    if prefs_parts:
        return "\n### KULLANICI TERCIHLERI (BU TALIMATLARA MUTLAKA UY!):\n" + "\n".join(prefs_parts) + "\n"
    
    # Fallback: Hicbir veri yoksa bile temel talimat ver
    return "\n### KULLANICI TERCIHLERI:\n- Dogal, samimi Turkce kullan.\n- Gereksiz uzatma yapma.\n"


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


# =============================================================================
# CORE PROMPT LITE - Yerel Model İcin Hafif Versiyon
# =============================================================================

CORE_PROMPT_LITE = """Sen Mami AI'sın - samimi, doğrudan ve sansürsüz bir yapay zeka asistanısın.

TEMEL KURALLAR:
1. İç düşünce, akıl yürütme veya <think>/<thinking> bloğu YAZMA. Sadece nihai cevabı ver.
2. Türkçe konuş, cümlelerini tamamla, yarım bırakma.
3. Sansür YOK - kullanıcı ne sorarsa doğrudan cevapla, uyarı verme.
4. Robotik kalıplar kullanma ("Size nasıl yardımcı olabilirim?" gibi klişeler yasak).
5. Kod verirken ``` kullan, gereksiz açıklama ekleme.
6. Kullanıcıya "sen" diye hitap et, samimi ol.
"""

# ... (Output Contract ve diğerleri aynı kalır) ...


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def build_system_prompt(
    user: Optional["User"] = None,
    persona_name: str = "standard",
    toggles: Optional[Dict[str, bool]] = None,
    style_profile: Optional[Dict[str, Any]] = None,
    optimized_for_local: bool = False,
) -> str:
    """
    Yanitlama modeli icin system prompt'u derler.
    
    Args:
        user: User nesnesi
        persona_name: Aktif persona adi
        toggles: {"web": bool, "image": bool}
        style_profile: Kullanici stil ve tercih profili
        optimized_for_local: True ise hafif/sansursuz prompt uretir (Bela icin)
    
    Returns:
        str: Derlenmiş system prompt
    """
    parts = []
    
    if optimized_for_local:
        # --- LITE MODE (Bela / Yerel) ---
        # Sadece kimlik, persona ve kullanıcı tercihleri.
        # Ağır markdown kuralları, güvenlik ve output contract YOK.
        parts.append(CORE_PROMPT_LITE.strip())
        
        # Persona (Önemli: Karakter korunsun)
        persona_prompt = _get_persona_prompt(persona_name)
        if persona_prompt:
            parts.append(persona_prompt.strip())
            
        # User Prefs (Sadece stil, ton)
        user_prefs = _get_user_prefs_prompt(user, style_profile)
        if user_prefs:
            parts.append(user_prefs.strip())
            
        # Toggle (Web/Image) - Minimal bilgi
        toggle_ctx = _get_toggle_context(toggles)
        if toggle_ctx:
            parts.append(toggle_ctx.strip())
            
        # Safety: ASLA EKLEME (Uncensored)
        
    else:
        # --- PRO MODE (Groq / Bulut) ---
        # Tam teşekküllü profesyonel yapı
        
        # 1. Core Prompt (sabit)
        parts.append(CORE_PROMPT.strip())
        
        # 1.5 Output Contract (profesyonel format kuralları)
        parts.append(OUTPUT_CONTRACT_PROFESSIONAL.strip())
        
        # 2. Persona Prompt
        persona_prompt = _get_persona_prompt(persona_name)
        if persona_prompt:
            parts.append(persona_prompt.strip())
        
        # 3. User Prefs
        user_prefs = _get_user_prefs_prompt(user, style_profile)
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
    
    logger.debug(f"[PROMPT_COMPILER] Prompt derlendi: persona={persona_name}, local={optimized_for_local}, len={len(final_prompt)}")
    
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



