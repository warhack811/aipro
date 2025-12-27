"""
Mami AI - Safe Callback Executor
=================================

Image generation callback'lerini güvenli şekilde çalıştırır.

Özellikler:
    - Exception handling
    - Automatic retry with exponential backoff
    - Failed callback tracking
    - Async/sync callback support
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class SafeCallbackExecutor:
    """
    Safe callback execution with retry and error tracking.

    Prevents job queue crashes when callback functions fail.
    """

    def __init__(self, max_retries: int = 2, retry_delay: float = 0.5):
        """
        Initialize safe callback executor.

        Args:
            max_retries: Maximum retry attempts (default: 2)
            retry_delay: Base delay between retries in seconds (default: 0.5)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.failed_callbacks: List[Dict[str, Any]] = []
        self._max_failed_history = 100  # Keep last 100 failures

    async def execute(
        self, callback: Callable, result: str, job_id: str, context: Dict[str, Any] | None = None
    ) -> bool:
        """
        Execute callback with retry logic.

        Args:
            callback: Callback function to execute
            result: Result to pass to callback
            job_id: Job identifier for tracking
            context: Optional context information

        Returns:
            bool: True if successful, False if all retries failed
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Support both async and sync callbacks
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    # Run sync callback in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, callback, result)

                # Success
                logger.debug(f"[SAFE_CALLBACK] Job {job_id} callback succeeded (attempt {attempt+1})")
                return True

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[SAFE_CALLBACK] Job {job_id} callback failed " f"(attempt {attempt+1}/{self.max_retries}): {e}"
                )

                # Retry with exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

        # All retries failed - log and track
        logger.error(
            f"[SAFE_CALLBACK] Job {job_id} callback failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

        self._track_failed_callback(job_id, result, last_error or Exception("Unknown error"), context)
        return False

    def _track_failed_callback(self, job_id: str, result: str, error: Exception, context: Dict[str, Any] | None = None):
        """Track failed callback for debugging."""
        failure_record = {
            "job_id": job_id,
            "result_preview": result[:100] if result else None,
            "error": str(error),
            "error_type": type(error).__name__,
            "failed_at": datetime.utcnow().isoformat(),
            "context": context or {},
            "retry_count": self.max_retries,
        }

        self.failed_callbacks.append(failure_record)

        # Limit history size
        if len(self.failed_callbacks) > self._max_failed_history:
            self.failed_callbacks = self.failed_callbacks[-self._max_failed_history :]

    def get_failed_count(self) -> int:
        """Get total number of failed callbacks."""
        return len(self.failed_callbacks)

    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failed callbacks."""
        return self.failed_callbacks[-limit:]

    def clear_failed_history(self):
        """Clear failed callback history."""
        self.failed_callbacks.clear()
        logger.info("[SAFE_CALLBACK] Failed callback history cleared")


# Global executor instance
safe_executor = SafeCallbackExecutor(max_retries=2, retry_delay=0.5)
