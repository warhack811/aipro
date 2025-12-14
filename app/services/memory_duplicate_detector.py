"""
Mami AI - Memory Duplicate Detection Service
============================================

Gelişmiş duplicate detection:
- Semantic similarity (ChromaDB vector distance)
- Text similarity (character-level)
- Entity-based comparison
- Configurable thresholds
"""

import re
import logging
from typing import Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class MemoryDuplicateDetector:
    """
    Hybrid duplicate detection servisi.
    
    Kombine yaklaşım:
    1. Semantic similarity (vector distance)
    2. Text similarity (exact match + token overlap)
    3. Importance-based dynamic thresholds
    """
    
    # Threshold sabitleri
    STRICT_SEMANTIC_THRESHOLD = 0.03  # %97 similarity
    NORMAL_SEMANTIC_THRESHOLD = 0.05  # %95 similarity
    LOOSE_SEMANTIC_THRESHOLD = 0.08   # %92 similarity
    
    STRICT_TEXT_THRESHOLD = 0.95
    NORMAL_TEXT_THRESHOLD = 0.85
    LOOSE_TEXT_THRESHOLD = 0.70
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Metni normalize eder (duplicate kontrolü için).
        
        Args:
            text: Normalize edilecek metin
            
        Returns:
            str: Normalize edilmiş metin
        """
        if not text:
            return ""
        
        # Küçük harfe çevir
        normalized = text.lower().strip()
        
        # Çoklu boşlukları tek boşluğa indir
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Türkçe karakter normalizasyonu
        normalized = normalized.replace("'", "'")
        normalized = normalized.replace(""", '"').replace(""", '"')
        
        # Yaygın eşanlamlılar
        normalized = normalized.replace("kullanıcı adı", "isim")
        normalized = normalized.replace("kullanıcı ismi", "isim")
        normalized = normalized.replace("adım", "isim")
        
        return normalized
    
    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """
        İki metin arasında karakter seviyesi benzerlik hesaplar.
        
        Args:
            text1: İlk metin
            text2: İkinci metin
            
        Returns:
            float: Benzerlik skoru (0.0-1.0)
        """
        # Normalize et
        t1 = MemoryDuplicateDetector.normalize_text(text1)
        t2 = MemoryDuplicateDetector.normalize_text(text2)
        
        # Exact match
        if t1 == t2:
            return 1.0
        
        # Boş kontrol
        if not t1 or not t2:
            return 0.0
        
        # Sequence matcher (character level)
        return SequenceMatcher(None, t1, t2).ratio()
    
    @staticmethod
    def extract_key_entities(text: str) -> set:
        """
        Metinden anahtar entity'leri çıkarır (basit yaklaşım).
        
        İleri seviye için spaCy kullanılabilir ama dependency eklemeden
        basit regex ile önemli kelimeleri yakalıyoruz.
        
        Args:
            text: Analiz edilecek metin
            
        Returns:
            set: Anahtar kelimeler
        """
        # Türkçe stopwords (yaygın kelimeler)
        stopwords = {
            'bir', 'bu', 'şu', 've', 'veya', 'ile', 'için', 'de', 'da',
            'mi', 'mı', 'mu', 'mü', 'ki', 'gibi', 'daha', 'çok', 'en',
            'var', 'yok', 'olan', 'olarak', 'ben', 'sen', 'o', 'biz',
            'siz', 'onlar', 'benim', 'senin', 'onun', 'bizim', 'sizin'
        }
        
        # Normalize
        normalized = MemoryDuplicateDetector.normalize_text(text)
        
        # Kelimelere ayır
        words = re.findall(r'\b\w+\b', normalized)
        
        # Stopwords'leri çıkar ve 3+ karakter olanları al
        entities = {w for w in words if len(w) >= 3 and w not in stopwords}
        
        return entities
    
    @classmethod
    def get_thresholds_for_importance(
        cls,
        importance: float
    ) -> Tuple[float, float]:
        """
        Importance seviyesine göre threshold'ları döndürür.
        
        Args:
            importance: Önem seviyesi (0.0-1.0)
            
        Returns:
            Tuple[float, float]: (semantic_threshold, text_threshold)
        """
        if importance > 0.8:
            # Yüksek önemli hafızalar için strict
            return cls.STRICT_SEMANTIC_THRESHOLD, cls.STRICT_TEXT_THRESHOLD
        elif importance > 0.5:
            # Orta önemli hafızalar için normal
            return cls.NORMAL_SEMANTIC_THRESHOLD, cls.NORMAL_TEXT_THRESHOLD
        else:
            # Düşük önemli hafızalar için loose
            return cls.LOOSE_SEMANTIC_THRESHOLD, cls.LOOSE_TEXT_THRESHOLD
    
    @classmethod
    def is_duplicate(
        cls,
        new_text: str,
        existing_text: str,
        semantic_distance: float,
        importance: float = 0.5,
        use_entity_check: bool = True
    ) -> Tuple[bool, str]:
        """
        Kombine duplicate detection.
        
        Args:
            new_text: Yeni hafıza metni
            existing_text: Mevcut hafıza metni
            semantic_distance: ChromaDB vector distance (0.0-2.0)
            importance: Hafıza önem seviyesi (0.0-1.0)
            use_entity_check: Entity kontrolü yap
            
        Returns:
            Tuple[bool, str]: (is_duplicate, reason)
        """
        # 1. Semantic similarity hesapla
        semantic_sim = 1.0 - semantic_distance
        
        # 2. Text similarity hesapla
        text_sim = cls.calculate_text_similarity(new_text, existing_text)
        
        # 3. Importance bazlı threshold'ları al
        sem_threshold, text_threshold = cls.get_thresholds_for_importance(importance)
        
        # 4. Exact match kontrolü
        if text_sim > 0.95:
            return True, f"exact_match (text_sim={text_sim:.2f})"
        
        # 5. Entity-based refinement ÖNCE (false positive önleme)
        if use_entity_check and semantic_sim > 0.90:
            new_entities = cls.extract_key_entities(new_text)
            existing_entities = cls.extract_key_entities(existing_text)
            
            if new_entities and existing_entities:
                # Jaccard similarity
                overlap = len(new_entities & existing_entities)
                union = len(new_entities | existing_entities)
                entity_sim = overlap / union if union > 0 else 0.0
                
                # Yüksek semantic ama düşük entity overlap → FARKLI
                # Örnek: "Kedimi seviyorum" vs "Köpeğimi seviyorum"
                # Semantic: %96, Entity overlap: %50 (seviyorum ortak, kedi≠köpek)
                if entity_sim < 0.4:
                    logger.debug(
                        f"[DUPLICATE] False positive önlendi: "
                        f"sem={semantic_sim:.2f}, entity_sim={entity_sim:.2f}, "
                        f"entities1={new_entities}, entities2={existing_entities}"
                    )
                    return False, f"entity_mismatch (entity_sim={entity_sim:.2f})"
        
        # 6. Çok yüksek semantic + orta text → Duplicate
        if semantic_sim > 0.97 and text_sim > 0.70:
            return True, f"high_semantic_match (sem={semantic_sim:.2f}, text={text_sim:.2f})"
        
        # 7. Yüksek semantic + yüksek text → Duplicate
        if semantic_sim > (1.0 - sem_threshold) and text_sim > text_threshold:
            return True, f"hybrid_match (sem={semantic_sim:.2f}, text={text_sim:.2f})"
        
        # 8. Duplicate değil
        return False, f"not_duplicate (sem={semantic_sim:.2f}, text={text_sim:.2f})"


# Singleton instance
detector = MemoryDuplicateDetector()