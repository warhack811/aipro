# Mami AI - Mimari Dokümantasyonu

Bu doküman, Mami AI projesinin yapısını ve modüllerini açıklar.
Yeni geliştiricilerin projeyi hızla anlaması için hazırlanmıştır.

---

## 📁 Proje Yapısı

```
mami_ai_v4/
├── app/                      # 🆕 Yeni modüler yapı
│   ├── main.py               # FastAPI uygulama giriş noktası
│   ├── config.py             # Uygulama yapılandırması
│   │
│   ├── api/                  # HTTP Endpoints (route tanımlamaları)
│   │   └── routes/           # admin, auth, chat, memory, system
│   │
│   ├── core/                 # Temel altyapı
│   │   ├── database.py       # SQLite & ChromaDB bağlantıları
│   │   ├── models.py         # SQLModel veri modelleri
│   │   ├── exceptions.py     # Özel hata sınıfları
│   │   ├── logger.py         # Merkezi loglama
│   │   ├── feature_flags.py  # Özellik açma/kapama
│   │   └── usage_limiter.py  # Rate limiting
│   │
│   ├── auth/                 # Kimlik doğrulama
│   │   ├── dependencies.py   # FastAPI dependency'leri
│   │   ├── session.py        # Oturum yönetimi
│   │   ├── user_manager.py   # Kullanıcı CRUD
│   │   ├── invite_manager.py # Davet kodları
│   │   └── remember.py       # "Beni Hatırla" özelliği
│   │
│   ├── chat/                 # Sohbet işleme mantığı
│   │   ├── processor.py      # Ana sohbet akışı
│   │   ├── decider.py        # Mesaj yönlendirme (router)
│   │   ├── answerer.py       # Groq ile yanıt üretimi
│   │   └── search.py         # İnternet araması işleme
│   │
│   ├── ai/                   # LLM entegrasyonları
│   │   ├── groq/             # Groq Cloud API
│   │   ├── ollama/           # Yerel Ollama modelleri
│   │   └── prompts/          # Sistem prompt'ları ve AI kimliği
│   │
│   ├── image/                # Görsel üretim
│   │   ├── manager.py        # İstek yönetimi
│   │   ├── queue.py          # İş kuyruğu
│   │   └── flux.py           # Flux/Forge API
│   │
│   ├── memory/               # Hafıza sistemleri
│   │   ├── store.py          # Uzun vadeli hafıza (ChromaDB)
│   │   ├── conversation.py   # Sohbet geçmişi (SQLite)
│   │   └── rag.py            # RAG doküman deposu
│   │
│   ├── search/               # İnternet araması
│   │   ├── manager.py        # Arama koordinasyonu
│   │   └── providers/        # Bing, Serper, DuckDuckGo
│   │
│   └── services/             # Yardımcı servisler
│       ├── formatting/       # Metin formatlama
│       ├── response_processor.py
│       ├── semantic_classifier.py
│       └── ...
│
├── api/                      # Eski API route'ları (çalışıyor)
├── auth/                     # Eski auth modülleri (çalışıyor)
├── core/                     # Eski core modülleri (çalışıyor)
├── router/                   # Eski chat router (çalışıyor)
├── services/                 # Eski servisler (çalışıyor)
│
├── ui/                       # Frontend
│   ├── chat.html             # Ana sohbet arayüzü
│   ├── admin.html            # Admin paneli
│   ├── login.html            # Giriş sayfası
│   ├── css/                  # Stiller
│   └── js/                   # JavaScript
│
├── data/                     # Runtime verileri (gitignore)
│   ├── app.db                # SQLite veritabanı
│   ├── chroma_db/            # ChromaDB vektör deposu
│   ├── images/               # Üretilen görseller
│   └── uploads/              # Yüklenen dosyalar
│
├── scripts/                  # Yardımcı scriptler
├── tests/                    # Test dosyaları
├── docs/                     # Dokümantasyon
│
├── main.py                   # Ana giriş noktası (backward compat)
├── requirements.txt          # Python bağımlılıkları
├── .env.example              # Ortam değişkenleri şablonu
└── .gitignore                # Git ignore kuralları
```

---

## 🔄 Veri Akışı

```
Kullanıcı Mesajı
       │
       ▼
┌──────────────┐
│   Frontend   │  (ui/chat.html + ui/js/chat.js)
│   (Browser)  │
└──────────────┘
       │ HTTP POST /api/user/chat
       ▼
┌──────────────┐
│  API Layer   │  (api/user_routes.py)
│  (FastAPI)   │
└──────────────┘
       │
       ▼
┌──────────────┐
│   Decider    │  (chat/decider.py)
│  (Yönlendirme)│
└──────────────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  GROQ    │  │ INTERNET │  │  IMAGE   │  │  LOCAL   │
│ (Chat)   │  │ (Search) │  │  (Flux)  │  │ (Ollama) │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
       │
       ▼
┌──────────────┐
│  Memory &    │  (memory/store.py, memory/conversation.py)
│  Context     │
└──────────────┘
       │
       ▼
┌──────────────┐
│   Response   │  (services/response_processor.py)
│  Formatting  │
└──────────────┘
       │
       ▼
   Kullanıcıya Yanıt
```

---

## 🗃️ Veritabanı Şeması

### SQLite (İlişkisel Veriler)

| Tablo | Açıklama |
|-------|----------|
| `users` | Kullanıcı hesapları |
| `sessions` | Aktif oturumlar |
| `conversations` | Sohbet başlıkları |
| `messages` | Sohbet mesajları |
| `invites` | Davet kodları |
| `feedback` | Kullanıcı geri bildirimleri |
| `usage_counters` | Günlük kullanım sayaçları |

### ChromaDB (Vektör Veritabanı)

| Koleksiyon | Açıklama |
|------------|----------|
| `memories` | Kullanıcı uzun vadeli hafızaları |
| `rag_docs` | Yüklenen dokümanlar (PDF, TXT) |

---

## 🔑 Önemli Modüller

### `app/chat/processor.py`
Ana sohbet işlemcisi. Kullanıcı mesajını alır, analiz eder, uygun servise yönlendirir.

### `app/chat/decider.py`
Mesaj niyetini belirler: CHAT, IMAGE, INTERNET, LOCAL_CHAT

### `app/memory/store.py`
ChromaDB ile semantik hafıza arama ve kayıt.

### `app/auth/dependencies.py`
FastAPI dependency'leri: `get_current_user`, `get_current_admin_user`

---

## 🚀 Çalıştırma

```bash
# Geliştirme
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📝 Yeni Geliştirici İçin Checklist

1. ✅ `.env.example` dosyasını `.env` olarak kopyala
2. ✅ Groq API anahtarını al ve `.env`'e ekle
3. ✅ `pip install -r requirements.txt`
4. ✅ `uvicorn main:app --reload`
5. ✅ http://localhost:8000 adresine git
6. ✅ Varsayılan giriş: `admin` / `admin`

---

## 🔧 Geliştirme Kuralları

1. **Türkçe Yorumlar**: Kod yorumları Türkçe olmalı
2. **Type Hints**: Tüm fonksiyonlarda tip belirtilmeli
3. **Docstrings**: Her modül, sınıf ve fonksiyon için docstring
4. **Logging**: `print()` yerine `logger.info/error()` kullan
5. **Exception Handling**: `MamiException` sınıflarını kullan

---

## 📞 Destek

Sorularınız için proje yöneticisiyle iletişime geçin.

