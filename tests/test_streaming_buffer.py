"""
Tests for Streaming Buffer Memory Management
=============================================

Bu test dosyası streaming buffer'ın memory leak'i önlediğini doğrular.
"""

import asyncio

import pytest

from app.chat.streaming_buffer import StreamingBuffer


class TestStreamingBuffer:
    """StreamingBuffer unit testleri"""

    def test_buffer_initialization(self):
        """Buffer doğru initialize ediliyor mu?"""
        buffer = StreamingBuffer(max_chunks=100)

        assert buffer.max_chunks == 100
        assert len(buffer) == 0
        assert buffer._finalized is None

    def test_append_chunks(self):
        """Chunk'lar doğru ekleniyor mu?"""
        buffer = StreamingBuffer(max_chunks=10)

        buffer.append("Hello")
        buffer.append(" ")
        buffer.append("World")

        assert len(buffer) == 3
        assert buffer._total_chunks_received == 3

    def test_circular_buffer_overflow(self):
        """Buffer dolunca en eski chunk siliniyor mu?"""
        buffer = StreamingBuffer(max_chunks=5)

        # 10 chunk ekle (max 5)
        for i in range(10):
            buffer.append(f"chunk{i}")

        # Sadece son 5 chunk kalmalı
        assert len(buffer) == 5
        assert buffer._chunks_dropped == 5

        # Son 5 chunk kontrol et
        chunks = list(buffer.chunks)
        assert chunks == ["chunk5", "chunk6", "chunk7", "chunk8", "chunk9"]

    def test_finalize(self):
        """Finalize doğru çalışıyor mu?"""
        buffer = StreamingBuffer(max_chunks=100)

        buffer.append("Hello")
        buffer.append(" ")
        buffer.append("World")

        result = buffer.finalize()

        assert result == "Hello World"
        assert buffer._finalized == "Hello World"
        assert len(buffer.chunks) == 0  # Buffer cleared

    def test_finalize_multiple_calls(self):
        """Finalize birden fazla çağrılabilir mi?"""
        buffer = StreamingBuffer(max_chunks=100)

        buffer.append("Test")

        result1 = buffer.finalize()
        result2 = buffer.finalize()

        assert result1 == result2 == "Test"

    def test_clear(self):
        """Clear tüm data'yı temizliyor mu?"""
        buffer = StreamingBuffer(max_chunks=100)

        buffer.append("Test")
        buffer.finalize()

        buffer.clear()

        assert len(buffer) == 0
        assert buffer._finalized is None
        assert buffer._total_chunks_received == 0

    def test_empty_chunks_ignored(self):
        """Boş chunk'lar ignore ediliyor mu?"""
        buffer = StreamingBuffer(max_chunks=100)

        buffer.append("")
        buffer.append("Valid")

        assert len(buffer) == 1
        assert buffer._total_chunks_received == 1

    def test_stats(self):
        """Stats doğru döndürülüyor mu?"""
        buffer = StreamingBuffer(max_chunks=5)

        for i in range(7):
            buffer.append(f"chunk{i}")

        stats = buffer.get_stats()

        assert stats["max_chunks"] == 5
        assert stats["current_chunks"] == 5
        assert stats["total_received"] == 7
        assert stats["dropped"] == 2
        assert stats["finalized"] is False

        buffer.finalize()
        stats = buffer.get_stats()
        assert stats["finalized"] is True


class TestStreamingBufferMemoryManagement:
    """Memory management testleri"""

    def test_memory_usage_stays_bounded(self):
        """Memory kullanımı sınırlı kalıyor mu?"""
        buffer = StreamingBuffer(max_chunks=100)

        # 1000 chunk ekle (max 100)
        for i in range(1000):
            buffer.append("x" * 100)  # 100 char chunks

        # Buffer max 100 chunk tutuyor
        assert len(buffer) == 100
        assert buffer._chunks_dropped == 900

        # Finalize sonrası buffer temiz
        result = buffer.finalize()
        assert len(buffer.chunks) == 0

    def test_large_chunks_handled(self):
        """Büyük chunk'lar handle ediliyor mu?"""
        buffer = StreamingBuffer(max_chunks=10)

        # 10KB chunk'lar ekle
        for i in range(20):
            buffer.append("x" * 10000)

        result = buffer.finalize()

        # Son 10 chunk var (10 * 10KB = 100KB)
        assert len(result) == 10 * 10000
        assert len(buffer.chunks) == 0  # Cleared after finalize


@pytest.mark.asyncio
class TestStreamingBufferAsyncUsage:
    """Async kullanım testleri"""

    async def test_async_streaming_simulation(self):
        """Async streaming simülasyonu"""
        buffer = StreamingBuffer(max_chunks=100)

        async def mock_stream():
            """Mock streaming source"""
            for i in range(50):
                await asyncio.sleep(0.001)  # Simulate async delay
                yield f"chunk{i} "

        # Stream chunks to buffer
        async for chunk in mock_stream():
            buffer.append(chunk)

        result = buffer.finalize()

        assert "chunk0" in result
        assert "chunk49" in result
        assert len(buffer.chunks) == 0

    async def test_concurrent_buffers(self):
        """Concurrent buffer'lar interference yapmıyor mu?"""

        async def process_stream(buffer_id: int):
            buffer = StreamingBuffer(max_chunks=50)

            for i in range(100):
                buffer.append(f"buffer{buffer_id}_chunk{i}")
                await asyncio.sleep(0.001)

            return buffer.finalize()

        # 3 concurrent stream
        results = await asyncio.gather(process_stream(1), process_stream(2), process_stream(3))

        # Her buffer kendi data'sını koruyor
        assert "buffer1_" in results[0]
        assert "buffer2_" in results[1]
        assert "buffer3_" in results[2]

        # Interference yok
        assert "buffer2_" not in results[0]
        assert "buffer1_" not in results[1]


class TestStreamingBufferEdgeCases:
    """Edge case testleri"""

    def test_max_chunks_zero(self):
        """max_chunks=0 durumu"""
        buffer = StreamingBuffer(max_chunks=0)

        buffer.append("Test")

        # Deque maxlen=0 hiçbir şey tutmaz
        assert len(buffer) == 0
        assert buffer.finalize() == ""

    def test_max_chunks_one(self):
        """max_chunks=1 durumu"""
        buffer = StreamingBuffer(max_chunks=1)

        buffer.append("First")
        buffer.append("Second")
        buffer.append("Third")

        # Sadece son chunk
        assert len(buffer) == 1
        assert list(buffer.chunks) == ["Third"]

    def test_unicode_chunks(self):
        """Unicode karakterler handle ediliyor mu?"""
        buffer = StreamingBuffer(max_chunks=100)

        buffer.append("Merhaba ")
        buffer.append("🌍 ")
        buffer.append("Dünya!")

        result = buffer.finalize()
        assert result == "Merhaba 🌍 Dünya!"

    def test_very_long_single_chunk(self):
        """Çok uzun tek chunk"""
        buffer = StreamingBuffer(max_chunks=10)

        # 1MB chunk
        long_chunk = "x" * (1024 * 1024)
        buffer.append(long_chunk)

        result = buffer.finalize()
        assert len(result) == 1024 * 1024
        assert len(buffer.chunks) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
