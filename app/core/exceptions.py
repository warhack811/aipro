"""
Mami AI - Özel Hata Sınıfları
=============================

Bu modül, uygulamada kullanılan özel exception sınıflarını tanımlar.
Her hata sınıfı:
- Teknik detay (loglama için)
- Kullanıcı dostu mesaj (UI'da gösterilecek)
- HTTP durum kodu

Kullanım:
    from app.core.exceptions import GroqAPIError, AuthenticationError
    
    try:
        response = await call_groq_api(...)
    except RateLimitError:
        raise GroqAPIError("Groq rate limit aşıldı")

Exception Hiyerarşisi:
    MamiException (base)
    ├── AuthenticationError (401)
    ├── DailyLimitError (429)
    ├── GroqAPIError (429)
    ├── ImageGenerationError (503)
    └── FeatureDisabledError (503)
"""

from typing import Optional


class MamiException(Exception):
    """
    Mami AI temel hata sınıfı.
    
    Tüm özel hatalar bu sınıftan türetilir. İki tür mesaj içerir:
    - message: Teknik detay (log dosyalarına yazılır)
    - user_message: Kullanıcı dostu mesaj (UI'da gösterilir)
    
    Attributes:
        message (str): Teknik hata mesajı (loglama için)
        user_message (str): Kullanıcıya gösterilecek mesaj
        status_code (int): HTTP durum kodu
    
    Example:
        >>> raise MamiException(
        ...     message="DB connection failed: timeout",
        ...     user_message="Bir hata oluştu, lütfen tekrar deneyin.",
        ...     status_code=500
        ... )
    """
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        status_code: int = 500
    ):
        """
        Args:
            message: Teknik hata mesajı
            user_message: Kullanıcı dostu mesaj (varsayılan: "Bir hata oluştu.")
            status_code: HTTP durum kodu (varsayılan: 500)
        """
        self.message = message
        self.user_message = user_message or "Bir hata oluştu."
        self.status_code = status_code
        super().__init__(message)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"


class AuthenticationError(MamiException):
    """
    Kimlik doğrulama hatası.
    
    Kullanıcı oturumu geçersiz veya süresi dolmuş olduğunda fırlatılır.
    HTTP 401 Unauthorized döndürür.
    
    Example:
        >>> raise AuthenticationError("Token expired")
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            user_message="Oturum süren dolmuş veya giriş yapmamışsın.",
            status_code=401
        )


class DailyLimitError(MamiException):
    """
    Günlük kullanım limiti hatası.
    
    Kullanıcı günlük istek limitini aştığında fırlatılır.
    HTTP 429 Too Many Requests döndürür.
    
    Example:
        >>> raise DailyLimitError("User exceeded 100 requests/day")
    """
    
    def __init__(self, message: str = "Günlük limitine ulaştın."):
        super().__init__(
            message=message,
            user_message="Bugünkü limitini doldurdun. Yarın tekrar devam edebiliriz. 😉",
            status_code=429
        )


class GroqAPIError(MamiException):
    """
    Groq API hatası.
    
    Groq API çağrısı başarısız olduğunda (rate limit, timeout vb.)
    fırlatılır. HTTP 429 döndürür.
    
    Example:
        >>> raise GroqAPIError("Rate limit exceeded: 429")
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            user_message="Yapay zeka beyni şu an aşırı yoğun. Biraz dinlenip tekrar deneyelim.",
            status_code=429
        )


class ImageGenerationError(MamiException):
    """
    Görsel üretim hatası.
    
    Flux/Forge API'den görsel üretilemediğinde fırlatılır.
    HTTP 503 Service Unavailable döndürür.
    
    Example:
        >>> raise ImageGenerationError("Forge API timeout")
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            user_message="Resim üretim servisi şu an yanıt vermiyor. Lütfen biraz sonra tekrar dene.",
            status_code=503
        )


class FeatureDisabledError(MamiException):
    """
    Özellik devre dışı hatası.
    
    Admin tarafından geçici olarak kapatılmış özellikler için kullanılır.
    HTTP 503 Service Unavailable döndürür.
    
    Attributes:
        feature (str): Devre dışı bırakılan özellik adı
    
    Example:
        >>> raise FeatureDisabledError("image_generation")
    """
    
    def __init__(self, feature: str):
        self.feature = feature
        super().__init__(
            message=f"Feature disabled: {feature}",
            user_message="Bu özellik şu anda bakımda veya geçici olarak kapalı.",
            status_code=503
        )


class SearchError(MamiException):
    """
    İnternet arama hatası.
    
    Arama sağlayıcıları (Bing, Serper, DuckDuckGo) başarısız
    olduğunda fırlatılır.
    
    Example:
        >>> raise SearchError("All search providers failed")
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            user_message="İnternet araması şu an yapılamıyor. Lütfen tekrar deneyin.",
            status_code=503
        )


class ValidationError(MamiException):
    """
    Girdi doğrulama hatası.
    
    Kullanıcı girdisi geçersiz olduğunda fırlatılır.
    HTTP 400 Bad Request döndürür.
    
    Example:
        >>> raise ValidationError("Message too long: 15000 chars")
    """
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(
            message=message,
            user_message=user_message or "Geçersiz giriş. Lütfen kontrol edip tekrar deneyin.",
            status_code=400
        )







