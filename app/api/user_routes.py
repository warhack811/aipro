import json
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, Depends, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, AsyncGenerator, Tuple, cast
from pathlib import Path

# Çekirdek Servisler
from app.core.usage_limiter import limiter
from app.core.models import User, Message, Conversation
from app.core.database import get_session
from app.auth.dependencies import get_current_active_user

# AI/İşleme Servisleri
from app.image.gpu_state import get_state, ModelState
from app.image.job_queue import job_queue
from app.image.pending_state import list_pending_jobs_for_user
from app.chat.processor import process_chat_message
from app.chat.decider import decide_memory_storage_async
from app.core.logger import get_logger
from app.services import user_preferences

# Store/Veri Servisleri
from app.memory.rag import add_document
from app.memory.store import list_memories, add_memory, delete_memory, update_memory
from app.core.feedback_store import add_feedback
from app.memory.conversation import (
    list_conversations as conv_list,
    load_messages as conv_load_messages,
    create_conversation as conv_create,
    append_message as conv_append,
    delete_conversation as conv_delete,
)

logger = get_logger(__name__)
router = APIRouter(tags=["user"])

# PDF Kütüphanesi Kontrolü
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("⚠️ PyPDF2 kütüphanesi yüklü değil, PDF yükleme çalışmayacak.")

UPLOAD_ROOT = Path("data") / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


# --- YARDIMCI FONKSİYONLAR ---

def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """Metni parçalar halinde böler."""
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        if end >= length:
            break
        start = end - overlap
    return [c for c in chunks if c]


def extract_text_from_pdf(file_path: Path) -> str:
    """PDF dosyasından basit metin çıkarma."""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 kütüphanesi yüklü değil.")
    
    # PyPDF2'yi kullanabilmek için import kontrolü
    import PyPDF2 as pdf_module
    
    text_parts = []
    with file_path.open("rb") as f:
        reader = pdf_module.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                text_parts.append(t)
    return "\n".join(text_parts)

def _build_message_metadata(engine: str, action: str, forced: bool, persona: bool, model: str) -> Dict[str, Any]:
    return {
        "engine": engine,
        "action": action,
        "mode": "forced_local" if forced else "normal",
        "persona_applied": persona,
        "model": model,
    }

# --- ŞEMALAR ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    force_local: bool = False
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    stream: bool = False

class ConversationSummaryOut(BaseModel):
    id: str
    title: Optional[str]
    created_at: Any
    updated_at: Any

class MessageOut(BaseModel):
    id: int  # ← Backend message ID (frontend eşleştirmesi için)
    role: str
    text: str
    time: Any
    extra_metadata: Optional[Dict[str, Any]] = None

class MemoryItemOut(BaseModel):
    id: str  # Index yerine ID (str)
    text: str
    created_at: Any
    importance: float
    tags: Optional[List[str]] = None
    category: Optional[str] = "genel"

class MemoryCreateIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    importance: float = 0.5
    tags: Optional[List[str]] = None
    category: Optional[str] = "genel"

class MemoryUpdateIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    importance: Optional[float] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = "genel"

class UserImageOut(BaseModel):
    index: int
    image_url: str
    prompt: str
    created_at: Any
    conversation_id: Optional[str] = None

class FeedbackIn(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=5000)
    feedback: str = Field(..., pattern="^(like|dislike)$")

class UserPreferenceIn(BaseModel):
    key: str = Field(..., min_length=1, max_length=64)
    value: str = Field(..., min_length=1)
    category: Optional[str] = "system"

class UserPreferenceOut(BaseModel):
    key: str
    value: str
    category: str
    source: str
    is_active: bool
    updated_at: Any

class UserPreferencesListOut(BaseModel):
    preferences: Dict[str, str]


# --- ENDPOINTS ---

@router.post("/chat")
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_active_user)
):
    """Kullanici ile sohbet endpoint'i. Stream destekler."""
    if user.id is None:
        raise HTTPException(status_code=400, detail="Geçersiz kullanıcı")
    user_id = user.id
    limiter.check_limits_pre_flight(user_id)
    username = user.username
    logger.info(f"[CHAT] {username}: '{payload.message}' (Stream: {payload.stream})")

    conv_id = payload.conversation_id
    if not conv_id:
        summary = conv_create(username=username, first_message=payload.message)
        conv_id = summary.id

    conv_append(username=username, conv_id=conv_id, role="user", text=payload.message)

    persona_applied = user_preferences.get_effective_preferences(user_id) != {}
    
    # PERSONA BAZLI MODEL ROUTING
    # Eğer kullanıcı model belirtmediyse, aktif persona'ya bakarak otomatik belirle
    requested_model = payload.model
    if not requested_model:
        from app.core.dynamic_config import config_service
        active_persona_name = user.active_persona or "standard"
        active_persona = config_service.get_persona(active_persona_name)
        
        if active_persona and active_persona.get("requires_uncensored", False):
            # Persona sansürsüz model gerektiriyorsa otomatik "bela" set et
            requested_model = "bela"
            logger.info(f"[CHAT] Persona '{active_persona_name}' requires_uncensored=True, model set to 'bela'")

    # --- STREAMING AKTİFSE ---
    if payload.stream:
        
        async def stream_and_save():
            full_reply = ""
            # process_chat_message stream modunda bir generator döndürür
            result_generator = await process_chat_message(
                username=username,
                message=payload.message,
                user=user,
                force_local=payload.force_local,
                conversation_id=conv_id,
                requested_model=requested_model,
                stream=True
            )
            
            # Streaming olmayan (ör. image/internet/local) yanıtlar için güvenli fallback
            if isinstance(result_generator, tuple) and len(result_generator) >= 2:
                # Tuple döndü (non-stream mode): (reply, semantic)
                full_reply = str(result_generator[0] or "")
                if full_reply:
                    # IMAGE_PENDING ve IMAGE_QUEUED marker'larını strip et - bunlar frontend için değil
                    if "[IMAGE_PENDING]" in full_reply:
                        full_reply = full_reply.replace("[IMAGE_PENDING]", "").strip()
                    if "[IMAGE_QUEUED]" in full_reply:
                        # IMAGE_QUEUED geldiğinde hiçbir şey gönderme - pending mesaj zaten DB'de
                        full_reply = ""
                    if full_reply:
                        yield full_reply
            elif hasattr(result_generator, "__aiter__"):
                # AsyncGenerator döndü (stream mode)
                async for chunk in result_generator:
                    if "[IMAGE_PENDING]" in chunk:
                        chunk = chunk.replace("[IMAGE_PENDING]", "").strip()
                    if "[IMAGE_QUEUED]" in chunk:
                        # IMAGE_QUEUED geldiğinde skip - pending mesaj zaten DB'de
                        continue
                    if chunk:
                        full_reply += chunk
                        yield chunk
            else:
                # Beklenmeyen durum - string olarak işle
                full_reply = str(result_generator or "")
                if full_reply:
                    yield full_reply
            
            # Stream bittikten sonra tam cevabı ve metadatayı kaydet
            logger.info(f"[CHAT_STREAM_END] User: {username}, Full reply length: {len(full_reply)}")
            
            # Metadata ve kullanım limiti
            engine = "groq"; action = "GROQ_REPLY"
            if full_reply.startswith("[BELA]") or payload.force_local:
                engine = "local"; action = "LOCAL_CHAT"
            meta = _build_message_metadata(
                engine=engine, action=action, forced=payload.force_local, 
                persona=persona_applied, model=payload.model or "default"
            )
            if engine == "local":
                save_text = full_reply.strip()
                if not save_text.startswith("[BELA]"):
                    save_text = f"[BELA] {save_text}"
            else:
                save_text = f"[GROQ] {full_reply}"
            # MEMORY FIX: Duplicate engellemek için buradan kaldırdık.
            
            conv_append(username=username, conv_id=conv_id, role="bot", text=save_text, extra_metadata=meta)
            limiter.consume_usage(user_id, full_reply)

        return StreamingResponse(
            stream_and_save(),
            media_type="text/plain",
            headers={"X-Conversation-ID": conv_id}
        )

    # --- STREAMING KAPALIYSA (NORMAL YANIT) ---
    else:
        try:
            result = await process_chat_message(
                username=username,
                message=payload.message,
                user=user,
                force_local=payload.force_local,
                conversation_id=conv_id,
                requested_model=requested_model,
                stream=False
            )
            # Normal modda (reply, semantic) tuple döner
            # Type annotation: Union[Tuple[str, Any], AsyncGenerator[str, None]]
            
            # Runtime type guard ile explicit casting
            if hasattr(result, "__aiter__"):
                # AsyncGenerator döndü (stream=False olmasına rağmen)
                chunks = []
                async_gen = cast(AsyncGenerator[str, None], result)
                async for chunk in async_gen:
                    chunks.append(chunk)
                reply = "".join(chunks)
                semantic = None
            else:
                # Tuple döndü
                tuple_result = cast(Tuple[str, Any], result)
                reply, semantic = tuple_result
        except Exception as e:
            logger.error(f'[CHAT] process_chat_message hata: {e}', exc_info=True)
            return {"ok": False, "error": "internal_error", "message": "Bir hata oluştu."}

        try:
            limiter.consume_usage(user_id, reply)
        except Exception as e:
            logger.debug(f"[CHAT] Usage limit consume failed: {e}")

        engine = "unknown"; action = "UNKNOWN"
        if reply.startswith("[BELA]"): engine = "local"; action = "LOCAL_CHAT"
        elif reply.startswith("[NET]"): engine = "internet"; action = "INTERNET"
        elif reply.startswith("[GROQ]"): engine = "groq"; action = "GROQ_REPLY"
        elif reply.startswith("[IMAGE]"): engine = "image"; action = "IMAGE"
        elif reply.startswith("[IMAGE_PENDING]"): engine = "image"; action = "IMAGE_PENDING"
        # MEMORY FIX: Duplicate engellemek için buradan kaldırdık.

        meta = _build_message_metadata(
            engine=engine, action=action, forced=payload.force_local, 
            persona=persona_applied, model=payload.model or "default"
        )
        conv_append(username=username, conv_id=conv_id, role="bot", text=reply, extra_metadata=meta)

        follow_body = reply
        follow_obj = None
        if "FOLLOWUPS_JSON:" in reply:
            try:
                body, json_part = reply.split("FOLLOWUPS_JSON:", 1)
                follow_body = body.strip()
                follow_obj = json.loads(json_part.strip())
            except Exception as e:
                logger.debug(f"[CHAT] Followups JSON parse failed: {e}")

        return {
            "ok": True,
            "reply": follow_body,
            "followups": follow_obj,
            "conversation_id": conv_id,
            "risk_info": {
                "domain": getattr(semantic, "domain", None),
                "risk_level": getattr(semantic, "risk_level", None),
            },
        }

@router.get("/conversations", response_model=List[ConversationSummaryOut])
async def get_conversations(user: User = Depends(get_current_active_user)):
    convs = conv_list(username=user.username)
    return [
        ConversationSummaryOut(
            id=c.id, title=c.title, created_at=c.created_at, updated_at=c.updated_at
        ) for c in convs
    ]

@router.get("/conversations/{conversation_id}", response_model=List[MessageOut])
async def get_conversation_messages(conversation_id: str, user: User = Depends(get_current_active_user)):
    msgs = conv_load_messages(username=user.username, conv_id=conversation_id)
    return [
        MessageOut(
            id=m.id,  # ← Backend message ID
            role=m.role,
            text=m.content if hasattr(m, "content") else m.text,
            time=m.created_at if hasattr(m, "created_at") else m.time,
            extra_metadata=m.extra_metadata if hasattr(m, "extra_metadata") else None,
        ) for m in msgs
    ]

@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str, user: User = Depends(get_current_active_user)):
    conv_delete(username=user.username, conv_id=conversation_id)
    return {"ok": True}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    user: User = Depends(get_current_active_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya adı bulunamadı.")
    
    filename = file.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "txt"):
        raise HTTPException(status_code=400, detail="Sadece PDF ve TXT destekleniyor.")

    user_dir = UPLOAD_ROOT / user.username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = filename.replace("/", "_").replace("\\", "_")
    dest_path = user_dir / safe_name
    
    content = await file.read()
    with dest_path.open("wb") as out:
        out.write(content)

    text = ""
    if ext == "pdf":
        try:
            text = extract_text_from_pdf(dest_path)
        except Exception:
            raise HTTPException(status_code=400, detail="PDF okunamadı.")
    else:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = content.decode("latin-1", errors="ignore")

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Metin çıkarılamadı.")

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Metin çok kısa.")

    for idx, chunk in enumerate(chunks):
        text_with_filename = f"[{filename}] {chunk}"
        add_document(
            text=text_with_filename,
            scope="user",
            owner=user.username,
            metadata={"source": "upload", "filename": filename, "chunk_index": idx, "conversation_id": conversation_id},
        )

    return {"ok": True, "filename": filename, "chunks": len(chunks)}

@router.get("/image/status")
async def check_image_status(user: User = Depends(get_current_active_user)):
    status = job_queue.get_queue_status()
    state_val = get_state()
    status["gpu_mode"] = state_val.value if hasattr(state_val, "value") else str(state_val)
    status["pending_jobs"] = list_pending_jobs_for_user(user.username)
    return status


@router.get("/image/job/{job_id}/status")
async def get_job_status_endpoint(job_id: str, user: User = Depends(get_current_active_user)):
    """
    Belirli bir job'un durumunu döndürür.
    Sayfa yenilendiğinde pending job'ların durumunu öğrenmek için kullanılır.
    """
    from app.image.pending_state import get_job_status
    
    job = get_job_status(job_id)
    if not job:
        # Job tamamlanmış veya hiç olmamış olabilir
        return {
            "job_id": job_id,
            "status": "unknown",
            "progress": 0,
            "queue_position": 0,
            "message": "Job bulunamadı - tamamlanmış veya geçersiz olabilir"
        }
    
    # Sadece bu kullanıcıya ait job'ları göster
    if job.get("username") != user.username:
        return {
            "job_id": job_id,
            "status": "unknown",
            "progress": 0,
            "queue_position": 0,
            "message": "Erişim izni yok"
        }
    
    return {
        "job_id": job_id,
        "status": "processing" if job.get("progress", 0) > 0 else "queued",
        "progress": job.get("progress", 0),
        "queue_position": job.get("queue_pos", 1),
        "conversation_id": job.get("conversation_id"),
    }


@router.post("/image/job/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str, user: User = Depends(get_current_active_user)):
    """
    Kuyruktaki bir görsel isteğini iptal eder.
    Sadece kuyrukta bekleyen işler iptal edilebilir.
    """
    success = await job_queue.cancel_job(job_id, user.username)
    
    if success:
        # Mesajı da güncelle
        from app.memory.conversation import update_message
        from app.image.pending_state import get_job_status
        
        job = get_job_status(job_id)
        if job:
            # Burada message_id yok, pending_state'te tutmuyoruz
            # WebSocket zaten cancelled durumunu gönderdi
            pass
        
        return {"success": True, "message": "Job iptal edildi"}
    
    return {"success": False, "message": "Job bulunamadı veya zaten işleniyor"}

# --- HAFIZA (MEMORY) ENDPOINTS ---

@router.get("/memories", response_model=List[MemoryItemOut])
async def list_user_memories(user: User = Depends(get_current_active_user)):
    items = await list_memories(user.username)
    result = []
    for it in items:
        safe_id = it.id if it.id else "unknown"
        result.append(MemoryItemOut(
            id=safe_id,
            text=it.text,
            created_at=it.created_at,
            importance=it.importance,
            tags=it.tags,
            category=it.topic or "genel",
        ))
    return result

@router.post("/memories", response_model=MemoryItemOut)
async def create_user_memory(body: MemoryCreateIn, user: User = Depends(get_current_active_user)):
    item = await add_memory(
        username=user.username,
        text=body.text,
        importance=body.importance,
        tags=body.tags,
    )
    safe_id = item.id if item.id else "new"
    return MemoryItemOut(
        id=safe_id,
        text=item.text,
        created_at=item.created_at,
        importance=item.importance,
        tags=item.tags,
        category=item.topic or "genel"
    )

@router.delete("/memories/all-delete")
async def delete_all_user_memories(user: User = Depends(get_current_active_user)):
    items = await list_memories(user.username)
    deleted = 0
    for item in items:
        mem_id = getattr(item, "id", None)
        if not mem_id:
            continue
        ok = await delete_memory(user.username, mem_id)
        if ok:
            deleted += 1
    return {"ok": True, "deleted": deleted}

@router.put("/memories/{memory_id}", response_model=MemoryItemOut)
async def update_user_memory(body: MemoryUpdateIn, memory_id: str, user: User = Depends(get_current_active_user)):
    item = await update_memory(
        username=user.username,
        memory_id=memory_id,
        text=body.text,
        importance=body.importance,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Memory not found")
    safe_id = item.id if item.id else memory_id
    return MemoryItemOut(
        id=safe_id,
        text=item.text,
        created_at=item.created_at,
        importance=item.importance,
        tags=item.tags,
        category=item.topic or "genel"
    )

@router.delete("/memories/{memory_id}")
async def delete_user_memory_endpoint(memory_id: str, user: User = Depends(get_current_active_user)):
    ok = await delete_memory(user.username, memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Silinemedi.")
    return {"ok": True}

# --- DİĞER ---

@router.post("/feedback")
async def submit_feedback(body: FeedbackIn, user: User = Depends(get_current_active_user)):
    add_feedback(
        username=user.username,
        conversation_id=body.conversation_id or "",
        message=body.message,
        feedback=body.feedback,
    )
    return {"ok": True}

@router.get("/images", response_model=List[UserImageOut])
async def list_user_images(limit: int = 50, user: User = Depends(get_current_active_user)):
    from sqlmodel import select, col
    with get_session() as session:
        stmt = (
            select(Message)
            .join(Conversation)
            .where(Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id)
            .where(Message.role == "bot")
            .order_by(col(Message.created_at).desc())
            .limit(limit * 3)
        )
        messages = session.exec(stmt).all()
        result = []
        for idx, msg in enumerate(messages):
            if "IMAGE_PATH:" in msg.content:
                image_url = msg.content.split("IMAGE_PATH:")[1].strip().split()[0]
                meta = msg.extra_metadata or {}
                result.append(UserImageOut(
                    index=idx,
                    image_url=image_url,
                    prompt=meta.get("prompt", "") or "Görsel",
                    created_at=msg.created_at,
                    conversation_id=msg.conversation_id
                ))
            if len(result) >= limit: break
        return result

@router.get("/preferences", response_model=UserPreferencesListOut)
async def get_my_preferences(category: Optional[str] = None, user: User = Depends(get_current_active_user)):
    # user.id None kontrolü - aktif kullanıcı için olmamalı ama tip güvenliği için
    if user.id is None:
        raise HTTPException(status_code=400, detail="Geçersiz kullanıcı ID")
    prefs = user_preferences.get_effective_preferences(user_id=user.id, category=category)
    return {"preferences": prefs}

@router.post("/preferences", response_model=UserPreferenceOut)
async def set_my_preference(body: UserPreferenceIn, user: User = Depends(get_current_active_user)):
    # user.id None kontrolü - aktif kullanıcı için olmamalı ama tip güvenliği için
    if user.id is None:
        raise HTTPException(status_code=400, detail="Geçersiz kullanıcı ID")
    
    # category None ise varsayılan değer ata
    category = body.category if body.category else "system"
    
    pref = user_preferences.set_user_preference(
        user_id=user.id, key=body.key, value=body.value, category=category
    )
    return UserPreferenceOut(
        key=pref.key, value=pref.value, category=pref.category,
        source=pref.source, is_active=pref.is_active, updated_at=pref.updated_at,
    )


# =============================================================================
# PERSONA / MOD SİSTEMİ API
# =============================================================================

class PersonaOut(BaseModel):
    """Persona çıktı modeli."""
    name: str
    display_name: str
    description: Optional[str] = None
    requires_uncensored: bool = False
    is_active: bool = True
    initial_message: Optional[str] = None


class PersonaListOut(BaseModel):
    """Persona listesi çıktı modeli."""
    personas: List[PersonaOut]
    active_persona: str


class PersonaSelectIn(BaseModel):
    """Persona seçim giriş modeli."""
    persona: str = Field(..., description="Seçilecek persona adı (ör: standard, lover, roleplay)")


class PersonaSelectOut(BaseModel):
    """Persona seçim çıktı modeli."""
    success: bool
    active_persona: str
    message: str


@router.get("/personas", response_model=PersonaListOut)
async def list_personas(user: User = Depends(get_current_active_user)):
    """
    Kullanılabilir persona/mod listesini döndürür.
    
    Returns:
        PersonaListOut: Persona listesi ve aktif persona
    """
    from app.core.dynamic_config import config_service
    from app.auth.permissions import user_can_use_local
    
    all_personas = config_service.get_all_personas()
    can_use_local = user_can_use_local(user)
    
    result = []
    for p in all_personas:
        # requires_uncensored persona'ları sadece local izni olanlar görebilir
        if p.get("requires_uncensored") and not can_use_local:
            continue
        
        if not p.get("is_active", True):
            continue
            
        result.append(PersonaOut(
            name=p.get("name", ""),
            display_name=p.get("display_name", p.get("name", "")),
            description=p.get("description"),
            requires_uncensored=p.get("requires_uncensored", False),
            is_active=p.get("is_active", True),
            initial_message=p.get("initial_message"),
        ))
    
    return PersonaListOut(
        personas=result,
        active_persona=user.active_persona or "standard"
    )


@router.get("/personas/active")
async def get_active_persona(user: User = Depends(get_current_active_user)):
    """
    Kullanıcının aktif persona/modunu döndürür.
    
    Returns:
        dict: Aktif persona bilgisi
    """
    from app.core.dynamic_config import config_service
    
    active_name = user.active_persona or "standard"
    persona = config_service.get_persona(active_name)
    
    if persona:
        return {
            "active_persona": active_name,
            "display_name": persona.get("display_name", active_name),
            "requires_uncensored": persona.get("requires_uncensored", False),
            "initial_message": persona.get("initial_message"),
        }
    
    return {
        "active_persona": "standard",
        "display_name": "Standart",
        "requires_uncensored": False,
        "initial_message": None,
    }


@router.post("/personas/select", response_model=PersonaSelectOut)
async def select_persona(body: PersonaSelectIn, user: User = Depends(get_current_active_user)):
    """
    Kullanıcının aktif persona/modunu değiştirir.
    
    İş kuralları:
        - Persona bulunamazsa 404
        - requires_uncensored=True ise user_can_use_local kontrolü → 403
        - Başarılıysa DB'de users.active_persona güncellenir
    
    Args:
        body: Seçilecek persona adı
    
    Returns:
        PersonaSelectOut: Seçim sonucu
    """
    from app.core.dynamic_config import config_service
    from app.auth.permissions import user_can_use_local
    from sqlmodel import select
    
    persona_name = body.persona.lower().strip()
    
    # 1. Persona'nın var olup olmadığını kontrol et
    persona = config_service.get_persona(persona_name)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona bulunamadı: {persona_name}"
        )
    
    # 2. Aktif değilse hata
    if not persona.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu persona aktif değil: {persona_name}"
        )
    
    # 3. requires_uncensored kontrolü
    if persona.get("requires_uncensored", False):
        if not user_can_use_local(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu modu kullanmak için yerel model izniniz gerekiyor."
            )
    
    # 4. DB'de güncelle
    with get_session() as session:
        db_user = session.get(User, user.id)
        if db_user:
            db_user.active_persona = persona_name
            session.add(db_user)
            session.commit()
            logger.info(f"[PERSONA] User {user.username} persona değiştirdi: {persona_name}")
    
    return PersonaSelectOut(
        success=True,
        active_persona=persona_name,
        message=f"Mod değiştirildi: {persona.get('display_name', persona_name)}"
    )
