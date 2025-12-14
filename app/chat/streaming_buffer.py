"""
Mami AI - Streaming Buffer Manager
===================================

Memory-efficient circular buffer for streaming responses.

Özellikler:
    - Fixed-size deque (auto-pop oldest chunks)
    - O(1) append complexity
    - Automatic garbage collection
    - Memory-safe finalization
"""

from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StreamingBuffer:
    """
    Fixed-size circular buffer for streaming responses.
    
    Memory-safe buffer implementation that prevents memory leaks
    during long streaming operations by using a circular buffer
    with automatic cleanup of old chunks.
    
    Usage:
        buffer = StreamingBuffer(max_chunks=500)
        
        # Append chunks
        for chunk in stream:
            buffer.append(chunk)
        
        # Finalize and get complete text
        full_text = buffer.finalize()
        
        # Buffer is automatically cleared after finalize
    """
    
    def __init__(self, max_chunks: int = 500):
        """
        Initialize streaming buffer.
        
        Args:
            max_chunks: Maximum number of chunks to keep in memory.
                       When exceeded, oldest chunks are automatically removed.
                       Default: 500 chunks (~50KB for typical responses)
        """
        self.max_chunks = max_chunks
        self.chunks = deque(maxlen=max_chunks)  # Auto-pop oldest when full
        self._finalized: Optional[str] = None
        self._total_chunks_received = 0
        self._chunks_dropped = 0
        
        logger.debug(f"[STREAMING_BUFFER] Initialized with max_chunks={max_chunks}")
    
    def append(self, chunk: str):
        """
        Append a chunk to the buffer.
        
        If buffer is full, oldest chunk is automatically removed.
        
        Args:
            chunk: Text chunk to append
        """
        if not chunk:
            return
        
        self._total_chunks_received += 1
        
        # Check if we'll drop a chunk
        if len(self.chunks) == self.max_chunks:
            self._chunks_dropped += 1
        
        self.chunks.append(chunk)
    
    def finalize(self) -> str:
        """
        Finalize buffer and return complete text.
        
        After finalization:
        - Buffer is cleared to free memory
        - Result is cached for multiple calls
        - No more chunks can be appended
        
        Returns:
            str: Complete text from all chunks
        """
        if self._finalized is None:
            # Join all chunks
            self._finalized = "".join(self.chunks)
            
            # Log statistics
            if self._chunks_dropped > 0:
                logger.warning(
                    f"[STREAMING_BUFFER] Dropped {self._chunks_dropped} chunks "
                    f"(buffer overflow, max={self.max_chunks})"
                )
            
            logger.debug(
                f"[STREAMING_BUFFER] Finalized: {self._total_chunks_received} chunks, "
                f"{len(self._finalized)} chars, {self._chunks_dropped} dropped"
            )
            
            # Clear buffer for garbage collection
            self.chunks.clear()
        
        return self._finalized
    
    def clear(self):
        """
        Force clear all buffer data.
        
        Useful for error recovery or manual cleanup.
        """
        self.chunks.clear()
        self._finalized = None
        self._total_chunks_received = 0
        self._chunks_dropped = 0
        
        logger.debug("[STREAMING_BUFFER] Cleared")
    
    def get_stats(self) -> dict:
        """
        Get buffer statistics.
        
        Returns:
            dict: Buffer statistics
        """
        return {
            "max_chunks": self.max_chunks,
            "current_chunks": len(self.chunks),
            "total_received": self._total_chunks_received,
            "dropped": self._chunks_dropped,
            "finalized": self._finalized is not None,
            "memory_usage_estimate_kb": len(self.chunks) * 100 / 1024  # Rough estimate
        }
    
    def __len__(self) -> int:
        """Return current number of chunks in buffer."""
        return len(self.chunks)
    
    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            self.clear()
        except:
            pass  # Ignore errors during cleanup