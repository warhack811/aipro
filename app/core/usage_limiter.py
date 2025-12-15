"""
Mami AI - Kullanım Limitleri Yönetimi
=====================================

Bu modül, kullanıcı başına istek limitlerini yönetir:
- Günlük Groq API çağrı limiti
- Günlük yerel model çağrı limiti
- Dakikalık mesaj limiti (spam koruması)

Kullanım:
    from app.core.usage_limiter import limiter
    
    # İstek öncesi kontrol (hata fırlatır)
    limiter.check_limits_pre_flight(user_id)
    
    # İstek sonrası kullanım kaydı
    limiter.consume_usage(user_id, reply_content)

Limitler:
    - LIMIT_GROQ_DAILY: 500 istek/gün
    - LIMIT_LOCAL_DAILY: 2000 istek/gün
    - LIMIT_CHAT_PER_MINUTE: 30 mesaj/dakika
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import func, select

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# LİMİT SABİTLERİ
# =============================================================================

# Günlük limitler
LIMIT_GROQ_DAILY: int = 500       # Groq API günlük istek limiti
LIMIT_LOCAL_DAILY: int = 2000     # Yerel model günlük istek limiti

# Spam koruması
LIMIT_CHAT_PER_MINUTE: int = 30   # Dakikalık maksimum mesaj sayısı


# =============================================================================
# KULLANIM LİMİTLEYİCİ SINIFI
# =============================================================================

class UsageLimiter:
    """
    Kullanım limitlerini kontrol eden ve sayaçları yöneten servis.
    
    Bu sınıf:
    - İstek öncesi limit kontrolü yapar
    - İstek sonrası kullanımı kaydeder
    - Günlük sayaçları yönetir
    
    Kullanım:
        >>> limiter.check_limits_pre_flight(user_id)  # HTTPException fırlatabilir
        >>> # ... işlem ...
        >>> limiter.consume_usage(user_id, "[GROQ] Yanıt...")
    """

    @staticmethod
    def _get_today_utc() -> date:
        """
        UTC olarak bugünün tarihini döndürür.
        
        Returns:
            date: Bugünün UTC tarihi
        """
        return datetime.utcnow().date()

    @staticmethod
    def _get_database_imports():
        """
        Veritabanı bağımlılıklarını lazy import eder.
        
        Import döngüsünü önlemek için kullanılır.
        """
        try:
            from app.core.database import get_session
            from app.core.models import Conversation, Message, UsageCounter
        except ImportError:
            # Eski import yolu (geçiş dönemi)
            from app.core.database import get_session
            from app.core.models import Conversation, Message, UsageCounter
        return get_session, UsageCounter, Message, Conversation

    @staticmethod
    def get_or_create_counter(user_id: int):
        """
        Bugün için kullanıcının sayaç kaydını getirir veya oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
        
        Returns:
            UsageCounter: Kullanıcının bugünkü sayaç kaydı
        """
        get_session, UsageCounter, _, _ = UsageLimiter._get_database_imports()
        today = UsageLimiter._get_today_utc()

        with get_session() as session:
            stmt = select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.usage_date == today,
            )
            counter = session.exec(stmt).first()

            if counter:
                return counter

            # Yoksa yeni oluştur
            counter = UsageCounter(user_id=user_id, usage_date=today)
            session.add(counter)
            session.commit()
            session.refresh(counter)
            return counter

    @staticmethod
    def check_limits_pre_flight(user_id: int) -> None:
        """
        İstek işlenmeden ÖNCE limitleri kontrol eder.
        
        Kontroller:
        1. Dakikalık mesaj limiti (spam koruması)
        2. Günlük toplam limit (Groq + Local)
        
        Args:
            user_id: Kullanıcı ID'si
        
        Raises:
            HTTPException: Limit aşıldığında 429 Too Many Requests
        
        Example:
            >>> try:
            ...     limiter.check_limits_pre_flight(user_id)
            ... except HTTPException as e:
            ...     print(f"Limit aşıldı: {e.detail}")
        """
        get_session, UsageCounter, Message, Conversation = UsageLimiter._get_database_imports()
        
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)

        # 1) Dakikalık limit kontrolü
        with get_session() as session:
            query = (
                select(func.count())
                .select_from(Message)
                .join(Conversation)
                .where(
                    Conversation.user_id == user_id,
                    Message.created_at >= one_minute_ago,
                    Message.role == "user",
                )
            )
            count_last_min = session.exec(query).one()

            if count_last_min >= LIMIT_CHAT_PER_MINUTE:
                logger.warning(
                    f"[LIMITER] Dakikalık limit aşıldı: user={user_id} "
                    f"count={count_last_min}/{LIMIT_CHAT_PER_MINUTE}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Çok hızlı mesaj gönderiyorsunuz. Lütfen biraz bekleyin.",
                )

        # 2) Günlük toplam limit kontrolü
        counter = UsageLimiter.get_or_create_counter(user_id)
        total_limit = LIMIT_GROQ_DAILY + LIMIT_LOCAL_DAILY

        if counter.total_chat_count >= total_limit:
            logger.warning(
                f"[LIMITER] Günlük limit aşıldı: user={user_id} "
                f"count={counter.total_chat_count}/{total_limit}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Günlük toplam mesaj limitinize ulaştınız.",
            )

    @staticmethod
    def consume_usage(user_id: int, engine: str = "groq") -> None:
        """
        İşlem tamamlandıktan sonra kullanımı kaydeder.
        
        Engine parametresine göre ilgili sayaç artırılır:
        - "groq": groq_count artırılır
        - "local": local_count artırılır
        - Her durumda total_chat_count artırılır
        
        Args:
            user_id: Kullanıcı ID'si
            engine: Model engine tipi ("groq" veya "local")
        
        Example:
            >>> limiter.consume_usage(user_id, engine="groq")
            >>> limiter.consume_usage(user_id, engine="local")
        """
        get_session, UsageCounter, _, _ = UsageLimiter._get_database_imports()
        today = UsageLimiter._get_today_utc()

        # Engine tipine göre sayaç artır
        is_groq = engine == "groq"
        is_local = engine == "local"

        with get_session() as session:
            stmt = select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.usage_date == today,
            )
            counter = session.exec(stmt).first()

            if not counter:
                counter = UsageCounter(user_id=user_id, usage_date=today)
                session.add(counter)

            # Sayaçları güncelle
            counter.total_chat_count += 1

            if is_groq:
                counter.groq_count += 1
            elif is_local:
                counter.local_count += 1

            session.add(counter)
            session.commit()

            logger.debug(
                f"[LIMITER] Kullanım kaydedildi: user={user_id} "
                f"total={counter.total_chat_count} groq={counter.groq_count} "
                f"local={counter.local_count}"
            )

    @staticmethod
    def get_user_usage(user_id: int) -> dict:
        """
        Kullanıcının bugünkü kullanım istatistiklerini döndürür.
        
        Args:
            user_id: Kullanıcı ID'si
        
        Returns:
            dict: Kullanım istatistikleri
        
        Example:
            >>> usage = limiter.get_user_usage(user_id)
            >>> print(usage)
            {
                'groq_count': 45,
                'local_count': 12,
                'total_count': 57,
                'groq_remaining': 455,
                'local_remaining': 1988
            }
        """
        counter = UsageLimiter.get_or_create_counter(user_id)
        
        return {
            "groq_count": counter.groq_count,
            "local_count": counter.local_count,
            "total_count": counter.total_chat_count,
            "groq_remaining": max(0, LIMIT_GROQ_DAILY - counter.groq_count),
            "local_remaining": max(0, LIMIT_LOCAL_DAILY - counter.local_count),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Dışarıdan kullanım için tek instance
limiter = UsageLimiter()







