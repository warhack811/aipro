# Kullanılmayan Fonksiyonlar Detaylı Analiz Raporu

**Tarih:** 15 Aralık 2025  
**Analiz Edilen Modüller:** app/core/logger.py, app/services/user_preferences.py

---

## 📊 EXECUTİVE SUMMARY

| Kategori | Kullanılmayan | Kullanılan | Toplam |
|----------|---------------|------------|--------|
| Logger Fonksiyonları | 4 | 1 | 5 |
| User Preferences | 5 | 2 | 7 |
| **TOPLAM** | **9** | **3** | **12** |

---

## 1️⃣ LOGGER FONKSİYONLARI ANALİZİ

### ✅ KULLANILAN FONKSİYON

#### `get_logger()` - 39 YERDE KULLANI LIYOR ✅

**Kullanım Yerleri:**
- `app/main.py` - Ana uygulama
- `app/api/*` - Tüm API route'ları (admin, auth, public, user)
- `app/chat/processor.py` - Chat işleme
- `app/core/*` - Core servisler (feedback, maintenance)
- `app/image/*` - Görsel işleme servisleri
- `app/search/*` - Arama servisleri
- `app/services/*` - İş mantığı servisleri

**Fonksiyon İmzası:**
```python
def get_logger(
    name: str = "mami",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger
```

**Özellikler:**
- ✅ Rotating file handler (5MB max, 3 backup)
- ✅ Console handler
- ✅ Tutarlı format
- ✅ Module bazlı logger isimlendirme

---

### ❌ KULLANILMAYAN FONKSİYONLAR

#### 1. `get_debug_logger()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def get_debug_logger(name: str = "mami.debug") -> logging.Logger:
    """Debug seviyesinde logger döndürür."""
    return get_logger(name, level=logging.DEBUG)
```

**Durum:** Sadece `get_logger()` ile wrapper. İç içe logger oluşturma.

**Kullanım Analizi:**
- ❌ Projede hiç çağrılmıyor
- ❌ Test dosyalarında kullanılmıyor
- ❌ Script'lerde kullanılmıyor

**FARK ANALİZİ:**
| Özellik | `get_logger()` | `get_debug_logger()` |
|---------|----------------|----------------------|
| Log Level | INFO (varsayılan) | DEBUG (sabit) |
| Esneklik | Level değiştirilebilir | Level sabit |
| Kullanım | 39 yerde | 0 yerde |

**Alternatif Kullanım:**
```python
# get_debug_logger() yerine:
logger = get_logger(__name__, level=logging.DEBUG)
```

---

#### 2. `configure_root_logger()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def configure_root_logger(level: int = logging.INFO) -> None:
    """Root logger'ı yapılandırır."""
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT
    )
```

**Durum:** Root logger yapılandırması. Tek seferlik çağrılmalı.

**Kullanım Analizi:**
- ❌ `main.py`'de çağrılmıyor
- ❌ Hiçbir startup script'te kullanılmıyor
- ⚠️ Root logger yapılandırılmamış

**FARK ANALİZİ:**
| Özellik | `get_logger()` | `configure_root_logger()` |
|---------|----------------|---------------------------|
| Kapsam | Module logger | Root logger (global) |
| Handler | File + Console | BasicConfig (console only) |
| Çağrı Sayısı | Her modülde | Bir kere (startup) |
| Kullanım | 39 yerde | 0 yerde |

**Potansiyel Kullanım:**
```python
# main.py başında:
configure_root_logger(level=logging.INFO)
```

---

#### 3. `log_request()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user: Optional[str] = None,
    extra: Optional[dict] = None
) -> None:
    """HTTP isteğini loglar."""
    user_str = f" user={user}" if user else ""
    extra_str = f" {extra}" if extra else ""
    logger.info(f"[REQUEST] {method} {path}{user_str}{extra_str}")
```

**Durum:** HTTP request logging utility. Middleware'de kullanılmalı.

**Kullanım Analizi:**
- ❌ FastAPI middleware'de kullanılmıyor
- ❌ Route handler'larda kullanılmıyor
- ⚠️ Request logging yapılmıyor

**FARK ANALİZİ:**
| Özellik | Manuel `logger.info()` | `log_request()` |
|---------|------------------------|-----------------|
| Format | Tutarsız | Standart format |
| User tracking | Manuel ekle | Otomatik |
| Extra data | Manual handling | Yapılandırılmış |
| Kullanım | Yaygın | 0 yerde |

**Önerilen Kullanım:**
```python
# FastAPI middleware:
@app.middleware("http")
async def log_requests(request: Request, call_next):
    log_request(logger, request.method, request.url.path, 
                user=get_current_user())
    response = await call_next(request)
    return response
```

---

#### 4. `log_response()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def log_response(
    logger: logging.Logger,
    status_code: int,
    duration_ms: float,
    extra: Optional[dict] = None
) -> None:
    """HTTP yanıtını loglar."""
    extra_str = f" {extra}" if extra else ""
    logger.info(f"[RESPONSE] status={status_code} duration={duration_ms:.2f}ms{extra_str}")
```

**Durum:** HTTP response logging utility. `log_request()` ile eşli.

**Kullanım Analizi:**
- ❌ FastAPI middleware'de kullanılmıyor
- ❌ Response handler'larda kullanılmıyor
- ⚠️ Response time tracking yapılmıyor

**FARK ANALİZİ:**
| Özellik | Manuel `logger.info()` | `log_response()` |
|---------|------------------------|------------------|
| Format | Tutarsız | Standart format |
| Duration tracking | Manuel hesapla | Parametreli |
| Status code | Manuel ekle | Otomatik |
| Kullanım | Nadir | 0 yerde |

**Önerilen Kullanım:**
```python
# FastAPI middleware:
@app.middleware("http")
async def log_responses(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    log_response(logger, response.status_code, duration)
    return response
```

---

## 2️⃣ USER PREFERENCES FONKSİYONLARI ANALİZİ

### ✅ KULLANILAN FONKSİYONLAR

#### `set_user_preference()` - 3 YERDE KULLANILIYOR ✅

**Kullanım Yerleri:**
1. `app/api/user_routes.py:641` - API endpoint
2. `app/services/user_preferences.py:328` - `set_user_formatting_preference()` içinde
3. `app/services/user_preferences.py:59` - Kendi tanımı

**Fonksiyon İmzası:**
```python
def set_user_preference(
    user_id: int,
    key: str,
    value: str,
    category: str = "system",
    source: str = "explicit",
) -> UserPreference
```

---

#### `get_effective_preferences()` - 6 YERDE KULLANILIYOR ✅

**Kullanım Yerleri:**
1. `app/services/user_context.py:68` - User context builder
2. `app/image/image_manager.py:91` - Style preferences
3. `app/chat/smart_router.py:325` - Feature preferences
4. `app/api/user_routes.py:191` - Persona check
5. `app/api/user_routes.py:629` - API endpoint
6. `app/services/user_preferences.py:282` - `get_user_formatting_preferences()` içinde

**Fonksiyon İmzası:**
```python
def get_effective_preferences(
    user_id: int,
    category: Optional[str] = None,
) -> Dict[str, str]
```

---

### ❌ KULLANILMAYAN FONKSİYONLAR

#### 1. `get_user_preferences()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def get_user_preferences(
    user_id: int,
    category: Optional[str] = None,
    include_inactive: bool = False,
) -> List[UserPreference]
```

**Durum:** List döndürür, `get_effective_preferences()` dict döndürür.

**FARK ANALİZİ:**
| Özellik | `get_user_preferences()` | `get_effective_preferences()` |
|---------|--------------------------|------------------------------|
| Return Type | `List[UserPreference]` | `Dict[str, str]` |
| Inactive kayıtlar | İsteğe bağlı dahil | Sadece aktif |
| Duplicates | Hepsi döner | En yeni kazanır |
| Kullanım | 0 yerde | 6 yerde |

**Ne Zaman Kullanılır:**
- ❌ Şu an: Hiç kullanılmıyor
- ✅ Potansiyel: Admin panelinde tüm kayıtları göstermek için

---

#### 2. `get_user_preference()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def get_user_preference(
    user_id: int,
    key: str,
    category: Optional[str] = None,
    only_active: bool = True,
) -> Optional[UserPreference]
```

**Durum:** Tek bir preference objesi döndürür.

**FARK ANALİZİ:**
| Özellik | `get_user_preference()` | `get_effective_preferences()` |
|---------|-------------------------|------------------------------|
| Return Type | `Optional[UserPreference]` | `Dict[str, str]` |
| Scope | Tek key | Tüm category |
| Return | Object | String value |
| Kullanım | 0 yerde | 6 yerde |

**Ne Zaman Kullanılır:**
- ❌ Şu an: Hiç kullanılmıyor
- ✅ Potansiyel: Tek bir preference'ın metadata'sına erişmek için

---

#### 3. `deactivate_user_preference()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def deactivate_user_preference(
    user_id: int,
    key: str,
    category: Optional[str] = None,
) -> int
```

**Durum:** Soft delete. `set_user_preference()` zaten eski kayıtları pasifleştirir.

**FARK ANALİZİ:**
| Özellik | `deactivate_user_preference()` | `set_user_preference()` |
|---------|--------------------------------|-------------------------|
| İşlem | Sadece pasifleştir | Pasifleştir + Yeni kayıt |
| Return | Etkilenen sayı | Yeni preference |
| Use Case | Silme işlemi | Güncelleme |
| Kullanım | 0 yerde | 3 yerde |

**Ne Zaman Kullanılır:**
- ❌ Şu an: Hiç kullanılmıyor
- ✅ Potansiyel: Kullanıcı bir tercihi silmek istediğinde (ama şu an API'de yok)

---

#### 4. `get_user_formatting_preferences()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def get_user_formatting_preferences(user_id: int) -> Dict[str, Any]:
    """Response formatting tercihlerini döndürür."""
    prefs = get_effective_preferences(user_id, category="formatting")
    # Varsayılan değerlerle birleştir
    return {
        "format_level": "rich",
        "enable_markdown": True,
        # ... 8 adet default
    }
```

**Durum:** `get_effective_preferences()` ile wrapper + defaults.

**FARK ANALİZİ:**
| Özellik | `get_user_formatting_preferences()` | `get_effective_preferences()` |
|---------|-------------------------------------|------------------------------|
| Category | Sadece "formatting" | Herhangi |
| Defaults | Var (8 adet) | Yok |
| Type Casting | Boolean parsing | String only |
| Kullanım | 0 yerde | 6 yerde |

**Ne Zaman Kullanılır:**
- ❌ Şu an: Hiç kullanılmıyor
- ✅ Potansiyel: Response processor'da formatting ayarları için

---

#### 5. `set_bulk_formatting_preferences()` - HİÇ KULLANILMIYOR ❌

**Tanım:**
```python
def set_bulk_formatting_preferences(
    user_id: int,
    preferences: Dict[str, Any],
) -> List[UserPreference]:
    """Birden fazla formatting tercihini toplu ayarlar."""
    results = []
    for key, value in preferences.items():
        pref = set_user_formatting_preference(user_id, key, value)
        results.append(pref)
    return results
```

**Durum:** Toplu güncelleme wrapper. Transaction yok!

**FARK ANALİZİ:**
| Özellik | `set_bulk_formatting_preferences()` | Manuel loop |
|---------|-------------------------------------|-------------|
| Transaction | ❌ Yok | ❌ Yok |
| Rollback | ❌ Kısmi başarı | ❌ Kısmi başarı |
| Performance | Kötü (N query) | Kötü (N query) |
| Kullanım | 0 yerde | - |

**Ne Zaman Kullanılır:**
- ❌ Şu an: Hiç kullanılmıyor
- ⚠️ Dikkat: Transaction yoksa tehlikeli (kısmi güncelleme riski)
- ✅ Potansiyel: Admin panelinde toplu ayar değişikliği

---

## 3️⃣ ÖNERİLER VE KARAR MATRISI

### 🔴 SİLİNMELİ (Yüksek Öncelik)

#### `get_debug_logger()` ❌ SİL
**Neden:**
- ✅ Gereksiz wrapper, `get_logger(name, level=DEBUG)` ile aynı
- ✅ Hiç kullanılmıyor
- ✅ Kod karmaşıklığı artırıyor

**Aksiyon:**
```python
# SİL: get_debug_logger() fonksiyonunu tamamen kaldır
# Eğer debug logger gerekirse:
logger = get_logger(__name__, level=logging.DEBUG)
```

---

#### `set_bulk_formatting_preferences()` ❌ SİL
**Neden:**
- ✅ Transaction yok (tehlikeli)
- ✅ Hiç kullanılmıyor
- ✅ Manuel loop daha güvenli

**Aksiyon:**
```python
# SİL: Fonksiyonu kaldır
# Toplu güncelleme gerekirse transaction ile yeniden yaz
```

---

### 🟡 KARAR VER (Orta Öncelik)

#### `log_request()` ve `log_response()` 🤔 KULLAN VEYA SİL

**Kullanma Senaryosu (ÖNERİLİR):**
```python
# main.py'ye ekle:
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Request log
    log_request(logger, request.method, str(request.url.path),
                user=getattr(request.state, 'user', None))
    
    # Response log
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    log_response(logger, response.status_code, duration)
    
    return response
```

**Silme Senaryosu:**
- Eğer FastAPI'nin kendi logging'i yeterli ise sil

**Karar:** ✅ KULLAN - API monitoring için değerli

---

#### `get_user_formatting_preferences()` 🤔 KULLAN VEYA SİL

**Kullanma Senaryosu:**
```python
# app/services/response_processor.py içinde:
def full_post_process(text: str, user_id: int) -> str:
    prefs = get_user_formatting_preferences(user_id)
    
    if prefs["enable_markdown"]:
        text = enhance_markdown(text)
    
    if prefs["enable_code_enhancement"]:
        text = enhance_code_blocks(text)
    
    return text
```

**Silme Senaryosu:**
- Formatting sistemi kullanılmayacaksa sil

**Karar:** ✅ KULLAN - Response quality için değerli

---

### 🟢 KORU (Düşük Öncelik)

#### `configure_root_logger()` ✅ KORU

**Neden:**
- ⚠️ Şu an kullanılmıyor AMA mantıklı
- ✅ Startup'ta root logger yapılandırması için gerekli
- ✅ 3rd party kütüphanelerin loglarını kontrol eder

**Önerilen Kullanım:**
```python
# main.py başına ekle:
configure_root_logger(level=logging.INFO)
```

**Karar:** ✅ KORU VE KULLAN

---

#### `get_user_preferences()` ✅ KORU

**Neden:**
- ✅ Admin paneli için değerli (tüm kayıt geçmişi)
- ✅ Debug için kullanılabilir
- ✅ `List[UserPreference]` ile metadata erişimi

**Potansiyel Kullanım:**
```python
# Admin panelinde:
def admin_user_prefs(user_id: int):
    all_prefs = get_user_preferences(user_id, include_inactive=True)
    return {
        "active": [p for p in all_prefs if p.is_active],
        "history": [p for p in all_prefs if not p.is_active]
    }
```

**Karar:** ✅ KORU - Admin/debug için yararlı

---

#### `get_user_preference()` ✅ KORU

**Neden:**
- ✅ Single preference object döndürür (metadata ile)
- ✅ Admin/debug için değerli
- ✅ Küçük fonksiyon, zarar yok

**Karar:** ✅ KORU

---

#### `deactivate_user_preference()` 🤔 KORU VEYA SİL

**Neden Koru:**
- ✅ Soft delete için gerekli
- ✅ Gelecekte silme özelliği eklenebilir

**Neden Sil:**
- ❌ Hiç kullanılmıyor
- ❌ API'de silme endpoint'i yok

**Karar:** ✅ KORU - Gelecek için hazır

---

## 4️⃣ AKSIYON PLANI

### 🔴 Hemen Yap (Bu Hafta)

```python
# 1. Gereksiz wrapper'ı sil
# app/core/logger.py'den kaldır:
# - get_debug_logger()

# 2. Tehlikeli fonksiyonu sil
# app/services/user_preferences.py'den kaldır:
# - set_bulk_formatting_preferences()
```

### 🟡 Karar Ver ve Uygula (Bu Ay)

```python
# 3. HTTP logging middleware'i ekle
# main.py'ye ekle:
@app.middleware("http")
async def logging_middleware(request, call_next):
    log_request(logger, request.method, request.url.path)
    start = time.time()
    response = await call_next(request)
    log_response(logger, response.status_code, (time.time() - start) * 1000)
    return response

# 4. Formatting preferences'ı kullan
# app/services/response_processor.py içinde kullan:
def full_post_process(text, user_id):
    prefs = get_user_formatting_preferences(user_id)
    # ... implementation
```

### 🟢 İyileştir (Gelecek)

```python
# 5. Root logger'ı yapılandır
# main.py başına ekle:
from app.core.logger import configure_root_logger
configure_root_logger(level=logging.INFO)

# 6. Admin panelinde preferences history göster
# Admin route'a ekle:
@router.get("/admin/users/{user_id}/preferences")
def get_user_pref_history(user_id: int):
    return get_user_preferences(user_id, include_inactive=True)
```

---

## 5️⃣ SONUÇ VE ÖNERİ

### 📊 Final Karar Tablosu

| Fonksiyon | Karar | Öncelik | Sebep |
|-----------|-------|---------|-------|
| `get_debug_logger()` | ❌ SİL | 🔴 Yüksek | Gereksiz wrapper |
| `configure_root_logger()` | ✅ KORU + KULLAN | 🟡 Orta | Startup için gerekli |
| `log_request()` | ✅ KORU + KULLAN | 🟡 Orta | Middleware'de kullan |
| `log_response()` | ✅ KORU + KULLAN | 🟡 Orta | Middleware'de kullan |
| `get_user_preferences()` | ✅ KORU | 🟢 Düşük | Admin için değerli |
| `get_user_preference()` | ✅ KORU | 🟢 Düşük | Admin için değerli |
| `deactivate_user_preference()` | ✅ KORU | 🟢 Düşük | Gelecek için hazır |
| `get_user_formatting_preferences()` | ✅ KORU + KULLAN | 🟡 Orta | Response quality için |
| `set_bulk_formatting_preferences()` | ❌ SİL | 🔴 Yüksek | Transaction yok, tehlikeli |

### 🎯 Özet Öneriler

1. **Hemen Sil (2 fonksiyon):** `get_debug_logger()`, `set_bulk_formatting_preferences()`
2. **Kullanmaya Başla (4 fonksiyon):** `configure_root_logger()`, `log_request()`, `log_response()`, `get_user_formatting_preferences()`
3. **Koru (3 fonksiyon):** `get_user_preferences()`, `get_user_preference()`, `deactivate_user_preference()`

### 💡 Toplam Kazanç

- **Silinecek:** ~30 satır kod
- **Kullanılacak:** ~150 satır kod aktif hale gelecek
- **Kod Kalitesi:** Daha iyi logging ve user preferences sistemi

---

**Hazırlayan:** Dead Code Analysis System  
**Son Güncelleme:** 15 Aralık 2025