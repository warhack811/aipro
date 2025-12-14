from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional

from app.core.prompts import (
    get_groq_system_prompt_tr,
    get_bela_system_prompt_tr_uncensored,
)


def _format_context_block(title: str, content: str) -> str:
    return f"### {title}\n{content.strip()}"


def build_model_prompt(
    provider: str,
    identity: Any,
    user_preferences: Dict[str, Any],
    context_blocks: Dict[str, Optional[str]],
    user_message: str,
    now_iso: Optional[str] = None,
    semantic: Optional[Dict[str, Any]] = None,
    user_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Tek merkezli prompt derleyici.
    - provider: 'groq' veya 'bela'
    - identity: core.identity.get_ai_identity() sonucu
    - user_preferences: ton/dil/tema vb. kullanıcı tercihleri
    - context_blocks: summary/memory/rag/recent gibi bloklar
    - user_message: ham kullanıcı mesajı
    """
    provider = (provider or "groq").lower()
    now_iso = now_iso or datetime.utcnow().isoformat()

    if provider == "bela":
        system_prompt = get_bela_system_prompt_tr_uncensored(identity, user_preferences, now_iso=now_iso, semantic=semantic)
    else:
        system_prompt = get_groq_system_prompt_tr(identity, user_preferences, now_iso=now_iso, semantic=semantic)
    
    # PLUGIN: Response Enhancement - Prompt'a formatlama talimatları ekle
    try:
        from app.plugins import get_plugin
        from app.plugins.response_enhancement.plugin import ResponseEnhancementPlugin
        
        plugin = get_plugin("response_enhancement")
        if plugin and plugin.is_enabled():
            # Type-safe casting for ResponseEnhancementPlugin
            if isinstance(plugin, ResponseEnhancementPlugin):
                system_prompt = plugin.enhance_prompt(
                    base_prompt=system_prompt,
                    context={"user_message": user_message}
                )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[PROMPT_ENGINE] Plugin enhancement failed: {e}")

    followup_rules = (
        "\n\n"
        "FOLLOWUPS INSTRUCTIONS:\n"
        "- Produce the normal answer first.\n"
        "- At the very end of the same line (no newline), append: "
        'FOLLOWUPS_JSON: {\"followups\":[\"q1\",\"q2\"],\"example\":\"sample sentence\"}\n'
        "- Use the keyword FOLLOWUPS_JSON only for this JSON block.\n"
        "- JSON must be single-line, no comments, no extra text.\n"
        "- If you cannot create followups, return FOLLOWUPS_JSON: {\"followups\":[],\"example\":\"\"}.\n"
        "- Do NOT include the word FOLLOWUPS_JSON inside the main answer text.\n"
        "- Use the user's language for the questions and example.\n"
    )
    system_prompt = system_prompt + followup_rules

    ordered_blocks = []
    summary = context_blocks.get("summary")
    if summary:
        ordered_blocks.append(_format_context_block("SOHBET ÖZETİ", summary))
    
    memory = context_blocks.get("memory")
    if memory:
        ordered_blocks.append(_format_context_block("KİŞİSEL HAFIZA", memory))
    
    rag = context_blocks.get("rag")
    if rag:
        ordered_blocks.append(_format_context_block("DOKÜMAN BİLGİSİ", rag))
    
    recent = context_blocks.get("recent")
    if recent:
        ordered_blocks.append(_format_context_block("SON MESAJLAR", recent))

    context_text = "\n\n".join(ordered_blocks) if ordered_blocks else ""

    return {
        "system_prompt": system_prompt,
        "context": context_text,
        "user_message": user_message,
    }
