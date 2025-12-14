# 🗺️ Mami AI - Proje Yol Haritası (Roadmap)

**Son Güncelleme:** 2025-12-12  
**Versiyon:** 2.1.0

---

## 📊 Genel Durum Özeti

| Kategori | Tamamlanan | Devam Eden | Planlanan |
|----------|------------|------------|-----------|
| Backend Core | 95% | 5% | - |
| Frontend (new-ui) | 90% | 10% | - |
| Hafıza Sistemi | 70% | 30% | - |
| Kalite Kontrol | 40% | 60% | - |
| Monitoring | 30% | 70% | - |

**Genel Kalite Skoru:** 8.4/10 → Hedef: 10/10

---

## ✅ TAMAMLANAN ÖZELLİKLER

### 🔙 Backend Sistemleri

#### Core Altyapı ✅
- [x] 5 Katmanlı Prompt Sistemi (Core, Persona, User Prefs, Toggles, Safety)
- [x] Smart Router (Groq/Local/Image/Internet yönlendirme)
- [x] Decider LLM (Semantik analiz ve aksiyon belirleme)
- [x] Answerer (Yanıt üretim modülü)
- [x] Streaming Response (SSE)

#### Hafıza & RAG ✅ (Temel)
- [x] ChromaDB tabanlı vektör depolama
- [x] Semantik arama
- [x] Soft delete desteği
- [x] Duplicate detection (temel)
- [x] Doküman chunking (PDF, TXT)

#### Görsel Üretim ✅
- [x] Flux/Forge entegrasyonu
- [x] NSFW algılama ve checkpoint seçimi
- [x] Circuit breaker (hata toleransı)
- [x] WebSocket progress bildirimi
- [x] Async job queue

#### İnternet Araması ✅
- [x] Multi-provider search (DuckDuckGo, Google fallback)
- [x] Structured parsers (hava, döviz, spor)
- [x] Source attribution
- [x] Async parallel queries

#### Güvenlik & Yetki ✅
- [x] 3 seviyeli sansür (Unrestricted, Normal, Strict)
- [x] Pattern-based NSFW detection
- [x] User permission system
- [x] JWT authentication

#### Persona/Mod ✅
- [x] 7 hazır persona
- [x] DB'den dinamik persona yönetimi
- [x] requires_uncensored → otomatik local model

### 🖥️ Frontend (ui-new) ✅

- [x] Responsive Chat Layout (Desktop + Mobile)
- [x] Streaming yanıt gösterimi
- [x] Code blocks + syntax highlighting
- [x] Memory Manager modal
- [x] Settings panel (4 sekme)
- [x] Command Palette (slash komutları)
- [x] Search (Ctrl+K)
- [x] Export/Import
- [x] Image Gallery
- [x] PWA desteği

---

## 🔴 FAZ 1: KRİTİK İYİLEŞTİRMELER (1. Hafta)

### 1.1 Hafıza Sistemi Yeniden Tasarımı 🧠
**Öncelik:** 🔴 En Yüksek | **Süre:** 2-3 gün

| İş | Açıklama | Durum |
|----|----------|-------|
| Structured User Profile | Sabit alanlar: name, age, city, profession, etc. | ⏳ |
| Memory Decider güncelleme | Sadece kişisel bilgileri kaydet, genel bilgileri reddet | ✅ Prompt güncellendi |
| Cleanup script | Mevcut yanlış hafızaları temizle | ✅ Script hazır |
| Çelişki yönetimi | "Artık Ankara'da yaşıyorum" → location_city güncelle | ⏳ |

**Detaylar:**
```python
class UserProfile:
    # Sabit Alanlar
    name: str
    age: int
    location_city: str
    profession: str
    marital_status: str
    
    # Liste Alanları
    hobbies: List[str]
    tech_skills: List[str]
    pets: List[Pet]
    
    # Serbest Form
    goals: List[str]
    custom_facts: List[str]
```

### 1.2 Cevap Kalite Kontrolü (Response Validator) ✅
**Öncelik:** 🔴 En Yüksek | **Süre:** 1-2 gün

| Kontrol | Açıklama | Durum |
|---------|----------|-------|
| Uzunluk kontrolü | Tercih edilen uzunluğa uygunluk | ⏳ |
| Yarım cümle düzeltme | Tamamlanmamış cümleleri tespit ve düzelt | ⏳ |
| Emoji kontrolü | use_emoji=false ise temizle | ⏳ |
| Tekrar kaldırma | Duplicate cümleleri sil | ⏳ |
| Kod bloğu kontrolü | Kapanmamış ``` tespit et | ⏳ |

### 1.3 Regenerate Endpoint 🔄
**Öncelik:** 🔴 Yüksek | **Süre:** 0.5 gün

```python
POST /user/chat/regenerate
{
    "message_id": "xxx",
    "instruction": "Daha kısa yaz"  # opsiyonel
}
```

### 1.4 Search Result Cache 🔍
**Öncelik:** 🔴 Yüksek | **Süre:** 0.5 gün

| Query Type | Cache TTL |
|------------|-----------|
| Döviz kuru | 5 dakika |
| Hava durumu | 15 dakika |
| Spor sonuçları | 30 dakika |
| Genel arama | 1 saat |

---

## 🟡 FAZ 2: ÖNEMLİ İYİLEŞTİRMELER (2. Hafta)

### 2.1 ML-Based Content Moderation 🛡️
**Öncelik:** 🟡 Yüksek | **Süre:** 1 gün

- Pattern matching + OpenAI Moderation API
- Audit logging (tüm kararları kaydet)
- User report system (false positive bildirimi)

### 2.2 Memory Decay Mechanism ⏳
**Öncelik:** 🟡 Yüksek | **Süre:** 1 gün

```python
# 30 günde kullanılmazsa importance yarıya düşer
new_importance = original * (0.5 ^ (days_unused / 30))
# Min importance: 0.1
```

### 2.3 Routing Cache 🚀
**Öncelik:** 🟡 Orta | **Süre:** 0.5 gün

- Benzer mesajlar için karar cache'le (5 dk TTL)
- "hava durumu nasıl" → INTERNET (cached)

### 2.4 Sliding Window + Summary 📜
**Öncelik:** 🟡 Orta | **Süre:** 1 gün

```
[ÖZET: İlk 20 mesajın özeti]
[SON 10 MESAJ: Tam içerik]
[MEVCUT MESAJ]
```

### 2.5 Message Importance Scoring 📊
**Öncelik:** 🟡 Orta | **Süre:** 0.5 gün

- İsim içeren mesaj: +0.3
- Hafızaya kaydedilmiş: +0.4
- Kod bloğu var: +0.3
- Like almış: +0.5
- Son 5 mesaj: +0.5

---

## 🟢 FAZ 3: İYİLEŞTİRMELER (3. Hafta)

### 3.1 Custom Persona Creator 🎭
**Öncelik:** 🟢 Orta | **Süre:** 1 gün

```python
POST /user/personas/custom
{
    "name": "my_assistant",
    "display_name": "Benim Asistanım",
    "system_prompt": "Sen yardımsever...",
    "initial_message": "Merhaba!"
}
```

- Max 5 custom persona/user
- Public sharing (opsiyonel)

### 3.2 Batch Image Generation 🎨
**Öncelik:** 🟢 Orta | **Süre:** 1 gün

- Tek prompt ile 4 varyasyon
- Style presets (Realistic, Anime, Artistic, Minimal)
- Image favorites

### 3.3 More Structured Parsers 🔎
**Öncelik:** 🟢 Düşük | **Süre:** 1 gün

- Film bilgisi (IMDB)
- Wikipedia özeti
- Tarif
- Ürün fiyatı karşılaştırma

### 3.4 Prometheus Metrics 📈
**Öncelik:** 🟢 Orta | **Süre:** 1 gün

```
mami_requests_total
mami_request_latency_seconds
mami_errors_total
mami_routing_groq_total
mami_memory_operations_total
```

### 3.5 Prompt Versioning 📝
**Öncelik:** 🟢 Düşük | **Süre:** 0.5 gün

- Prompt değişikliklerini izle
- A/B test desteği
- Rollback özelliği

---

## 🔵 FAZ 4: GELİŞMİŞ ÖZELLİKLER (4+ Hafta)

### 4.1 Voice Input/Output 🎤
**Öncelik:** 🔵 Gelecek | **Süre:** 3 gün

- STT (Speech-to-Text): Whisper API
- TTS (Text-to-Speech): ElevenLabs/OpenAI
- Voice personas

### 4.2 Plugin System 🔌
**Öncelik:** 🔵 Gelecek | **Süre:** 3 gün

- Custom command registration
- External API integrations
- Plugin marketplace (opsiyonel)

### 4.3 Team Collaboration 👥
**Öncelik:** 🔵 Gelecek | **Süre:** 2 gün

- Paylaşılan sohbetler
- Link ile paylaşım
- Annotations

### 4.4 Advanced Analytics Dashboard 📊
**Öncelik:** 🔵 Gelecek | **Süre:** 2 gün

- Kullanım istatistikleri
- Kalite metrikleri
- User satisfaction trends

### 4.5 Full Test Coverage 🧪
**Öncelik:** 🔵 Gelecek | **Süre:** 3 gün

- Unit tests (>80% coverage)
- Integration tests
- E2E tests (Playwright)
- Load tests (Locust)

---

## 📋 FRONTEND İYİLEŞTİRMELERİ

### Tamamlanan ✅
- [x] BottomNav modal bağlantıları
- [x] ImageGallery API uyumu
- [x] CommandPalette action'ları
- [x] usePreferences hook entegrasyonu

### Planlanan ⏳
| İş | Öncelik | Faz |
|----|---------|-----|
| Message Regenerate button | 🔴 Yüksek | Faz 1 |
| Scroll to message | 🟡 Orta | Faz 2 |
| Feedback API (like/dislike) | 🟡 Orta | Faz 2 |
| User Profile Card | 🟢 Düşük | Faz 3 |
| Offline Support (PWA) | 🟢 Düşük | Faz 3 |
| A11y improvements | 🔵 Gelecek | Faz 4 |

---

## 🏗️ TEKNİK BORÇ (Technical Debt)

### Yüksek Öncelik
- [ ] deleteAllConversations frontend call (backend endpoint yok)
- [ ] Import functionality (ExportImport.tsx TODO)
- [ ] Feedback API frontend entegrasyonu

### Orta Öncelik
- [ ] Feature flags UI entegrasyonu
- [ ] Admin panel new-ui entegrasyonu
- [ ] Kullanılmayan import'ları temizle

### Düşük Öncelik
- [ ] Sentry error tracking entegrasyonu
- [ ] Performance profiling
- [ ] Bundle size optimizasyonu

---

## 📅 ZAMAN ÇİZELGESİ

```
2025-12-12 ─────────────────────────────────────────────────────►

FAZ 1: KRİTİK (1 Hafta)
├── Hafıza Sistemi Yeniden Tasarımı
├── Response Validator
├── Regenerate Endpoint
└── Search Cache

FAZ 2: ÖNEMLİ (1 Hafta)  
├── ML Moderation
├── Memory Decay
├── Routing Cache
└── Sliding Window

FAZ 3: İYİLEŞTİRME (1 Hafta)
├── Custom Personas
├── Batch Image Gen
├── More Parsers
└── Prometheus Metrics

FAZ 4: GELİŞMİŞ (2+ Hafta)
├── Voice I/O
├── Plugin System
├── Team Collab
└── Full Tests

────────────────────────────────────────────► v1.0 Production
```

---

## 🎯 KALİTE HEDEFLERİ

### Mevcut → Hedef Skorlar

| Sistem | Mevcut | Faz 1 | Faz 2 | Faz 3 | Final |
|--------|--------|-------|-------|-------|-------|
| Hafıza | 7/10 | 9/10 | 10/10 | 10/10 | 10/10 |
| Prompt | 9/10 | 9/10 | 9/10 | 10/10 | 10/10 |
| Sohbet | 8/10 | 9/10 | 10/10 | 10/10 | 10/10 |
| Görsel | 9/10 | 9/10 | 9/10 | 10/10 | 10/10 |
| Arama | 8/10 | 9/10 | 9/10 | 10/10 | 10/10 |
| Güvenlik | 7/10 | 7/10 | 9/10 | 10/10 | 10/10 |
| Router | 9/10 | 9/10 | 10/10 | 10/10 | 10/10 |
| Kalite K. | 5/10 | 8/10 | 9/10 | 10/10 | 10/10 |
| **GENEL** | **8.4** | **8.9** | **9.4** | **9.8** | **10.0** |

---

## 💡 NOTLAR VE KARARLAR

### Hafıza Sistemi
- ✅ Karar: Hibrit model (Structured + Free-form)
- ✅ Karar: Genel bilgiler (başkent, tanım) ASLA kaydedilmeyecek
- ✅ Karar: Decay mechanism 30 gün half-life ile

### Cevap Kalitesi
- ✅ Karar: Yarım cümle kontrolü kritik
- ✅ Karar: LLM tabanlı gramer düzeltme → Gereksiz (maliyet)
- ✅ Karar: Emoji temizleme → Basit regex yeterli

### Güvenlik
- ✅ Karar: OpenAI Moderation API entegrasyonu önerilir
- ✅ Karar: Audit logging zorunlu

---

## 📚 İLGİLİ DOKÜMANLAR

| Doküman | Açıklama |
|---------|----------|
| [BACKEND_ANALYSIS_REPORT.md](./BACKEND_ANALYSIS_REPORT.md) | Detaylı backend analizi |
| [FRONTEND_ANALYSIS_REPORT.md](./FRONTEND_ANALYSIS_REPORT.md) | Frontend entegrasyon analizi |
| [IMPROVEMENTS_FOR_10_10.md](./IMPROVEMENTS_FOR_10_10.md) | 10/10 için teknik detaylar |
| [QUALITY_MASTER_PLAN.md](./QUALITY_MASTER_PLAN.md) | Kapsamlı kalite planı |

---

*Bu roadmap proje ilerlemesine göre düzenli olarak güncellenmektedir.*  
*Son güncelleme: 2025-12-12 23:37*
