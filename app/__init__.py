import os

# ChromaDB Telemetry Kapatma (Global)
# Bu ayarlar, ChromaDB veya PostHog'un hatalı telemetri gönderimini
# ve "capture() takes 1 positional argument but 3 were given" hatasını önler.
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPLEMENTATION"] = "none"

"""
Mami AI - Ana Uygulama Paketi
=============================

Bu paket, Mami AI uygulamasının tüm modüllerini içerir.

Alt Paketler:
    - core: Veritabanı, modeller, yapılandırma
    - auth: Kimlik doğrulama ve yetkilendirme
    - api: HTTP endpoint'leri
    - chat: Sohbet işleme mantığı
    - ai: LLM entegrasyonları (Groq, Ollama)
    - image: Görsel üretim
    - search: İnternet araması
    - memory: Hafıza ve RAG sistemleri
    - services: Yardımcı servisler

Kullanım:
    from app.config import get_settings
    from app.core.database import get_session
    from app.chat.processor import process_chat_message
"""

__version__ = "4.2.0"
__author__ = "Mami AI Team"
