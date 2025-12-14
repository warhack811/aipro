"""
Mami AI - Dinamik Yapılandırma Servisi
======================================

Bu modül, veritabanında saklanan dinamik yapılandırmaları yönetir.
Memory cache ile performans optimize edilmiştir.

Kullanım:
    from app.core.dynamic_config import config_service
    
    # Değer okuma
    app_name = config_service.get("system.app_name", default="Mami AI")
    
    # Tüm kategoriyi okuma
    ui_settings = config_service.get_category("ui")
    
    # Değer yazma (Admin)
    config_service.set("system.app_name", "Yeni İsim", updated_by="admin")
    
    # Model config
    answer_model = config_service.get_model("answer")
    
    # Aktif tema
    theme = config_service.get_active_theme()

Cache Stratejisi:
    - TTL: 60 saniye (yapılandırılabilir)
    - set() çağrıldığında ilgili cache invalidate edilir
    - Startup'ta kritik config'ler preload edilir

Thread Safety:
    - Tüm operasyonlar thread-safe
    - Lock mekanizması ile race condition önlenir
"""

import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from threading import Lock
from typing import Any, Dict, List, Optional, TypeVar, Union

from sqlmodel import Session, select

# Modül logger'ı
logger = logging.getLogger(__name__)

# Generic type for type hints
T = TypeVar('T')


# =============================================================================
# CACHE IMPLEMENTATION
# =============================================================================

class ConfigCache:
    """
    Thread-safe, TTL destekli memory cache.
    
    Redis kullanmak yerine basit memory cache tercih edildi çünkü:
    1. Tek instance uygulama (Redis overhead gereksiz)
    2. Config değişiklikleri nadir (cache hit oranı yüksek)
    3. Deployment basitliği
    
    Attributes:
        _cache: Önbellek dictionary
        _timestamps: Değer yazılma zamanları
        _lock: Thread safety için lock
        _default_ttl: Varsayılan TTL (saniye)
    """
    
    def __init__(self, default_ttl: int = 60):
        """
        Args:
            default_ttl: Varsayılan cache süresi (saniye)
        """
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Cache'den değer okur.
        
        Args:
            key: Cache anahtarı
        
        Returns:
            Değer veya None (bulunamadı/expire oldu)
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            # TTL kontrolü
            timestamp = self._timestamps.get(key)
            if timestamp and datetime.utcnow() - timestamp > timedelta(seconds=self._default_ttl):
                # Expire olmuş, temizle
                del self._cache[key]
                del self._timestamps[key]
                return None
            
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Cache'e değer yazar.
        
        Args:
            key: Cache anahtarı
            value: Saklanacak değer
        """
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = datetime.utcnow()
    
    def delete(self, key: str) -> None:
        """Cache'den değer siler."""
        with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
    
    def delete_pattern(self, pattern: str) -> None:
        """
        Pattern'e uyan tüm key'leri siler.
        
        Args:
            pattern: Silinecek key prefix'i (ör: "system.")
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
                self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Tüm cache'i temizler."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        with self._lock:
            return {
                "total_keys": len(self._cache),
                "ttl_seconds": self._default_ttl,
            }


# =============================================================================
# DYNAMIC CONFIG SERVICE
# =============================================================================

class DynamicConfigService:
    """
    Dinamik yapılandırma yönetim servisi.
    
    Veritabanından config okuma/yazma, cache yönetimi,
    tip dönüşümü ve validasyon işlemlerini yönetir.
    """
    
    def __init__(self, cache_ttl: int = 60):
        """
        Args:
            cache_ttl: Cache TTL süresi (saniye)
        """
        self._cache = ConfigCache(default_ttl=cache_ttl)
        self._initialized = False
    
    # -------------------------------------------------------------------------
    # LAZY IMPORTS (Circular import önleme)
    # -------------------------------------------------------------------------
    
    def _get_session(self):
        """Database session lazy import."""
        from app.core.database import get_session
        return get_session
    
    def _get_models(self):
        """Config models lazy import."""
        from app.core.config_models import (
            APIConfig,
            ConfigValueType,
            ImageGenConfig,
            ModelConfig,
            PersonaConfig,
            SystemConfig,
            ThemeConfig,
            UITextConfig,
        )
        return {
            'SystemConfig': SystemConfig,
            'ModelConfig': ModelConfig,
            'APIConfig': APIConfig,
            'ThemeConfig': ThemeConfig,
            'PersonaConfig': PersonaConfig,
            'ImageGenConfig': ImageGenConfig,
            'UITextConfig': UITextConfig,
            'ConfigValueType': ConfigValueType,
        }
    
    # -------------------------------------------------------------------------
    # TYPE CONVERSION
    # -------------------------------------------------------------------------
    
    def _convert_value(self, value: str, value_type: str) -> Any:
        """
        String değeri belirtilen tipe dönüştürür.
        
        Args:
            value: String değer
            value_type: Hedef tip (string, integer, float, boolean, json)
        
        Returns:
            Dönüştürülmüş değer
        """
        if value is None:
            return None
        
        try:
            if value_type == "string":
                return value
            elif value_type == "integer":
                return int(value)
            elif value_type == "float":
                return float(value)
            elif value_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif value_type == "json":
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"[CONFIG] Tip dönüşüm hatası: {value} -> {value_type}: {e}")
            return value
    
    def _serialize_value(self, value: Any) -> str:
        """
        Değeri string'e dönüştürür (DB'ye yazma için).
        
        Args:
            value: Herhangi bir değer
        
        Returns:
            String representation
        """
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)
    
    def _detect_value_type(self, value: Any) -> str:
        """Değerin tipini otomatik algılar."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (dict, list)):
            return "json"
        else:
            return "string"
    
    # -------------------------------------------------------------------------
    # SYSTEM CONFIG (Key-Value)
    # -------------------------------------------------------------------------
    
    def get(
        self, 
        key: str, 
        default: T = None,
        use_cache: bool = True
    ) -> Union[T, Any]:
        """
        Yapılandırma değerini okur.
        
        Args:
            key: Config anahtarı (ör: "system.app_name")
            default: Bulunamazsa döndürülecek varsayılan değer
            use_cache: Cache kullanılsın mı
        
        Returns:
            Config değeri veya default
        
        Example:
            >>> app_name = config_service.get("system.app_name", "Mami AI")
        """
        cache_key = f"config:{key}"
        
        # Cache kontrolü
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
        
        # DB'den oku
        models = self._get_models()
        SystemConfig = models['SystemConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                config = session.exec(
                    select(SystemConfig).where(SystemConfig.key == key)
                ).first()
                
                if config is None:
                    return default
                
                # Tip dönüşümü
                value = self._convert_value(config.value, config.value_type)
                
                # Cache'e yaz
                if use_cache:
                    self._cache.set(cache_key, value)
                
                return value
                
        except Exception as e:
            logger.error(f"[CONFIG] Okuma hatası ({key}): {e}")
            return default
    
    def get_many(self, keys: List[str], use_cache: bool = True) -> Dict[str, Any]:
        """
        Birden fazla config değerini okur.
        
        Args:
            keys: Config anahtarları listesi
            use_cache: Cache kullanılsın mı
        
        Returns:
            Key-value dictionary
        """
        result = {}
        uncached_keys = []
        
        # Önce cache'den dene
        if use_cache:
            for key in keys:
                cache_key = f"config:{key}"
                cached = self._cache.get(cache_key)
                if cached is not None:
                    result[key] = cached
                else:
                    uncached_keys.append(key)
        else:
            uncached_keys = keys
        
        # Cache'de olmayanları DB'den al
        if uncached_keys:
            models = self._get_models()
            SystemConfig = models['SystemConfig']
            get_session = self._get_session()
            
            try:
                with get_session() as session:
                    configs = session.exec(
                        select(SystemConfig).where(SystemConfig.key.in_(uncached_keys))
                    ).all()
                    
                    for config in configs:
                        value = self._convert_value(config.value, config.value_type)
                        result[config.key] = value
                        
                        if use_cache:
                            self._cache.set(f"config:{config.key}", value)
                            
            except Exception as e:
                logger.error(f"[CONFIG] Toplu okuma hatası: {e}")
        
        return result
    
    def get_category(self, category: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Bir kategorideki tüm config'leri okur.
        
        Args:
            category: Kategori adı (system, ui, models, vb.)
            use_cache: Cache kullanılsın mı
        
        Returns:
            Key-value dictionary (key'ler prefix'siz)
        """
        cache_key = f"category:{category}"
        
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
        
        models = self._get_models()
        SystemConfig = models['SystemConfig']
        get_session = self._get_session()
        
        result = {}
        
        try:
            with get_session() as session:
                configs = session.exec(
                    select(SystemConfig).where(SystemConfig.category == category)
                ).all()
                
                for config in configs:
                    # Key'den category prefix'ini kaldır
                    short_key = config.key
                    if short_key.startswith(f"{category}."):
                        short_key = short_key[len(category) + 1:]
                    
                    result[short_key] = self._convert_value(config.value, config.value_type)
            
            if use_cache:
                self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"[CONFIG] Kategori okuma hatası ({category}): {e}")
            return {}
    
    def set(
        self, 
        key: str, 
        value: Any,
        value_type: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Yapılandırma değerini yazar/günceller.
        
        Args:
            key: Config anahtarı
            value: Yeni değer
            value_type: Değer tipi (otomatik algılanır)
            category: Kategori (key'den çıkarılır)
            description: Açıklama
            updated_by: Güncelleyen kullanıcı
        
        Returns:
            bool: Başarılı mı
        """
        models = self._get_models()
        SystemConfig = models['SystemConfig']
        get_session = self._get_session()
        
        # Tip algılama
        if value_type is None:
            value_type = self._detect_value_type(value)
        
        # Kategori çıkarma (key'den)
        if category is None and "." in key:
            category = key.split(".")[0]
        
        try:
            with get_session() as session:
                # Mevcut kayıt var mı?
                config = session.exec(
                    select(SystemConfig).where(SystemConfig.key == key)
                ).first()
                
                serialized = self._serialize_value(value)
                
                if config:
                    # Güncelle
                    config.value = serialized
                    config.value_type = value_type
                    config.updated_at = datetime.utcnow()
                    if updated_by:
                        config.updated_by = updated_by
                    if description:
                        config.description = description
                else:
                    # Yeni oluştur
                    config = SystemConfig(
                        key=key,
                        value=serialized,
                        value_type=value_type,
                        category=category or "system",
                        description=description,
                        updated_by=updated_by,
                    )
                    session.add(config)
                
                session.commit()
            
            # Cache invalidate
            self._cache.delete(f"config:{key}")
            if category:
                self._cache.delete(f"category:{category}")
            
            logger.info(f"[CONFIG] Güncellendi: {key} = {value} (by: {updated_by})")
            return True
            
        except Exception as e:
            logger.error(f"[CONFIG] Yazma hatası ({key}): {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Config kaydını siler."""
        models = self._get_models()
        SystemConfig = models['SystemConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                config = session.exec(
                    select(SystemConfig).where(SystemConfig.key == key)
                ).first()
                
                if config:
                    category = config.category
                    session.delete(config)
                    session.commit()
                    
                    # Cache invalidate
                    self._cache.delete(f"config:{key}")
                    self._cache.delete(f"category:{category}")
                    
                    return True
                return False
                
        except Exception as e:
            logger.error(f"[CONFIG] Silme hatası ({key}): {e}")
            return False
    
    # -------------------------------------------------------------------------
    # MODEL CONFIG
    # -------------------------------------------------------------------------
    
    def get_model(self, purpose: str, provider: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Belirtilen amaç için model yapılandırmasını döndürür.
        
        Args:
            purpose: Kullanım amacı (answer, decider, semantic, uncensored)
            provider: Sağlayıcı filtresi (opsiyonel)
        
        Returns:
            Model config dict veya None
        """
        cache_key = f"model:{purpose}:{provider or 'any'}"
        
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        models = self._get_models()
        ModelConfig = models['ModelConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                query = select(ModelConfig).where(
                    ModelConfig.purpose == purpose,
                    ModelConfig.is_active == True
                )
                
                if provider:
                    query = query.where(ModelConfig.provider == provider)
                
                # Öncelik ve default sıralaması
                query = query.order_by(
                    ModelConfig.is_default.desc(),
                    ModelConfig.priority.desc()
                )
                
                config = session.exec(query).first()
                
                if config:
                    result = {
                        "name": config.name,
                        "display_name": config.display_name,
                        "provider": config.provider,
                        "model_id": config.model_id,
                        "parameters": config.parameters,
                        "capabilities": config.capabilities,
                    }
                    self._cache.set(cache_key, result)
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"[CONFIG] Model okuma hatası ({purpose}): {e}")
            return None
    
    def get_all_models(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Tüm model yapılandırmalarını döndürür."""
        models = self._get_models()
        ModelConfig = models['ModelConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                query = select(ModelConfig)
                if active_only:
                    query = query.where(ModelConfig.is_active == True)
                
                configs = session.exec(query.order_by(ModelConfig.purpose, ModelConfig.priority.desc())).all()
                
                return [
                    {
                        "id": c.id,
                        "name": c.name,
                        "display_name": c.display_name,
                        "provider": c.provider,
                        "model_id": c.model_id,
                        "purpose": c.purpose,
                        "is_active": c.is_active,
                        "is_default": c.is_default,
                        "parameters": c.parameters,
                        "capabilities": c.capabilities,
                    }
                    for c in configs
                ]
                
        except Exception as e:
            logger.error(f"[CONFIG] Model listesi hatası: {e}")
            return []
    
    # -------------------------------------------------------------------------
    # THEME CONFIG
    # -------------------------------------------------------------------------
    
    def get_active_theme(self) -> Optional[Dict[str, Any]]:
        """Varsayılan aktif temayı döndürür."""
        cache_key = "theme:default"
        
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        models = self._get_models()
        ThemeConfig = models['ThemeConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                theme = session.exec(
                    select(ThemeConfig).where(
                        ThemeConfig.is_active == True,
                        ThemeConfig.is_default == True
                    )
                ).first()
                
                if not theme:
                    # Default yoksa ilk aktifi al
                    theme = session.exec(
                        select(ThemeConfig).where(ThemeConfig.is_active == True)
                        .order_by(ThemeConfig.sort_order)
                    ).first()
                
                if theme:
                    result = {
                        "name": theme.name,
                        "display_name": theme.display_name,
                        "colors": theme.colors,
                        "fonts": theme.fonts,
                        "custom_css": theme.custom_css,
                    }
                    self._cache.set(cache_key, result)
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"[CONFIG] Tema okuma hatası: {e}")
            return None
    
    def get_all_themes(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Tüm temaları döndürür."""
        models = self._get_models()
        ThemeConfig = models['ThemeConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                query = select(ThemeConfig)
                if active_only:
                    query = query.where(ThemeConfig.is_active == True)
                
                themes = session.exec(query.order_by(ThemeConfig.sort_order)).all()
                
                return [
                    {
                        "name": t.name,
                        "display_name": t.display_name,
                        "is_default": t.is_default,
                        "colors": t.colors,
                        "fonts": t.fonts,
                    }
                    for t in themes
                ]
                
        except Exception as e:
            logger.error(f"[CONFIG] Tema listesi hatası: {e}")
            return []
    
    # -------------------------------------------------------------------------
    # PERSONA CONFIG
    # -------------------------------------------------------------------------
    
    def get_persona(self, name: str) -> Optional[Dict[str, Any]]:
        """Persona/mod yapılandırmasını döndürür."""
        cache_key = f"persona:{name}"
        
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        models = self._get_models()
        PersonaConfig = models['PersonaConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                persona = session.exec(
                    select(PersonaConfig).where(
                        PersonaConfig.name == name,
                        PersonaConfig.is_active == True
                    )
                ).first()
                
                if persona:
                    result = {
                        "name": persona.name,
                        "display_name": persona.display_name,
                        "mode_type": persona.mode_type,
                        "description": persona.description,
                        "icon": persona.icon,
                        "system_prompt": persona.system_prompt,
                        "personality_traits": persona.personality_traits,
                        "behavior_rules": persona.behavior_rules,
                        "allowed_providers": persona.allowed_providers,
                        "requires_uncensored": persona.requires_uncensored,
                        "preference_override_mode": persona.preference_override_mode,
                        "example_dialogues": persona.example_dialogues,
                    }
                    self._cache.set(cache_key, result)
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"[CONFIG] Persona okuma hatası ({name}): {e}")
            return None
    
    def get_all_personas(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Tüm personaları döndürür."""
        models = self._get_models()
        PersonaConfig = models['PersonaConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                query = select(PersonaConfig)
                if active_only:
                    query = query.where(PersonaConfig.is_active == True)
                
                personas = session.exec(query.order_by(PersonaConfig.sort_order)).all()
                
                return [
                    {
                        "name": p.name,
                        "display_name": p.display_name,
                        "mode_type": p.mode_type,
                        "description": p.description,
                        "icon": p.icon,
                        "is_default": p.is_default,
                        "requires_uncensored": p.requires_uncensored,
                    }
                    for p in personas
                ]
                
        except Exception as e:
            logger.error(f"[CONFIG] Persona listesi hatası: {e}")
            return []
    
    # -------------------------------------------------------------------------
    # UI TEXT CONFIG
    # -------------------------------------------------------------------------
    
    def get_text(self, key: str, locale: str = "tr", default: str = "") -> str:
        """UI metnini döndürür."""
        cache_key = f"text:{locale}:{key}"
        
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        models = self._get_models()
        UITextConfig = models['UITextConfig']
        get_session = self._get_session()
        
        try:
            with get_session() as session:
                text = session.exec(
                    select(UITextConfig).where(
                        UITextConfig.key == key,
                        UITextConfig.locale == locale
                    )
                ).first()
                
                if text:
                    self._cache.set(cache_key, text.value)
                    return text.value
                
                return default
                
        except Exception as e:
            logger.error(f"[CONFIG] Text okuma hatası ({key}): {e}")
            return default
    
    # -------------------------------------------------------------------------
    # CACHE MANAGEMENT
    # -------------------------------------------------------------------------
    
    def invalidate_cache(self, pattern: Optional[str] = None) -> None:
        """
        Cache'i temizler.
        
        Args:
            pattern: Silinecek key pattern'i (None = tümü)
        """
        if pattern:
            self._cache.delete_pattern(pattern)
            logger.info(f"[CONFIG] Cache temizlendi: {pattern}*")
        else:
            self._cache.clear()
            logger.info("[CONFIG] Tüm cache temizlendi")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Cache istatistiklerini döndürür."""
        return self._cache.stats()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global singleton instance
config_service = DynamicConfigService(cache_ttl=60)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_config(key: str, default: Any = None) -> Any:
    """
    Kısayol fonksiyon - config değeri okur.
    
    Args:
        key: Config anahtarı
        default: Varsayılan değer
    
    Returns:
        Config değeri
    
    Example:
        >>> app_name = get_config("system.app_name", "Mami AI")
    """
    return config_service.get(key, default)


def set_config(key: str, value: Any, updated_by: str = "system") -> bool:
    """
    Kısayol fonksiyon - config değeri yazar.
    
    Args:
        key: Config anahtarı
        value: Yeni değer
        updated_by: Güncelleyen
    
    Returns:
        Başarılı mı
    """
    return config_service.set(key, value, updated_by=updated_by)







