from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.core.logger import get_logger
from app.memory.conversation import get_conversation_summary_text, get_recent_context
from app.memory.rag import search_documents
from app.memory.store import search_memories
from app.services import user_preferences
from app.services.semantic_classifier import analyze_message_semantics

logger = get_logger(__name__)


# Yeni yardımcı: herhangi bir nesneyi güvenli şekilde dict'e çevirir
def _to_mapping(obj: Any) -> Optional[Dict]:
    try:
        if obj is None:
            return None
        return obj.dict() if hasattr(obj, "dict") else dict(obj)
    except Exception as e:
        logger.debug(f"[USER_CONTEXT] _to_mapping conversion failed: {e}")
        return None


async def build_user_context(
    username: str,
    message: str,
    conversation_id: Optional[str],
    semantic: Optional[dict],
    user: Any,
) -> Dict[str, Any]:
    """
    Kullanıcıya ait semantic + stil + hafıza + risk bilgisini tek pakette döndürür.
    Hata toleranslıdır; alt çağrılar başarısız olursa ilgili alan boş bırakılır.
    """
    context: Dict[str, Any] = {
        "semantic": None,
        "style_profile": {},
        "memory_blocks": {
            "recent": None,
            "summary": None,
            "personal": [],
            "rag_hits": [],
        },
        "risk_profile": {},
        "recent_messages": None,
    }

    # Semantic analiz yoksa yeniden çalıştır
    sem_obj = semantic
    if sem_obj is None:
        try:
            sem_obj = await analyze_message_semantics(message)
        except Exception as e:
            logger.error(f"[USER_CONTEXT] semantic analiz hatası: {e}")
            sem_obj = None
    # semantic objesini dict'e çevir (güvenli yardımcı kullanılarak)
    sem_dict = None
    try:
        if sem_obj:
            sem_dict = _to_mapping(sem_obj)
            context["semantic"] = sem_dict
    except Exception as e:
        logger.error(f"[USER_CONTEXT] semantic dict hatası: {e}")

    # Stil / tercih profili
    try:
        raw_prefs = user_preferences.get_effective_preferences(user.id) if user else {}
    except Exception as e:
        logger.error(f"[USER_CONTEXT] preferences okunamadı: {e}")
        raw_prefs = {}

    try:
        inferred = user_preferences.infer_style_from_message_and_semantic(message, sem_obj)
    except Exception as e:
        logger.error(f"[USER_CONTEXT] stil çıkarımı hatası: {e}")
        inferred = {}

    try:
        style_profile = user_preferences.merge_style_preferences(raw_prefs, inferred)
        context["style_profile"] = style_profile
    except Exception as e:
        logger.error(f"[USER_CONTEXT] stil birleştirme hatası: {e}")

    # Hafıza blokları
    mb = context["memory_blocks"]
    if conversation_id:
        try:
            summary = get_conversation_summary_text(conversation_id)
            if summary:
                mb["summary"] = summary
        except Exception as e:
            logger.error(f"[USER_CONTEXT] summary hatası: {e}")
        try:
            recent = get_recent_context(username, conversation_id, max_messages=4)
            if recent:
                mb["recent"] = recent
                context["recent_messages"] = recent
        except Exception as e:
            logger.error(f"[USER_CONTEXT] recent context hatası: {e}")

    try:
        memories = await search_memories(username, message, max_items=3)
        if memories:
            mb["personal"] = [m.text for m in memories if getattr(m, "text", None)]
    except Exception as e:
        logger.error(f"[USER_CONTEXT] personal memory hatası: {e}")

    try:
        rag_docs = search_documents(message, owner=username, max_items=2)
        if rag_docs:
            # Daha sağlam formatlama: metadata veya text eksikse güvenli davran
            hits = []
            for d in rag_docs:
                text = getattr(d, "text", "") or ""
                metadata = getattr(d, "metadata", {}) or {}
                filename = metadata.get("filename", "Doc")
                preview = (text[:400] + "...") if text else "(no text)"
                hits.append(f"{filename}: {preview}")
            mb["rag_hits"] = hits
    except Exception as e:
        logger.error(f"[USER_CONTEXT] RAG arama hatası: {e}")

    # Risk profili (basit türetim)
    try:
        domain = (sem_dict or {}).get("domain")
        risk_level = (sem_dict or {}).get("risk_level")
        risk_profile = {"domain": domain, "risk_level": risk_level}
        if risk_level == "high" and domain in {"finance", "health", "legal"}:
            risk_profile["caution"] = "high"
        elif risk_level == "medium":
            risk_profile["caution"] = "medium"
        else:
            risk_profile["caution"] = "low"
        context["risk_profile"] = risk_profile
    except Exception as e:
        logger.error(f"[USER_CONTEXT] risk profili hatası: {e}")

    return context
