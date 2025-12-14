from __future__ import annotations

from typing import Any, Dict, List, Optional

_pending_jobs: Dict[str, Dict[str, Any]] = {}


def register_pending_job(job_id: str, username: str, conversation_id: Optional[str], queue_pos: int) -> None:
    _pending_jobs[job_id] = {
        "job_id": job_id,
        "username": username,
        "conversation_id": conversation_id,
        "queue_pos": queue_pos,
        "progress": 0,
    }


def update_pending_job(job_id: str, progress: Optional[int] = None, queue_pos: Optional[int] = None) -> None:
    job = _pending_jobs.get(job_id)
    if not job:
        return
    if progress is not None:
        job["progress"] = max(0, min(progress, 100))
    if queue_pos is not None:
        job["queue_pos"] = queue_pos


def remove_pending_job(job_id: str) -> None:
    _pending_jobs.pop(job_id, None)


def list_pending_jobs_for_user(username: str) -> List[Dict[str, Any]]:
    return [
        dict(job)
        for job in _pending_jobs.values()
        if job["username"] == username
    ]


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """job_id ile bekleyen job'un durumunu döndürür."""
    job = _pending_jobs.get(job_id)
    if job:
        return dict(job)
    return None
