"""
Mami AI - Context Truncation Manager
====================================

Akıllı context truncation:
- Importance-based message prioritization
- Message boundary'lerde kesme
- Critical information preservation
- Sliding window + summarization
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextTruncationManager:
    """
    Akıllı context truncation yöneticisi.
    
    Özellikler:
    - Importance skorlarına göre mesaj önceliklendirme
    - Message boundary'lerde kesme (ortadan kesme yok)
    - Critical bilgi koruması
    - Token budget yönetimi
    """
    
    # Context sabitleri
    DEFAULT_CHAR_LIMIT = 8000
    TRUNCATION_NOTICE = (
        "### 📋 BAĞLAM KISALTILDI\n"
        "Bağlam çok uzun olduğu için en önemli bilgiler korundu.\n\n"
    )
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Token tahmini (4 char ≈ 1 token).
        
        Args:
            text: Tahmin edilecek metin
            
        Returns:
            int: Tahmini token sayısı
        """
        if not text:
            return 0
        return max(1, len(text) // 4)
    
    @staticmethod
    def calculate_message_importance(
        message: Dict[str, str],
        position_index: int,
        total_messages: int
    ) -> float:
        """
        Mesaj önem skoru hesaplar.
        
        Faktörler:
        1. Position (yeni mesajlar daha önemli)
        2. Role (user mesajları assistant'tan daha önemli)
        3. Length (çok kısa mesajlar daha az önemli)
        4. Content type (soru işareti, kod bloğu vb.)
        
        Args:
            message: Mesaj dict (role, content)
            position_index: Mesajın pozisyon indexi (0=en eski)
            total_messages: Toplam mesaj sayısı
            
        Returns:
            float: Önem skoru (0.0-1.0)
        """
        content = message.get("content", "")
        role = message.get("role", "user")
        
        # 1. Position importance (yeni mesajlar daha önemli)
        # Son %20: 1.0, İlk %20: 0.3
        position_weight = 0.3 + (0.7 * position_index / max(1, total_messages - 1))
        
        # 2. Role importance
        role_weight = 1.0 if role == "user" else 0.8
        
        # 3. Length importance (çok kısa < 20 char daha az önemli)
        length = len(content)
        if length < 20:
            length_weight = 0.5
        elif length < 50:
            length_weight = 0.7
        else:
            length_weight = 1.0
        
        # 4. Content type importance
        content_weight = 1.0
        
        # Soru işareti var mı? (user'ın sorusu önemli)
        if "?" in content:
            content_weight = max(content_weight, 1.1)
        
        # Kod bloğu var mı? (teknik içerik önemli)
        if "```" in content or "def " in content or "class " in content:
            content_weight = max(content_weight, 1.2)
        
        # Kritik kelimeler (önemli bilgi içeriyor olabilir)
        critical_keywords = ["önemli", "kritik", "unutma", "hatırla", "dikkat", "warning", "error"]
        if any(kw in content.lower() for kw in critical_keywords):
            content_weight = max(content_weight, 1.15)
        
        # Final importance score
        importance = (
            position_weight * 0.4 +
            role_weight * 0.2 +
            length_weight * 0.2 +
            content_weight * 0.2
        )
        
        return min(1.0, importance)
    
    @classmethod
    def truncate_messages_by_importance(
        cls,
        messages: List[Dict[str, str]],
        token_budget: int,
        preserve_system: bool = True
    ) -> Tuple[List[Dict[str, str]], bool]:
        """
        Mesajları importance'a göre truncate eder.
        
        Args:
            messages: Mesaj listesi
            token_budget: Maksimum token limiti
            preserve_system: System mesajını koru
            
        Returns:
            Tuple[List[Dict[str, str]], bool]: (truncated_messages, was_truncated)
        """
        if not messages:
            return [], False
        
        # System message'ı ayır
        system_msg = None
        content_messages = messages
        
        if preserve_system and messages[0].get("role") == "system":
            system_msg = messages[0]
            content_messages = messages[1:]
            
            # System token'ını budget'tan düş
            system_tokens = cls.estimate_tokens(system_msg.get("content", ""))
            token_budget = max(500, token_budget - system_tokens)
        
        if not content_messages:
            return ([system_msg] if system_msg else []), False
        
        # Her mesaja importance skoru ata
        scored_messages = []
        total = len(content_messages)
        
        for idx, msg in enumerate(content_messages):
            importance = cls.calculate_message_importance(msg, idx, total)
            tokens = cls.estimate_tokens(msg.get("content", ""))
            
            scored_messages.append({
                "message": msg,
                "importance": importance,
                "tokens": tokens,
                "index": idx
            })
        
        # Importance'a göre sırala (yüksekten düşüğe)
        scored_messages.sort(key=lambda x: x["importance"], reverse=True)
        
        # Budget dahilinde seç
        selected = []
        total_tokens = 0
        
        for scored in scored_messages:
            if total_tokens + scored["tokens"] <= token_budget:
                selected.append(scored)
                total_tokens += scored["tokens"]
            else:
                # Token limiti aşıldı, en önemli mesajları aldık
                break
        
        # Orijinal sıraya geri dön (temporal order)
        selected.sort(key=lambda x: x["index"])
        
        # Mesajları çıkar
        result_messages = [s["message"] for s in selected]
        
        # Truncation oldu mu?
        was_truncated = len(result_messages) < len(content_messages)
        
        # System message'ı başa ekle
        if system_msg:
            result_messages = [system_msg] + result_messages
        
        logger.info(
            f"[CONTEXT_TRUNCATE] {len(content_messages)} mesaj → {len(result_messages)} mesaj | "
            f"Budget: {token_budget} tokens | Truncated: {was_truncated}"
        )
        
        return result_messages, was_truncated
    
    @classmethod
    def truncate_text_smart(
        cls,
        text: str,
        char_limit: int = DEFAULT_CHAR_LIMIT,
        add_notice: bool = True
    ) -> str:
        """
        Metni akıllıca truncate eder.
        
        - Paragraf boundary'lerinde keser
        - Son cümleyi tamamlar
        - Truncation notice ekler
        
        Args:
            text: Truncate edilecek metin
            char_limit: Karakter limiti
            add_notice: Truncation notice ekle
            
        Returns:
            str: Truncate edilmiş metin
        """
        if not text:
            return text
        
        if len(text) <= char_limit:
            return text
        
        # Notice için yer ayır
        notice_len = len(cls.TRUNCATION_NOTICE) if add_notice else 0
        effective_limit = char_limit - notice_len - 50  # Buffer
        
        if effective_limit <= 100:
            # Çok kısa limit, metni olduğu gibi dön
            return text[:char_limit].rstrip()
        
        # Paragraf boundary'lerinde kes
        truncated = text[:effective_limit]
        
        # Son paragrafı bul
        last_para = truncated.rfind("\n\n")
        if last_para > effective_limit * 0.7:  # En az %70'ini aldıysak
            truncated = truncated[:last_para]
        else:
            # Son cümleyi tamamla
            last_period = truncated.rfind(".")
            last_exclaim = truncated.rfind("!")
            last_question = truncated.rfind("?")
            
            last_sentence = max(last_period, last_exclaim, last_question)
            
            if last_sentence > effective_limit * 0.8:  # En az %80'ini aldıysak
                truncated = truncated[:last_sentence + 1]
        
        truncated = truncated.rstrip()
        
        # Notice ekle
        if add_notice:
            return f"{cls.TRUNCATION_NOTICE}{truncated}"
        
        return truncated
    
    @classmethod
    def build_context_blocks(
        cls,
        sections: List[str],
        char_limit: int = DEFAULT_CHAR_LIMIT
    ) -> str:
        """
        Context bloklarını birleştirir ve truncate eder.
        
        Args:
            sections: Context section listesi
            char_limit: Maksimum karakter limiti
            
        Returns:
            str: Birleştirilmiş ve truncate edilmiş context
        """
        if not sections:
            return ""
        
        # Boş olmayan section'ları al
        valid_sections = [s for s in sections if s and s.strip()]
        
        if not valid_sections:
            return ""
        
        # Header ekle
        header = "📚 BAĞLAM BİLGİLERİ\n\n"
        
        # Birleştir
        full_context = header + "\n\n".join(valid_sections)
        
        # Truncate
        return cls.truncate_text_smart(full_context, char_limit, add_notice=True)


# Singleton instance
context_manager = ContextTruncationManager()