# image/job_queue.py
from __future__ import annotations

import asyncio
import threading
import time
from typing import Callable, Optional
from uuid import uuid4

from app.core.logger import get_logger
from app.image.flux_stub import generate_image_via_forge
from app.image.gpu_state import switch_to_flux, switch_to_gemma
from app.websocket_sender import ImageJobStatus, send_image_progress

logger = get_logger(__name__)


class ImageJob:
    def __init__(
        self,
        username: str,
        prompt: str,
        conversation_id: Optional[str],
        on_done: Callable[[str], None],
        job_id: Optional[str] = None,
        checkpoint_name: Optional[str] = None,
        message_id: Optional[int] = None,  # Güncellenecek mesaj ID'si
    ):
        self.username = username
        self.prompt = prompt
        self.conversation_id = conversation_id
        self.on_done = on_done
        self.progress = 0
        self.queue_pos = 0
        self.job_id = job_id or str(uuid4())
        self.checkpoint_name = checkpoint_name  # Opsiyonel checkpoint override
        self.message_id = message_id  # Güncellenecek mesaj ID'si


class ImageJobQueue:
    """
    Görsel üretim iş kuyruğu.

    Worker lazy initialization ile başlatılır - ilk iş eklendiğinde
    event loop hazır olduğunda çalışır.
    """

    def __init__(self):
        self._queue: "asyncio.Queue[ImageJob]" = asyncio.Queue()
        self._gpu_lock = asyncio.Lock()
        self._worker_task = None
        self._started = False
        self._current_job: ImageJob | None = None  # Aktif işlenen job
        self._cancelled_jobs: set[str] = set()  # İptal edilen job_id'ler

    def _ensure_worker_started(self):
        """Worker'ı lazily başlatır (event loop hazır olduğunda)."""
        if not self._started:
            try:
                loop = asyncio.get_running_loop()
                self._worker_task = loop.create_task(self._worker_loop())
                self._started = True
                logger.info("[IMAGE_QUEUE] Worker başlatıldı")
            except RuntimeError:
                # Event loop yok - startup event'te başlatılacak
                pass

    # ---------- ASYNC WORKER ----------
    async def _worker_loop(self) -> None:
        while True:
            job = await self._queue.get()

            # İptal edilmiş mi kontrol et
            if job.job_id in self._cancelled_jobs:
                logger.info(f"[IMAGE_QUEUE] ⏭️ Skipping cancelled job: {job.job_id}")
                self._cancelled_jobs.discard(job.job_id)
                self._queue.task_done()
                continue

            self._current_job = job
            await self._process_single_job(job)
            self._current_job = None
            self._queue.task_done()

    async def _process_single_job(self, job: ImageJob) -> None:
        logger.info(f"[IMAGE_QUEUE] Çiziliyor: user={job.username}, checkpoint={job.checkpoint_name}")
        try:
            # Üretim başlamadan önce cancelled kontrolü
            if job.job_id in self._cancelled_jobs:
                logger.info(f"[IMAGE_QUEUE] 🛑 Job cancelled before start: {job.job_id}")
                self._cancelled_jobs.discard(job.job_id)
                return

            switch_to_flux()
            # progress döngüsü generate_image_via_forge İÇİNDE
            # checkpoint_name'i Forge'a gönder
            image_url = await generate_image_via_forge(job.prompt, job, checkpoint_name=job.checkpoint_name)

            # Üretim sonrası cancelled kontrolü (interrupt sonrası)
            if job.job_id in self._cancelled_jobs:
                logger.info(f"[IMAGE_QUEUE] 🛑 Job was cancelled during processing: {job.job_id}")
                self._cancelled_jobs.discard(job.job_id)
                return

            job.on_done(image_url)
        except Exception as e:
            # Cancelled job'lar için error gönderme
            if job.job_id in self._cancelled_jobs:
                logger.info(f"[IMAGE_QUEUE] Job cancelled (exception ignored): {job.job_id}")
                self._cancelled_jobs.discard(job.job_id)
                return

            logger.error(f"[IMAGE_QUEUE] Resim hatası: {e}")
            # Hata durumunu WebSocket üzerinden gönder
            try:
                await send_image_progress(
                    username=job.username,
                    conversation_id=job.conversation_id,
                    job_id=job.job_id,
                    status=ImageJobStatus.ERROR,
                    progress=0,
                    queue_position=job.queue_pos,
                    prompt=job.prompt,
                    error=str(e),
                )
            except Exception as ws_err:
                logger.debug(f"[IMAGE_QUEUE] WS error notification failed: {ws_err}")
            job.on_done(f"(IMAGE ERROR) {e}")
        finally:
            switch_to_gemma()

    # ---------- KUYRUĞA EKLE ----------
    async def _send_queued_status(self, job: ImageJob, queue_pos: int) -> None:
        """İş kuyruğa alındığında QUEUED durumunu gönderir."""
        try:
            await send_image_progress(
                username=job.username,
                conversation_id=job.conversation_id,
                job_id=job.job_id,
                status=ImageJobStatus.QUEUED,
                progress=0,
                queue_position=queue_pos,
                prompt=job.prompt,
                estimated_seconds=queue_pos * 30,  # Her iş için ~30 saniye tahmin
            )
        except Exception as e:
            logger.debug(f"[IMAGE_QUEUE] WS queued notification failed: {e}")

    def add_job(self, job: ImageJob) -> int:
        """İşi kuyruğa ekler ve worker'ı başlatır."""
        # Worker'ın başlatıldığından emin ol
        self._ensure_worker_started()

        queue_pos = self._queue.qsize() + 1
        job.queue_pos = queue_pos
        self._queue.put_nowait(job)
        logger.info(f"[IMAGE_QUEUE] İş eklendi: {job.job_id}, pozisyon: {queue_pos}")

        # QUEUED durumunu async olarak gönder
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._send_queued_status(job, queue_pos))
        except RuntimeError:
            pass  # Event loop yok

        return queue_pos

    async def cancel_job(self, job_id: str, username: str) -> bool:
        """
        Job'u iptal et - hem kuyruktan hem aktif üretimden.
        Returns: True if cancelled, False if not found.
        """
        import httpx

        from app.core.config import settings

        # 1️⃣ KUYRUKTAN KALDIR
        temp_jobs = []
        found_job = None

        while not self._queue.empty():
            try:
                job = self._queue.get_nowait()
                if job.job_id == job_id and job.username == username:
                    found_job = job
                else:
                    temp_jobs.append(job)
            except asyncio.QueueEmpty:
                break

        # Diğer job'ları geri koy
        for job in temp_jobs:
            self._queue.put_nowait(job)

        if found_job:
            logger.info(f"[IMAGE_QUEUE] 🗑️ Job removed from queue: {job_id}")

            # Cancelled durumunu gönder
            try:
                await send_image_progress(
                    username=found_job.username,
                    conversation_id=found_job.conversation_id,
                    job_id=found_job.job_id,
                    status=ImageJobStatus.ERROR,
                    progress=0,
                    queue_position=0,
                    prompt=found_job.prompt,
                    error="İptal edildi",
                )
            except Exception as e:
                logger.debug(f"[IMAGE_QUEUE] WS cancel notification failed: {e}")

            return True

        # 2️⃣ AKTİF JOB İSE FORGE'A INTERRUPT GÖNDER
        if self._current_job and self._current_job.job_id == job_id:
            logger.info(f"[IMAGE_QUEUE] ⏸️ Interrupting active job: {job_id}")

            # Cancelled set'e ekle
            self._cancelled_jobs.add(job_id)

            # Forge API interrupt
            try:
                interrupt_url = f"{settings.FORGE_BASE_URL}/sdapi/v1/interrupt"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(interrupt_url)
                    logger.info(f"[IMAGE_QUEUE] Forge interrupt response: {response.status_code}")
            except Exception as e:
                logger.warning(f"[IMAGE_QUEUE] ⚠️ Forge interrupt failed (job marked as cancelled): {e}")

            # Cancelled durumunu gönder
            try:
                await send_image_progress(
                    username=self._current_job.username,
                    conversation_id=self._current_job.conversation_id,
                    job_id=job_id,
                    status=ImageJobStatus.ERROR,
                    progress=self._current_job.progress,
                    queue_position=0,
                    prompt=self._current_job.prompt,
                    error="İptal edildi",
                )
            except Exception as e:
                logger.debug(f"[IMAGE_QUEUE] WS cancel notification failed: {e}")

            return True

        # Job bulunamadı
        logger.warning(f"[IMAGE_QUEUE] ❓ Job not found for cancellation: {job_id}")
        return False

    def get_queue_status(self) -> dict:
        return {"pending_jobs": self._queue.qsize(), "is_processing": self._gpu_lock.locked()}


# Tek instance
job_queue = ImageJobQueue()
