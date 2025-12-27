import threading
import time

import schedule

from app.auth.user_manager import list_users
from app.core.logger import get_logger
from app.memory.store import cleanup_old_memories

logger = get_logger(__name__)


async def daily_memory_cleanup():
    """Her gece çalışır, tüm kullanıcıların eski hafızalarını temizler (Vektör sisteminde NO-OP)."""
    logger.info("[MAINTENANCE] Günlük hafıza temizliği başlatılıyor...")
    users = list_users()
    total_removed = 0

    # DİKKAT: cleanup_old_memories fonksiyonu, yeni ChromaDB mimarisinde
    # index tabanlı çalıştığı için artık hiçbir işlem yapmaz (NO-OP).
    # Bu fonksiyon sadece eski mimariden kalmadır ve ileride arşive alınmalıdır.

    for user in users:
        # cleanup_old_memories çağrısı, ChromaDB entegrasyonundan sonra pasiftir.
        removed = await cleanup_old_memories(user.username)
        total_removed += removed

    logger.info(f"[MAINTENANCE] Temizlik tamamlandı. {total_removed} kayıt silindi (çoğu NO-OP).")


def start_maintenance_scheduler():
    """Bakım görevlerini başlatır."""
    import asyncio

    def daily_cleanup_wrapper():
        """Async cleanup'ı sync context'te çalıştıran wrapper."""
        try:
            asyncio.run(daily_memory_cleanup())
        except Exception as e:
            logger.error(f"[MAINTENANCE] Cleanup failed: {e}")

    # Her gün sabah 03:00'te hafıza temizliğini planla
    schedule.every().day.at("03:00").do(daily_cleanup_wrapper)

    def run_scheduler():
        """Scheduler'ı arka planda sürekli çalıştıran döngü."""
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Her saat kontrol et

    thread = threading.Thread(target=run_scheduler, daemon=True, name="maintenance")
    thread.start()
    logger.info("[MAINTENANCE] Bakım scheduler başlatıldı.")
