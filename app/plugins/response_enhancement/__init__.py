"""
Response Enhancement Plugin
===========================

Profesyonel seviye cevap formatlaması ve zenginleştirme plugin'i.
ChatGPT, Claude gibi büyük chatbot'ların cevap kalitesini hedefler.

Özellikler:
- Gelişmiş prompt engineering
- Akıllı yapılandırma (steps, comparison, table)
- Görsel zenginleştirme (emoji, callout, separator)
- Kod bloğu iyileştirmeleri
- Markdown otomasyonu
"""

from app.plugins.response_enhancement.plugin import ResponseEnhancementPlugin

__all__ = ["ResponseEnhancementPlugin"]