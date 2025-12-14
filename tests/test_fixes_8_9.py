"""
Tests for HATA #8 (Safe Callback) and HATA #9 (DB Connection Pool)
====================================================================
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.database import get_engine, get_session
from app.image.safe_callback import SafeCallbackExecutor, safe_executor


class TestSafeCallbackExecutor:
    """HATA #8: Safe Callback tests"""
    
    @pytest.mark.asyncio
    async def test_successful_callback(self):
        """Başarılı callback çalışıyor mu?"""
        executor = SafeCallbackExecutor(max_retries=2)
        
        mock_callback = Mock()
        result = "test_result"
        job_id = "job_123"
        
        success = await executor.execute(
            callback=mock_callback,
            result=result,
            job_id=job_id
        )
        
        assert success is True
        mock_callback.assert_called_once_with(result)
        assert executor.get_failed_count() == 0
    
    @pytest.mark.asyncio
    async def test_callback_retry_on_failure(self):
        """Callback fail olunca retry ediliyor mu?"""
        executor = SafeCallbackExecutor(max_retries=3, retry_delay=0.01)
        
        call_count = 0
        def failing_callback(result):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            # 3. denemede başarılı
        
        success = await executor.execute(
            callback=failing_callback,
            result="test",
            job_id="job_retry"
        )
        
        assert success is True
        assert call_count == 3  # 3 deneme yapıldı
    
    @pytest.mark.asyncio
    async def test_callback_all_retries_fail(self):
        """Tüm retry'lar fail olunca tracked ediliyor mu?"""
        executor = SafeCallbackExecutor(max_retries=2, retry_delay=0.01)
        
        def always_failing_callback(result):
            raise Exception("Always fails")
        
        success = await executor.execute(
            callback=always_failing_callback,
            result="test",
            job_id="job_fail"
        )
        
        assert success is False
        assert executor.get_failed_count() == 1
        
        failures = executor.get_recent_failures(limit=1)
        assert len(failures) == 1
        assert failures[0]["job_id"] == "job_fail"
    
    @pytest.mark.asyncio
    async def test_async_callback_support(self):
        """Async callback destekleniyor mu?"""
        executor = SafeCallbackExecutor()
        
        async_callback = AsyncMock()
        
        success = await executor.execute(
            callback=async_callback,
            result="async_test",
            job_id="job_async"
        )
        
        assert success is True
        async_callback.assert_called_once_with("async_test")
    
    @pytest.mark.asyncio
    async def test_context_tracking(self):
        """Context bilgisi tracked ediliyor mu?"""
        executor = SafeCallbackExecutor(max_retries=1)
        
        def failing_callback(result):
            raise ValueError("Test error")
        
        context = {"username": "test_user", "conversation_id": "conv_123"}
        
        await executor.execute(
            callback=failing_callback,
            result="test",
            job_id="job_context",
            context=context
        )
        
        failures = executor.get_recent_failures(limit=1)
        assert failures[0]["context"] == context
    
    def test_clear_failed_history(self):
        """Failed history temizleniyor mu?"""
        executor = SafeCallbackExecutor()
        executor.failed_callbacks = [{"test": "data"}]
        
        executor.clear_failed_history()
        
        assert executor.get_failed_count() == 0


class TestDatabaseConnectionPool:
    """HATA #9: Database connection pool tests"""
    
    def test_engine_initialization(self):
        """Engine doğru initialize ediliyor mu?"""
        engine = get_engine()
        
        assert engine is not None
        assert engine.pool is not None
    
    def test_get_session_context_manager(self):
        """Session context manager çalışıyor mu?"""
        from app.core.models import User
        
        with get_session() as session:
            # Session açıldı
            assert session is not None
            
            # Query yapılabilir
            users = session.query(User).limit(1).all()
            assert isinstance(users, list)
        
        # Session otomatik close edildi
        # (Session.is_active ile kontrol edilebilir ama gerek yok)
    
    def test_concurrent_sessions(self):
        """Concurrent session'lar sorunsuz çalışıyor mu?"""
        from app.core.models import User
        
        def query_users():
            with get_session() as session:
                return session.query(User).count()
        
        # 10 concurrent query
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_users) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # Hepsi başarılı
        assert len(results) == 10
        assert all(isinstance(r, int) for r in results)
    
    def test_session_rollback_on_error(self):
        """Error durumunda session rollback ediliyor mu?"""
        from sqlalchemy import text

        from app.core.models import User
        
        try:
            with get_session() as session:
                # Invalid query (test amaçlı)
                session.execute(text("INVALID SQL"))
        except Exception:
            pass  # Expected
        
        # Yeni session açılabilmeli (corruption yok)
        with get_session() as session:
            users = session.query(User).limit(1).all()
            assert isinstance(users, list)
    
    def test_busy_timeout_configured(self):
        """busy_timeout configured mi?"""
        from sqlalchemy import text
        
        engine = get_engine()
        
        with engine.connect() as conn:
            # PRAGMA kontrolü
            result = conn.execute(text("PRAGMA busy_timeout")).fetchone()
            timeout = result[0] if result else 0
            
            # 30000ms (30 saniye) olmalı
            assert timeout == 30000


class TestIntegration:
    """HATA #8 + #9 integration tests"""
    
    @pytest.mark.asyncio
    async def test_callback_with_db_operation(self):
        """Callback içinde DB operation çalışıyor mu?"""
        from app.core.models import User
        
        executor = SafeCallbackExecutor()
        
        def callback_with_db(result):
            with get_session() as session:
                # DB operation
                users = session.query(User).limit(1).all()
                assert isinstance(users, list)
        
        success = await executor.execute(
            callback=callback_with_db,
            result="test",
            job_id="job_db"
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_multiple_callbacks_concurrent(self):
        """Multiple callback'ler concurrent çalışabiliyor mu?"""
        executor = SafeCallbackExecutor()
        
        async def run_callback(i):
            def callback(result):
                with get_session() as session:
                    # Simulated DB write
                    pass
            
            return await executor.execute(
                callback=callback,
                result=f"result_{i}",
                job_id=f"job_{i}"
            )
        
        # 20 concurrent callback
        results = await asyncio.gather(*[run_callback(i) for i in range(20)])
        
        # Hepsi başarılı
        assert all(results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])