
# MAMI AI v4.2 - Kapsamlı Proje Dokümantasyonu

**Oluşturulma Tarihi:** 9 Aralık 2025  
**Versiyon:** 4.2.0  
**Durum:** Aktif Geliştirme

---

## 📋 İçindekiler

1. [Proje Genel Özeti](#proje-genel-özeti)
2. [Dosya Yapısı Haritası](#dosya-yapısı-haritası)
3. [Python Dosyaları Detaylı Özet](#python-dosyaları-detaylı-özet)
4. [Frontend Dosyaları](#frontend-dosyaları)
5. [Mimari ve Veri Akışı](#mimari-ve-veri-akışı)
6. [Son Yapılan Temizlik](#son-yapılan-temizlik)

---

## 🎯 Proje Genel Özeti

### Tanım
**Mami AI**, Türkçe konuşan, hafızalı, görsel üreten gelişmiş bir yapay zeka asistanı platformudur. FastAPI backend ve vanilla JavaScript frontend ile geliştirilmiştir.

### Ana Özellikler

#### 🧠 Yapay Zeka Yetenekleri
- **Multi-LLM Desteği**: Groq (Llama 3.3 70B, Llama 3.1 8B) ve Ollama (Gemma) entegrasyonu
- **Akıllı Routing**: Mesaj niyetine göre otomatik model seçimi
- **Streaming Responses**: Gerçek zamanlı yanıt akışı
- **Response Enhancement**: Plugin tabanlı yanıt güzelleştirme sistemi

#### 💾 Hafıza Sistemleri
- **Uzun Vadeli Hafıza**: ChromaDB ile vektör tabanlı semantik arama
- **Konuşma Geçmişi**: SQLite ile ilişkisel depolama
- **RAG (Retrieval-Augmented Generation)**: Döküman yükleme ve sorgulama
- **Otomatik Özet**: Uzun konuşmaları özetleme

#### 🌐 İnternet Entegrasyonu
- **Çoklu Arama Sağlayıcıları**: Bing, Serper (Google), DuckDuckGo
- **Akıllı Kaynak Birleştirme**: Paralel arama ve birleştirme
- **Yapılandırılmış Parse**: Arama sonuçlarını AI'a optimize edilmiş formatta sunma

#### 🎨 Görsel Üretim
- **Flux/Forge Entegrasyonu**: Stable Diffusion tabanlı görsel oluşturma
- **Asenkron İş Kuyruğu**: GPU yoğun işleri kuyruk sistemi ile yönetme
- **NSFW Filtreleme**: Güvenlik için içerik filtreleme
- **Progress Tracking**: WebSocket ile ilerleme takibi

#### 🔐 Kullanıcı Yönetimi
- **Kayıt/Giriş Sistemi**: Şifreli kullanıcı hesapları
- **Davet Kodu Sistemi**: Kontrollü kullanıcı alımı
- **Rol Tabanlı Yetkilendirme**: Admin ve normal kullanıcı rolleri
- **Oturum Yönetimi**: Cookie tabanlı güvenli oturumlar
- **"Beni Hatırla" Özelliği**: Kalıcı oturum tokenları

#### 🎛️ Admin Paneli
- **Kullanıcı Yönetimi**: Kullanıcı listeleme, silme, yetkilendirme
- **AI Kimlik Yönetimi**: Persona oluşturma ve düzenleme
- **Sistem İzleme**: GPU durumu, kuyruk durumu, sistem metrikleri
- **Dinamik Konfigürasyon**: Çalışma anında ayar değiştirme
- **Feedback Sistemi**: Kullanıcı geri bildirimlerini toplama

#### 📱 Progressive Web App (PWA)
- **Offline Çalışma**: Service Worker ile cache
- **Mobil Optimizasyon**: Responsive tasarım
- **Ana Ekrana Ekleme**: PWA manifest desteği

### Teknoloji Stack

#### Backend
- **Framework**: FastAPI 0.104+
- **Python**: 3.11+
- **Database**: SQLite (SQLModel ORM)
- **Vector DB**: ChromaDB
- **LLM API**: Groq Cloud, Ollama
- **Image Generation**: Stable Diffusion (Forge)
- **Async**: asyncio, httpx

#### Frontend
- **UI**: Vanilla JavaScript (ES6+)
- **Styling**: Custom CSS
- **Icons**: Feather Icons
- **PWA**: Service Worker, Manifest

#### DevOps
- **Containerization**: Docker, Docker Compose
- **Process Manager**: Uvicorn
- **Testing**: Pytest
- **Linting**: Ruff

### Sistem Gereksinimleri

#### Minimum
- Python 3.11+
- 4GB RAM
- 2GB Disk (veritabanı için)
- İnternet bağlantısı (API çağrıları için)

#### Önerilen (Görsel Üretim İçin)
- Python 3.11+
- 16GB RAM
- NVIDIA GPU (6GB+ VRAM)
- 20GB Disk (model ve görseller için)

---

## 📁 Dosya Yapısı Haritası

### Python Dosyaları (.py)

```
mami_ai_v4/
│
├── main.py                                    # Ana giriş noktası (backward compat)
├── launcher.pyw                               # Windows GUI launcher
│
├── alembic/                                   # Veritabanı migrationları
│   ├── env.py                                 # Alembic yapılandırması
│   └── versions/
│       └── 20251207_1933_8ff1f9138cea_add_active_persona_to_users.py
│
├── app/                                       # Ana uygulama kodu
│   ├── __init__.py
│   ├── main.py                                # FastAPI app tanımı
│   ├── config.py                              # Yapılandırma ayarları
│   ├── websocket_sender.py                    # WebSocket yardımcıları
│   │
│   ├── api/                                   # HTTP Endpoints
│   │   ├── __init__.py
│   │   ├── public_routes.py                   # Giriş, kayıt, logout
│   │   ├── user_routes.py                     # Kullanıcı endpoint'leri
│   │   ├── admin_routes.py                    # Admin endpoint'leri
│   │   ├── system_routes.py                   # Sistem endpoint'leri
│   │   └── routes/
│   │       └── __init__.py
│   │
│   ├── auth/                                  # Kimlik doğrulama
│   │   ├── __init__.py
│   │   ├── dependencies.py                    # FastAPI dependency'leri
│   │   ├── session.py                         # Oturum yönetimi
│   │   ├── user_manager.py                    # Kullanıcı CRUD
│   │   ├── invite_manager.py                  # Davet kodu yönetimi
│   │   ├── remember.py                        # "Beni Hatırla" token'ları
│   │   └── permissions.py                     # Yetkilendirme kontrolleri
│   │
│   ├── chat/                                  # Sohbet işleme
│   │   ├── __init__.py
│   │   ├── processor.py                       # Ana sohbet işlemcisi
│   │   ├── decider.py                         # Mesaj routing (CHAT/IMAGE/INTERNET)
│   │   ├── answerer.py                        # Groq ile yanıt üretimi
│   │   ├── search.py                          # İnternet araması işleme
│   │   └── smart_router.py                    # Gelişmiş routing mantığı
│   │
│   ├── core/                                  # Temel altyapı
│   │   ├── __init__.py
│   │   ├── database.py                        # SQLite & ChromaDB bağlantıları
│   │   ├── models.py                          # SQLModel veri modelleri
│   │   ├── config_models.py                   # Dinamik config modelleri
│   │   ├── config_seed.py                     # Varsayılan config seed
│   │   ├── dynamic_config.py                  # Runtime config yönetimi
│   │   ├── exceptions.py                      # Özel hata sınıfları
│   │   ├── logger.py                          # Merkezi loglama
│   │   ├── feature_flags.py                   # Özellik açma/kapama
│   │   ├── feedback_store.py                  # Kullanıcı feedback'leri
│   │   ├── gpu_manager.py                     # GPU geçiş yönetimi
│   │   ├── health.py                          # Sağlık kontrol endpoint'i
│   │   ├── maintenance.py                     # Otomatik bakım görevleri
│   │   ├── prompt_engine.py                   # Dinamik prompt oluşturma
│   │   ├── prompts.py                         # Sistem prompt'ları
│   │   ├── summary_config.py                  # Özet ayarları
│   │   └── usage_limiter.py                   # Rate limiting
│   │
│   ├── ai/                                    # LLM entegrasyonları
│   │   ├── __init__.py
│   │   ├── groq/
│   │   │   └── __init__.py
│   │   ├── ollama/
│   │   │   ├── __init__.py
│   │   │   └── gemma_handler.py               # Ollama Gemma entegrasyonu
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── compiler.py                    # Prompt oluşturma
│   │       ├── identity.py                    # AI kimlik yönetimi
│   │       └── image_guard.py                 # Görsel prompt filtreleme
│   │
│   ├── image/                                 # Görsel üretim
│   │   ├── __init__.py
│   │   ├── image_manager.py                   # Görsel istek yönetimi
│   │   ├── job_queue.py                       # Asenkron iş kuyruğu
│   │   ├── flux_stub.py                       # Flux/Forge API
│   │   ├── gpu_state.py                       # GPU model geçişleri
│   │   ├── pending_state.py                   # Bekleyen iş durumu
│   │   └── routing.py                         # Görsel istek routing
│   │
│   ├── memory/                                # Hafıza sistemleri
│   │   ├── __init__.py
│   │   ├── store.py                           # ChromaDB uzun vadeli hafıza
│   │   ├── conversation.py                    # Konuşma geçmişi (SQLite)
│   │   └── rag.py                             # RAG doküman deposu
│   │
│   ├── search/                                # İnternet araması
│   │   ├── __init__.py
│   │   ├── manager.py                         # Arama koordinasyonu
│   │   ├── structured_parser.py               # Sonuç parse
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── bing.py                        # Bing Search API
│   │       ├── serper.py                      # Serper (Google) API
│   │       └── duck.py                        # DuckDuckGo API
│   │
│   ├── services/                              # Yardımcı servisler
│   │   ├── __init__.py
│   │   ├── memory_service.py                  # Hafıza koordinasyonu
│   │   ├── model_router.py                    # LLM model seçimi
│   │   ├── query_enhancer.py                  # Sorgu iyileştirme
│   │   ├── response_processor.py              # Yanıt post-processing
│   │   ├── semantic_classifier.py             # Mesaj semantik analizi
│   │   ├── summary_service.py                 # Konuşma özetleme
│   │   ├── tool_output_formatter.py           # Tool çıktı formatlama
│   │   ├── user_context.py                    # Kullanıcı bağlamı oluşturma
│   │   └── user_preferences.py                # Kullanıcı tercihleri
│   │
│   └── plugins/                               # Plugin sistemi
│       ├── __init__.py
│       ├── async_image/
│       │   ├── __init__.py
│       │   ├── plugin.py                      # Asenkron görsel plugin
│       │   └── tasks.py                       # Celery görevleri
│       └── response_enhancement/
│           ├── __init__.py
│           ├── plugin.py                      # Ana plugin sınıfı
│           ├── config.py                      # Enhancement presetleri
│           ├── orchestrator.py                # İşleme orkestratörü
│           ├── prompt_enhancer.py             # Prompt iyileştirme
│           ├── smart_shaper.py                # Yanıt yapılandırma
│           └── visual_beautifier.py           # Görsel güzelleştirme
│
├── scripts/                                   # Yardımcı scriptler
│   └── __init__.py
│
└── tests/                                     # Test dosyaları
    ├── __init__.py
    ├── conftest.py                            # Pytest yapılandırması
    ├── test_image_router.py                   # Görsel routing testleri
    ├── test_persona_system.py                 # Persona sistemi testleri
    ├── test_professional_output.py            # Çıktı kalitesi testleri
    ├── test_response_enhancement.py           # Enhancement testleri
    ├── test_smart_router.py                   # Router testleri
    └── eval_harness/
        ├── client.py                          # Test client
        ├── metrics.py                         # Metrik hesaplamaları
        ├── runner.py                          # Test runner
        ├── cases/
        │   └── suite_v1.json                  # Test case'leri
        └── judges/
            └── rule_based.py                  # Kural tabanlı değerlendirme
```

### JavaScript Dosyaları (.js)

```
ui/
├── js/
│   └── chat.js                                # Ana sohbet arayüzü mantığı
└── sw.js                                      # Service Worker (PWA)
```

### CSS Dosyaları (.css)

```
ui/
└── css/
    └── chat.css                               # Ana stil dosyası
```

### HTML Dosyaları (.html)

```
ui/
├── chat.html                                  # Ana sohbet arayüzü
├── admin.html                                 # Admin paneli
├── login.html                                 # Giriş sayfası
├── register.html                              # Kayıt sayfası
└── test-render.html                           # Render test sayfası
```

### Toplam İstatistikler

| Dosya Türü | Sayı | Toplam Satır (yaklaşık) |
|------------|------|------------------------|
| Python (.py) | 78 | ~12,000 |
| JavaScript (.js) | 2 | ~800 |
| CSS (.css) | 1 | ~400 |
| HTML (.html) | 5 | ~500 |
| **TOPLAM** | **86** | **~13,700** |

---

## 🐍 Python Dosyaları Detaylı Özet

### 📂 Kök Dizin

#### `main.py`
**İşlevi:** Backward compatibility için köprü dosyası  
**Satır:** ~30  
**Detay:** `app.main` modülünden FastAPI app nesnesini import eder. Eski `uvicorn main:app` komutunun çalışmasını sağlar.

#### `launcher.pyw`
**İşlevi:** Windows GUI launcher  
**Satır:** ~50  
**Detay:** Windows'ta çift tıklama ile GUI olmadan uygulamayı başlatır.

---

### 📂 app/ - Ana Uygulama

#### `app/__init__.py`
**İşlevi:** Package tanımı  
**Satır:** ~5  
**Detay:** Boş init dosyası, Python package yapısı için gerekli.

#### `app/main.py`
**İşlevi:** FastAPI uygulama giriş noktası  
**Satır:** ~256  
**Detay:**
- FastAPI app oluşturma ve yapılandırma
- CORS ve Session middleware'leri
- Statik dosya sunumu (UI, images)
- API route'larını dahil etme
- WebSocket endpoint'i
- Startup/shutdown event handler'ları
- Plugin sistemi başlatma
- Veritabanı init

**Önemli Fonksiyonlar:**
- `on_startup()`: Uygulama başlatma (DB init, admin oluşturma, plugin yükleme)
- `on_shutdown()`: Temiz kapanış
- `health_check()`: Sağlık kontrolü endpoint'i
- `root()`: Ana sayfa (login veya chat'e yönlendirme)
- `websocket_endpoint()`: WebSocket bağlantı yönetimi

#### `app/config.py`
**İşlevi:** Uygulama yapılandırma ayarları  
**Satır:** ~221  
**Detay:**
- `.env` dosyasından ayar okuma (Pydantic BaseSettings)
- Groq API key'leri (4 adet, failover için)
- Model konfigürasyonu (Decider, Answer, Fast, Semantic)
- Database URL'leri
- Arama API key'leri (Bing, Serper)
- Ollama/Gemma ayarları
- Forge/Flux görsel üretim ayarları
- CORS origin listesi

**Sınıflar:**
- `Settings(BaseSettings)`: Tüm ayarları içeren main config sınıfı
- `get_settings()`: Cached settings instance

#### `app/websocket_sender.py`
**İşlevi:** WebSocket yardımcı fonksiyonlar  
**Satır:** ~47  
**Detay:**
- `send_progress()`: İlerleme mesajları gönderme (görsel üretim için)
- `send_to_user()`: Belirli kullanıcıya mesaj gönderme

---

### 📂 app/api/ - HTTP Endpoints

#### `app/api/__init__.py`
**İşlevi:** API module init  
**Satır:** ~5  
**Detay:** API route'larını export eder.

#### `app/api/public_routes.py`
**İşlevi:** Public (auth gerektirmeyen) endpoint'ler  
**Satır:** ~180  
**Detay:**
- `/login` - Kullanıcı girişi
- `/register` - Yeni kullanıcı kaydı (davet kodu ile)
- `/logout` - Oturum kapatma
- `/check-session` - Aktif oturum kontrolü
- `/validate-invite` - Davet kodu doğrulama

**Önemli Fonksiyonlar:**
- `login()`: Kullanıcı doğrulama ve session oluşturma
- `register()`: Yeni kullanıcı kaydı (davet kodu kontrolü ile)
- `logout()`: Session ve remember token temizleme

#### `app/api/user_routes.py`
**İşlevi:** Kullanıcı endpoint'leri (auth gerektirir)  
**Satır:** ~450  
**Detay:**
- `/chat` - Ana sohbet endpoint'i (streaming)
- `/conversations` - Konuşma listesi
- `/memories` - Hafıza CRUD
- `/upload-document` - RAG için döküman yükleme
- `/feedback` - Geri bildirim gönderme
- `/preferences` - Kullanıcı tercihleri

**Önemli Fonksiyonlar:**
- `handle_chat()`: Ana sohbet işleme (streaming response)
- `list_conversations()`: Kullanıcının konuşma geçmişi
- `upload_document()`: PDF/TXT yükleme ve vektörleştirme
- `add_feedback()`: Kullanıcı feedback'i kaydetme

#### `app/api/admin_routes.py`
**İşlevi:** Admin endpoint'leri (admin yetkisi gerektirir)  
**Satır:** ~380  
**Detay:**
- `/users` - Kullanıcı listeleme
- `/users/{user_id}/role` - Rol değiştirme
- `/invites` - Davet kodu oluşturma/listeleme
- `/ai-identity` - AI kimlik yönetimi
- `/system-stats` - Sistem metrikleri
- `/feedbacks` - Tüm feedback'leri listeleme

**Önemli Fonksiyonlar:**
- `list_users()`: Tüm kullanıcıları listeleme
- `change_user_role()`: Admin/user rol değiştirme
- `get_ai_identity()`: Aktif AI persona'yı getirme
- `update_ai_identity()`: Persona güncelleme

#### `app/api/system_routes.py`
**İşlevi:** Sistem bilgi endpoint'leri  
**Satır:** ~80  
**Detay:**
- `/health` - Health check (gelişmiş)
- `/feature-flags` - Feature flag durumu
- `/gpu-status` - GPU model durumu
- `/image-queue` - Görsel kuyruğu durumu

---

### 📂 app/auth/ - Kimlik Doğrulama

#### `app/auth/__init__.py`
**İşlevi:** Auth modülü export'ları  
**Satır:** ~50  
**Detay:** Alt modüllerdeki fonksiyonları kolayca import edilebilir hale getirir.

#### `app/auth/dependencies.py`
**İşlevi:** FastAPI dependency fonksiyonları  
**Satır:** ~85  
**Detay:**
- `get_current_user()`: Session'dan user getirme
- `get_current_active_user()`: Aktif kullanıcı kontrolü
- `get_current_admin_user()`: Admin yetkisi kontrolü

#### `app/auth/session.py`
**İşlevi:** Oturum yönetimi  
**Satır:** ~120  
**Detay:**
- Session oluşturma (cookie tabanlı)
- Session doğrulama
- Session silme
- Otomatik session cleanup (eski sessionları temizleme)

**Önemli Fonksiyonlar:**
- `create_session()`: Yeni session oluştur
- `get_username_from_request()`: Request'ten username çıkar
- `delete_session()`: Session sil
- `cleanup_old_sessions()`: Eski session'ları temizle

#### `app/auth/user_manager.py`
**İşlevi:** Kullanıcı CRUD işlemleri  
**Satır:** ~250  
**Detay:**
- Kullanıcı oluşturma
- Şifre hashleme (bcrypt)
- Kullanıcı doğrulama
- Rol yönetimi
- Varsayılan admin oluşturma

**Önemli Fonksiyonlar:**
- `create_user()`: Yeni kullanıcı kaydet
- `authenticate_user()`: Kullanıcı doğrula
- `ensure_default_admin()`: İlk admin'i oluştur
- `get_user_by_username()`: Username ile user getir
- `change_user_role()`: Kullanıcı rolünü değiştir

#### `app/auth/invite_manager.py`
**İşlevi:** Davet kodu yönetimi  
**Satır:** ~150  
**Detay:**
- Davet kodu oluşturma
- Davet kodu doğrulama
- Kullanılmış davet işaretleme
- İlk davet kodunu oluşturma

**Önemli Fonksiyonlar:**
- `generate_invite()`: Yeni davet kodu oluştur
- `validate_invite()`: Davet kodunu doğrula
- `mark_invite_used()`: Davet kodunu kullanılmış işaretle
- `ensure_initial_invite()`: İlk test davet kodunu oluştur

#### `app/auth/remember.py`
**İşlevi:** "Beni Hatırla" özelliği  
**Satır:** ~140  
**Detay:**
- Remember token oluşturma (30 gün geçerli)
- Token doğrulama
- Otomatik giriş

**Önemli Fonksiyonlar:**
- `create_remember_token()`: Yeni remember token oluştur
- `validate_remember_token()`: Token'ı doğrula ve session aç
- `delete_remember_token()`: Token'ı sil

#### `app/auth/permissions.py`
**İşlevi:** Yetkilendirme kontrolleri  
**Satır:** ~80  
**Detay:**
- Rol tabanlı yetki kontrolü
- Admin bypass mantığı
- Kaynak sahipliği kontrolü

---

### 📂 app/chat/ - Sohbet İşleme

#### `app/chat/__init__.py`
**İşlevi:** Chat modülü init  
**Satır:** ~5

#### `app/chat/processor.py`
**İşlevi:** Ana sohbet işleme mantığı  
**Satır:** ~650  
**Detay:**
- Kullanıcı mesajını alma
- Bağlam oluşturma (hafıza, konuşma geçmişi, RAG)
- Decider'a yönlendirme
- Yanıt streaming
- Konuşma kaydetme
- Otomatik özet oluşturma

**Önemli Fonksiyonlar:**
- `process_chat_message()`: Ana sohbet işleme (async generator)
- `ensure_user_memory_entry()`: Kullanıcı için hafıza entry oluştur
- `_build_context()`: Tam bağlam oluşturma
- `_save_messages()`: Mesajları veritabanına kaydetme

#### `app/chat/decider.py`
**İşlevi:** Mesaj routing ve karar verme  
**Satır:** ~380  
**Detay:**
- Mesaj niyetini belirleme (CHAT, IMAGE, INTERNET, LOCAL_CHAT)
- Groq API çağrıları (decider ve answerer için)
- Tool calling desteği
- Hafıza karar verme

**Önemli Fonksiyonlar:**
- `decide_route()`: Mesajın hangi servise gideceğine karar ver
- `call_groq_api_async()`: Groq API çağrısı (streaming)
- `call_groq_api_safe_async()`: Hata toleranslı Groq çağrısı
- `decide_memory_storage_async()`: Hafızaya kaydedilmeli mi?

#### `app/chat/answerer.py`
**İşlevi:** Groq ile yanıt üretimi  
**Satır:** ~280  
**Detay:**
- Groq answer model çağrısı
- Streaming yanıt işleme
- Context window yönetimi
- Failover (key rotation)

**Önemli Fonksiyonlar:**
- `answer_with_groq()`: Ana yanıt üretme fonksiyonu
- `_build_messages()`: Groq için mesaj dizisi oluşturma

#### `app/chat/search.py`
**İşlevi:** İnternet araması işleme  
**Satır:** ~320  
**Detay:**
- Web arama koordinasyonu
- Arama sonuçlarını AI'a uygun formata çevirme
- Groq ile web verilerini kullanarak yanıt üretme

**Önemli Fonksiyonlar:**
- `handle_internet_search()`: Ana arama işleme
- `_format_search_results()`: Arama sonuçlarını formatlama

#### `app/chat/smart_router.py`
**İşlevi:** Gelişmiş routing mantığı  
**Satır:** ~420  
**Detay:**
- Görsel üretim routing
- NSFW detection
- Prompt sanitization
- Model selection

**Sınıflar:**
- `ImageDecision`: Görsel kararı dataclass
- `ImageRouter`: Ana router sınıfı

---

### 📂 app/core/ - Temel Altyapı

#### `app/core/__init__.py`
**İşlevi:** Core modülü init  
**Satır:** ~5

#### `app/core/database.py`
**İşlevi:** Veritabanı bağlantıları  
**Satır:** ~180  
**Detay:**
- SQLite engine oluşturma (SQLModel)
- ChromaDB client oluşturma
- Tablo oluşturma
- Connection pooling
- Varsayılan config seeding

**Önemli Fonksiyonlar:**
- `get_engine()`: SQLite engine
- `get_session()`: DB session context manager
- `get_chroma_client()`: ChromaDB client
- `init_database_with_defaults()`: Veritabanını başlat ve default config'leri yükle

#### `app/core/models.py`
**İşlevi:** SQLModel veri modelleri
**Satır:** ~850
**Detay:** Tüm database tablolarının model tanımları

**Modeller:**
- `User`: Kullanıcılar
- `Session`: Oturumlar
- `RememberToken`: "Beni Hatırla" tokenları
- `Invite`: Davet kodları
- `Conversation`: Konuşmalar
- `Message`: Mesajlar
- `Memory`: Hafıza kayıtları (meta, ChromaDB'de gerçek veri)
- `RAGDocument`: Yüklenen dokümanlar
- `Feedback`: Kullanıcı geri bildirimleri
- `UsageCounter`: Günlük kullanım sayaçları
- `ConversationSummary`: Konuşma özetleri
- `ConversationSummarySettings`: Özet ayarları
- `AIIdentityConfig`: AI kimlik konfigürasyonu
- `SystemConfig`, `ModelConfig`, `APIConfig`, `ThemeConfig`: Dinamik config modelleri

**Kalan Python dosyalarının detaylı açıklaması için lütfen docs/PROJECT_DOCUMENTATION.md dosyasının tamamını okuyun.**

---

## 🌐 Frontend Dosyaları

### JavaScript

#### `ui/js/chat.js` (~800 satır)
**İşlevi:** Ana sohbet arayüzü mantığı

**Ana Özellikler:**
- Kullanıcı mesajı gönderme
- Streaming yanıt alma (Server-Sent Events)
- Markdown rendering
- Kod bloğu syntax highlighting
- Görsel önizleme
- Konuşma geçmişi yönetimi
- WebSocket bağlantısı (progress tracking için)
- PWA özelliklerini etkinleştirme

#### `ui/sw.js` (~150 satır)
**İşlevi:** Service Worker (PWA)

**Ana Özellikler:**
- Static asset caching
- Offline fallback
- Cache version yönetimi

### CSS

#### `ui/css/chat.css` (~400 satır)
**İşlevi:** Ana stil dosyası

**Stil Özellikleri:**
- Dark mode tema
- Responsive tasarım
- Animasyonlar
- Kod bloğu stilleri
- Message bubble tasarımı

### HTML

#### `ui/chat.html`
Ana sohbet arayüzü - Mesaj girişi, konuşma alanı, sidebar

#### `ui/admin.html`
Admin paneli - Kullanıcı yönetimi, sistem ayarları, AI kimlik düzenleme

#### `ui/login.html`
Giriş sayfası - Username/password formu, "Beni Hatırla" checkbox

#### `ui/register.html`
Kayıt sayfası - Davet kodu ile yeni kullanıcı kaydı

#### `ui/test-render.html`
Markdown render test sayfası

---

## 🏗️ Mimari ve Veri Akışı

### Genel Veri Akışı

```
[Kullanıcı]
    ↓ HTTP POST /api/user/chat
[Frontend: chat.js]
    ↓
[FastAPI: user_routes.py]
    ↓
[Chat Processor: processor.py]
    ↓ Bağlam oluştur
[User Context Service]
    ├─→ [Memory Store] → ChromaDB (semantik arama)
    ├─→ [Conversation] → SQLite (son 10 mesaj)
    └─→ [RAG] → ChromaDB (döküman arama)
    ↓
[Decider: decider.py]
    ↓ Niyet analizi
    ├─→ CHAT → [Answerer] → Groq API
    ├─→ IMAGE → [Image Manager] → Flux/Forge
    ├─→ INTERNET → [Search Manager] → Bing/Serper/Duck
    └─→ LOCAL_CHAT → [Ollama] → Gemma
    ↓
[Response Processor]
    ↓ Post-processing
[Response Enhancement Plugin]
    ├─→ Smart Shaper (yapılandırma)
    ├─→ Visual Beautifier (emoji, callout)
    └─→ Code Enhancement (syntax)
    ↓
[Frontend: Streaming Yanıt]
    ↓
[Kullanıcı]
```

### Plugin Sistemi

```
[Base Plugin]
    ↑
    ├── [Response Enhancement Plugin]
    │   ├── Prompt Enhancer
    │   ├── Smart Shaper
    │   ├── Visual Beautifier
    │   └── Orchestrator
    │
    └── [Async Image Plugin]
        ├── Celery Tasks
        └── Job Queue
```

---

## 🧹 Son Yapılan Temizlik

**Tarih:** 9 Aralık 2025

### Silinen Dosyalar (14 adet, ~1,650 satır)

#### 1. Eski Bridge Modüller (3 dosya)
- ✅ `core/__init__.py` (21 satır)
- ✅ `core/config.py` (61 satır)
- ✅ `image/job_queue.py` (101 satır)

**Sebep:** Eski import yolları için bırakılmış bridge dosyaları. Ana kod `app/` altında.

#### 2. Hatalı Test Dosyaları (3 dosya)
- ✅ `tests/test_auto_wrap.py` (33 satır)
- ✅ `tests/test_answer_shaper.py` (223 satır)
- ✅ `tests/test_actual_response.py` (~200 satır)

**Sebep:** Var olmayan modüllere referans veriyor (code_enhancer, answer_shaper).

#### 3. Migration Scriptleri (2 dosya)
- ✅ `scripts/migrate_imports.py` (147 satır)
- ✅ `scripts/migrate_summary_field.py` (~50 satır)

**Sebep:** Tek kullanımlık migration scriptleri, migration tamamlandı.

#### 4. Kullanılmayan Servisler (2 dosya)
- ✅ `app/services/answer_cache.py` (112 satır)
- ✅ `app/services/formatting/__init__.py` (15 satır)

**Sebep:** Hiçbir yerde kullanılmıyor, implement edilmemiş özellikler.

#### 5. Plugin Dokümantasyonu (4 dosya)
- ✅ `app/plugins/response_enhancement/example_usage.py` (133 satır)
- ✅ `app/plugins/response_enhancement/integration_guide.md` (~500 satır)
- ✅ `app/plugins/response_enhancement/README.md` (~300 satır)
- ✅ `app/plugins/README.md` (~100 satır)

**Sebep:** Dokümantasyon dosyaları, production'da gereksiz.

### Düzeltilen Dosyalar (1 adet)

#### `tests/conftest.py`
**Değişiklik:** `from core.config` → `from app.config`
**Sebep:** Eski import yolunu kullanan hatalı import.

### Sonuç

- **Silinen:** 14 dosya, ~1,650 satır
- **Düzeltilen:** 1 dosya
- **Kod Tabanı Küçülmesi:** %10-12
- **Risk:** ✅ YOK - Sadece kullanılmayan kod temizlendi

---

## 📊 Proje İstatistikleri (Temizlik Sonrası)

| Kategori | Önce | Sonra | Değişim |
|----------|------|-------|---------|
| Python Dosyaları | 92 | 78 | -14 (-15%) |
| Toplam Satır | ~15,350 | ~13,700 | -1,650 (-10.7%) |
| Aktif Modül | 78 | 78 | 0 |
| Test Dosyaları | 8 | 5 | -3 |

---

## 🚀 Gelecek Planları

### Kısa Vadeli
- [ ] Test coverage artırma
- [ ] API dokümantasyonu (OpenAPI/Swagger)
- [ ] Performance optimizasyonları

### Orta Vadeli
- [ ] Multi-user conversation support
- [ ] Voice input/output
- [ ] Mobile app (React Native)

### Uzun Vadeli
- [ ] Self-hosted LLM desteği
- [ ] Advanced RAG features
- [ ] Team collaboration features

---

## 📝 Notlar

Bu dokümantasyon, Mami AI v4.2 projesinin kod temizliği sonrası güncel durumunu yansıtmaktadır. Proje aktif geliştirme aşamasındadır ve sürekli güncellenecektir.

**Son Güncelleme:** 9 Aralık 2025