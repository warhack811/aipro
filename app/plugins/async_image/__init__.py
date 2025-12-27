"""
Async Image Generation Plugin
==============================

Bu plugin görsel üretimini Celery ile asenkron yapar.
Mevcut sisteme dokunmadan çalışır.
"""

from app.plugins.async_image.plugin import AsyncImagePlugin

__all__ = ["AsyncImagePlugin"]
