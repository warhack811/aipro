# 🏆 Mami AI - Kalite Maksimizasyonu Master Planı

**Tarih:** 2025-12-12  
**Hedef:** Tüm sistemleri ChatGPT/Claude seviyesine çıkarmak  
**Versiyon:** 1.0

---

## 📑 İÇİNDEKİLER

1. [Hafıza Sistemi](#1-hafiza-sistemi)
2. [Prompt Sistemi](#2-prompt-sistemi)
3. [Sohbet İşleme](#3-sohbet-isleme)
4. [Görsel Üretim](#4-gorsel-uretim)
5. [İnternet Arama](#5-internet-arama)
6. [Persona/Mod Sistemi](#6-personamod-sistemi)
7. [Router Sistemi](#7-router-sistemi)
8. [Güvenlik/Sansür](#8-guvenliksansur)
9. [Cevap Kalite Kontrolü](#9-cevap-kalite-kontrolu)
10. [Frontend/UX](#10-frontendux)
11. [Altyapı/DevOps](#11-altyapidevops)
12. [Monitoring/Analytics](#12-monitoringanalytics)
13. [Test Altyapısı](#13-test-altyapisi)
14. [Uygulama Öncelik Sırası](#14-uygulama-oncelik-sirasi)

---

## 1. HAFIZA SİSTEMİ

### 🎯 Hedef: Kişisel asistan seviyesinde kullanıcı tanıma

### Mevcut Durum
- ❌ Serbest text formatı
- ❌ Genel bilgiler de kaydediliyor
- ❌ Çelişki yönetimi zayıf

### Öneriler

#### 1.1 Yapılandırılmış Kullanıcı Profili
```python
class UserProfile:
    # STRUCTURED FIELDS
    name: str
    age: int
    gender: str  # male/female/other
    location_city: str
    location_country: str
    profession: str
    company: str
    marital_status: str
    children_count: int
    
    # LISTS
    hobbies: List[str]
    languages: List[str]
    tech_skills: List[str]
    pets: List[Pet]
    family_members: List[FamilyMember]
    
    # FREE-FORM
    goals: List[str]
    custom_facts: List[str]
```

**Fayda:** Direkt erişim, çelişki tespiti, UI profil kartı

#### 1.2 Akıllı Hafıza Kayıt Kuralları
| Kaydet ✅ | Kaydetme ❌ |
|-----------|-------------|
| "Adım Mehmet" | "Türkiye'nin başkenti Ankara" |
| "İstanbul'da yaşıyorum" | "Python bir dil" |
| "Yazılımcıyım" | "2+2=4" |
| "React öğreniyorum" | "Bugün hava güzel" |

#### 1.3 Memory Decay (Zaman Azalması)
```python
# 30 günde kullanılmazsa importance yarıya düşer
new_importance = original * (0.5 ^ (days_unused / 30))
```

#### 1.4 Hafıza Özeti (50+ kayıt için)
```
"Bu kullanıcı: 28 yaşında yazılımcı, İstanbul'da yaşıyor,
evli ve 1 çocuğu var. Python ve React kullanıyor,
futbol seyretmeyi seviyor. Şu an İngilizce öğreniyor."
```

#### 1.5 Duplicate Detection İyileştirmesi
- Semantic similarity > 0.85 → Aynı bilgi, kaydetme
- Çelişki varsa → Eski kaydı invalidate et

---

## 2. PROMPT SİSTEMİ

### 🎯 Hedef: Tutarlı, doğal, kişiselleştirilmiş yanıtlar

### Öneriler

#### 2.1 Prompt Versioning
```python
class PromptVersion:
    version: str  # "v1.2.3"
    hash: str
    created_at: datetime
    changelog: str
    ab_test_weight: float  # A/B test için
```

**Fayda:** Rollback, A/B test, performans karşılaştırma

#### 2.2 Dynamic Prompt Length
```python
if question_length < 50:
    add_instruction("Kısa ve öz cevap ver")
elif question_length > 200:
    add_instruction("Detaylı açıkla")
```

#### 2.3 Context-Aware Prompting
```python
# Sohbet bağlamına göre prompt ayarla
if is_follow_up_question:
    add_instruction("Önceki cevabı referans al")
if user_seems_confused:
    add_instruction("Daha basit açıkla")
```

#### 2.4 Prompt Analytics
- Hangi prompt versiyonu daha iyi yanıt üretiyor?
- Token/kalite oranı
- User satisfaction by prompt version

---

## 3. SOHBET İŞLEME

### 🎯 Hedef: Akıcı, bağlamsal, hatırlayan sohbetler

### Öneriler

#### 3.1 Sliding Window + Summary
```
[ÖZET: İlk 20 mesajın özeti - 2-3 cümle]
[SON 10 MESAJ: Tam içerik]
[MEVCUT MESAJ]
```

**Fayda:** Token tasarrufu, uzun sohbetlerde bağlam korunur

#### 3.2 Message Importance Scoring
```python
IMPORTANCE_FACTORS = {
    "contains_user_name": 0.3,
    "contains_memory": 0.4,
    "is_question": 0.2,
    "has_code": 0.3,
    "user_liked": 0.5,
    "is_recent": 0.5,
}
```

#### 3.3 Context Caching
- Aynı sohbet için context cache (60 saniye TTL)
- Yeni mesaj eklenene kadar geçerli

#### 3.4 Conversation Compression
```
Orijinal: 5 ayrı hava durumu sorusu
Compressed: "Kullanıcı hava durumu sorgularında bulundu"
```

#### 3.5 Regenerate Özelliği
```python
POST /user/chat/regenerate
{
    "message_id": "xxx",
    "instruction": "Daha kısa yaz"  # opsiyonel
}
```

---

## 4. GÖRSEL ÜRETİM

### 🎯 Hedef: Hızlı, kaliteli, kontrollü görsel üretim

### Öneriler

#### 4.1 Batch Generation
```python
# Tek prompt ile 4 varyasyon
await generate_batch(
    prompt="Güzel bir manzara",
    variations=4,
    variation_strength=0.3
)
```

#### 4.2 Style Presets
```python
STYLE_PRESETS = {
    "realistic": "photorealistic, 8k, detailed",
    "anime": "anime style, vibrant colors",
    "artistic": "oil painting, artistic",
    "minimal": "minimalist, clean lines",
}
```

#### 4.3 Image History & Favorites
- Son 100 görsel sakla
- Favori işaretleme
- Prompt'u yeniden kullan

#### 4.4 Upscaling
```python
# Tamamlanan görseli 2x-4x büyüt
POST /user/image/upscale
{"image_id": "xxx", "scale": 2}
```

#### 4.5 Progress UX İyileştirmesi
```
[Kuyrukta: 2. sıra] → [Oluşturuluyor: %45] → [Tamamlandı ✓]
                                              [4 varyasyon göster]
```

#### 4.6 Negative Prompt Templates
```python
DEFAULT_NEGATIVE = "blurry, low quality, distorted, ugly"
PORTRAIT_NEGATIVE = "deformed face, extra limbs, ..."
```

---

## 5. İNTERNET ARAMA

### 🎯 Hedef: Hızlı, doğru, kaynaklı bilgi

### Öneriler

#### 5.1 Result Caching
```python
CACHE_TTL = {
    "weather": 15 * 60,    # 15 dk
    "exchange": 5 * 60,     # 5 dk
    "sports": 30 * 60,      # 30 dk
    "general": 60 * 60,     # 1 saat
}
```

#### 5.2 Source Quality Scoring
```python
TRUSTED_SOURCES = {
    "gov.tr": 1.0,
    "edu.tr": 0.9,
    "wikipedia.org": 0.85,
    "bbc.com": 0.8,
}
```

#### 5.3 More Structured Parsers
| Domain | Parser | Output |
|--------|--------|--------|
| weather | parse_weather | temp, humidity, forecast |
| exchange | parse_exchange | rate, change |
| sports | parse_sports | score, teams |
| **movie** | parse_movie | title, rating, director |
| **wikipedia** | parse_wiki | summary, categories |
| **recipe** | parse_recipe | ingredients, steps |
| **product** | parse_product | price, stores |

#### 5.4 Rate Limiting
```python
LIMITS = {
    "per_minute": 10,
    "per_day": 100,
}
```

#### 5.5 Hallucination Check
```python
# Cevaptaki bilgiyi kaynaklarla doğrula
if not verify_claim_in_sources(claim, sources):
    add_disclaimer("Bu bilgi doğrulanamamıştır")
```

---

## 6. PERSONA/MOD SİSTEMİ

### 🎯 Hedef: Tutarlı, kişilikli, özelleştirilebilir modlar

### Öneriler

#### 6.1 Custom Persona Creator
```python
POST /user/personas/custom
{
    "name": "my_assistant",
    "display_name": "Benim Asistanım",
    "system_prompt": "Sen yardımsever bir asistansın...",
    "initial_message": "Merhaba! Size nasıl yardımcı olabilirim?",
    "avatar_emoji": "🤖"
}
```

#### 6.2 Persona Memory Isolation
- Her persona için ayrı hafıza
- Persona değişince context sıfırla (opsiyonel)

#### 6.3 Persona Templates
```python
TEMPLATES = {
    "teacher": "Öğretmen şablonu - sabırlı, açıklayıcı",
    "mentor": "Mentor şablonu - motive edici, yönlendirici",
    "coder": "Yazılımcı şablonu - teknik, kod odaklı",
}
```

#### 6.4 Persona Analytics
- Hangi persona en çok kullanılıyor?
- User satisfaction by persona

#### 6.5 Mood Adaptation
```python
# Kullanıcı ruh haline göre ton ayarla
if user_seems_frustrated:
    adapt_tone("daha sabırlı ve yardımsever")
```

---

## 7. ROUTER SİSTEMİ

### 🎯 Hedef: Hızlı, doğru, güvenilir yönlendirme

### Öneriler

#### 7.1 Routing Cache
```python
# Benzer mesajlar için cache
"hava durumu nasıl" → INTERNET (cached 5 dk)
"dolar kaç" → INTERNET (cached 5 dk)
```

#### 7.2 Confidence Scoring
```python
class RoutingDecision:
    target: str
    confidence: float  # 0.0-1.0
    fallback: str      # confidence < 0.7 ise
```

#### 7.3 Smart Fallback Chain
```
GROQ → [fail] → LOCAL → [fail] → STUB_RESPONSE
```

#### 7.4 Routing Analytics (Prometheus)
```
mami_routing_groq_total 1234
mami_routing_local_total 567
mami_routing_image_total 89
mami_routing_avg_latency_ms 45.2
```

#### 7.5 User History Aware Routing
```python
# Kullanıcı genelde kod soruyor → GROQ ağırlığı artır
user_patterns = analyze_user_history(user_id)
adjust_routing_weights(user_patterns)
```

---

## 8. GÜVENLİK/SANSÜR

### 🎯 Hedef: Güvenli ama esnek içerik kontrolü

### Öneriler

#### 8.1 ML-Based Content Moderation
```python
# Pattern matching + OpenAI Moderation API
async def moderate(content: str):
    # 1. Hızlı pattern check
    if pattern_check(content).is_flagged:
        return blocked
    
    # 2. ML check (OpenAI API)
    result = await openai_moderate(content)
    return result
```

#### 8.2 Audit Logging
```python
@dataclass
class ModerationAuditEntry:
    timestamp: datetime
    user_id: int
    content_hash: str  # Gizlilik için hash
    decision: str      # allowed/blocked/flagged
    reason: str
    reviewed: bool
```

#### 8.3 User Report System
```python
POST /user/report/content
{
    "content_id": "xxx",
    "report_type": "false_positive",  # veya "missed_nsfw"
    "description": "Bu neden engellendi?"
}
```

#### 8.4 Contextual Safety
```python
# Bağlama göre güvenlik ayarla
if topic == "medical":
    apply_medical_safety()  # Tıbbi tavsiye uyarısı
elif topic == "legal":
    apply_legal_safety()    # Hukuki sorumluluk reddi
```

#### 8.5 Gradual Escalation
```
Uyarı 1: "Bu içerik uygunsuz olabilir"
Uyarı 2: "İçerik politikamıza aykırı"
Block:   "Bu istek işlenemiyor"
```

---

## 9. CEVAP KALİTE KONTROLÜ

### 🎯 Hedef: Tutarlı, hatasız, tercihlere uygun çıktılar

### Öneriler

#### 9.1 Response Validator
```python
class ResponseValidator:
    def validate(self, response, user_prefs):
        issues = []
        
        # Uzunluk kontrolü
        if not self._check_length(response, user_prefs):
            issues.append("length_mismatch")
        
        # Emoji kontrolü
        if not user_prefs.get("use_emoji"):
            response = self._remove_emojis(response)
        
        # Yarım cümle kontrolü
        if self._has_incomplete_sentence(response):
            response = self._fix_incomplete(response)
        
        # Tekrar kontrolü
        if self._has_repetition(response):
            response = self._remove_repetition(response)
        
        return ValidationResult(response, issues)
```

#### 9.2 Quality Metrics
```python
QUALITY_METRICS = {
    "completeness": "Yarım kalan cümle yok",
    "relevance": "Soruyla ilgili cevap",
    "length_match": "Tercih edilen uzunlukta",
    "format_correct": "Markdown düzgün",
    "no_repetition": "Tekrar yok",
}
```

#### 9.3 Auto-Regenerate Trigger
```python
# Kalite skoru düşükse otomatik yeniden üret
if quality_score < 0.6:
    response = await regenerate_with_feedback(
        "Cevabı daha kısa ve öz yaz"
    )
```

#### 9.4 Streaming Quality Check
```python
# Streaming sırasında kontrol
async for chunk in stream:
    if detect_hallucination_pattern(chunk):
        inject_warning()
    if detect_incomplete_code_block(buffer):
        await close_code_block()
```

#### 9.5 User Feedback Loop
```python
# Like/Dislike feedback'i topla
if user_disliked:
    log_quality_issue(
        response_id=id,
        user_prefs=prefs,
        response_metrics=metrics
    )
```

---

## 10. FRONTEND/UX

### 🎯 Hedef: Modern, hızlı, sezgisel arayüz

### Öneriler

#### 10.1 Optimistic Updates
```typescript
// Mesaj anında görünsün, sonra doğrula
function sendMessage(text) {
    // 1. Hemen UI'a ekle
    addMessageOptimistic(text)
    
    // 2. Backend'e gönder
    await api.sendMessage(text)
    
    // 3. Hata varsa geri al
}
```

#### 10.2 Skeleton Loading
```typescript
// Gerçek içerik yerine placeholder göster
<MessageSkeleton lines={3} />
```

#### 10.3 Infinite Scroll + Virtualization
```typescript
// Sadece görünen mesajları render et
<VirtualizedMessageList 
    messages={messages}
    overscan={5}
/>
```

#### 10.4 Offline Support (PWA)
```typescript
// Çevrimdışı mesaj kuyruğu
if (!navigator.onLine) {
    queueMessageForLater(message)
    showOfflineIndicator()
}
```

#### 10.5 Accessibility (a11y)
```typescript
// Ekran okuyucu desteği
<Message 
    role="article"
    aria-label={`${sender} dedi: ${content}`}
/>
```

#### 10.6 Dark Mode Refinement
- True black (#000) yerine soft black (#121212)
- Kontrast oranı WCAG AA uyumlu
- Auto-switch (sistem tercihi)

#### 10.7 Micro-Interactions
- Mesaj gönderme animasyonu
- Typing indicator (3 nokta)
- Like/Dislike bounce effect
- Smooth scroll on new message

---

## 11. ALTYAPI/DEVOPS

### 🎯 Hedef: Güvenilir, ölçeklenebilir, izlenebilir sistem

### Öneriler

#### 11.1 Health Checks
```python
GET /health
{
    "status": "healthy",
    "components": {
        "database": "ok",
        "chromadb": "ok",
        "groq_api": "ok",
        "forge_api": "ok"
    }
}
```

#### 11.2 Graceful Degradation
```python
# Servis çökerse zarif düşüş
if not groq_available:
    use_local_model()  # Fallback
if not forge_available:
    return placeholder_image()
```

#### 11.3 Rate Limiting (API)
```python
# RedisRateLimiter
@rate_limit(calls=100, period=60)  # 100 call/min
async def chat(request):
    ...
```

#### 11.4 Request Tracing
```python
# Her isteğe unique ID ata
X-Request-ID: abc-123-xyz
# Tüm log'larda bu ID'yi kullan
```

#### 11.5 Config Hot Reload
```python
# Restart olmadan config değiştir
POST /admin/config/reload
```

#### 11.6 Database Migrations
```bash
# Alembic ile versiyon kontrolü
alembic upgrade head
alembic downgrade -1
```

---

## 12. MONITORING/ANALYTICS

### 🎯 Hedef: Gerçek zamanlı görünürlük, proaktif müdahale

### Öneriler

#### 12.1 Prometheus Metrics
```python
# Önemli metrikler
mami_requests_total
mami_request_latency_seconds
mami_errors_total
mami_active_users
mami_messages_per_minute
mami_image_generations_total
mami_memory_operations_total
```

#### 12.2 Grafana Dashboards
- Request/Response Latency
- Error Rates by Endpoint
- Model Usage Distribution
- User Activity Heatmap
- Memory Usage Trends

#### 12.3 Alerting
```yaml
# Prometheus Alert Rules
- alert: HighErrorRate
  expr: rate(mami_errors_total[5m]) > 0.1
  for: 5m
  labels:
    severity: critical

- alert: SlowResponses
  expr: histogram_quantile(0.95, mami_request_latency) > 5
  for: 10m
  labels:
    severity: warning
```

#### 12.4 User Analytics
```python
# Kullanıcı davranış analizi
- En çok kullanılan özellikler
- Ortalama session süresi
- Persona tercihleri
- Hata sıklığı per user
```

#### 12.5 Quality Analytics
```python
# Cevap kalitesi takibi
- Like/Dislike oranı
- Regenerate oranı
- Ortalama cevap uzunluğu
- Yarım cümle oranı
```

---

## 13. TEST ALTYAPISI

### 🎯 Hedef: Güvenilir, kapsamlı, otomatik test

### Öneriler

#### 13.1 Unit Test Coverage (>80%)
```python
# pytest ile kritik fonksiyonlar
def test_memory_should_not_store_general_knowledge():
    result = decide_memory_storage(
        "Türkiye'nin başkenti ne?",
        "Ankara"
    )
    assert result["store"] == False

def test_routing_image_request():
    decision = route_message("/görsel bir kedi çiz")
    assert decision.target == "IMAGE"
```

#### 13.2 Integration Tests
```python
# Tam akış testi
async def test_full_chat_flow():
    response = await client.post("/chat", json={
        "message": "Merhaba, benim adım Test"
    })
    assert response.status_code == 200
    
    # Memory kaydedildi mi?
    memories = await client.get("/memories")
    assert any("Test" in m["text"] for m in memories)
```

#### 13.3 E2E Tests (Playwright)
```typescript
test('user can send message', async ({ page }) => {
    await page.goto('/')
    await page.fill('[data-testid="chat-input"]', 'Merhaba')
    await page.click('[data-testid="send-button"]')
    await expect(page.locator('.message-bubble')).toContainText('Merhaba')
})
```

#### 13.4 Load Testing (Locust)
```python
class ChatUser(HttpUser):
    @task
    def send_message(self):
        self.client.post("/chat", json={
            "message": "Test mesajı"
        })
```

#### 13.5 Prompt Regression Tests
```python
# Prompt değişikliklerinde kalite düşmemeli
def test_prompt_quality_regression():
    test_cases = load_test_cases()
    for case in test_cases:
        response = generate(case.input)
        score = evaluate_quality(response, case.expected)
        assert score >= case.min_score
```

---

## 14. UYGULAMA ÖNCELİK SIRASI

### 🔴 ACIL (1. Hafta)
| # | İş | Sistem | Etki |
|---|---|--------|------|
| 1 | Structured Memory | Hafıza | Yüksek |
| 2 | Response Validator (basic) | Kalite | Yüksek |
| 3 | Search Cache | Arama | Orta |
| 4 | Regenerate Endpoint | Sohbet | Yüksek |

### 🟡 ÖNEMLİ (2. Hafta)
| # | İş | Sistem | Etki |
|---|---|--------|------|
| 5 | ML Moderation | Güvenlik | Yüksek |
| 6 | Memory Decay | Hafıza | Orta |
| 7 | Routing Cache | Router | Orta |
| 8 | Sliding Window | Sohbet | Orta |

### 🟢 İYİLEŞTİRME (3. Hafta)
| # | İş | Sistem | Etki |
|---|---|--------|------|
| 9 | Custom Personas | Persona | Orta |
| 10 | Batch Image Gen | Görsel | Düşük |
| 11 | More Parsers | Arama | Düşük |
| 12 | Prometheus Metrics | Monitoring | Orta |

### 🔵 GELİŞMİŞ (4. Hafta+)
| # | İş | Sistem | Etki |
|---|---|--------|------|
| 13 | Voice Input/Output | Yeni | Yüksek |
| 14 | Plugin System | Yeni | Orta |
| 15 | Team Collaboration | Yeni | Orta |
| 16 | Full Test Coverage | Test | Yüksek |

---

## 📊 ÖZET TABLO

| Sistem | Mevcut | Hedef | Öncelikli İyileştirmeler |
|--------|--------|-------|--------------------------|
| Hafıza | 8/10 | 10/10 | Structured fields, decay |
| Prompt | 9/10 | 10/10 | Versioning, analytics |
| Sohbet | 8/10 | 10/10 | Sliding window, regenerate |
| Görsel | 9/10 | 10/10 | Batch gen, history |
| Arama | 8/10 | 10/10 | Cache, more parsers |
| Persona | 9/10 | 10/10 | Custom personas |
| Router | 9/10 | 10/10 | Cache, analytics |
| Güvenlik | 7/10 | 10/10 | ML moderation, audit |
| Kalite | 6/10 | 10/10 | Validator, feedback loop |
| Frontend | 8/10 | 10/10 | PWA, a11y, animations |
| DevOps | 7/10 | 10/10 | Monitoring, alerting |
| Test | 5/10 | 10/10 | Unit, E2E, load tests |

---

## ⏱️ TAHMİNİ SÜRE

| Faz | Süre | Sonuç |
|-----|------|-------|
| Acil (1. Hafta) | 5 gün | Core kalite artışı |
| Önemli (2. Hafta) | 5 gün | Tüm sistemler 8+ |
| İyileştirme (3. Hafta) | 5 gün | Tüm sistemler 9+ |
| Gelişmiş (4+ Hafta) | 10 gün | 10/10 hedef |

**TOPLAM: ~4 hafta intensif çalışma**

---

*Bu doküman Mami AI'ı dünya standartlarına çıkarmak için gereken tüm iyileştirmeleri içerir.*  
*Son güncelleme: 2025-12-12*
