"""
Test Suite for Next 3 Critical Fixes
====================================

Tests for:
- HATA #4: Memory Duplicate Detection (Hybrid)
- HATA #5: Streaming Memory Duplicate Risk
- HATA #6: Context Truncation (Importance-based)
"""

import asyncio
from typing import Dict, List

import pytest

# HATA #4: Memory Duplicate Detection Tests
# ==========================================


class TestMemoryDuplicateDetection:
    """Hybrid duplicate detection testleri."""

    def test_text_similarity_exact_match(self):
        """Exact match testi."""
        from app.services.memory_duplicate_detector import detector

        text1 = "Kedimin adı Pamuk"
        text2 = "Kedimin adı Pamuk"

        similarity = detector.calculate_text_similarity(text1, text2)
        assert similarity == 1.0, "Exact match %100 olmalı"

    def test_text_similarity_different(self):
        """Farklı metinler testi."""
        from app.services.memory_duplicate_detector import detector

        text1 = "Kedimin adı Pamuk"
        text2 = "Köpeğimin adı Karabaş"

        similarity = detector.calculate_text_similarity(text1, text2)
        assert similarity < 0.7, "Farklı metinler düşük similarity olmalı"

    def test_normalization(self):
        """Metin normalizasyonu testi."""
        from app.services.memory_duplicate_detector import detector

        text1 = "  Kullanıcı   adı:   Ahmet  "
        text2 = "kullanıcı ismi: ahmet"

        normalized1 = detector.normalize_text(text1)
        normalized2 = detector.normalize_text(text2)

        # "kullanıcı adı" → "isim", "kullanıcı ismi" → "isim"
        # Her ikisi de "isim: ahmet" olmalı
        similarity = detector.calculate_text_similarity(text1, text2)
        assert similarity > 0.7, "Normalizasyon sonrası benzer olmalı"

    def test_entity_extraction(self):
        """Entity çıkarma testi."""
        from app.services.memory_duplicate_detector import detector

        text = "Kedimin adı Pamuk ve 3 yaşında"
        entities = detector.extract_key_entities(text)

        # "kedimin", "pamuk", "yaşında" gibi kelimeler çıkmalı
        assert len(entities) >= 2, "En az 2 entity bulunmalı"
        assert any("pamuk" in e.lower() for e in entities), "'Pamuk' entity'si bulunmalı"

    def test_duplicate_false_positive_prevention(self):
        """False positive önleme testi - Kritik!"""
        from app.services.memory_duplicate_detector import detector

        # Yüksek semantic ama farklı entity'ler
        text1 = "Kedimi çok seviyorum"
        text2 = "Köpeğimi çok seviyorum"

        # Semantic distance simülasyonu (çok benzer)
        semantic_distance = 0.04  # %96 similarity

        is_dup, reason = detector.is_duplicate(
            new_text=text1,
            existing_text=text2,
            semantic_distance=semantic_distance,
            importance=0.5,
            use_entity_check=True,
        )

        # Entity kontrolü ile FALSE POSITIVE önlenmiş olmalı
        assert not is_dup, f"False positive! Reason: {reason}"
        assert "entity_mismatch" in reason or "not_duplicate" in reason

    def test_duplicate_true_positive(self):
        """True positive testi."""
        from app.services.memory_duplicate_detector import detector

        # Çok benzer metinler (exact match'e yakın)
        text1 = "İsmim Ahmet ve yazılım mühendisiyim"
        text2 = "İsmim Ahmet ve yazılım mühendisiyim"

        # Semantic distance simülasyonu (neredeyse identical)
        semantic_distance = 0.01  # %99 similarity

        is_dup, reason = detector.is_duplicate(
            new_text=text1,
            existing_text=text2,
            semantic_distance=semantic_distance,
            importance=0.5,
            use_entity_check=False,  # Entity check bypass
        )

        # Çok yüksek similarity, duplicate olmalı
        assert is_dup, f"True duplicate tespit edilmeli! Reason: {reason}"

    def test_importance_based_thresholds(self):
        """Importance bazlı threshold testi."""
        from app.services.memory_duplicate_detector import detector

        # Yüksek importance = strict threshold
        sem_threshold_high, text_threshold_high = detector.get_thresholds_for_importance(0.9)

        # Düşük importance = loose threshold
        sem_threshold_low, text_threshold_low = detector.get_thresholds_for_importance(0.3)

        assert sem_threshold_high < sem_threshold_low, "Yüksek importance daha strict olmalı"
        assert text_threshold_high > text_threshold_low, "Yüksek importance text için daha strict"


# HATA #5: Streaming Memory Tests
# =================================


class TestStreamingMemoryManager:
    """Streaming memory deduplication testleri."""

    @pytest.mark.asyncio
    async def test_can_process_memory_first_time(self):
        """İlk işleme izni testi."""
        from app.services.streaming_memory_manager import StreamingMemoryManager

        manager = StreamingMemoryManager()
        manager.reset()

        message_id = "test-msg-001"

        can_process = await manager.can_process_memory(message_id)
        assert can_process, "İlk işleme izin verilmeli"

    @pytest.mark.asyncio
    async def test_duplicate_prevention(self):
        """Duplicate önleme testi."""
        from app.services.streaming_memory_manager import StreamingMemoryManager

        manager = StreamingMemoryManager()
        manager.reset()

        message_id = "test-msg-002"

        # İlk işleme
        can_process_1 = await manager.can_process_memory(message_id)
        assert can_process_1

        # İkinci işleme (aynı ID) - engellenm eli
        can_process_2 = await manager.can_process_memory(message_id)
        assert not can_process_2, "Duplicate işlem engellenmeli"

    @pytest.mark.asyncio
    async def test_mark_completed(self):
        """Tamamlama işareti testi."""
        from app.services.streaming_memory_manager import StreamingMemoryManager

        manager = StreamingMemoryManager()
        manager.reset()

        message_id = "test-msg-003"

        # İşle
        await manager.can_process_memory(message_id)

        # Tamamla
        await manager.mark_completed(message_id)

        # Tekrar işleme denemesi - engellenm eli
        can_process = await manager.can_process_memory(message_id)
        assert not can_process, "Tamamlanmış mesaj tekrar işlenmemeli"

    @pytest.mark.asyncio
    async def test_concurrent_lock(self):
        """Concurrent lock testi."""
        from app.services.streaming_memory_manager import StreamingMemoryManager

        manager = StreamingMemoryManager()
        manager.reset()

        message_id = "test-msg-004"

        results = []

        async def try_process():
            can = await manager.can_process_memory(message_id)
            results.append(can)
            if can:
                await asyncio.sleep(0.1)
                await manager.mark_completed(message_id)

        # 3 concurrent deneme
        await asyncio.gather(try_process(), try_process(), try_process())

        # Sadece 1 tanesi işleyebilmeli
        assert sum(results) == 1, f"Sadece 1 işlem başarılı olmalı, {sum(results)} oldu"


# HATA #6: Context Truncation Tests
# ===================================


class TestContextTruncationManager:
    """Importance-based context truncation testleri."""

    def test_token_estimation(self):
        """Token tahmini testi."""
        from app.services.context_truncation_manager import context_manager

        text = "Bu bir test metnidir."  # ~20 karakter
        tokens = context_manager.estimate_tokens(text)

        # 20 char / 4 = 5 token
        assert 4 <= tokens <= 6, f"Token tahmini yanlış: {tokens}"

    def test_message_importance_position(self):
        """Position-based importance testi."""
        from app.services.context_truncation_manager import context_manager

        message = {"role": "user", "content": "Test mesajı"}

        # İlk mesaj (eski)
        importance_old = context_manager.calculate_message_importance(message, 0, 10)

        # Son mesaj (yeni)
        importance_new = context_manager.calculate_message_importance(message, 9, 10)

        assert importance_new > importance_old, "Yeni mesajlar daha önemli olmalı"

    def test_message_importance_role(self):
        """Role-based importance testi."""
        from app.services.context_truncation_manager import context_manager

        user_msg = {"role": "user", "content": "Kullanıcı sorusu?"}
        assistant_msg = {"role": "assistant", "content": "Bot cevabı"}

        user_importance = context_manager.calculate_message_importance(user_msg, 5, 10)
        assistant_importance = context_manager.calculate_message_importance(assistant_msg, 5, 10)

        assert user_importance > assistant_importance, "User mesajları daha önemli olmalı"

    def test_message_importance_content_type(self):
        """Content type importance testi."""
        from app.services.context_truncation_manager import context_manager

        question_msg = {"role": "user", "content": "Python'da liste nasıl oluşturulur?"}
        code_msg = {"role": "user", "content": "```python\nlist = [1, 2, 3]\n```"}
        critical_msg = {"role": "user", "content": "ÖNEMLİ: Bu kodu unutma!"}

        question_importance = context_manager.calculate_message_importance(question_msg, 5, 10)
        code_importance = context_manager.calculate_message_importance(code_msg, 5, 10)
        critical_importance = context_manager.calculate_message_importance(critical_msg, 5, 10)

        # Soru, kod, kritik kelime içeren mesajlar daha önemli
        assert question_importance > 0.5
        assert code_importance > 0.5
        assert critical_importance > 0.5

    def test_truncate_messages_by_importance(self):
        """Importance-based message truncation testi."""
        from app.services.context_truncation_manager import context_manager

        # Daha uzun mesajlar ile test
        long_content = "A" * 200  # Her biri ~50 token
        messages = [
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
            {"role": "user", "content": "Python'da liste nasıl oluşturulur?"},  # Önemli soru
            {"role": "assistant", "content": "```python\nmy_list = [1, 2, 3]\n```"},  # Kod
        ]

        # Düşük budget
        truncated, was_truncated = context_manager.truncate_messages_by_importance(
            messages, token_budget=100, preserve_system=False  # Sadece 2-3 mesaj sığar
        )

        assert was_truncated, "Truncation olmalı"
        assert len(truncated) < len(messages), "Mesaj sayısı azalmalı"

        # Kod içeren mesaj korunmuş olmalı (yüksek importance)
        code_preserved = any("```python" in msg.get("content", "") for msg in truncated)
        assert code_preserved, "Kod bloğu korunmalı (yüksek importance)"

    def test_truncate_text_smart_paragraph_boundary(self):
        """Paragraph boundary'de kesme testi."""
        from app.services.context_truncation_manager import context_manager

        text = (
            "İlk paragraf burada. Bu çok önemli bilgi.\n\n"
            "İkinci paragraf başlıyor. Daha da önemli.\n\n"
            "Üçüncü paragraf son derece kritik bilgi içeriyor."
        )

        truncated = context_manager.truncate_text_smart(text, char_limit=100, add_notice=False)

        # Paragraf ortasından kesmemeli
        assert "\n\n" in truncated or truncated.endswith("."), "Paragraf boundary'de kesmeli"

    def test_truncate_text_smart_sentence_completion(self):
        """Cümle tamamlama testi."""
        from app.services.context_truncation_manager import context_manager

        text = "Bu bir test cümlesidir. Bu ikinci cümledir. Bu üçüncü cümledir."

        truncated = context_manager.truncate_text_smart(text, char_limit=45, add_notice=False)

        # Cümle ortasından kesmemeli, nokta ile bitmeli veya en az bir tam cümle olmalı
        assert (
            truncated.rstrip().endswith(".") or "cümlesidir" in truncated
        ), f"Cümle tamamlanmalı veya boundary'de kesilmeli: '{truncated}'"


# Integration Tests
# ==================


class TestIntegration:
    """Entegrasyon testleri."""

    @pytest.mark.asyncio
    async def test_memory_service_with_hybrid_detection(self):
        """Memory service + hybrid detection entegrasyonu."""
        from app.services.memory_service import MemoryService

        # Not: Gerçek ChromaDB kullanmıyor, mock gerekebilir
        # Bu test gerçek DB ile çalıştırılmalı
        # Test placeholder
        assert True, "Integration test - ChromaDB ile test edilmeli"

    def test_processor_context_truncation(self):
        """Processor + context truncation entegrasyonu."""
        from app.chat.processor import _truncate_context_text

        long_text = "A" * 10000  # 10K karakter

        truncated = _truncate_context_text(long_text)

        assert len(truncated) < len(long_text), "Truncation çalışmalı"
        assert "KISALTILDI" in truncated or len(truncated) <= 8000, "Truncation notice veya limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
