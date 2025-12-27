"""
Response Enhancement Plugin - Konfigürasyon
===========================================

Plugin ayarları ve seçenekleri
"""

from typing import Any, Dict


class EnhancementConfig:
    """Plugin konfigürasyonu"""

    # Varsayılan ayarlar
    DEFAULT_OPTIONS = {
        # Prompt enhancement
        "enhance_prompts": True,
        # Response processing
        "enable_smart_shaping": True,
        "enable_markdown": True,
        "enable_beautification": True,
        # Beautification detayları
        "add_emojis": True,
        "add_callouts": True,
        "add_separators": True,
        "enhance_code_blocks": True,
        "create_summary_box": True,
        # Kalite kontrol
        "min_response_length": 50,
        "max_emoji_count": 6,
    }

    # Format presetleri
    PRESETS = {
        "minimal": {
            "enhance_prompts": False,
            "enable_smart_shaping": False,
            "enable_markdown": True,
            "enable_beautification": False,
            "add_emojis": False,
        },
        "normal": {
            "enhance_prompts": True,
            "enable_smart_shaping": True,
            "enable_markdown": True,
            "enable_beautification": False,
            "add_emojis": False,
        },
        "rich": {
            "enhance_prompts": True,
            "enable_smart_shaping": True,
            "enable_markdown": True,
            "enable_beautification": True,
            "add_emojis": True,
            "add_callouts": True,
            "add_separators": True,
            "enhance_code_blocks": True,
            "create_summary_box": True,
        },
        # YENİ: ChatGPT kalitesinde profesyonel çıktı
        "professional": {
            "enhance_prompts": True,
            # SMART SHAPING KAPALI - "Özet:" header ekliyor
            "enable_smart_shaping": False,
            "enable_markdown": True,
            # BEAUTIFICATION KAPALI - emoji/callout/📌 Özet ekliyor
            "enable_beautification": False,
            "enable_code_enhancement": True,
            "enable_data_formatting": True,
            # Emoji ve callout KAPALI - temiz profesyonel görünüm
            "add_emojis": False,
            "add_callouts": False,
            "add_separators": False,
            "create_summary_box": False,
            # Kod blokları aktif
            "enhance_code_blocks": True,
            # Türkçe optimizasyonu (hafif)
            "turkish_optimization": True,
            # Answer shaping KAPALI
            "enable_answer_shaping": False,
        },
    }

    # Varsayılan preset
    DEFAULT_PRESET = "professional"

    @classmethod
    def get_options(cls, preset: str = None, custom: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Konfigürasyon seçeneklerini al.

        Args:
            preset: 'minimal', 'normal', 'rich', 'professional' (None ise DEFAULT_PRESET)
            custom: Özel ayarlar (preset'i override eder)

        Returns:
            Birleştirilmiş ayarlar
        """
        # Preset'i al (None ise default)
        preset = preset or cls.DEFAULT_PRESET
        options = cls.PRESETS.get(preset, cls.PRESETS[cls.DEFAULT_PRESET]).copy()

        # Custom ayarları ekle
        if custom:
            options.update(custom)

        return options

    @classmethod
    def validate_options(cls, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ayarları doğrula ve varsayılanlarla doldur.

        Args:
            options: Kullanıcı ayarları

        Returns:
            Doğrulanmış ayarlar
        """
        validated = cls.DEFAULT_OPTIONS.copy()
        validated.update(options)
        return validated
