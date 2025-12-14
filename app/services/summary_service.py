import logging
from datetime import datetime
from typing import Optional

from sqlmodel import asc, func, select

from app.chat.decider import call_groq_api_safe_async
from app.core.database import get_session
from app.core.models import ConversationSummary, Message
from app.core.summary_config import get_summary_settings

logger = logging.getLogger(__name__)

async def should_update_summary(conversation_id: str) -> bool:
    """
    Özetin güncellenmesi gerekip gerekmediğini kontrol eder.
    Hem last_message_id hem de message_count_at_update kullanır.
    """
    config = get_summary_settings()
    if not config.summary_enabled:
        return False

    with get_session() as session:
        # Toplam mesaj sayısı
        total = session.exec(select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)).one()
        if total < config.summary_first_threshold:
            return False

        summary = session.get(ConversationSummary, conversation_id)
        
        # Özet hiç oluşturulmamışsa, oluştur
        if not summary:
            logger.info(f"[SUMMARY] İlk özet tetiklendi: {conversation_id} ({total} mesaj)")
            return True
        
        # last_message_id veya message_count bazlı kontrol
        new_messages_since_update = total - summary.message_count_at_update
        
        if new_messages_since_update >= config.summary_update_step:
            logger.info(f"[SUMMARY] Güncelleme tetiklendi: {conversation_id} ({new_messages_since_update} yeni mesaj)")
            return True
            
        return False

async def generate_and_save_summary(conversation_id: str) -> None:
    """
    Sohbet özetini oluşturur ve kaydeder.
    Progressive summarization: Eski mesajlar özetlenir, yeniler bağlama eklenir.
    
    Args:
        conversation_id: Özet oluşturulacak sohbet ID'si
    """
    config = get_summary_settings()
    if not config.summary_enabled:
        return

    with get_session() as session:
        summary_rec = session.get(ConversationSummary, conversation_id)
        
        # Toplam mesaj sayısını al
        total_messages = session.exec(
            select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
        ).one()
        
        # Hangi mesajları alacağız?
        query = select(Message).where(Message.conversation_id == conversation_id).order_by(asc(Message.id))
        
        if summary_rec and summary_rec.message_count_at_update > 0:
            # Incremental: Sadece özetten sonraki mesajları al
            # message_count_at_update kullanarak skip yapıyoruz
            query = query.offset(summary_rec.message_count_at_update).limit(config.summary_max_messages)
        else:
            # İlk özet - son N mesajı al
            query = query.limit(config.summary_max_messages)

        messages = list(session.exec(query).all())
        if not messages:
            return

        last_message_id = messages[-1].id if messages else None
        transcript = "\n".join(f"{m.role}: {m.content}" for m in messages)

        if summary_rec and summary_rec.summary:
            # Mevcut özeti yeni bilgilerle güncelle
            user_content = f"MEVCUT ÖZET:\n{summary_rec.summary}\n\nYENİ MESAJLAR ({len(messages)} adet):\n{transcript}"
            instruction = "Mevcut özeti yeni bilgilerle birleştir. Önemli detayları koru, gereksizleri çıkar."
        else:
            # Sıfırdan özet
            user_content = transcript
            instruction = "Bu konuşmayı yapılandırılmış şekilde özetle."

        system_prompt = f"""Sen profesyonel bir sohbet özetleyicisisin. Türkçe çalışıyorsun.

GÖREV: {instruction}

ÖNEMLİ BİLGİLERİ KORU:
- Kullanıcının ismi, tercihleri, kişisel bilgileri
- Alınan kararlar ve sonuçlar
- Kullanıcının istekleri ve hedefleri
- Önemli tarih/sayı/isim gibi veriler

FORMAT:
- 4-6 cümlelik akıcı bir paragraf yaz
- 'Kullanıcı dedi ki' gibi tekrarlardan kaçın
- Kronolojik sırayı koru
- Maksimum 150 kelime

SADECE ÖZETİ YAZ, başka açıklama ekleme."""

        new_summary, _ = await call_groq_api_safe_async(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.15,  # Daha deterministik
            max_retries=2
        )

        if not new_summary:
            logger.error(f"[SUMMARY] Özet üretilemedi: {conversation_id}")
            return

        new_summary = new_summary.strip()

        if summary_rec:
            summary_rec.summary = new_summary
            summary_rec.last_message_id = last_message_id
            summary_rec.updated_at = datetime.utcnow()
            summary_rec.message_count_at_update = total_messages
        else:
            summary_rec = ConversationSummary(
                conversation_id=conversation_id,
                summary=new_summary,
                last_message_id=last_message_id,
                updated_at=datetime.utcnow(),
                message_count_at_update=total_messages
            )
        
        session.add(summary_rec)
        session.commit()
        logger.info(f"[SUMMARY] {'Güncellendi' if summary_rec else 'Oluşturuldu'}: {conversation_id} ({total_messages} mesaj)")

        logger.info(f"[SUMMARY] {'Güncellendi' if summary_rec.conversation_id else 'Oluşturuldu'}: {conversation_id}")