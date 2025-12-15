"""
Mami AI - Uygulama Yapılandırması
=================================

Bu modül, uygulamanın tüm yapılandırma ayarlarını yönetir.
Ayarlar öncelikle .env dosyasından, yoksa varsayılan değerlerden okunur.

Kullanım:
    from app.config import get_settings
    
    settings = get_settings()
    print(settings.APP_NAME)

Ortam Değişkenleri:
    Tüm ayarlar .env dosyasından veya sistem ortam değişkenlerinden
    okunabilir. Örnek .env dosyası için .env.example'a bakın.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Uygulama yapılandırma sınıfı.
    
    Pydantic BaseSettings kullanarak .env dosyasından veya
    ortam değişkenlerinden otomatik değer okur.
    
    Attributes:
        APP_NAME: Uygulama adı
        DEBUG: Debug modu (True: geliştirme, False: production)
        SECRET_KEY: JWT ve session imzalama için gizli anahtar
    """
    
    # =========================================================================
    # GENEL UYGULAMA AYARLARI
    # =========================================================================
    APP_NAME: str = Field(default="Mami AI", description="Uygulama adı")
    DEBUG: bool = Field(default=True, description="Debug modu")
    
    # Sunucu Ayarları
    API_HOST: str = Field(default="0.0.0.0", description="API sunucu adresi")
    API_PORT: int = Field(default=8000, description="API sunucu portu")
    
    # Güvenlik - KRİTİK: Production'da mutlaka değiştirin!
    SECRET_KEY: str = Field(
        default="super-secret-dev-key-change-this",
        description="Oturum ve JWT imzalama için gizli anahtar"
    )
    
    # =========================================================================
    # VERİTABANI AYARLARI
    # =========================================================================
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Veritabanı bağlantı URL'si. Boşsa sqlite:///data/app.db kullanılır"
    )
    CHROMA_PERSIST_DIR: str = Field(
        default="data/chroma_db",
        description="ChromaDB vektör veritabanı dizini"
    )
    
    # =========================================================================
    # GROQ API AYARLARI (Ana LLM Sağlayıcısı)
    # =========================================================================
    # Ana ve yedek API anahtarları - Rate limit durumunda otomatik geçiş
    GROQ_API_KEY: str = Field(default="", description="Groq API ana anahtar")
    GROQ_API_KEY_BACKUP: str = Field(default="", description="Groq API yedek anahtar 1")
    GROQ_API_KEY_3: str = Field(default="", description="Groq API yedek anahtar 2")
    GROQ_API_KEY_4: str = Field(default="", description="Groq API yedek anahtar 3")
    
    # Model Stratejisi: Farklı görevler için optimize edilmiş modeller
    # NOT: llama-3.1-70b-versatile Groq tarafından kullanımdan kaldırıldı (Aralık 2024)
    GROQ_DECIDER_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Router/Decider için kullanılan model"
    )
    GROQ_ANSWER_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Ana cevap üretimi için model (yüksek kalite)"
    )
    GROQ_FAST_MODEL: str = Field(
        default="llama-3.1-8b-instant",
        description="Hızlı işlemler için model (semantic, özet)"
    )
    GROQ_SEMANTIC_MODEL: str = Field(
        default="llama-3.1-8b-instant",
        description="Semantic classifier için model"
    )
    
    # =========================================================================
    # İNTERNET ARAMA AYARLARI
    # =========================================================================
    # Bing Search API
    BING_API_KEY: str = Field(default="", description="Bing Search API anahtarı")
    BING_ENDPOINT: str = Field(
        default="https://api.bing.microsoft.com/v7.0/search",
        description="Bing Search API endpoint"
    )
    
    # Serper (Google Search) API
    SERPER_API_KEY: str = Field(default="", description="Serper (Google) API anahtarı")
    SERPER_ENDPOINT: str = Field(
        default="https://google.serper.dev/search",
        description="Serper API endpoint"
    )
    
    # =========================================================================
    # OLLAMA AYARLARI (Yerel LLM)
    # =========================================================================
    OLLAMA_BASE_URL: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama sunucu adresi"
    )
    OLLAMA_LOCAL_MODEL: str = Field(
        default="josiefied-qwen3-8b",
        description="Ollama'da kullanılacak model adı"
    )
    
    # =========================================================================
    # GÖRSEL ÜRETİM AYARLARI (Forge/Flux)
    # =========================================================================
    FORGE_BASE_URL: str = Field(
        default="http://127.0.0.1:7860",
        description="Forge/Stable Diffusion WebUI adresi"
    )
    FORGE_TXT2IMG_PATH: str = Field(
        default="/sdapi/v1/txt2img",
        description="Text-to-image API endpoint"
    )
    FORGE_TIMEOUT: int = Field(
        default=1200,
        description="Görsel üretim zaman aşımı (saniye)"
    )
    
    # Flux checkpoint seçimleri
    FLUX_STANDARD_CHECKPOINT: str = Field(
        default="flux1-dev-bnb-nf4-v2.safetensors",
        description="Standard (safe content) Flux checkpoint"
    )
    FLUX_NSFW_CHECKPOINT: str = Field(
        default="fluxedUpFluxNSFW_51FP8.safetensors",
        description="Uncensored (NSFW allowed) Flux checkpoint"
    )
    
    # Legacy - backward compatibility
    FORGE_FLUX_CHECKPOINT: str = Field(
        default="fluxedUpFluxNSFW_51FP8.safetensors",
        description="[DEPRECATED] Kullanılacak Flux model dosyası (fallback)"
    )
    
    # =========================================================================
    # CORS AYARLARI
    # =========================================================================
    CORS_ORIGINS: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        description="İzin verilen origin'ler (virgülle ayrılmış)"
    )
    
    # =========================================================================
    # PYDANTIC YAPILANDIRMASI
    # =========================================================================
    class Config:
        """Pydantic model yapılandırması."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Extra alanları yoksay (geriye uyumluluk için)
        extra = "ignore"
    
    # =========================================================================
    # YARDIMCI METODLAR
    # =========================================================================
    def get_cors_origins_list(self) -> List[str]:
        """
        CORS origin'lerini liste olarak döndürür.
        
        Returns:
            List[str]: İzin verilen origin URL'leri listesi
        """
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def get_groq_api_keys(self) -> List[str]:
        """
        Tüm geçerli Groq API anahtarlarını liste olarak döndürür.
        Rate limit durumunda sırayla denenmek üzere.
        
        Returns:
            List[str]: Boş olmayan API anahtarları listesi
        """
        keys = [
            self.GROQ_API_KEY,
            self.GROQ_API_KEY_BACKUP,
            self.GROQ_API_KEY_3,
            self.GROQ_API_KEY_4,
        ]
        return [k for k in keys if k]


@lru_cache()
def get_settings() -> Settings:
    """
    Uygulama ayarlarını döndürür (Singleton pattern).
    
    lru_cache ile sarıldığından, ilk çağrıda Settings nesnesi
    oluşturulur ve sonraki çağrılarda aynı nesne döndürülür.
    
    Returns:
        Settings: Uygulama yapılandırma nesnesi
    
    Example:
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
        Mami AI
    """
    return Settings()

