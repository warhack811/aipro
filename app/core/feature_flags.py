"""
Mami AI - Özellik Bayrakları (Feature Flags)
============================================

Bu modül, uygulama özelliklerini dinamik olarak açıp kapatmayı sağlar.
Admin panel üzerinden veya programatik olarak özellikler kontrol edilebilir.

Kullanım:
    from app.core.feature_flags import feature_enabled, set_feature_flag
    
    # Özellik açık mı kontrol et
    if feature_enabled("image_generation"):
        process_image_request()
    
    # Özelliği kapat
    set_feature_flag("image_generation", False)

Depolama:
    data/feature_flags.json dosyasında JSON formatında saklanır.

Varsayılan Davranış:
    Tanımlı olmayan özellikler varsayılan olarak açık (True) kabul edilir.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# YAPILANDIRMA
# =============================================================================

# Proje kök dizini (app/ klasörünün bir üstü)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FLAGS_PATH = PROJECT_ROOT / "data" / "feature_flags.json"

# =============================================================================
# GLOBAL CACHE
# =============================================================================

_flags_cache: Dict[str, bool] = {}
_loaded: bool = False

# =============================================================================
# DAHİLİ FONKSİYONLAR
# =============================================================================

def _load_flags() -> None:
    """
    JSON dosyasından feature flag'leri yükler ve cache'ler.
    
    Dosya yoksa veya okunamazsa, tüm özellikler varsayılan (True) kabul edilir.
    """
    global _flags_cache, _loaded

    if not FLAGS_PATH.exists():
        logger.debug(f"[FLAGS] Dosya bulunamadı: {FLAGS_PATH}")
        _flags_cache = {}
        _loaded = True
        return

    try:
        data = json.loads(FLAGS_PATH.read_text(encoding="utf-8"))
        _flags_cache = {k: bool(v) for k, v in data.items()}
        logger.info(f"[FLAGS] {len(_flags_cache)} flag yüklendi")
    except json.JSONDecodeError as e:
        logger.error(f"[FLAGS] JSON parse hatası: {e}")
        _flags_cache = {}
    except Exception as e:
        logger.error(f"[FLAGS] Dosya okuma hatası: {e}")
        _flags_cache = {}

    _loaded = True


def _save_flags() -> None:
    """Cache'deki flag'leri dosyaya kaydeder."""
    try:
        FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        FLAGS_PATH.write_text(
            json.dumps(_flags_cache, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"[FLAGS] Değişiklikler kaydedildi: {FLAGS_PATH}")
    except Exception as e:
        logger.error(f"[FLAGS] Dosya yazma hatası: {e}")


# =============================================================================
# PUBLIC API
# =============================================================================

def feature_enabled(key: str, default: bool = True) -> bool:
    """
    Bir özelliğin açık olup olmadığını kontrol eder.
    
    Args:
        key: Özellik anahtarı (ör: "image_generation", "chat", "bela_mode")
        default: Anahtar tanımlı değilse kullanılacak varsayılan değer
    
    Returns:
        bool: Özellik açık (True) veya kapalı (False)
    
    Example:
        >>> if feature_enabled("chat"):
        ...     process_chat()
        >>> 
        >>> if feature_enabled("experimental_feature", default=False):
        ...     try_experimental()
    """
    if not _loaded:
        _load_flags()
    return _flags_cache.get(key, default)


def set_feature_flag(key: str, value: bool) -> None:
    """
    Bir özelliğin durumunu değiştirir.
    
    Değişiklik hem belleğe hem de diske kaydedilir.
    
    Args:
        key: Özellik anahtarı
        value: Yeni durum (True: açık, False: kapalı)
    
    Example:
        >>> set_feature_flag("image_generation", False)  # Görsel üretimini kapat
        >>> set_feature_flag("image_generation", True)   # Tekrar aç
    """
    global _flags_cache
    
    if not _loaded:
        _load_flags()

    old_value = _flags_cache.get(key)
    _flags_cache[key] = value
    
    _save_flags()
    
    logger.info(f"[FLAGS] '{key}' değiştirildi: {old_value} → {value}")


def get_all_flags() -> Dict[str, bool]:
    """
    Tüm tanımlı flag'leri döndürür.
    
    Returns:
        Dict[str, bool]: Tüm flag'lerin kopyası
    
    Example:
        >>> flags = get_all_flags()
        >>> print(flags)
        {'chat': True, 'image_generation': False, ...}
    """
    if not _loaded:
        _load_flags()
    return _flags_cache.copy()


def reload_flags() -> None:
    """
    Flag'leri diskten yeniden yükler.
    
    Dosya harici olarak değiştirildiyse cache'i güncellemek için kullanılır.
    """
    global _loaded
    _loaded = False
    _load_flags()
    logger.info("[FLAGS] Cache yeniden yüklendi")


# =============================================================================
# BİLİNEN FEATURE FLAG'LER (Dokümantasyon)
# =============================================================================
"""
Sistemde kullanılan bilinen flag'ler:

chat                - Ana sohbet özelliği
image_generation    - Görsel üretimi (Flux/Forge)
file_upload         - Dosya yükleme (PDF, TXT)
internet            - İnternet araması
bela_mode           - Yerel model (Ollama) kullanımı
groq_enabled        - Groq API kullanımı
"""







