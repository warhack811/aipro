

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlmodel import select

from app.auth.user_manager import get_user_by_username
from app.core.database import get_session
from app.core.logger import get_logger
from app.core.models import Feedback, User

logger = get_logger(__name__)

def add_feedback(
    username: str,
    conversation_id: str,
    message: str,
    feedback: str,
) -> Feedback:
    """Yeni feedback kaydı ekler (SQL)"""
    feedback = feedback.lower().strip()
    if feedback not in ("like", "dislike"):
        raise ValueError("feedback 'like' veya 'dislike' olmalı.")
    
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"Kullanıcı bulunamadı: {username}")
    
    if not user.id:
        raise ValueError(f"Kullanıcı ID'si geçersiz: {username}")
    
    with get_session() as session:
        fb = Feedback(
            user_id=user.id,
            conversation_id=conversation_id or None,
            message_content=message,
            feedback_type=feedback,
        )
        session.add(fb)
        session.commit()
        session.refresh(fb)
        logger.info(f"[FEEDBACK] user={username} type={feedback}")
        return fb

def list_all_feedback(limit_per_user: int = 200) -> List[dict]:
    """Tüm feedback kayıtlarını döner (Admin için)"""
    from sqlmodel import col, desc
    
    with get_session() as session:
        stmt = (
            select(Feedback, User)
            .join(User, col(Feedback.user_id) == col(User.id))
            .order_by(desc(Feedback.created_at))
            .limit(limit_per_user)
        )
        results = session.exec(stmt).all()
        
        items = []
        for fb, user in results:
            items.append({
                "username": user.username,
                "conversation_id": fb.conversation_id or "",
                "message": fb.message_content,
                "feedback": fb.feedback_type,
                "created_at": fb.created_at.isoformat(),
            })
        return items