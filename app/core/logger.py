"""
Mami AI - Merkezi Loglama Sistemi
=================================

Bu modül, uygulama genelinde tutarlı loglama sağlar.

Özellikler:
    - Console çıktısı (geliştirme için)
    - Dönen log dosyası (production için)
    - Maksimum 5MB dosya boyutu, 3 yedek dosya
    - Tutarlı format: timestamp - modül - seviye - mesaj

Kullanım:
    from app.core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("İşlem başladı")
    logger.error("Hata oluştu", exc_info=True)

Log Dosyası:
    logs/mami.log (ve mami.log.1, mami.log.2, mami.log.3 yedekleri)

Log Seviyeleri:
    - DEBUG: Detaylı debug bilgisi
    - INFO: Genel bilgi mesajları
    - WARNING: Uyarılar
    - ERROR: Hata mesajları
    - CRITICAL: Kritik hatalar
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# =============================================================================
# YAPILANDIRMA SABİTLERİ
# =============================================================================

# Log dizini
LOG_DIR = Path("logs")

# Dosya boyutu limitleri
MAX_LOG_FILE_SIZE = 5_000_000  # 5 MB
BACKUP_COUNT = 3               # 3 yedek dosya (toplam ~20 MB)

# Log formatı
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# LOGGER FONKSİYONLARI
# =============================================================================

def _ensure_log_directory() -> None:
    """Log dizininin var olduğundan emin ol."""
    LOG_DIR.mkdir(exist_ok=True)


def get_logger(
    name: str = "mami",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Yapılandırılmış logger döndürür.
    
    Her modül için ayrı bir logger oluşturulur, ancak tüm loglar
    aynı dosyaya ve console'a yazılır. Handler'ların tekrar
    eklenmesini önlemek için kontrol yapılır.
    
    Args:
        name: Logger adı (genellikle __name__ kullanılır)
        level: Log seviyesi (varsayılan: INFO)
        log_to_file: Dosyaya log yaz (varsayılan: True)
        log_to_console: Console'a log yaz (varsayılan: True)
    
    Returns:
        logging.Logger: Yapılandırılmış logger nesnesi
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Uygulama başlatıldı")
        2024-01-01 12:00:00 - app.main - INFO - Uygulama başlatıldı
        
        >>> logger.error("Hata!", exc_info=True)  # Stack trace ile
    """
    logger = logging.getLogger(name)
    
    # Handler zaten eklenmişse tekrar ekleme
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Formatter oluştur
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console Handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File Handler (Rotating)
    if log_to_file:
        _ensure_log_directory()
        log_file = LOG_DIR / "mami.log"
        
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=MAX_LOG_FILE_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_debug_logger(name: str = "mami.debug") -> logging.Logger:
    """
    Debug seviyesinde logger döndürür.
    
    Geliştirme sırasında detaylı log için kullanılır.
    Production'da DEBUG logları dosyaya yazılmaz (performans).
    
    Args:
        name: Logger adı
    
    Returns:
        logging.Logger: DEBUG seviyesinde logger
    """
    return get_logger(name, level=logging.DEBUG)


def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Root logger'ı yapılandırır.
    
    Tüm kütüphanelerin loglarını kontrol etmek için kullanılır.
    Genellikle main.py'de bir kere çağrılır.
    
    Args:
        level: Log seviyesi
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT
    )


# =============================================================================
# LOG YARDIMCI FONKSİYONLARI
# =============================================================================

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user: Optional[str] = None,
    extra: Optional[dict] = None
) -> None:
    """
    HTTP isteğini loglar.
    
    Args:
        logger: Logger nesnesi
        method: HTTP metodu (GET, POST vb.)
        path: İstek yolu
        user: Kullanıcı adı (varsa)
        extra: Ek bilgiler
    """
    user_str = f" user={user}" if user else ""
    extra_str = f" {extra}" if extra else ""
    logger.info(f"[REQUEST] {method} {path}{user_str}{extra_str}")


def log_response(
    logger: logging.Logger,
    status_code: int,
    duration_ms: float,
    extra: Optional[dict] = None
) -> None:
    """
    HTTP yanıtını loglar.
    
    Args:
        logger: Logger nesnesi
        status_code: HTTP durum kodu
        duration_ms: İşlem süresi (milisaniye)
        extra: Ek bilgiler
    """
    extra_str = f" {extra}" if extra else ""
    logger.info(f"[RESPONSE] status={status_code} duration={duration_ms:.2f}ms{extra_str}")

