# 🚀 Enterprise Orchestrator Router - Blueprint v1

> Beyin fırtınası özeti - Implementation için referans doküman

---

## 📋 İçindekiler

1. [Mimari Genel Bakış](#mimari-genel-bakış)
2. [Model Seçim Stratejisi](#model-seçim-stratejisi)
3. [API Key Yönetimi](#api-key-yönetimi)
4. [Specialist-Stylist Pipeline](#specialist-stylist-pipeline)
5. [Selective Jury](#selective-jury)
6. [RAG Intelligent Gate](#rag-intelligent-gate)
7. [Sansür Seviyeleri](#sansür-seviyeleri)
8. [Memory Sistemi](#memory-sistemi)
9. [Output Sanitizer](#output-sanitizer)
10. [Fallback Garantisi](#fallback-garantisi)
11. [Plugin Mimarisi](#plugin-mimarisi)
12. [Ek Özellikler](#ek-özellikler)

---

## 1. Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR PLUGIN                          │
├─────────────────────────────────────────────────────────────────┤
│  Katman 1: Intent Classifier                                    │
│  → Tek LLM çağrısı ile: intent, complexity, domain, RAG kararı  │
├─────────────────────────────────────────────────────────────────┤
│  Katman 2: Capability Router                                    │
│  → Tool seçimi: Web Search, RAG, Image Gen                      │
├─────────────────────────────────────────────────────────────────┤
│  Katman 3: Model Selector                                       │
│  → Complexity + Domain + Persona = En uygun model               │
├─────────────────────────────────────────────────────────────────┤
│  Katman 4: Response Pipeline                                    │
│  → Specialist → Stylist → Jury → Sanitizer → Output             │
└─────────────────────────────────────────────────────────────────┘
```

### Intent Classifier Detay (%95+ Başarı)

```
┌────────────────────────────┬────────────────────────────────────┐
│  INTENT CLASSIFIER         │  SAFETY LAYER                     │
│  (Scout, ~100ms)           │  (Llama Guard, ~100ms)            │
│  PARALEL                   │  PARALEL                          │
│  → Complexity, Domain      │  → NSFW detection                 │
│  → Multi-intent → tasks[]  │  → Prompt injection               │
│  → Tool hints, RAG         │  → Risk category                  │
└────────────────────────────┴────────────────────────────────────┘
```

### Multi-Intent `tasks[]` Yapısı (v4.1)

> ⚠️ **Review Feedback:** Tek mesajda birden fazla görev olabilir

```python
# Intent Classifier çıktısı:
{
    "tasks": [
        {"id": "t1", "type": "research", "query": "X'i araştır", "solver": "web"},
        {"id": "t2", "type": "summarize", "query": "Sonucu özetle", "solver": "qwen", "depends_on": ["t1"]},
        {"id": "t3", "type": "image", "query": "Z görseli üret", "solver": "forge"}
    ],
    "composer": "auto"  # topological sort: t1 → t2, t3 paralel
}

# Composer stratejisi (Final Patch)
# - depends_on boş → paralel çalışabilir
# - depends_on dolu → sıralı bekle
# - Topological sort ile optimal sıralama
```

---

## 2. Model Seçim Stratejisi (Capability Catalog)

> ⚠️ **Review Feedback:** Model adına bağlı routing yerine capability-based selection

### Capability Catalog Yaklaşımı

```python
# Router model adı seçmez, required_capabilities üretir:
required = {
    "capabilities": ["coding", "high_precision", "tr"],
    "quality": "high",
    "needs_tools": ["none"],
    "verify": True,
    "style": True
}

# ModelSelector catalog üzerinden en uygun modeli seçer:
model = catalog.best_match(required)
```

### Model Catalog (Minimal Skor - Consensus v5.2)

> 🤝 **Gemini-ChatGPT Consensus:** 6 alanlık minimal skor seti yeterli

```python
MODEL_CATALOG = {
    "llama-3.1-8b-instant": {
        "strengths": {"coding": 1, "analysis": 1, "creative": 2, "tr_natural": 2, "tool_planning": 1},
        "quality_tier": "med",
        "latency_tier": "fast",
        "cost_tier": "low",
        "can_judge": False,
        "can_rewrite": False
    },
    "qwen3-32b": {
        "strengths": {"coding": 2, "analysis": 3, "creative": 2, "tr_natural": 3, "tool_planning": 3},
        "quality_tier": "high",
        "latency_tier": "med",
        "cost_tier": "med",
        "can_judge": True,
        "can_rewrite": True
    },
    "kimi-k2": {
        # social_chat = TR slang / sokak ağzı / doğal samimiyet (VIP Param)
        "strengths": {"coding": 2, "analysis": 2, "creative": 3, "tr_natural": 3, "tool_planning": 2, "social_chat": 3},
        "quality_tier": "high",
        "latency_tier": "med",
        "cost_tier": "med",
        "can_judge": False,
        "can_rewrite": True  # Stylist primary
    },
    "gpt-oss-120b": {
        "strengths": {"coding": 3, "analysis": 3, "creative": 2, "tr_natural": 2, "tool_planning": 3},
        "quality_tier": "high",
        "latency_tier": "slow",
        "cost_tier": "high",
        "can_judge": True,
        "can_rewrite": False
    },
    "llama-70b": {
        "strengths": {"coding": 2, "analysis": 3, "creative": 2, "tr_natural": 2, "tool_planning": 2},
        "quality_tier": "high",
        "latency_tier": "slow",
        "cost_tier": "high",
        "can_judge": True,
        "can_rewrite": False
    }
}
# Final Patch: tool_planning + social_chat eklendi
```

### Avantaj
- 6 alan yeterli, genişletilebilir
- tier sistemi basit ama ifade gücü var
- can_judge/can_rewrite explicit

---

## 3. API Key Yönetimi (Load-Aware)

> ⚠️ **Review Feedback:** %80 eşiği yerine load-aware + cooldown

### Strateji: Load-Aware + Cooldown

```python
# Key seçimi: least-loaded (son 60s RPM/TPM + hata oranı)
def select_key(model: str) -> APIKey:
    keys = get_available_keys(model)
    return min(keys, key=lambda k: k.load_score)

# 429 alan key: 10-30s cooldown (circuit breaker)
if response.status == 429:
    key.cooldown(seconds=random.randint(10, 30))
    
# Model başına key deneme: 1-2 (fail-fast), sonra cascade
max_key_attempts = 2
```

### Cascade Zincirleri
```python
FALLBACK_CHAINS = {
    "creative": ["kimi-k2", "qwen3-32b", "llama-70b"],
    "code": ["gpt-oss-120b", "llama-70b", "qwen3-32b"],
    "general": ["qwen3-32b", "kimi-k2", "llama-3.1-8b-instant"],
}
```

---

## 4. Specialist-Stylist Pipeline (Output Contract)

> ⚠️ **Review Feedback:** Kod dışı teknik veriler de korunmalı

### Specialist Output Contract

```python
class SpecialistOutput:
    solution: str           # Stylist SADECE bunu düzenler
    code_blocks: List[str]  # IMMUTABLE
    claims: List[str]       # IMMUTABLE - teknik iddialar
    actions: List[str]      # IMMUTABLE - adımlar
    assumptions: List[str]  # IMMUTABLE
    evidence: dict          # IMMUTABLE - serper/RAG özet
```

### Stylist Kuralı
```python
# Stylist sadece solution alanını rewrite eder
styled_output = stylist.rewrite(specialist_output.solution)

# Diğer alanlar dokunulmaz
final = merge(
    styled_output,
    specialist_output.code_blocks,
    specialist_output.claims,
    specialist_output.evidence
)
```

### Consistency Check (Kod Cevapları İçin) (Final v5.3)

> 🤝 **ChatGPT Önerisi:** Metin-kod uyumu kontrol

```python
# Sadece kod içeren cevaplarda aktif
if has_code_blocks and complexity == "high":
    consistency = judge.check(
        question="Metindeki adımlar kodla uyumlu mu?",
        text=styled_output.solution,
        code=specialist_output.code_blocks
    )
    if consistency < 0.7:
        # Rewrite'ı geri al veya "sadece ton değiştir" ile tekrar dene
        styled_output = stylist.rewrite(solution, mode="tone_only")
```

### Pipeline Ne Zaman Aktif?
- GPT-OSS veya Llama cevap verdiyse + stil uyumu gerekiyorsa
- Kimi zaten cevap verdiyse → Pipeline gereksiz

### Streaming Rewrite Mimarisi (Consensus v5.3)

> 🤝 **Gemini + ChatGPT Consensus:** Semantic Buffering + Transparent Mode

#### Temel Prensipler
```
Specialist Stream → Segmenter → Stylist Queue → User
                         ↓
                   Code Block? → Bypass (Transparent Mode)
```

#### Buffer Stratejisi (Semantic Windowing)

```python
# Varsayılan parametreler (VIP Revision v5.8)
CONFIG = {
    "max_buffer_time_ms": 600,
    "min_tokens": 35,
    "target_tokens": 75,           # 60-90 arası (VIP)
    "max_tokens": 160,
    "stylist_timeout_ms": 2000,
    "max_queue_segments": 3
}

# Ultra hızlı mod (VIP)
CONFIG_FAST = {"target_tokens": 50, "max_buffer_time_ms": 400}

# Flush tetikleyicileri
# Fence kapanışı satır başında: \n``` veya \n~~~ (VIP)
FLUSH_TRIGGERS = [".", "!", "?", "\n\n"]
```

#### Kod Bloğu Koruması (Karakter Bazlı State Machine - Final Patch)

```python
async def streaming_pipeline(specialist_stream):
    buffer = ""
    in_code_block = False
    lookback = ""  # Son 5 karakter (fence tespiti için)
    queue_size = 0
    
    async for token in specialist_stream:
        lookback = (lookback + token)[-5:]  # 5 char lookback buffer
        
        # Karakter bazlı fence tespiti (token parçalı gelebilir)
        if "```" in lookback and not in_code_block:
            in_code_block = True
            if buffer:
                yield await stylist.rewrite(buffer)
                buffer = ""
            yield token
            continue
        elif "```" in lookback and in_code_block:
            in_code_block = False
            yield token
            continue

        if in_code_block:
            yield token  # Transparent Mode: bypass
        else:
            buffer += token
            queue_size = get_queue_size()
            
            # Backpressure algoritması (Final Polish)
            if queue_size > 5:
                # Kritik: Stylist bypass, passthrough
                set_flag("styling_degraded", True)  # UI sinyali
                yield buffer
                buffer = ""
                # Cooldown: 15 saniye bypass devam et
                await asyncio.sleep(0)  # non-blocking
            elif queue_size > 3:
                # Orta: Segment büyüt (80 → 140)
                if should_flush(buffer, FLUSH_TRIGGERS, {"target_tokens": 140}):
                    styled = await stylist.rewrite(buffer)
                    yield styled
                    buffer = ""
            elif should_flush(buffer, FLUSH_TRIGGERS, CONFIG):
                styled = await stylist.rewrite(buffer)
                yield styled
                buffer = ""
            
            # Cooldown recovery
            if queue_size <= 2 and get_flag("styling_degraded"):
                set_flag("styling_degraded", False)

    if buffer:
        yield await stylist.rewrite(buffer)
```

#### Fallback Mekanizması

| Durum | Aksiyon |
|-------|---------|
| Stylist timeout (>2s) | Passthrough + log |
| Queue > 3 segment | Segment 80→140 büyüt |
| Queue > 5 segment | **Bypass** + `styling_degraded` flag + **15s cooldown** |
| Cooldown recovery | Queue ≤ 2 → Stylist geri aç |
| Stylist hata | Passthrough + alternatif model |

#### Latency Profili
- **İlk token:** ~500-800ms (kabul edilebilir)
- **Segment arası:** ~200-400ms
- **Kod bloğu:** Anlık (bypass)

---

## 5. Selective Jury (Kalite Odaklı)

> ⚠️ **Review Feedback:** Stil/persona puanı çıkarıldı (zaten stylist çözüyor)

### Ne Zaman Aktif?
- Karmaşık sorular (complexity=high)
- Yüksek riskli domain (health, legal, finance)
- RAG belirsizliği yüksek

### Puanlama Kriterleri (Sadece Kalite)
```python
criteria = {
    "correctness": 25,          # Teknik doğruluk
    "instruction_adherence": 25, # Talimata uyum
    "completeness": 20,          # Tamlık
    "hallucination": 20,         # Uydurma/desteksiz iddia
    "safety": 10                 # Güvenlik
}
# Toplam: 100 puan, stil YOK
```

### Aksiyon
- Puan < 70 → 1 retry (max)
- Puan ≥ 70 → Gönder

### Verify vs Jury Ayrımı (Triple Consensus v5.6)

> 🤝 **Claude + Gemini + ChatGPT Consensus:** Streaming → Jury off

| Durum | Yöntem | Açıklama |
|-------|--------|----------|
| **streaming_enabled = true** | **Jury OFF** | Streaming ile jury çelişir |
| **Casual chat (risk=low)** | **Verify OFF** | Adaptif: gereksiz kontrol yok (VIP) |
| Default | **Tek solver** | Çoğu durumda yeterli |
| risk=high (kod/finans/tıp/hukuk) | **Verify** | 1 solver + hızlı ikinci göz |
| Tool kullanıldı | **Verify** | Tool sonucu kontrol |
| Kullanıcı memnuniyetsizse/retry | **Jury** | 2 solver, best-of seç (non-streaming only) |
| confidence çok düşük (<0.5) | **Jury** | 2 solver, best-of seç (non-streaming only) |

```python
# Jury nadir ama yüksek etkili bir mod
if user_dissatisfied or confidence < 0.5:
    # Jury mode: 2 aday üret, birini seç
    candidates = [solver1.run(), solver2.run()]
    
    # Similarity-Based Bypass (Final Patch)
    # Metrik: Hash/normalize + n-gram Jaccard (hızlı, embedding yok)
    similarity = calculate_similarity(candidates[0], candidates[1])
    # Algoritma:
    # 1. Normalize (whitespace, punctuation temizle)
    # 2. N-gram Jaccard similarity (n=3)
    # 3. Eşik: 0.90 = çok benzer (Final Polish)
    if similarity > 0.90:
        # Cevaplar çok benzer, judge gereksiz
        winner = max(candidates, key=lambda c: c.confidence)
    else:
        winner = jury.select_best(candidates)
        
elif risk == "high" or tool_used:
    # Verify mode: hızlı kontrol
    result = solver.run()
    result = verifier.check(result)
else:
    # Default: tek solver
    result = solver.run()
```

---

## 6. RAG Intelligent Gate (Adaptive RAG)

### Büyük AI Tekniklerinden İlham

1. **Adaptive RAG**: Sorgu türüne göre strateji değiştir
2. **Query Classification**: LLM ile kaynak belirleme
3. **Retrieval Grader**: Alakasız chunk'ları filtrele
4. **Self-Assessment**: Cevap güvenini değerlendir

### Query Classification (İlk Adım)

```python
LLM → "Bu soru için hangi kaynak?"
    → "llm_knowledge": LLM bilgisi yeterli
    → "web_search": Güncel bilgi gerekli
    → "rag_search": Kullanıcı belgeleri gerekli
    → "multi_source": Birden fazla kaynak
```

### 3 Aşamalı Karar

> ⚠️ **Review Feedback:** Net kural tablosu eklendi

| Sinyal | Kaynak | Örnek |
|--------|--------|-------|
| "güncel", "fiyat", "haber", "şimdi" | **Serper** | "Bugün dolar kaç?" |
| "belgede", "pdf", "dosyada", "TCK" | **RAG** | "TCK 157 ne diyor?" |
| İkisi de yok | **LLM Knowledge** | "Python nedir?" |

```
Aşama 1: Açık referans var mı?
  - Serper sinyalleri → Web Search
  - RAG sinyalleri → RAG aç
  - "devam et", "özetle" (belgesiz) → RAG kapa

Aşama 2: Belirsiz → Quick Relevance Check
  - Kullanıcı belgelerine hızlı bakış
  - Relevance > 0.7 → RAG aç

Aşama 3: Hiç belge yok → RAG kapa
```

### Hybrid Search (Triple Consensus v5.7)

> 🤝 **Claude + Gemini + ChatGPT Consensus:** Adaptive Semantic + Keyword

```python
def hybrid_search(query, top_k=20):
    has_exact = detect_patterns(query)  # "Madde 157", "TCK", "v2.1.0"
    
    if has_exact:
        # Keyword-first: BM25 %70 + Semantic %30
        bm25_results = bm25.search(query, top_k=top_k)
        semantic_results = chromadb.search(query, top_k=top_k//2)
        return rrf_fusion(bm25_results, semantic_results, alpha=0.7)
    else:
        # Semantic-first: Vector %70 + BM25 %30
        semantic_results = chromadb.search(query, top_k=top_k)
        bm25_results = bm25.search(query, top_k=top_k//2)
        return rrf_fusion(semantic_results, bm25_results, alpha=0.7)

# Query rewrite for exact match
# "Madde 157" → ["157. madde", "madde 157", "TCK 157"]
```

### Retrieval Pipeline (Triple Consensus)

```python
def retrieve_with_grading(query, top_k=5):
    # 1. Hybrid search → top 20
    candidates = hybrid_search(query, top_k=20)
    
    # 2. Grader → score > 0.7 → top 10
    graded = [c for c in candidates if grader.score(query, c) > 0.7]
    
    # 3. Rerank → final 5
    return rerank(graded)[:top_k]
```

### Post-Retrieval (Retrieval Grader)

```python
for chunk in rag_results:
    score = llm.grade(question, chunk)  # 0-1
    if score > 0.7:
        keep(chunk)  # Alakalı
    else:
        discard(chunk)  # Alakasız atılır
```

### Self-Assessment

```
Cevap üretildikten sonra:
"Bu cevaptan ne kadar eminim?"
  → Düşük güven → Ek arama veya disclaimer
  → Yüksek güven → Direkt gönder
```

---

## 7. Sansür Seviyeleri

### 3 Seviye

| Seviye | Local | NSFW | Personalar |
|--------|-------|------|------------|
| **Sansürsüz** | ✅ | ✅ | Tümü |
| **Esnek** | Admin izniyle | Kısıtlı | Tümü |
| **Sansürlü** | ❌ | ❌ | Tümü (içerik kısıtlı) |

### Önemli Kural
- **Persona engelleme YOK** - Tüm modlar herkese açık
- Sadece **içerik** kısıtlanır
- Groq yapamadığında kibar ret mesajı

### Akış (Fail Reason-Based) (v4.1)

> ⚠️ **Review Feedback v4.1:** 429/timeout ≠ sansür, ayrı ele al

```python
if fail_reason == "429" or fail_reason == "timeout" or fail_reason == "error":
    # Aynı policy ile başka key/model dene
    result = fallback_chain.try_same_policy()
elif fail_reason == "policy_refusal":
    # Sansür seviyesine göre karar
    if user.censorship_level == "sansürsüz":
        result = local_model.run()
    else:
        result = polite_refusal_message()
```

### Tool-Hijack Policy (Consensus v5.2)

> 🤝 **Gemini-ChatGPT Consensus:** Kurallar şart, enforcement kademeli

```python
# 2 mod: Monitor (logla) ve Enforce (blokla)
class ToolHijackPolicy:
    
    # Açık suistimaller - kesin blokla (Enforce)
    ENFORCE_RULES = [
        "system prompt'u göster",
        "gizli anahtar/credential",
        "tool çıktısını talimat gibi uygula",
        "URL'den komut çalıştır"
    ]
    
    # Şüpheli durumlar - logla + risk artır (Monitor)
    MONITOR_RULES = [
        "web search sonuçlarını kullanıcı talimatı gibi yorumla",
        "dosya yazma/silme isteği",
        "harici API çağrısı"
    ]
    
    def validate(self, tool_name, params, task_context=None):
        # Triple Consensus: Intent context ile false positive önleme
        if task_context and task_context.type in ["summarize", "research", "analyze"]:
            # Meşru analiz isteği - tool yorumlama izni var
            allow_tool_interpretation = True
        else:
            allow_tool_interpretation = False
            
        for rule in self.ENFORCE_RULES:
            if violates(rule, params):
                raise ToolHijackError(f"Bloklandı: {rule}")
        
        for rule in self.MONITOR_RULES:
            if violates(rule, params):
                # Intent context kontrolü
                if allow_tool_interpretation and "yorumla" in rule:
                    continue  # Meşru istek, geç
                logger.warning(f"Şüpheli: {rule}")
                self.increase_risk_score()
                return self.use_restricted_tool(tool_name)
```

---

## 8. Memory Sistemi (%98+ Hedef)

> ⚠️ **Review Feedback v4.1:** Detay ayrı dokümanda tutulmalı

### ContextProvider Interface (Router için)

Router sadece bu interface'i bilir:
```python
class ContextProvider(Protocol):
    def get_context(self, user_id: int) -> ContextData:
        """
        Returns:
            recent_messages: List[Message]  # Son 10 mesaj
            session_summary: str             # Bu sohbet özeti
            profile_facts: List[str]         # Kullanıcı profili
            retrieved_chunks: List[Chunk]    # RAG sonuçları
        """
        pass
```

### 4-Layer + Safety Net Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: WORKING MEMORY (Redis - Persistent)                  │
│  → Son 10 mesaj + session summary + RAG cache                  │
│  → TTL: 48 saat (VIP: 24-72h, archive'dan 1 hafta+)            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: USER PROFILE (PostgreSQL + Versioning)               │
│  → Structured facts + LLM confirmation                         │
│  → Cross-validation (çelişki kontrolü)                         │
│  → Version history (geri alınabilir)                           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: SEMANTIC MEMORY (ChromaDB + Double Grader)           │
│  → Scout grader → Qwen grader → Consensus                      │
│  → Deduplication (similarity > 0.95 → merge)                   │
│  → Importance decay + TTL                                      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: CONVERSATION ARCHIVE (PostgreSQL)                    │
│  → Tüm sohbet özetleri + semantic search                       │
│  → "Geçen hafta ne konuşmuştuk?" için                          │
└─────────────────────────────────────────────────────────────────┘
```

### Safety Mekanizmaları

| Risk | Çözüm |
|------|-------|
| Server crash | Redis persistence |
| Yanlış profile | LLM confirmation + versioning |
| Çakışan bilgi | Cross-validation → kullanıcıya sor |
| Alakasız memory | Double grader (Scout + Qwen) |
| Duplicate | Embedding deduplication |
| Stale data | Importance decay + TTL |
| **Yeni fact gecikmesi** | **Anında Working Memory güncelleme** (Final v5.3) |

### Proactive Profile Learning

```python
# CRITICAL: Fact extraction stream bittikten sonra yapılmalı (Final Patch)
async def on_stream_finish(full_response, user_id):
    facts = await extract_facts(full_response)
    for fact in facts:
        # Simhash dedup (Triple Consensus)
        if not simhash_exists(user_id, fact):
            await profile.add_with_confirmation(user_id, fact)
            await working_memory.update(user_id, fact)
```

### Cache Invalidation (Triple Consensus v5.7)

> 🤝 **Claude + Gemini + ChatGPT Consensus:** Scoped + Versioned

```python
# RAG Cache Invalidation
def on_document_upload(user_id, doc_id):
    # Scoped: Sadece bu kullanıcının ilgili cache'i
    redis.delete(f"rag_cache:{user_id}:*")
    
    # Versioned (gelecek): corpus_version tracking
    # corpus_version = hash(file_ids + timestamps)
    # Eski cache TTL ile ölür

# Cache key format
# rag:{user_id}:{corpus_version}:{query_hash}
```

### Rolling Summary (Triple Consensus)

```python
# Summary update frequency (VIP Revision v5.8)
async def on_message(user_id, msg, response, turn_count):
    append_to_working_memory()
    
    # Normal: Her 8 turn (6-10 arası - VIP)
    if turn_count % 8 == 0:
        asyncio.create_task(update_summary_async())
    
    # Critical: Anında ("Beni X diye çağır", "Hatırla")
    if has_critical_info(response):
        await update_summary_immediate()
    
    # Topic shift: Intent classifier tetikler
    if intent.topic_changed:
        asyncio.create_task(update_summary_async())
```

### RAG → Memory Policy (Triple Consensus)

```python
# RAW CHUNK'LAR MEMORY'YE YAZILMAZ (şişer + stale olur)
# Sadece metadata kaydet:
class RAGMetadataTracker:
    async def on_rag_query(user_id, query, results):
        await memory.add_interaction(
            user_id=user_id,
            type="rag_query",
            summary=f"'{query}' araştırdı",
            doc_ids=[r.doc_id for r in results[:3]],  # Sadece top-3
            importance=0.6
        )
        # Faydası: "Geçen hafta o PDF'te ne aramıştın?" → Memory'den

# Memory ↔ RAG Routing
def get_source(query, user_id):
    # 1. Conversation/tercih/karar → Memory
    # 2. Belge/policy/madde → RAG
    # 3. Belirsiz → Memory quick-check → gerekirse RAG
```

---

## 9. Output Sanitizer (Minimal)

> ⚠️ **Review Feedback:** İngilizce kelime temizleme kaldırıldı (teknik metni bozar)

### Sadece Güvenli İşlemler

```python
# Sanitizer SADECE:
1. Markdown fence kapatma (açık ``` kapat)
2. Bozuk format düzeltme
3. Çok sınırlı güvenli normalize

# YAPILMAYACAK:
# - "the/and/but" temizleme (teknik metni bozar)
# - Marka/kütüphane adlarına dokunma
```

### Dil Temizliği Gerekliyse
```
Stylist rewrite-only ile yapılsın (bu scope dışında)
```

### Konum
```
... → Jury → Sanitizer → Kullanıcı
```

---

## 10. Fallback Garantisi

### %100 Cevapsız Kalmama

```
Model 1 (4 key) → tümü dolu
        ↓
Model 2 (4 key) → tümü dolu
        ↓
Model 3 (4 key) → tümü dolu
        ↓
Local Ollama → hata/kapalı
        ↓
Static mesaj: "Yoğunluk var, biraz sonra dene 🙏"
```

### Her Tool İçin
- Web timeout → "Arama yapamadım, bildiğimle cevaplıyorum"
- RAG boş → "Belgelerinde bulamadım"
- Image hata → "Görsel oluşturulamadı"

---

## 11. Plugin Mimarisi (Core vs Plugin) (v5.1)

> ⚠️ **Review Feedback v5.1:** Değişkenlik yüksek → plugin, stabilite kritik → core

### Core (Bypass Edilemez, Stabil)

```
app/core/orchestrator/
├── scheduler.py          # Key rotation, timeouts, retries, cooldown
├── safety_guard.py       # Injection + content policy (NON-BYPASSABLE)
├── observability.py      # Trace, metrics, logging (ortak standart)
└── plugin_host.py        # Plugin loader, config, feature flags
```

### Plugins (A/B Test, Değişime Açık)

```
app/plugins/
├── router_policy/        # Intent + risk + capability mantığı
│   ├── classifier.py
│   ├── capability.py
│   └── model_selector.py
│
├── tools/                # Her tool ayrı plugin
│   ├── serper/
│   ├── forge/
│   └── rag/
│
├── rag_strategy/         # RAG gate, retrieval grader, query rewrite
│   ├── gate.py
│   ├── grader.py
│   └── rewriter.py
│
├── quality_control/      # Verify/Jury
│   ├── jury.py
│   ├── verifier.py
│   └── config.py
│
├── style_rewrite/        # Ton/duygu/stil
│   ├── stylist.py
│   └── persona.py
│
└── context_provider/     # (Opsiyonel) Memory impl
    └── memory.py
```

### Neden Bu Ayrım?

| Bileşen | Neden Plugin/Core |
|---------|-------------------|
| Router Policy | Sürekli evrilir, A/B test |
| Tools | Yeni tool = core'a dokunma |
| RAG Strategy | Sürekli tuning |
| Quality Control | Eşikler, judge model değişir |
| Style | Kullanıcı ayarlarıyla evrilir |
| Scheduler | **Core** - Stabilite kritik |
| Safety | **Core** - Bypass edilemez |
| Observability | **Core** - Ortak standart |

### Interface Kuralı
```python
# Interface core'da, implementasyon plugin'de
class ContextProvider(Protocol):  # core/interfaces.py
    def get_context(self, user_id: int) -> ContextData: ...

class MemoryPlugin(ContextProvider):  # plugins/context_provider/
    def get_context(self, user_id: int) -> ContextData:
        # Implementasyon
```

### Gradual Migration Strategy
```
Phase 1: Plugin eklenir (eski sistem çalışır)
Phase 2: Feature flag ile geçiş
Phase 3: Eski sistem kaldırılır
```

---

## 12. Config & Ayarlar

### Mevcut DynamicConfigService Üzerine Kurulu

```python
# Orchestrator config keys
orchestrator.intent.model = "llama-3.1-8b-instant"
orchestrator.intent.confidence_threshold = 0.8
orchestrator.safety.model = "llama-guard-4-12b"
orchestrator.memory.layer1_ttl = 86400
orchestrator.routing.creative = "kimi-k2"
orchestrator.routing.code = "gpt-oss-120b"
```

### OrchestratorConfig Wrapper

```python
class OrchestratorConfig:
    def __init__(self, config_service: DynamicConfigService):
        self._config = config_service
    
    @property
    def intent_model(self) -> str:
        return self._config.get("orchestrator.intent.model", "llama-3.1-8b-instant")
    
    @property
    def model_routing(self) -> dict:
        return {
            "simple": self._config.get("orchestrator.routing.simple", "llama-3.1-8b-instant"),
            "creative": self._config.get("orchestrator.routing.creative", "kimi-k2"),
            "code": self._config.get("orchestrator.routing.code", "gpt-oss-120b"),
        }
```

### Pydantic Validation
```python
# Geçersiz config → fallback + warning log
valid_models = ["gpt-oss-120b", "llama-70b", "qwen3-32b"]
if value not in valid_models:
    return default_value
```

---

## 12. Ek Özellikler

| Özellik | Durum |
|---------|-------|
| Multi-Tool Parallel | ✅ Kilitlendi |
| Proactive Suggestions | 📌 Eklenecek |
| Confidence Signaling | 🔶 Test lazım |
| Prompt Caching | 🔶 Araştırılacak |
| Streaming | ✅ Mevcut |
| Graceful Failure | ✅ Kilitlendi |

---

## 13. Multi-Tool Parallel Execution

### Konsept
Kullanıcı tek mesajda birden fazla istek yapabilir:
```
"Bugün hava nasıl? Bir de güneş batımı resmi çiz"
→ Intent: [weather, image]
→ Paralel: asyncio.gather(web_search, image_gen)
→ Birleştir: "İstanbul 18°C 🌤️ İşte resmin: [image]"
```

### Paralel vs Sıralı
| Durum | Yöntem |
|-------|--------|
| Tool'lar bağımsız | ✅ Paralel (asyncio.gather) |
| Tool B, A'nın sonucuna bağlı | ❌ Sıralı |

### Limit
- Max 4-5 paralel tool
- Daha fazlaysa: "Çok fazla istek, hangisinden başlayayım?"

---

## 14. Entegrasyonlar

### Image Routing
- Mevcut `image/routing.py` kullanılacak
- Orchestrator wrapper olarak çağırır

### Context Truncation
- Memory sistemiyle birlikte yeniden tasarlanacak
- Kısa sohbet → Tam history
- Uzun sohbet → Summary + son 10 mesaj

### Summary Service
- Mevcut `summary_service.py` referans
- Hierarchical Memory'nin Session katmanında kullanılacak

---

## 16. Structured Logging & Observability

### Trace-Based Logging
```python
# Her istek için benzersiz trace ID
trace_id = generate_trace_id()

# Karar noktalarında event log
events = [
    {"step": "intent_classify", "result": "code", "latency_ms": 45},
    {"step": "model_select", "model": "gpt-oss-120b", "reason": "complexity=high"},
    {"step": "key_select", "key": "key_2", "usage": "75%"},
    {"step": "rag_decision", "result": "skip", "reason": "no_doc_reference"},
    {"step": "response", "total_latency_ms": 1320}
]

# Tek JSON log satırı (sorgulanabilir)
logger.info(json.dumps({"trace_id": trace_id, "events": events}))
```

### Depolama
- JSON dosya veya SQLite
- Admin panel için sorgulanabilir

---

## 17. Metrics & Analytics Dashboard

### Toplanacak Metrikler
```python
class OrchestratorMetrics:
    # Model
    model_calls: Counter       # {"kimi-k2": 1250, "gpt-oss": 340}
    model_latency: Histogram   # Latency dağılımı
    model_errors: Counter
    
    # Key
    key_usage: Gauge           # {"key_1": 45%, "key_2": 72%}
    key_rotations: Counter
    
    # RAG
    rag_hit_rate: Gauge
    rag_skipped: Counter
    
    # Quality
    jury_scores: Histogram
    jury_retries: Counter
    fallback_used: Counter
    
    # UX
    avg_response_time: Gauge
    error_rate: Gauge
```

### Export
- Günlük JSON rapor
- Admin API endpoint

---

## 18. User Feedback Loop

### 3 Katmanlı Feedback

**Katman 1: Implicit**
- Kullanıcı kopyaladı → Beğendi
- Hemen yeni soru → Yetersiz

**Katman 2: Explicit**
- 👍 / 👎 butonları
- "Neden kötü?" dropdown

**Katman 3: Learning**
- Kötü cevaplar → Pattern analizi
- Model selector'a feedback

### Veri Yapısı
```python
class FeedbackRecord:
    user_id: int
    message: str
    response: str
    model_used: str
    rating: Literal["positive", "negative"]
    reason: Optional[str]
    routing_context: dict
```

---

## 19. Timeout & Circuit Breaker

### Per-Model Timeout
```python
TIMEOUTS = {
    "llama-3.1-8b-instant": 10,
    "qwen3-32b": 20,
    "kimi-k2": 25,
    "gpt-oss-120b": 45,
    "local": 60,
    "image_gen": 120,
}
```

### Circuit Breaker
```python
# Son 5 dakikada 3+ hata → Model devre dışı
if failure_count >= 3:
    circuit_open = True
    use_fallback_model()
```

### Fallback Zinciri
```
Timeout/Error → Fallback model → Local → Static mesaj
```

## 20. Error Handling

### Exception Hierarchy
```python
class OrchestratorError(Exception): pass
class IntentClassificationError(OrchestratorError): pass
class ModelUnavailableError(OrchestratorError): pass
class RAGError(OrchestratorError): pass
class ToolExecutionError(OrchestratorError): pass
```

### Graceful Degradation
```python
try:
    response = await specialist.generate(...)
except ModelUnavailableError:
    response = await fallback_chain.try_next(...)
except ToolExecutionError as e:
    response = f"⚠️ {e.tool_name} çalışmıyor. {e.fallback_response}"
```

---

## 21. Proactive Suggestions

### Akış
```
Specialist cevap → should_suggest? → Scout öneri üret → Birleştir
```

### Koşullar
- complexity != "simple"
- not is_continuation
- user_preference != "off"
- Timeout: max 3s

---

## 22. Prompt Caching

### Redis-Based Application Cache
```python
# Değişmeyen prompt parçaları cache'lenir:
- System prompt (persona bazlı, TTL: 1 saat)
- User context (session bazlı, TTL: 1 saat)
- RAG results (soru bazlı, TTL: 1 saat)
```

### Kazanım: ~%25 token, ~50ms latency

---

## 23. Testing Stratejisi

### 3-Katmanlı Test Piramidi

**Unit Tests:**
- Intent Classifier prompts
- Model selector logic
- Sanitizer rules

**Integration Tests:**
- Full pipeline (Intent → Model → Response)
- Memory CRUD operations
- Fallback chain

**E2E Tests:**
- Gerçek API çağrıları (sandbox)
- Multi-turn conversations
- Error scenarios

### Test Coverage Hedefi: %80+

---

## 24. Migration Planı

### 3-Phase Gradual Migration

**Phase 1: Parallel (2 hafta)**
- Orchestrator plugin eklenir
- Feature flag = OFF
- Eski sistem çalışmaya devam

**Phase 2: A/B Test (1 hafta)**
- Feature flag = %10 → %50 → %100
- Metrics karşılaştırma
- Rollback hazır

**Phase 3: Cleanup (1 hafta)**
- Eski smart_router.py kaldırılır
- Documentation güncellenir
- Performance tuning

### Rollback Planı
```python
if orchestrator_error_rate > 5%:
    feature_flag.set("orchestrator", False)
    alert_admin()
```

---

## ⏭️ Blueprint v4 - Complete

Tüm tasarım konuları tamamlandı. Implementation için hazır.

### Toplam Bölümler: 24
1. Mimari Genel Bakış + Intent Classifier
2. Model Seçim Stratejisi
3. API Key Yönetimi
4. Specialist-Stylist Pipeline
5. Selective Jury
6. Adaptive RAG
7. Sansür Seviyeleri
8. Memory Sistemi (%98+)
9. Output Sanitizer
10. Fallback Garantisi
11. Plugin Mimarisi (%98+)
12. Config & Ayarlar
13-19. Ek Özellikler (Multi-Tool, Logging, Metrics, Feedback, Timeout)
20. Error Handling
21. Proactive Suggestions
22. Prompt Caching
23. Testing Stratejisi
24. Migration Planı

