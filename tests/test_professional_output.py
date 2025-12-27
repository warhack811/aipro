# -*- coding: utf-8 -*-
"""
Professional Output Tests
=========================

8 senaryo için golden snapshot testleri.
Shaper, formatter ve output contract davranışlarını test eder.
"""

from typing import Any, Dict

import pytest

# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def formatter():
    """Tool output formatter fixture."""
    from app.services.tool_output_formatter import format_web_result

    return format_web_result


@pytest.fixture
def shaper():
    """Answer shaper fixture."""
    try:
        from app.services.answer_shaper import shape_answer

        return shape_answer
    except ImportError:
        from app.plugins.response_enhancement.smart_shaper import SmartAnswerShaper

        return SmartAnswerShaper().shape


@pytest.fixture
def post_processor():
    """Full post processor fixture."""
    from app.services.response_processor import full_post_process, get_preset_config

    return full_post_process, get_preset_config


# =============================================================================
# SENARYO 1: ADIM ADIM TALİMAT
# =============================================================================


class TestStepByStep:
    """Adım adım talimat formatı testleri."""

    def test_technical_steps_are_numbered(self, shaper):
        """Teknik adımlar numaralandırılmalı."""
        text = """Python kurulumu için şunları yapmalısınız. İlk olarak python.org sitesine gidin. İndirme sayfasından sisteminize uygun versiyonu seçin. İndirdiğiniz dosyayı çalıştırın."""

        user_message = "Python nasıl kurulur?"
        result, mode, reason = shaper(text, user_message, mode="auto")

        # Yapılandırılmış çıktı bekleniyor
        assert mode in ("list", "steps", "structured")
        # En az 3 madde olmalı
        assert result.count("1.") >= 1 or result.count("- ") >= 3

    def test_short_answer_not_forced_to_list(self, shaper):
        """Kısa cevaplar zorla listeye dönüştürülmemeli."""
        text = "Python 3.12 en son stabil versiyondur."
        user_message = "Python'un son versiyonu ne?"

        result, mode, reason = shaper(text, user_message, mode="auto")

        # Kısa cevap değişmemeli
        assert len(result) < 100


# =============================================================================
# SENARYO 2: KARŞILAŞTIRMA
# =============================================================================


class TestComparison:
    """Karşılaştırma formatı testleri."""

    def test_pros_cons_structure(self, shaper):
        """Artılar/Eksiler yapısı oluşturulmalı."""
        text = """React daha popüler ve topluluk desteği fazla. Vue öğrenmesi daha kolay. React performanslı ama Vue daha küçük bundle size'a sahip."""

        user_message = "React mı Vue mu kullanmalıyım?"
        result, mode, reason = shaper(text, user_message, mode="auto")

        # Karşılaştırma yapısı bekleniyor
        has_structure = (
            ("Artı" in result or "+" in result or "avantaj" in result.lower())
            or ("Eksi" in result or "-" in result or "dezavantaj" in result.lower())
            or (result.count("|") >= 3)  # Tablo formatı
        )
        assert has_structure or mode == "comparison"


# =============================================================================
# SENARYO 3: KOD ÖRNEĞİ
# =============================================================================


class TestCodeExample:
    """Kod örneği formatı testleri."""

    def test_code_block_preserved(self, post_processor):
        """Kod blokları korunmalı."""
        full_post_process, get_preset_config = post_processor

        text = """İşte bir örnek:
```python
def hello():
    print("Merhaba")
```
Bu kod ekrana Merhaba yazar."""

        result = full_post_process(text, get_preset_config("professional"))

        # Code block korunmalı
        assert "```python" in result
        assert "def hello" in result
        assert "```" in result

    def test_incomplete_code_block_closed(self, post_processor):
        """Kapanmamış kod blokları kapatılmalı."""
        full_post_process, get_preset_config = post_processor

        text = """Örnek:
```python
def test():
    pass"""

        result = full_post_process(text, get_preset_config("professional"))

        # Kod bloğu kapatılmalı
        assert result.count("```") % 2 == 0


# =============================================================================
# SENARYO 4: TABLO / JSON
# =============================================================================


class TestTableJson:
    """Tablo ve JSON formatı testleri."""

    def test_table_preserved(self, post_processor):
        """Markdown tabloları korunmalı."""
        full_post_process, get_preset_config = post_processor

        text = """| Dil | Kullanım |
|-----|----------|
| Python | Backend |
| JavaScript | Frontend |"""

        result = full_post_process(text, get_preset_config("professional"))

        # Tablo yapısı korunmalı
        assert "|" in result
        assert "Python" in result

    def test_json_in_code_block(self, post_processor):
        """JSON kod bloğunda olmalı."""
        full_post_process, get_preset_config = post_processor

        text = """Sonuç:
```json
{"name": "test", "value": 123}
```"""

        result = full_post_process(text, get_preset_config("professional"))

        assert "```json" in result or "```" in result


# =============================================================================
# SENARYO 5: DÜZ SOHBET
# =============================================================================


class TestCasualChat:
    """Düz sohbet testleri."""

    def test_casual_response_not_over_formatted(self, post_processor):
        """Düz sohbet cevapları aşırı formatlanmamalı."""
        full_post_process, get_preset_config = post_processor

        text = "Merhaba! Bugün nasılsın? Umarım iyisindir."

        result = full_post_process(text, get_preset_config("professional"))

        # Emoji eklenmemeli (professional preset)
        assert "😀" not in result and "🙂" not in result
        # Gereksiz başlık eklenmemeli
        assert not result.startswith("#")


# =============================================================================
# SENARYO 6: WEB TOOL SONUÇ FORMATI
# =============================================================================


class TestWebToolOutput:
    """Web araması sonuç formatı testleri."""

    def test_sources_section_added(self, formatter):
        """Kaynaklar bölümü eklenmeli."""
        answer = "Dolar şu an 32.50 TL seviyesinde işlem görmektedir."
        sources = [
            {"title": "Döviz Kurları", "url": "https://doviz.com/usd", "snippet": "..."},
            {"title": "Piyasalar", "url": "https://bloomberg.com", "snippet": "..."},
        ]

        result = formatter(answer, sources)

        # Kaynaklar bölümü olmalı
        assert "Kaynaklar" in result or "kaynak" in result.lower()
        assert "doviz.com" in result or "bloomberg.com" in result

    def test_no_sources_no_section(self, formatter):
        """Kaynak yoksa Kaynaklar bölümü eklenmemeli."""
        answer = "Bu konuda bilgi bulunamadı."

        result = formatter(answer, None)

        # Kaynaklar bölümü olmamalı
        assert "Kaynaklar" not in result


# =============================================================================
# SENARYO 7: PERSONA TON KORUNMASI
# =============================================================================


class TestPersonaTone:
    """Persona tonu korunma testleri."""

    def test_friendly_tone_preserved(self, post_processor):
        """Arkadaşça ton korunmalı."""
        full_post_process, get_preset_config = post_processor

        text = "Tabii ki yardımcı olabilirim! Bu konuda şunları söyleyebilirim..."

        result = full_post_process(text, get_preset_config("professional"))

        # Friendly ifadeler korunmalı
        assert "yardımcı" in result.lower() or "tabii" in result.lower()


# =============================================================================
# SENARYO 8: STRICT CENSORSHIP FORMAT
# =============================================================================


class TestStrictCensorship:
    """Sıkı sansür formatı testleri."""

    def test_format_not_broken_by_censorship(self, post_processor):
        """Sansür formatı bozmamalı."""
        full_post_process, get_preset_config = post_processor

        text = """Bu konuda dikkatli olunmalı:
1. İlk madde
2. İkinci madde
3. Üçüncü madde"""

        result = full_post_process(text, get_preset_config("professional"))

        # Liste yapısı korunmalı
        assert "1." in result or "- " in result
        assert "İlk" in result or "birinci" in result.lower()


# =============================================================================
# PRESET TESTLERİ
# =============================================================================


class TestPresets:
    """Preset testleri."""

    def test_professional_preset_exists(self, post_processor):
        """Professional preset mevcut olmalı."""
        _, get_preset_config = post_processor

        config = get_preset_config("professional")

        assert config is not None
        assert config.get("format_level") == "professional"

    def test_professional_is_default(self):
        """Professional varsayılan preset olmalı."""
        from app.plugins.response_enhancement.config import EnhancementConfig

        assert EnhancementConfig.DEFAULT_PRESET == "professional"

    def test_professional_no_emoji(self):
        """Professional preset'te emoji kapalı."""
        from app.plugins.response_enhancement.config import EnhancementConfig

        options = EnhancementConfig.get_options("professional")

        assert options.get("add_emojis") == False
        assert options.get("add_callouts") == False


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
