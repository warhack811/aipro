from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from sqlalchemy import desc
from sqlmodel import select

from app.core.database import get_session
from app.core.models import UserPreference

logger = logging.getLogger(__name__)


def get_user_preferences(
    user_id: int,
    category: Optional[str] = None,
    include_inactive: bool = False,
) -> List[UserPreference]:
    """Belirli bir kullanıcının tercih listesini döndürür."""
    with get_session() as db:
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)

        if category is not None:
            stmt = stmt.where(UserPreference.category == category)

        if not include_inactive:
            stmt = stmt.where(UserPreference.is_active == True)

        stmt = stmt.order_by(desc(cast(Any, UserPreference.updated_at)))
        return list(db.exec(stmt).all())


def get_user_preference(
    user_id: int,
    key: str,
    category: Optional[str] = None,
    only_active: bool = True,
) -> Optional[UserPreference]:
    """Belirli bir tercihi döndürür."""
    with get_session() as db:
        stmt = select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.key == key,
        )

        if category is not None:
            stmt = stmt.where(UserPreference.category == category)

        if only_active:
            stmt = stmt.where(UserPreference.is_active == True)

        stmt = stmt.order_by(desc(cast(Any, UserPreference.updated_at)))
        return db.exec(stmt).first()


def set_user_preference(
    user_id: int,
    key: str,
    value: str,
    category: str = "system",
    source: str = "explicit",
) -> UserPreference:
    """Bir kullanıcı tercihini ayarlar (upsert: Önceki aktif kayıtları pasife çeker)."""
    now = datetime.utcnow()

    with get_session() as db:
        try:
            # Mevcut aktif kayıtları pasife çek
            stmt = select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.key == key,
            )
            if category:
                stmt = stmt.where(UserPreference.category == category)

            existing_items = list(db.exec(stmt).all())

            for pref in existing_items:
                if pref.is_active:
                    pref.is_active = False
                    pref.updated_at = now
                    db.add(pref)

            # Yeni aktif kaydı oluştur
            new_pref = UserPreference(
                user_id=user_id,
                key=key,
                value=str(value),
                category=category or "system",
                source=source or "explicit",
                is_active=True,
                updated_at=now,
            )
            db.add(new_pref)
            db.commit()
            db.refresh(new_pref)

            logger.info(
                "[PREF] set_user_preference: user_id=%s key=%s value=%s",
                user_id,
                key,
                value,
            )

            return new_pref

        except Exception as exc:
            db.rollback()
            logger.error("[PREF] set_user_preference hatası: %s", exc)
            raise


def deactivate_user_preference(
    user_id: int,
    key: str,
    category: Optional[str] = None,
) -> int:
    """Belirli bir tercihi pasif hale getirir (Soft Delete)."""
    now = datetime.utcnow()
    affected = 0

    with get_session() as db:
        try:
            stmt = select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.key == key,
                UserPreference.is_active == True,
            )
            if category is not None:
                stmt = stmt.where(UserPreference.category == category)

            items = list(db.exec(stmt).all())
            for pref in items:
                pref.is_active = False
                pref.updated_at = now
                db.add(pref)
                affected += 1

            if affected:
                db.commit()
            return affected

        except Exception as exc:
            db.rollback()
            logger.error("[PREF] deactivate_user_preference hatası: %s", exc)
            raise


def get_effective_preferences(
    user_id: int,
    category: Optional[str] = None,
) -> Dict[str, str]:
    """Kullan?c?n?n aktif ve en g?ncel tercihlerini (key -> value) d?nd?r?r."""
    result: Dict[str, UserPreference] = {}

    with get_session() as db:
        stmt = select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.is_active == True,
        )
        if category is not None:
            stmt = stmt.where(UserPreference.category == category)

        # En yeni kayıt en önde (Aynı key için sadece en yenisi alınır)
        stmt = stmt.order_by(desc(cast(Any, UserPreference.updated_at)))
        items = list(db.exec(stmt).all())

        for pref in items:
            if pref.key not in result:
                result[pref.key] = pref

    return {key: pref.value for key, pref in result.items()}


# --- Modernize edilmiş stil çıkarımı ve birleştirme (son tanımlar geçerlidir) ---


def _infer_style_v2(message: str, semantic: Any) -> Dict[str, Any]:
    defaults = {
        "tone": "neutral",
        "formality": "medium",
        "detail_level": "medium",
        "use_emoji": False,
        "emotional_support": False,
        "caution_level": "medium",
    }
    try:
        lowered = (message or "").lower()
        words = lowered.split()
        getter = semantic or {}
        if isinstance(semantic, dict):
            s_get = semantic.get
        else:
            s_get = lambda k, default=None: getattr(semantic, k, default)
        intent = s_get("intent_type", "") or s_get("intent_type", "") or ""
        domain = s_get("domain", "") or s_get("domain", "") or ""
        risk_level = s_get("risk_level", "") or s_get("risk_level", "") or ""

        detail = defaults["detail_level"]
        if "detayl" in lowered or "uzun anlat" in lowered or "acik acik" in lowered or len(words) > 30:
            detail = "long"
        elif len(words) <= 8 and "?" in message:
            detail = "short"

        tone = defaults["tone"]
        formality = defaults["formality"]
        emotional = defaults["emotional_support"]
        caution = defaults["caution_level"]

        emoji_found = bool(re.search(r"[\U0001F600-\U0001F64F]:\)|:\(|;\\)", message))

        emotional_cues = ["kotu hissediyorum", "moralim bozuk", "uzgunum", "yardim et", "cok zor", "stresliyim"]
        if any(cue in lowered for cue in emotional_cues) or "emotional" in intent:
            emotional = True
            tone = "friendly"
            formality = "low"

        if domain in {"finance", "legal", "health"}:
            formality = "high" if "acil" in lowered else "medium"
            if tone == "neutral":
                tone = "serious"
            caution = "high" if risk_level == "high" else "medium"
        elif risk_level == "high":
            caution = "high"

        if message.count("!") >= 2 and domain not in {"finance", "legal", "health"}:
            tone = "friendly" if tone == "neutral" else tone
            formality = "low"

        return {
            "tone": tone or defaults["tone"],
            "formality": formality or defaults["formality"],
            "detail_level": detail,
            "use_emoji": emoji_found,
            "emotional_support": emotional,
            "caution_level": caution,
        }
    except Exception as e:
        logger.debug(f"[STYLE_INFER_V2] Style inference failed: {e}")
        return defaults.copy()


def infer_style_from_message_and_semantic(message: str, semantic: Any) -> Dict[str, Any]:
    """Override: gelişmiş stil çıkarımı."""
    return _infer_style_v2(message, semantic)


def merge_style_preferences(user_prefs: Dict[str, Any], inferred: Dict[str, Any]) -> Dict[str, Any]:
    """Override: explicit > inferred; yeni alanları da kapsar."""
    result = inferred.copy()
    if user_prefs:
        tone = user_prefs.get("tone")
        if tone:
            result["tone"] = tone
        formality = user_prefs.get("formality")
        if formality:
            result["formality"] = formality
        detail = user_prefs.get("detail_level") or user_prefs.get("answer_length")
        if detail:
            result["detail_level"] = detail
        use_emoji = user_prefs.get("use_emoji")
        if use_emoji is not None:
            result["use_emoji"] = str(use_emoji).lower() == "true"
        emotional_support = user_prefs.get("emotional_support")
        if emotional_support is not None:
            result["emotional_support"] = str(emotional_support).lower() == "true"
        caution = user_prefs.get("caution_level") or user_prefs.get("risk_tolerance")
        if caution:
            result["caution_level"] = caution
    return result


# --- Response Formatting Preferences (YENİ) ---


def get_user_formatting_preferences(user_id: int) -> Dict[str, Any]:
    """
    Kullanıcının response formatting tercihlerini döndürür.

    Returns:
        Format ayarları dictionary'si (response_processor için)
    """
    prefs = get_effective_preferences(user_id, category="formatting")

    # Varsayılan değerler
    defaults = {
        "format_level": "rich",  # minimal, normal, rich
        "enable_markdown": True,
        "enable_code_enhancement": True,
        "enable_beautification": True,
        "enable_data_formatting": True,
        "add_emojis": True,
        "callout_boxes": True,
        "turkish_optimization": True,
    }

    # Kullanıcı tercihlerini uygula
    result = defaults.copy()

    if "format_level" in prefs:
        result["format_level"] = prefs["format_level"]

    # Boolean değerleri parse et
    for key in [
        "enable_markdown",
        "enable_code_enhancement",
        "enable_beautification",
        "enable_data_formatting",
        "add_emojis",
        "callout_boxes",
        "turkish_optimization",
    ]:
        if key in prefs:
            result[key] = str(prefs[key]).lower() in ("true", "1", "yes")

    logger.debug(f"[FORMATTING_PREFS] User {user_id}: {result}")
    return result


def set_user_formatting_preference(
    user_id: int,
    key: str,
    value: Any,
) -> UserPreference:
    """
    Kullanıcının bir formatting tercihini ayarlar.

    Args:
        user_id: Kullanıcı ID
        key: Tercih anahtarı (format_level, add_emojis, vb.)
        value: Tercih değeri

    Returns:
        Oluşturulan UserPreference
    """
    return set_user_preference(
        user_id=user_id,
        key=key,
        value=str(value),
        category="formatting",
        source="explicit",
    )
