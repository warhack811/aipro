"""
Merkezi Prompt Yönetimi
Zaman farkındalığı, persona ve kimlik katmanları burada üretilir.
"""
import locale
from datetime import datetime
from typing import Any, Dict, Optional

from app.ai.prompts.identity import get_ai_identity

# Türkçe tarih formatı için (destek yoksa sessiz geç)
try:
    locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")
except Exception:
    pass


def _time_context(now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    date_str = now.strftime("%d %B %Y, %A")
    time_str = now.strftime("%H:%M")
    return (
        f"🕒 ŞU ANKİ ZAMAN: {date_str} | Saat: {time_str}\n"
        "Kullanıcıya cevap verirken bu zamanı dikkate al. (Örn: Geceyse 'iyi geceler' de, sabahsa günaydın.)"
    )


def get_system_prompt(persona_settings: Dict[str, Any] | None = None) -> str:
    """
    Eski genel sistem prompt (kimlik/branding dinamik).
    """
    if persona_settings is None:
        persona_settings = {}

    identity = get_ai_identity()
    base_persona = (
        f"SEN '{identity.display_name}'sin. Sıradan bir bot değilsin, profesyonel bir AI Asistanısın.\n"
        f"KİMLİK: {identity.product_family} içinde konumlan, geliştirici: {identity.developer_name}.\n"
        "DİL: Akıcı ve doğal Türkçe kullan. Robotik kalıplardan ('Size nasıl yardımcı olabilirim') kaçın.\n"
        "KURALLAR:\n"
        "- Asla 'Ben bir yapay zekayım' diye cümleye başlama.\n"
        "- Kullanıcı kısa yazarsa kısa, detay isterse detaylı cevap ver.\n"
    )

    tone = persona_settings.get("tone")
    if tone == "serious":
        base_persona += "\nTON: Ciddi ve resmi ol. Emoji kullanma."
    elif tone == "humorous":
        base_persona += "\nTON: Esprili ve eğlenceli ol, uygun yerde espri yap."
    elif tone == "sarcastic":
        base_persona += "\nTON: Hafif iğneleyici ve sarkastik bir ton kullan."

    return f"{base_persona}\n\n{_time_context()}"


def get_groq_system_prompt_tr(
    identity: Any,
    persona_settings: Dict[str, Any] | None = None,
    now_iso: str | None = None,
    semantic: Dict[str, Any] | None = None,
) -> str:
    """
    Groq için güvenli, profesyonel, Türkçe system prompt.
    İsimler/marka dinamik kimlikten gelir.
    """
    if persona_settings is None:
        persona_settings = {}

    now = datetime.fromisoformat(now_iso) if now_iso else datetime.now()
    date_str = now.strftime("%d %B %Y, %A")
    time_str = now.strftime("%H:%M")

    tone = persona_settings.get("tone") or "samimi"
    detail_level = persona_settings.get("detail_level") or "dengeli"
    use_emoji = persona_settings.get("use_emoji") == "true"
    emoji_note = "Emoji az ve yerinde kullan." if use_emoji else "Emoji kullanma."

    sem = semantic or {}
    domain = sem.get("domain") or "general"
    risk = sem.get("risk_level") or "low"
    sens = ", ".join(sem.get("sensitivity") or []) or "none"
    advice = sem.get("advice_type") or "none"

    advice_note = ""
    if advice == "general_guidance":
        advice_note = "- Genel yol göster: mantıklı seçenekleri açıkla, kullanıcıya karar alanı bırak.\n"
    elif advice == "strong_guidance":
        advice_note = "- Net fikir ver: en mantıklı 1-2 seçeneği belirt, nedenlerini kısa söyle.\n"
    elif advice == "high_risk_personal_decision":
        advice_note = "- Dürüst ol, analiz yap, senaryo çıkar, son kararı kullanıcıya bırak. Kısa feragat ekle: 'Son karar sana ait.'\n"

    return (
        f"Sen {identity.display_name}'sin. Türkçe konuşursun, profesyonel ve güvenlisin.\n"
        f"Tarih/Saat: {date_str} - {time_str}\n"
        f"Ton: {tone}, Detay: {detail_level}. {emoji_note}\n"
        f"Semantik: domain={domain}, risk={risk}, sensitivity={sens}, advice={advice}\n"
        "- Kısa ve net cümleler kur; bilgi verici ve öğretici ol.\n"
        "- Kaynak/RAG/İnternet bilgisi kullanabilirsin; metni kısalt, listeyi şişirme.\n"
        "- Gereksiz özür dileme; bilmediğinde dürüstçe söyle.\n"
        "- Yatırım/sağlık/hukuk yüksek riskte karar verme; analiz et, riskleri belirt, yönlendir ama son kararı kullanıcıya bırak.\n"
        f"{advice_note}"
    )


def get_bela_system_prompt_tr_uncensored(
    identity: Any,
    persona_settings: Dict[str, Any] | None = None,
    now_iso: str | None = None,
    semantic: Dict[str, Any] | None = None,
) -> str:
    """
    Bela (Gemma 2 9B uncensored) için doğal, daha özgür Türkçe system prompt.
    Yasal/güvenlik sınırlarını ihlal etmez; suç yönlendirmesi vermez.
    """
    if persona_settings is None:
        persona_settings = {}

    now = datetime.fromisoformat(now_iso) if now_iso else datetime.now()
    date_str = now.strftime("%d %B %Y, %A")
    time_str = now.strftime("%H:%M")

    tone = persona_settings.get("tone") or "doğal"
    use_emoji = persona_settings.get("use_emoji") == "true"
    emoji_note = "Emoji kullanabilirsin ama abartma." if use_emoji else "Emoji kullanma."

    sem = semantic or {}
    domain = sem.get("domain") or "general"
    risk = sem.get("risk_level") or "low"
    sens = ", ".join(sem.get("sensitivity") or []) or "none"
    advice = sem.get("advice_type") or "none"

    advice_note = ""
    if advice == "general_guidance":
        advice_note = "- Açık konuş, mantıklı yolları öner; 'ben olsam' perspektifiyle paylaş.\n"
    elif advice == "strong_guidance":
        advice_note = "- Net tavır al: en makul seçeneği söyle, nedenlerini belirt; arkadaşça ama yönlendirici ol.\n"
    elif advice == "high_risk_personal_decision":
        advice_note = "- Dürüstçe fikrini söyle, senaryoları anlat, riskleri belirt; son kararın kullanıcıda olduğunu kısa bir cümleyle hatırlat.\n"

    return (
        f"Sen {identity.display_name}'sin; Türkçe, insansı ve filtrelenmemiş bir arkadaş gibi konuş.\n"
        f"Tarih/Saat: {date_str} - {time_str}\n"
        f"Ton: {tone}. {emoji_note}\n"
        f"Semantik: domain={domain}, risk={risk}, sensitivity={sens}, advice={advice}\n"
        "- Din/siyaset/cinsellik/argo dahil doğal konuş, ama yasa dışı zarar yönlendirmesi yapma.\n"
        "- Sansürsüz hissettir; kaçınma, lafı dolandırma, direkt cevap ver.\n"
        "- Sağlık/finans/hukuk yüksek riskte zarar verici talimat verme; genel bilgi ve yönlendirme yap, 'son adım sana ait' vurgula.\n"
        f"{advice_note}"
    )
