"""
Mami AI - Circuit Breaker for Forge API
========================================

Forge API'yi cascade failure'dan korumak için circuit breaker pattern.

Kullanım:
    from app.image.circuit_breaker import forge_circuit_breaker
    
    if forge_circuit_breaker.can_attempt():
        result = await call_forge_api(...)
        forge_circuit_breaker.record_success()
    else:
        return PLACEHOLDER_IMAGE
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker durumları"""
    CLOSED = "closed"          # Normal çalışma - istekler geçiyor
    OPEN = "open"              # Hata durumu - istekler engelleniyor
    HALF_OPEN = "half_open"    # Test modu - sınırlı istek


class ForgeCircuitBreaker:
    """
    Circuit breaker for Forge API.
    
    Pattern:
    - CLOSED → (5 hata) → OPEN
    - OPEN → (60s timeout) → HALF_OPEN
    - HALF_OPEN → (başarı) → CLOSED
    - HALF_OPEN → (hata) → OPEN
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_timeout: int = 30
    ):
        """
        Args:
            failure_threshold: Kaç hata sonrası OPEN durumuna geçilir
            timeout_seconds: OPEN durumunda ne kadar beklenir
            half_open_timeout: HALF_OPEN durumunda ne kadar test edilir
        """
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_timeout = timedelta(seconds=half_open_timeout)
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
    
    def can_attempt(self) -> bool:
        """
        İstek yapılabilir mi kontrol et.
        
        Returns:
            bool: True ise istek yapılabilir
        """
        now = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            # Normal durum - tüm istekler geçebilir
            return True
        
        if self.state == CircuitState.OPEN:
            # Hata durumu - timeout geçtiyse HALF_OPEN'a geç
            if self.last_failure_time:
                elapsed = now - self.last_failure_time
                if elapsed >= self.timeout:  # >= kullan, timeout=0 edge case için
                    logger.info("[CIRCUIT] OPEN → HALF_OPEN (timeout geçti)")
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                    self.success_count = 0
                    return True
            
            # Timeout henüz geçmedi - istekleri engelle
            remaining = self.timeout - (now - self.last_failure_time) if self.last_failure_time else timedelta(0)
            logger.warning(f"[CIRCUIT] OPEN - istekler engelleniyor ({remaining.seconds}s kaldı)")
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Test modu - sınırlı istek
            # İlk test isteğine izin ver
            return True
        
        return False
    
    def record_success(self):
        """Başarılı istek kaydı"""
        self.failure_count = 0
        self.success_count += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Test başarılı - CLOSED'a dön
            logger.info("[CIRCUIT] HALF_OPEN → CLOSED (test başarılı)")
            self.state = CircuitState.CLOSED
            self.last_state_change = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            logger.debug(f"[CIRCUIT] CLOSED - başarı kaydedildi (toplam başarı: {self.success_count})")
    
    def record_failure(self, error: Optional[Exception] = None):
        """Başarısız istek kaydı"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        error_msg = f": {error}" if error else ""
        logger.warning(f"[CIRCUIT] Hata kaydedildi ({self.failure_count}/{self.failure_threshold}){error_msg}")
        
        if self.state == CircuitState.HALF_OPEN:
            # Test başarısız - tekrar OPEN'a dön
            logger.error("[CIRCUIT] HALF_OPEN → OPEN (test başarısız)")
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
            return
        
        if self.failure_count >= self.failure_threshold:
            # Threshold aşıldı - OPEN durumuna geç
            logger.error(f"[CIRCUIT] CLOSED → OPEN (threshold aşıldı: {self.failure_count} hata)")
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()
    
    def get_state(self) -> dict:
        """
        Circuit breaker durumunu döndür (monitoring için).
        
        Returns:
            dict: Durum bilgileri
        """
        now = datetime.now()
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "time_in_current_state": (now - self.last_state_change).seconds,
        }
    
    def reset(self):
        """Circuit breaker'ı sıfırla (manuel müdahale için)"""
        logger.info("[CIRCUIT] Manuel reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now()


# Global circuit breaker instance
forge_circuit_breaker = ForgeCircuitBreaker(
    failure_threshold=5,      # 5 hata
    timeout_seconds=60,       # 60 saniye bekle
    half_open_timeout=30      # 30 saniye test
)