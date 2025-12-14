# Image Queue System - Proje Durumu ve Analiz

> **Oluşturulma Tarihi:** 2024-12-13
> **Son Güncelleme:** 2024-12-13

---

## 1. MEVCUT PROJE YAPISI

### 1.1 Dosya Ağacı (Özet)

```
d:\ai\mami_ai_v4\
├── app/                          # Backend (FastAPI)
│   ├── api/                      # API endpoints
│   ├── auth/                     # Authentication
│   ├── chat/                     # Chat processing
│   │   ├── processor.py          # ⭐ Ana mesaj işleme
│   │   └── smart_router.py       # Mesaj yönlendirme
│   ├── image/                    # 🎨 GÖRSEL ÜRETİM SİSTEMİ
│   │   ├── image_manager.py      # İş yönetimi
│   │   ├── job_queue.py          # Kuyruk sistemi
│   │   ├── flux_stub.py          # Forge API iletişimi
│   │   ├── routing.py            # NSFW/model seçimi
│   │   ├── pending_state.py      # Bekleyen işler
│   │   ├── gpu_state.py          # GPU state yönetimi
│   │   ├── circuit_breaker.py    # Hata yönetimi
│   │   └── safe_callback.py      # Callback güvenliği
│   ├── memory/                   # Conversation memory
│   │   └── conversation.py       # ⭐ Mesaj DB işlemleri
│   ├── websocket_sender.py       # ⭐ WebSocket gönderimi
│   └── main.py                   # FastAPI app
│
├── ui-new/                       # Frontend (React + Vite)
│   └── src/
│       ├── components/
│       │   └── chat/
│       │       ├── MessageBubble.tsx     # ⭐ Mesaj render
│       │       ├── ImageProgressCard.tsx # ⭐ Progress UI
│       │       └── ImageCompletedCard.tsx
│       ├── hooks/
│       │   ├── useWebSocket.ts           # ⭐ WebSocket bağlantısı
│       │   └── useImageProgress.ts       # ⭐ Progress cache
│       ├── stores/
│       │   ├── chatStore.ts              # ⭐ Chat state (Zustand)
│       │   └── imageJobsStore.ts         # Job tracking
│       ├── api/
│       │   └── client.ts                 # API calls
│       └── types/
│           └── index.ts                  # TypeScript types
│
└── docs/                         # Dokümantasyon
```

### 1.2 Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| **Frontend** | React 18 + TypeScript + Vite |
| **State Management** | Zustand |
| **Styling** | CSS Variables + Framer Motion |
| **Backend** | Python FastAPI |
| **Database** | SQLite (SQLAlchemy ORM) |
| **Image Generation** | Stable Diffusion Forge API |
| **Real-time** | WebSocket (native) |

---

## 2. MEVCUT WEBSOCKET YAPISI

### 2.1 Backend WebSocket (`websocket_sender.py`)

```python
# Bağlantı yönetimi
connected: Dict[Any, str] = {}  # {ws: username}

# Progress gönderme
async def send_image_progress(
    username: str,
    conversation_id: Optional[str],
    job_id: str,
    status: ImageJobStatus,  # queued/processing/complete/error
    progress: int,
    queue_position: int,
    message_id: Optional[int] = None,  # DB message ID
    ...
)
```

### 2.2 Frontend WebSocket (`useWebSocket.ts`)

```typescript
// Singleton connection
let globalWs: WebSocket | null = null

// Event handling
handleMessage = (event: MessageEvent) => {
    if (message.type === 'image_progress') {
        // 1. Progress cache güncelle
        updateProgressFromWebSocket(data)
        
        // 2. Mesaj bul ve job_id ata
        // ⚠️ SORUN: Birden fazla pending mesaj varsa YANLIŞ eşleşme
    }
}
```

### 2.3 Forge Response Formatı (Örnek)

```json
{
    "type": "image_progress",
    "job_id": "3256592a-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "conversation_id": "9f2a46be-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "status": "processing",
    "progress": 45,
    "queue_position": 1,
    "message_id": 113,
    "prompt": "a beautiful sunset over mountains...",
    "estimated_seconds": 25
}
```

---

## 3. MEVCUT CHAT SİSTEMİ

### 3.1 Mesaj Saklama

| Katman | Nerede | Kalıcı mı? |
|--------|--------|------------|
| Frontend State | `chatStore.messages[]` (Zustand) | ❌ Sayfa yenilenir kaybolur |
| Progress Cache | `progressCache` (Map) | ❌ Sayfa yenilenir kaybolur |
| Backend DB | `messages` table (SQLite) | ✅ Kalıcı |

### 3.2 Mesaj Render (`MessageBubble.tsx`)

```typescript
// Mesaj tipi tespiti
const isPending = content.includes('[IMAGE_PENDING]')
const isCompleted = content.includes('IMAGE_PATH:')

// Render
if (isPending && currentJob) {
    return <ImageProgressCard job={currentJob} />
}
if (isCompleted && imageUrl) {
    return <ImageCompletedCard imageUrl={imageUrl} />
}
return <StandardMessage />
```

### 3.3 Sayfa Yenilendiğinde

```typescript
// ChatArea.tsx veya useEffect
const messages = await chatApi.getMessages(conversationId)
// ⚠️ SORUN: extra_metadata.job_id henüz yazılmamış olabilir
// ⚠️ SORUN: progressCache boş, WebSocket henüz bağlanmadı
```

---

## 4. MEVCUT RESİM ÜRETİM AKIŞI

### 4.1 Akış Diyagramı

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. KULLANICI: "kedi çiz"                                           │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. processor.py: build_image_prompt() → "fluffy cat, detailed..."  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. processor.py: append_message() → message_id: 113                │
│    İçerik: "[IMAGE_PENDING] Görsel isteğiniz kuyruğa alındı..."    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. image_manager.py: request_image_generation(message_id=113)      │
│    → Job oluştur (job_id: "3256592a...")                           │
│    → update_message(113, extra_metadata={job_id: "3256592a..."})   │
│    → Kuyruğa ekle                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. job_queue.py: _worker_loop()                                    │
│    → GPU'ya geç (switch_to_flux)                                   │
│    → flux_stub.py: generate_image_via_forge()                      │
│    → Progress loop: her 1 saniyede WebSocket gönder                │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. TAMAMLANDI:                                                     │
│    → on_complete() callback                                        │
│    → update_message(113, "[IMAGE] Resminiz hazır\nIMAGE_PATH:...")  │
│    → WebSocket: status="complete", image_url="..."                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Kritik Dosyalar ve Fonksiyonlar

| Dosya | Fonksiyon | Görev |
|-------|-----------|-------|
| `processor.py` | `process_chat_message()` | Ana orchestrator |
| `processor.py` | `build_image_prompt()` | Prompt hazırlama |
| `image_manager.py` | `request_image_generation()` | Job oluşturma |
| `job_queue.py` | `ImageJobQueue._worker_loop()` | Kuyruk işleme |
| `flux_stub.py` | `generate_image_via_forge()` | Forge API çağrısı |
| `conversation.py` | `update_message()` | DB güncelleme |
| `websocket_sender.py` | `send_image_progress()` | WS broadcast |

---

## 5. YAŞANAN SORUNLAR (CHECKLIST)

| Sorun | Durum | Açıklama |
|-------|-------|----------|
| Progress güncellemeleri yanlış mesaja gidiyor | ✅ EVET | Frontend job_id olmadan ilk pending mesajı alıyor |
| Sayfa yenilenince progress bilgileri kayboluyor | ✅ EVET | progressCache in-memory, kalıcı değil |
| Farklı chat'lerde mesajlar karışıyor | ⚠️ Kısmen | conversation_id kontrolü var ama race condition |
| Sıra numaraları doğru gösterilmiyor | ✅ EVET | queue_pos statik kalıyor, güncellenmiyor |
| Progress hiç güncellenmiyor | ✅ EVET | job_id eşleşmediğinde useImageProgress null dönüyor |
| **ID Tip Uyumsuzluğu** | ✅ EVET | Backend: integer ID, Frontend: string ID |
| **Race Condition** | ✅ EVET | Mesaj yüklenir → job_id henüz yok → WS gelir → eşleşemez |

---

## 6. HEDEF ÖZELLİKLER

### İstenen Davranış

1. **Kullanıcı resim istediğinde:**
   - Anında chat'te mesaj görünmeli
   - Sıra pozisyonu gösterilmeli: "#3 sırada"
   - Prompt gösterilmeli (kısaltılmış)
   - Tahmini süre gösterilmeli

2. **Üretim başladığında:**
   - Status "işleniyor" olmalı
   - Progress bar %0'dan %100'e animasyonlu ilerlemeli
   - Kalan süre tahmini güncellenmeli
   - Shimmer/loading placeholder görseli olmalı

3. **Sayfa yenilendiğinde:**
   - Pending işler korunmalı
   - Progress durumu doğru gösterilmeli
   - Queue pozisyonu güncel olmalı

4. **Tamamlandığında:**
   - Görsel gösterilmeli
   - Prompt bilgisi saklanmalı
   - Lightbox açılabilmeli
   - Regenerate butonu olmalı

5. **Hata durumunda:**
   - Hata mesajı gösterilmeli
   - Retry butonu olmalı

---

## 7. KÖK NEDEN ANALİZİ

### Temel Sorun: ID Eşleştirmesi

```
Backend DB:   message.id = 113 (INTEGER)
Frontend:     message.id = "msg-conv-123-0" (STRING - generated)
WebSocket:    message_id = 113 (INTEGER)

→ Frontend, WebSocket'ten gelen message_id=113'ü eşleştiremez!
```

### Çözüm Gerekliliği

1. **Tek ID Sistemi:** UUID kullan (hem backend hem frontend)
2. **Sync Response:** Job başlatıldığında job_id chat response'ta dön
3. **DB as Truth:** Progress için de DB'yi kullan, cache'i kaldır

---

## 8. ÖNERİLEN MİMARİ

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                  │
├─────────────────────────────────────────────────────────────────────┤
│  POST /chat → Response: {message_id: UUID, job_id: UUID}            │
│                                                                     │
│  messages[].id = UUID (same as backend)                             │
│  messages[].extra_metadata.job_id = UUID                            │
│                                                                     │
│  WebSocket: job:progress → find by job_id → update UI               │
└─────────────────────────────────────────────────────────────────────┘
                              ↕ UUID
┌─────────────────────────────────────────────────────────────────────┐
│                           BACKEND                                   │
├─────────────────────────────────────────────────────────────────────┤
│  messages.id = UUID (primary key, not auto-increment)               │
│  image_jobs.id = UUID                                               │
│  image_jobs.message_id = UUID (FK to messages)                      │
│  image_jobs.status, progress, queue_position (DB'de sakla)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. SONRAKI ADIMLAR

1. **Öncelik 1:** ID sistemini UUID'ye çevir
2. **Öncelik 2:** Chat response'a job_id ekle
3. **Öncelik 3:** Frontend'de DB ID kullan
4. **Öncelik 4:** Progress state'i DB'ye taşı
5. **Öncelik 5:** Queue pozisyonunu dinamik güncelle

**Tahmini Süre:** 2-3 gün (tam refactoring)
