import logging
from datetime import datetime
from typing import Optional

from sqlmodel import select

from app.core.database import get_session
from app.core.models import ConversationSummarySettings

logger = logging.getLogger(__name__)


def _build_default_settings() -> ConversationSummarySettings:
    """Varsayılan otomatik özetleme ayarlarını oluşturur (Agresif ayarlar)."""
    return ConversationSummarySettings(
        id=1,
        summary_enabled=True,
        summary_first_threshold=6,  # İlk özet 6 mesajdan sonra (önceki: 12)
        summary_update_step=6,  # Sonraki güncellemeler 6 mesajda bir (önceki: 10)
        summary_max_messages=60,  # LLM'e gönderilecek maksimum mesaj (önceki: 40)
    )


def get_summary_settings() -> ConversationSummarySettings:
    """DB'den özet ayarlarını okur. Yoksa varsayılanı kullanır."""
    with get_session() as session:
        try:
            settings = session.get(ConversationSummarySettings, 1)
            if not settings:
                logger.info("[CONFIG] Özet ayarları ilk kez oluşturuluyor...")
                settings = _build_default_settings()
                session.add(settings)
                session.commit()
                session.refresh(settings)
            return settings
        except Exception as e:
            logger.error(f"[CONFIG] Özet ayarları okunamadı, varsayılana düşüldü: {e}")
            # DB hatası durumunda bile sistemi kilitlememek için in-memory default
            return _build_default_settings()


def update_summary_settings(
    enabled: Optional[bool] = None,
    first_threshold: Optional[int] = None,
    update_step: Optional[int] = None,
    max_messages: Optional[int] = None,
) -> ConversationSummarySettings:
    """Otomatik özetleme ayarlarını günceller."""
    with get_session() as session:
        settings = session.get(ConversationSummarySettings, 1)
        if not settings:
            settings = _build_default_settings()
            session.add(settings)

        if enabled is not None:
            settings.summary_enabled = enabled
        if first_threshold is not None:
            settings.summary_first_threshold = first_threshold
        if update_step is not None:
            settings.summary_update_step = update_step
        if max_messages is not None:
            settings.summary_max_messages = max_messages

        settings.updated_at = datetime.utcnow()

        session.add(settings)
        session.commit()
        session.refresh(settings)

        logger.info(f"[CONFIG] Özet ayarları güncellendi: {settings}")
        return settings
