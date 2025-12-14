# 🎯 Mami AI - 10/10 İçin Gerekli İyileştirmeler

**Tarih:** 2025-12-12  
**Hedef:** Tüm sistemleri 10/10 kaliteye çıkarmak  
**Tahmini Süre:** 2-3 hafta

---

## 📊 Mevcut Durum vs Hedef

| Sistem | Mevcut | Hedef | Eksik |
|--------|--------|-------|-------|
| Prompt Katmanları | 9/10 | 10/10 | Versioning, Analytics |
| Hafıza & RAG | 8/10 | 10/10 | Decay, Summarization |
| Sohbet Geçmişi | 8/10 | 10/10 | Sliding Window, Cache |
| Görsel Üretim | 9/10 | 10/10 | Batch, History |
| Mod/Persona | 9/10 | 10/10 | Custom Persona |
| Sansür Sistemi | 7/10 | 10/10 | ML Detection, Audit |
| Router Sistemi | 9/10 | 10/10 | Cache, Analytics |
| İnternet Arama | 8/10 | 10/10 | Cache, More Parsers |

---

## 1. PROMPT KATMANLARI → 10/10

### Mevcut: 9/10 | Eksik: 1 puan

#### 1.1 Prompt Versioning Sistemi

**Dosya:** `app/ai/prompts/version_manager.py` (YENİ)

```python
"""
Prompt Version Manager
======================
Prompt değişikliklerini takip eder, A/B test desteği sağlar.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import hashlib

@dataclass
class PromptVersion:
    version: str           # "v1.2.3"
    hash: str              # İçerik hash'i
    created_at: datetime
    author: str
    changelog: str
    is_active: bool = True
    ab_test_weight: float = 1.0  # A/B test için ağırlık

class PromptVersionManager:
    """Prompt versiyonlarını yönetir."""
    
    def __init__(self):
        self.versions: Dict[str, PromptVersion] = {}
        self.active_version: str = "v1.0.0"
    
    def register_version(self, version: str, prompt_content: str, changelog: str):
        """Yeni prompt versiyonu kaydeder."""
        content_hash = hashlib.sha256(prompt_content.encode()).hexdigest()[:12]
        self.versions[version] = PromptVersion(
            version=version,
            hash=content_hash,
            created_at=datetime.now(),
            author="system",
            changelog=changelog,
        )
    
    def get_prompt_for_user(self, user_id: int) -> str:
        """A/B test için kullanıcıya uygun prompt versiyonunu döndürür."""
        # User ID'ye göre consistent hash ile versiyon seç
        pass
    
    def rollback(self, version: str):
        """Önceki versiyona geri dön."""
        pass
    
    def get_stats(self) -> Dict:
        """Versiyon istatistikleri (hangi versiyon daha iyi performans)."""
        pass
```

#### 1.2 Prompt Analytics

**Dosya:** `app/services/prompt_analytics.py` (YENİ)

```python
"""
Prompt Analytics
================
Prompt performansını ölçer.
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PromptMetrics:
    version: str
    total_requests: int
    avg_response_time_ms: float
    avg_token_count: int
    user_satisfaction_rate: float  # like/dislike oranı
    error_rate: float

class PromptAnalytics:
    """Prompt performans analizi."""
    
    def record_request(self, version: str, response_time: float, tokens: int):
        """İstek kaydeder."""
        pass
    
    def record_feedback(self, version: str, is_positive: bool):
        """Kullanıcı feedback'i kaydeder."""
        pass
    
    def get_best_performing_version(self) -> str:
        """En iyi performans gösteren versiyonu döndürür."""
        pass
    
    def generate_report(self) -> Dict:
        """Performans raporu üretir."""
        pass
```

**Entegrasyon:**
```python
# app/ai/prompts/compiler.py içinde
from app.ai.prompts.version_manager import prompt_version_manager
from app.services.prompt_analytics import prompt_analytics

def build_system_prompt(user=None, persona_name="standard", toggles=None):
    # Mevcut kod...
    
    # Analytics tracking
    prompt_analytics.record_request(
        version=prompt_version_manager.active_version,
        tokens=_estimate_tokens(final_prompt)
    )
    
    return final_prompt
```

---

## 2. HAFIZA & RAG SİSTEMİ → 10/10

### Mevcut: 8/10 | Eksik: 2 puan

#### 2.1 Memory Decay Mechanism

**Dosya:** `app/memory/decay.py` (YENİ)

```python
"""
Memory Decay System
===================
Kullanılmayan hafızaların önemini zamanla azaltır.
"""

from datetime import datetime, timedelta
from typing import List
import math

class MemoryDecay:
    """Hafıza decay yöneticisi."""
    
    # Decay parametreleri
    HALF_LIFE_DAYS = 30  # 30 günde yarı ömür
    MIN_IMPORTANCE = 0.1  # Minimum importance
    USAGE_BOOST = 0.2    # Kullanımda artış
    
    def calculate_decayed_importance(
        self, 
        original_importance: float,
        created_at: datetime,
        last_accessed: datetime
    ) -> float:
        """
        Exponential decay ile güncel importance hesaplar.
        
        Formula: I(t) = I₀ × (0.5)^(t/T½)
        """
        now = datetime.now()
        days_since_access = (now - last_accessed).days
        
        decay_factor = math.pow(0.5, days_since_access / self.HALF_LIFE_DAYS)
        decayed = original_importance * decay_factor
        
        return max(decayed, self.MIN_IMPORTANCE)
    
    def boost_on_access(self, current_importance: float) -> float:
        """Hafıza kullanıldığında importance artır."""
        boosted = min(1.0, current_importance + self.USAGE_BOOST)
        return boosted
    
    def run_decay_job(self):
        """Tüm hafızalar için decay uygula (cron job)."""
        # memory_service üzerinden tüm hafızaları güncelle
        pass
```

#### 2.2 Hierarchical Memory Summarization

**Dosya:** `app/memory/summarizer.py` (YENİ)

```python
"""
Memory Summarizer
=================
50+ hafızası olan kullanıcılar için özet üretir.
"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class MemoryCluster:
    topic: str
    summary: str
    memory_ids: List[str]
    importance: float

class MemorySummarizer:
    """Hafıza özetleyici."""
    
    CLUSTER_THRESHOLD = 50  # Bu sayıdan fazla hafıza varsa özetle
    
    async def should_summarize(self, user_id: int) -> bool:
        """Özet gerekli mi?"""
        count = await self._get_memory_count(user_id)
        return count >= self.CLUSTER_THRESHOLD
    
    async def cluster_memories(self, user_id: int) -> List[MemoryCluster]:
        """
        Hafızaları konulara göre kümele.
        
        Adımlar:
        1. Tüm hafızaları al
        2. Embedding'lere göre k-means clustering
        3. Her küme için LLM ile özet üret
        """
        pass
    
    async def generate_user_profile(self, user_id: int) -> str:
        """
        Kullanıcı profili özeti üret.
        
        Örnek output:
        "Bu kullanıcı yazılım geliştiricisi, Python ve React kullanıyor,
        İstanbul'da yaşıyor, 2 çocuğu var, futbol seviyor..."
        """
        pass
```

#### 2.3 RAG Chunking İyileştirmesi

**Dosya:** `app/memory/rag.py` güncelleme

```python
# Mevcut chunk_text fonksiyonunu güncelle

def chunk_text_smart(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,  # 50'den 100'e artır
    respect_sentences: bool = True  # Cümle sınırlarına dikkat et
) -> List[str]:
    """
    Akıllı metin chunking.
    
    İyileştirmeler:
    - Cümle ortasından bölme
    - Daha fazla overlap
    - Paragraf önceliği
    """
    if not respect_sentences:
        return _simple_chunk(text, chunk_size, overlap)
    
    # Cümlelere böl
    sentences = _split_into_sentences(text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) > chunk_size and current_chunk:
            # Chunk'ı kaydet
            chunks.append(" ".join(current_chunk))
            
            # Overlap için son cümleleri tut
            overlap_sentences = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_length += len(s)
                else:
                    break
            
            current_chunk = overlap_sentences
            current_length = overlap_length
        
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
```

---

## 3. SOHBET GEÇMİŞİ → 10/10

### Mevcut: 8/10 | Eksik: 2 puan

#### 3.1 Sliding Window + Summary

**Dosya:** `app/chat/processor.py` güncelleme

```python
def build_history_sliding_window(
    username: str,
    conversation_id: str,
    window_size: int = 10,
    include_summary: bool = True
) -> List[Dict[str, str]]:
    """
    Sliding window ile history oluştur.
    
    Format:
    [ÖZET] İlk 20 mesajın özeti
    [SON 10 MESAJ] Tam mesajlar
    """
    from app.memory.conversation import get_messages, get_summary
    
    messages = get_messages(conversation_id)
    
    if len(messages) <= window_size:
        return messages
    
    result = []
    
    # Özet ekle
    if include_summary:
        summary = get_summary(conversation_id)
        if summary:
            result.append({
                "role": "system",
                "content": f"[ÖNCEKİ SOHBET ÖZETİ]\n{summary}"
            })
    
    # Son N mesajı tam ekle
    result.extend(messages[-window_size:])
    
    return result
```

#### 3.2 Message Importance Scoring

**Dosya:** `app/services/message_scorer.py` (YENİ)

```python
"""
Message Importance Scorer
=========================
Her mesaja önem skoru atar, truncation'da kullanılır.
"""

from typing import Dict, List

class MessageScorer:
    """Mesaj önem skorlayıcı."""
    
    # Önem faktörleri
    FACTORS = {
        "contains_name": 0.3,      # Kullanıcı adı geçiyor
        "contains_memory": 0.4,    # Hafızaya kaydedilmiş bilgi
        "is_question": 0.2,        # Soru içeriyor
        "has_code": 0.3,           # Kod bloğu var
        "recent": 0.5,             # Son 5 mesaj
        "user_feedback": 0.5,      # Like almış
    }
    
    def score_message(self, message: Dict, position: int, total: int) -> float:
        """Mesaja 0-1 arası önem skoru atar."""
        score = 0.0
        
        content = message.get("content", "")
        metadata = message.get("metadata", {})
        
        # İsim kontrolü
        if "benim adım" in content.lower() or "adım" in content.lower():
            score += self.FACTORS["contains_name"]
        
        # Son mesajlar daha önemli
        if position >= total - 5:
            score += self.FACTORS["recent"]
        
        # Kod bloğu varsa önemli
        if "```" in content:
            score += self.FACTORS["has_code"]
        
        # Feedback varsa
        if metadata.get("liked"):
            score += self.FACTORS["user_feedback"]
        
        return min(1.0, score)
    
    def select_important_messages(
        self, 
        messages: List[Dict], 
        token_budget: int
    ) -> List[Dict]:
        """Token budget içinde en önemli mesajları seç."""
        scored = []
        for i, msg in enumerate(messages):
            score = self.score_message(msg, i, len(messages))
            scored.append((score, i, msg))
        
        # Skora göre sırala, budget içinde seç
        scored.sort(reverse=True)
        
        selected = []
        total_tokens = 0
        
        for score, idx, msg in scored:
            msg_tokens = len(msg.get("content", "")) // 4
            if total_tokens + msg_tokens <= token_budget:
                selected.append((idx, msg))
                total_tokens += msg_tokens
        
        # Orijinal sıraya göre döndür
        selected.sort(key=lambda x: x[0])
        return [msg for idx, msg in selected]
```

#### 3.3 Context Caching

**Dosya:** `app/services/context_cache.py` (YENİ)

```python
"""
Context Cache
=============
Aynı sohbet için context'i cache'le.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib

class ContextCache:
    """Context cache yöneticisi."""
    
    TTL_SECONDS = 60  # 1 dakika cache
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
    
    def _make_key(self, conversation_id: str, message_count: int) -> str:
        """Cache key oluştur."""
        return f"{conversation_id}:{message_count}"
    
    def get(self, conversation_id: str, message_count: int) -> Optional[str]:
        """Cache'den context al."""
        key = self._make_key(conversation_id, message_count)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["context"]
    
    def set(self, conversation_id: str, message_count: int, context: str):
        """Context'i cache'le."""
        key = self._make_key(conversation_id, message_count)
        self._cache[key] = {
            "context": context,
            "expires_at": datetime.now() + timedelta(seconds=self.TTL_SECONDS)
        }
    
    def invalidate(self, conversation_id: str):
        """Sohbet için tüm cache'i temizle."""
        prefix = f"{conversation_id}:"
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]

# Singleton
context_cache = ContextCache()
```

---

## 4. GÖRSEL ÜRETİM → 10/10

### Mevcut: 9/10 | Eksik: 1 puan

#### 4.1 Batch Generation

**Dosya:** `app/image/batch_generator.py` (YENİ)

```python
"""
Batch Image Generator
=====================
Tek prompt ile birden fazla varyasyon üretir.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class BatchJob:
    prompt: str
    variations: int
    seed_start: int
    job_ids: List[str]

class BatchGenerator:
    """Toplu görsel üretici."""
    
    MAX_VARIATIONS = 4
    
    async def generate_batch(
        self,
        prompt: str,
        user,
        variations: int = 4,
        variation_strength: float = 0.3
    ) -> List[str]:
        """
        Aynı prompt ile birden fazla varyasyon üret.
        
        Args:
            prompt: Ana prompt
            variations: Üretilecek görsel sayısı
            variation_strength: Varyasyon gücü (0-1)
        
        Returns:
            List[str]: Üretilen görsel URL'leri
        """
        from app.image.routing import decide_image_job
        from app.image.job_queue import image_job_queue
        
        variations = min(variations, self.MAX_VARIATIONS)
        
        # Her varyasyon için farklı seed
        base_seed = self._generate_base_seed()
        
        jobs = []
        for i in range(variations):
            # Prompt'a hafif varyasyon ekle
            varied_prompt = self._add_variation(prompt, i, variation_strength)
            
            spec = decide_image_job(varied_prompt, user)
            if not spec.blocked:
                job = await image_job_queue.enqueue(
                    prompt=varied_prompt,
                    user_id=user.id,
                    seed=base_seed + i,
                    batch_id=f"batch_{base_seed}"
                )
                jobs.append(job)
        
        # Tüm job'ların tamamlanmasını bekle
        results = await asyncio.gather(*[
            self._wait_for_job(job) for job in jobs
        ])
        
        return [r for r in results if r is not None]
    
    def _add_variation(self, prompt: str, index: int, strength: float) -> str:
        """Prompt'a varyasyon ekle."""
        variations = [
            "",  # Orijinal
            ", slightly different angle",
            ", alternative composition",
            ", different lighting",
        ]
        return prompt + variations[index % len(variations)]
```

#### 4.2 Image History / Favorites

**Dosya:** `app/image/history.py` (YENİ)

```python
"""
Image History Manager
=====================
Kullanıcının görsel geçmişini yönetir.
"""

from typing import List, Dict, Optional
from datetime import datetime

class ImageHistory:
    """Görsel geçmişi yöneticisi."""
    
    MAX_HISTORY = 100  # Kullanıcı başına max
    
    async def add_to_history(
        self,
        user_id: int,
        image_url: str,
        prompt: str,
        spec: Dict
    ):
        """Görsel geçmişe ekle."""
        # DB'ye kaydet (UserImage modeli zaten var)
        pass
    
    async def get_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Kullanıcının görsel geçmişini getir."""
        pass
    
    async def add_to_favorites(self, user_id: int, image_id: str):
        """Görseli favorilere ekle."""
        pass
    
    async def get_favorites(self, user_id: int) -> List[Dict]:
        """Favori görselleri getir."""
        pass
    
    async def delete_from_history(self, user_id: int, image_id: str):
        """Geçmişten sil."""
        pass
    
    async def reuse_prompt(self, image_id: str) -> str:
        """Görselin prompt'unu al (yeniden kullanım için)."""
        pass
```

---

## 5. MOD/PERSONA SİSTEMİ → 10/10

### Mevcut: 9/10 | Eksik: 1 puan

#### 5.1 Custom Persona Creator

**Dosya:** `app/services/custom_persona.py` (YENİ)

```python
"""
Custom Persona Manager
======================
Kullanıcıların kendi personalarını oluşturmasına izin verir.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class CustomPersona:
    id: str
    user_id: int
    name: str
    display_name: str
    system_prompt: str
    initial_message: Optional[str]
    avatar_url: Optional[str]
    is_public: bool = False  # Diğer kullanıcılarla paylaş
    created_at: str

class CustomPersonaManager:
    """Özel persona yöneticisi."""
    
    MAX_PERSONAS_PER_USER = 5
    MAX_PROMPT_LENGTH = 2000
    
    async def create_persona(
        self,
        user_id: int,
        name: str,
        display_name: str,
        system_prompt: str,
        initial_message: Optional[str] = None
    ) -> CustomPersona:
        """
        Yeni özel persona oluştur.
        
        Validation:
        - İsim unique olmalı
        - Prompt length kontrolü
        - Max persona sayısı kontrolü
        """
        # Limit kontrolü
        existing = await self.list_user_personas(user_id)
        if len(existing) >= self.MAX_PERSONAS_PER_USER:
            raise ValueError("Maksimum persona sayısına ulaştınız")
        
        # Prompt length
        if len(system_prompt) > self.MAX_PROMPT_LENGTH:
            raise ValueError("Prompt çok uzun")
        
        # Oluştur ve kaydet
        persona = CustomPersona(
            id=self._generate_id(),
            user_id=user_id,
            name=name.lower().replace(" ", "_"),
            display_name=display_name,
            system_prompt=system_prompt,
            initial_message=initial_message,
            avatar_url=None,
            created_at=datetime.now().isoformat()
        )
        
        await self._save_persona(persona)
        return persona
    
    async def list_user_personas(self, user_id: int) -> List[CustomPersona]:
        """Kullanıcının özel personalarını listele."""
        pass
    
    async def delete_persona(self, user_id: int, persona_id: str):
        """Persona sil."""
        pass
    
    async def get_public_personas(self) -> List[CustomPersona]:
        """Paylaşılan personaları listele."""
        pass
```

#### 5.2 Persona API Endpoints

**Dosya:** `app/api/user_routes.py` eklemeler

```python
# Mevcut persona endpoint'lerine ekle

@router.post("/personas/custom", response_model=CustomPersonaOut)
async def create_custom_persona(
    body: CustomPersonaIn,
    user: User = Depends(get_current_active_user)
):
    """Özel persona oluştur."""
    from app.services.custom_persona import custom_persona_manager
    
    persona = await custom_persona_manager.create_persona(
        user_id=user.id,
        name=body.name,
        display_name=body.display_name,
        system_prompt=body.system_prompt,
        initial_message=body.initial_message,
    )
    
    return CustomPersonaOut.from_orm(persona)

@router.get("/personas/custom", response_model=List[CustomPersonaOut])
async def list_custom_personas(user: User = Depends(get_current_active_user)):
    """Kullanıcının özel personalarını listele."""
    pass

@router.delete("/personas/custom/{persona_id}")
async def delete_custom_persona(
    persona_id: str,
    user: User = Depends(get_current_active_user)
):
    """Özel persona sil."""
    pass
```

---

## 6. SANSÜR SİSTEMİ → 10/10

### Mevcut: 7/10 | Eksik: 3 puan

#### 6.1 ML-Based Content Moderation

**Dosya:** `app/services/content_moderator.py` (YENİ)

```python
"""
ML-Based Content Moderator
==========================
Pattern matching'e ek olarak ML tabanlı içerik analizi.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import aiohttp

@dataclass
class ModerationResult:
    is_flagged: bool
    categories: Dict[str, bool]
    scores: Dict[str, float]
    source: str  # "pattern", "openai", "local"

class ContentModerator:
    """İçerik moderatörü."""
    
    def __init__(self):
        self.openai_available = self._check_openai_key()
    
    async def moderate(self, content: str) -> ModerationResult:
        """
        İçeriği analiz et.
        
        Cascade:
        1. Hızlı pattern matching (ucuz)
        2. OpenAI Moderation API (doğru)
        3. Local fallback (offline)
        """
        # 1. Pattern matching (hızlı, ilk filtre)
        pattern_result = self._pattern_check(content)
        if pattern_result.is_flagged:
            return pattern_result
        
        # 2. OpenAI Moderation API
        if self.openai_available:
            try:
                return await self._openai_moderate(content)
            except Exception:
                pass
        
        # 3. Pattern result as fallback
        return pattern_result
    
    def _pattern_check(self, content: str) -> ModerationResult:
        """Pattern-based hızlı kontrol."""
        from app.image.routing import _detect_nsfw_in_prompt
        
        is_nsfw = _detect_nsfw_in_prompt(content)
        
        return ModerationResult(
            is_flagged=is_nsfw,
            categories={"nsfw": is_nsfw},
            scores={"nsfw": 1.0 if is_nsfw else 0.0},
            source="pattern"
        )
    
    async def _openai_moderate(self, content: str) -> ModerationResult:
        """OpenAI Moderation API çağrısı."""
        from app.config import get_settings
        
        settings = get_settings()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/moderations",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"input": content}
            ) as resp:
                data = await resp.json()
        
        result = data["results"][0]
        
        return ModerationResult(
            is_flagged=result["flagged"],
            categories=result["categories"],
            scores=result["category_scores"],
            source="openai"
        )

# Singleton
content_moderator = ContentModerator()
```

#### 6.2 Audit Logging

**Dosya:** `app/services/moderation_audit.py` (YENİ)

```python
"""
Moderation Audit Logger
=======================
Tüm moderation kararlarını loglar.
"""

from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class AuditEntry:
    id: str
    timestamp: datetime
    user_id: int
    content_type: str  # "text", "image_prompt"
    content_hash: str  # Gizlilik için hash
    decision: str      # "allowed", "blocked", "flagged"
    reason: str
    categories: Dict[str, bool]
    reviewed: bool = False
    reviewer_notes: Optional[str] = None

class ModerationAuditLogger:
    """Moderation audit logger."""
    
    async def log(
        self,
        user_id: int,
        content: str,
        content_type: str,
        decision: str,
        reason: str,
        categories: Dict[str, bool]
    ) -> str:
        """Audit kaydı oluştur."""
        import hashlib
        
        entry = AuditEntry(
            id=self._generate_id(),
            timestamp=datetime.now(),
            user_id=user_id,
            content_type=content_type,
            content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            decision=decision,
            reason=reason,
            categories=categories,
        )
        
        await self._save_entry(entry)
        return entry.id
    
    async def get_flagged_for_review(self, limit: int = 50) -> List[AuditEntry]:
        """İncelenmesi gereken kayıtları getir (admin panel için)."""
        pass
    
    async def mark_reviewed(self, entry_id: str, notes: str):
        """Kaydı incelendi olarak işaretle."""
        pass
    
    async def get_stats(self) -> Dict:
        """Moderation istatistikleri."""
        return {
            "total_requests": 0,
            "blocked_count": 0,
            "flagged_count": 0,
            "false_positive_rate": 0.0,
        }

# Singleton
audit_logger = ModerationAuditLogger()
```

#### 6.3 User Report System

**Dosya:** `app/api/user_routes.py` eklemeler

```python
class ContentReportIn(BaseModel):
    content_id: str
    report_type: str  # "false_positive", "missed_nsfw", "other"
    description: Optional[str] = None

@router.post("/report/content")
async def report_content(
    body: ContentReportIn,
    user: User = Depends(get_current_active_user)
):
    """
    İçerik raporu gönder.
    
    Kullanıcı yanlış engelleme veya kaçan içerik bildirebilir.
    """
    from app.services.moderation_audit import audit_logger
    
    await audit_logger.add_user_report(
        user_id=user.id,
        content_id=body.content_id,
        report_type=body.report_type,
        description=body.description
    )
    
    return {"success": True, "message": "Raporunuz alındı"}
```

---

## 7. ROUTER SİSTEMİ → 10/10

### Mevcut: 9/10 | Eksik: 1 puan

#### 7.1 Routing Cache

**Dosya:** `app/chat/routing_cache.py` (YENİ)

```python
"""
Routing Cache
=============
Benzer mesajlar için routing kararını cache'le.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib

class RoutingCache:
    """Routing kararı cache."""
    
    TTL_SECONDS = 300  # 5 dakika
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
    
    def _normalize_message(self, message: str) -> str:
        """Mesajı normalize et (cache key için)."""
        # Küçük harf, boşlukları temizle
        normalized = message.lower().strip()
        # Sayıları mask'le (hava durumu 15 derece vs 20 derece aynı route)
        import re
        normalized = re.sub(r'\d+', 'NUM', normalized)
        return normalized
    
    def _make_key(self, message: str, persona: str) -> str:
        """Cache key oluştur."""
        normalized = self._normalize_message(message)
        key_input = f"{normalized}:{persona}"
        return hashlib.md5(key_input.encode()).hexdigest()
    
    def get(self, message: str, persona: str) -> Optional[str]:
        """Cache'den routing target al."""
        key = self._make_key(message, persona)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["target"]
    
    def set(self, message: str, persona: str, target: str):
        """Routing kararını cache'le."""
        key = self._make_key(message, persona)
        self._cache[key] = {
            "target": target,
            "expires_at": datetime.now() + timedelta(seconds=self.TTL_SECONDS)
        }

routing_cache = RoutingCache()
```

#### 7.2 Routing Analytics (Prometheus)

**Dosya:** `app/services/routing_metrics.py` (YENİ)

```python
"""
Routing Metrics
===============
Prometheus metrikleri için routing istatistikleri.
"""

from typing import Dict
from collections import defaultdict
from datetime import datetime

class RoutingMetrics:
    """Routing metrikleri."""
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.latencies: Dict[str, list] = defaultdict(list)
    
    def record_route(self, target: str, latency_ms: float):
        """Route kararını kaydet."""
        self.counters[f"route_{target}"] += 1
        self.latencies[target].append(latency_ms)
        
        # Son 1000 kaydı tut
        if len(self.latencies[target]) > 1000:
            self.latencies[target] = self.latencies[target][-1000:]
    
    def get_prometheus_metrics(self) -> str:
        """Prometheus format metrikleri."""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f"mami_routing_{key}_total {value}")
        
        # Latency histograms
        for target, latencies in self.latencies.items():
            if latencies:
                avg = sum(latencies) / len(latencies)
                lines.append(f"mami_routing_{target}_latency_avg_ms {avg:.2f}")
        
        return "\n".join(lines)
    
    def get_dashboard_data(self) -> Dict:
        """Dashboard için data."""
        total = sum(self.counters.values())
        
        distribution = {}
        for key, value in self.counters.items():
            target = key.replace("route_", "")
            distribution[target] = {
                "count": value,
                "percentage": (value / total * 100) if total > 0 else 0
            }
        
        return {
            "total_requests": total,
            "distribution": distribution,
        }

routing_metrics = RoutingMetrics()
```

---

## 8. İNTERNET ARAMA → 10/10

### Mevcut: 8/10 | Eksik: 2 puan

#### 8.1 Search Result Caching

**Dosya:** `app/search/cache.py` (YENİ)

```python
"""
Search Result Cache
===================
Arama sonuçlarını cache'le.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib
import json

class SearchCache:
    """Arama sonuçları cache."""
    
    # TTL by query type
    TTL_CONFIG = {
        "weather": 900,     # 15 dakika
        "exchange": 300,    # 5 dakika
        "sports": 1800,     # 30 dakika
        "general": 3600,    # 1 saat
    }
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
    
    def _make_key(self, query: str) -> str:
        """Query'yi cache key'e dönüştür."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_ttl(self, query_type: str) -> int:
        """Query tipine göre TTL döndür."""
        return self.TTL_CONFIG.get(query_type, self.TTL_CONFIG["general"])
    
    def get(self, query: str) -> Optional[List[Dict]]:
        """Cache'den sonuçları al."""
        key = self._make_key(query)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["results"]
    
    def set(self, query: str, results: List[Dict], query_type: str = "general"):
        """Sonuçları cache'le."""
        key = self._make_key(query)
        ttl = self._get_ttl(query_type)
        
        self._cache[key] = {
            "results": results,
            "query_type": query_type,
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }
    
    def clear_expired(self):
        """Süresi dolan cache'leri temizle."""
        now = datetime.now()
        keys_to_delete = [
            k for k, v in self._cache.items() 
            if now > v["expires_at"]
        ]
        for key in keys_to_delete:
            del self._cache[key]

search_cache = SearchCache()
```

#### 8.2 Daha Fazla Structured Parser

**Dosya:** `app/search/structured_parser.py` eklemeler

```python
# Mevcut parser'lara ek

def parse_movie_result(snippets: List, movie_name: str) -> Dict:
    """
    Film bilgisi parse et.
    
    Output:
    {
        "title": "Inception",
        "year": 2010,
        "director": "Christopher Nolan",
        "rating": 8.8,
        "genres": ["Sci-Fi", "Thriller"],
        "duration": "148 min"
    }
    """
    pass

def parse_wikipedia_result(snippets: List, topic: str) -> Dict:
    """
    Wikipedia özeti parse et.
    
    Output:
    {
        "title": "Python (programming language)",
        "summary": "Python is a high-level...",
        "categories": ["Programming languages"],
        "url": "https://en.wikipedia.org/..."
    }
    """
    pass

def parse_product_price_result(snippets: List, product: str) -> Dict:
    """
    Ürün fiyatı parse et.
    
    Output:
    {
        "product": "iPhone 15 Pro",
        "price_range": {"min": 45000, "max": 55000},
        "currency": "TRY",
        "stores": [
            {"name": "Apple", "price": 54999},
            {"name": "Hepsiburada", "price": 52999}
        ]
    }
    """
    pass

def parse_recipe_result(snippets: List, dish: str) -> Dict:
    """
    Tarif bilgisi parse et.
    
    Output:
    {
        "name": "Karnıyarık",
        "prep_time": "30 min",
        "cook_time": "45 min",
        "servings": 4,
        "ingredients": [...],
        "steps": [...]
    }
    """
    pass
```

#### 8.3 Search Rate Limiting

**Dosya:** `app/search/rate_limiter.py` (YENİ)

```python
"""
Search Rate Limiter
===================
Kullanıcı bazlı arama limiti.
"""

from typing import Dict
from datetime import datetime, timedelta

class SearchRateLimiter:
    """Arama rate limiter."""
    
    DAILY_LIMIT = 100  # Günlük max arama
    MINUTE_LIMIT = 10  # Dakikada max arama
    
    def __init__(self):
        self._daily_counts: Dict[int, Dict] = {}
        self._minute_counts: Dict[int, Dict] = {}
    
    def can_search(self, user_id: int) -> tuple[bool, str]:
        """Kullanıcı arama yapabilir mi?"""
        now = datetime.now()
        today = now.date()
        current_minute = now.replace(second=0, microsecond=0)
        
        # Günlük limit kontrolü
        if user_id in self._daily_counts:
            entry = self._daily_counts[user_id]
            if entry["date"] == today and entry["count"] >= self.DAILY_LIMIT:
                return False, "Günlük arama limitinize ulaştınız"
        
        # Dakika limit kontrolü
        if user_id in self._minute_counts:
            entry = self._minute_counts[user_id]
            if entry["minute"] == current_minute and entry["count"] >= self.MINUTE_LIMIT:
                return False, "Çok fazla arama yapıyorsunuz, lütfen bekleyin"
        
        return True, ""
    
    def record_search(self, user_id: int):
        """Arama kaydı."""
        now = datetime.now()
        today = now.date()
        current_minute = now.replace(second=0, microsecond=0)
        
        # Günlük sayaç
        if user_id not in self._daily_counts or self._daily_counts[user_id]["date"] != today:
            self._daily_counts[user_id] = {"date": today, "count": 0}
        self._daily_counts[user_id]["count"] += 1
        
        # Dakika sayaç
        if user_id not in self._minute_counts or self._minute_counts[user_id]["minute"] != current_minute:
            self._minute_counts[user_id] = {"minute": current_minute, "count": 0}
        self._minute_counts[user_id]["count"] += 1

search_rate_limiter = SearchRateLimiter()
```

---

## 📊 ÖZET: 10/10 İÇİN TOPLAM İŞ

### Yeni Dosyalar (17 adet)

| Dosya | Satır | Öncelik |
|-------|-------|---------|
| prompts/version_manager.py | ~100 | Orta |
| services/prompt_analytics.py | ~80 | Orta |
| memory/decay.py | ~60 | Yüksek |
| memory/summarizer.py | ~80 | Orta |
| services/message_scorer.py | ~100 | Orta |
| services/context_cache.py | ~60 | Orta |
| image/batch_generator.py | ~100 | Düşük |
| image/history.py | ~80 | Düşük |
| services/custom_persona.py | ~120 | Orta |
| services/content_moderator.py | ~100 | **Yüksek** |
| services/moderation_audit.py | ~80 | **Yüksek** |
| chat/routing_cache.py | ~60 | Orta |
| services/routing_metrics.py | ~80 | Orta |
| search/cache.py | ~80 | **Yüksek** |
| search/rate_limiter.py | ~60 | Orta |
| + structured_parser.py eklemeleri | ~200 | Düşük |

**Toplam: ~1500 satır yeni kod**

### Güncellenecek Dosyalar

| Dosya | Değişiklik |
|-------|------------|
| chat/processor.py | sliding_window, message_scoring |
| memory/rag.py | smart chunking |
| api/user_routes.py | custom persona, report endpoints |

---

## ⏱️ TAHMİNİ SÜRE

| Öncelik | İşler | Süre |
|---------|-------|------|
| Yüksek | Moderation, Search Cache, Memory Decay | 3-4 gün |
| Orta | Version Manager, Context Cache, Routing Cache | 3-4 gün |
| Düşük | Batch Gen, Custom Persona, Parsers | 2-3 gün |

**TOPLAM: 8-11 iş günü (~2 hafta)**

---

## 🎯 ÖNCELİK SIRASI

1. **content_moderator.py + moderation_audit.py** (Sansür: 7→10)
2. **search/cache.py** (Arama: 8→10)
3. **memory/decay.py** (Hafıza: 8→10)
4. **chat/routing_cache.py** (Router: 9→10)
5. **services/context_cache.py** (Sohbet: 8→10)
6. **prompts/version_manager.py** (Prompt: 9→10)
7. Diğerleri...

---

*Bu doküman 10/10 hedefi için gereken tüm iyileştirmeleri içerir.*  
*Tahmini tamamlanma: 2 hafta*  
*Son güncelleme: 2025-12-12*
