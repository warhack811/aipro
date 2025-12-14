"""
Mami AI - Ana Sohbet İşlemcisi
==============================

Bu modül, kullanıcı mesajlarını işleyen ana akış kontrolcüsüdür.

İşlem Akışı:
    1. Semantic analiz
    2. Decider ile yönlendirme kararı
    3. Uygun servise yönlendirme (Groq, Ollama, Internet, Image)
    4. Hafıza güncelleme
    5. Özet tetikleme

Desteklenen Aksiyonlar:
    - GROQ_REPLY: Ana sohbet (RAG + Memory)
    - IMAGE: Görsel üretim
    - INTERNET: Web araması
    - LOCAL_CHAT: Yerel model (Ollama/Bela)

Kullanım:
    from app.chat.processor import process_chat_message
    
    reply, semantic = await process_chat_message(
        username="john",
        message="Merhaba, nasılsın?",
        user=user_obj,
        conversation_id="conv-123"
    )
"""

from __future__ import annotations

import asyncio
import re
import logging
from html import escape as html_escape
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, Union, AsyncGenerator, List

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# CONTEXT AYARLARI
# =============================================================================

GROQ_HISTORY_LIMIT = 24
"""Groq için maksimum history mesajı."""

CONTEXT_CHAR_LIMIT = 8000
"""Maksimum context karakter limiti."""

HISTORY_TOKEN_BUDGET_GROQ = 3000
"""Groq için token budget."""

HISTORY_TOKEN_BUDGET_LOCAL = 1500
"""Local model için token budget."""

CONTEXT_TRUNCATED_NOTICE = (
    "### BAĞLAM KISALTILDI\n"
    "Bağlam çok uzun olduğu için sadece son kısımlar korunuyor."
)


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    from app.config import get_settings
    from app.core.logger import get_logger
    from app.core.feature_flags import feature_enabled
    from app.core.exceptions import FeatureDisabledError
    from app.core.models import User
    from app.chat.decider import run_decider_async, decide_memory_storage_async
    from app.chat.answerer import generate_answer, generate_answer_stream
    from app.chat.search import handle_internet_action
    from app.chat.smart_router import route_message, RoutingTarget, ToolIntent
    from app.services.semantic_classifier import analyze_message_semantics
    from app.services.user_context import build_user_context
    from app.services.model_router import choose_model_for_request
    from app.services.summary_service import should_update_summary, generate_and_save_summary
    from app.services.query_enhancer import enhance_query_for_search
    from app.memory.store import search_memories, add_memory, delete_memory
    from app.memory.conversation import load_messages, append_message
    from app.memory.rag import search_documents
    from app.ai.prompts.identity import get_ai_identity
    from app.ai.ollama.gemma_handler import run_local_chat, run_local_chat_stream
    from app.image.image_manager import request_image_generation
    from app.image.job_queue import job_queue
    
    return (
        get_settings, get_logger, feature_enabled, FeatureDisabledError, User,
        run_decider_async, decide_memory_storage_async, generate_answer, generate_answer_stream,
        handle_internet_action, route_message, RoutingTarget, ToolIntent, analyze_message_semantics,
        build_user_context, choose_model_for_request, should_update_summary, generate_and_save_summary,
        enhance_query_for_search, search_memories, add_memory, delete_memory,
        load_messages, append_message, search_documents, run_local_chat, run_local_chat_stream,
        get_ai_identity, request_image_generation, job_queue
    )


def _get_conversation_summary():
    """Conversation summary import."""
    try:
        from app.memory.conversation import get_conversation_summary_text
    except ImportError:
        from app.memory.conversation import get_conversation_summary_text
    return get_conversation_summary_text


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def _norm_mem_text(s: str) -> str:
    """Hafıza metnini normalize eder (duplicate kontrolü için)."""
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("'", "'").replace(""", '"').replace(""", '"')
    s = s.replace("kullanıcı adı", "isim")
    s = s.replace("kullanıcı ismi", "isim")
    s = s.replace("adım", "isim")
    return s


def _mem_key(s: str) -> str:
    """Hafıza metnini upsert anahtarı için normalize eder."""
    if not s:
        return ""
    return _norm_mem_text(s)


def _estimate_tokens(text: str) -> int:
    """Token tahmini (4 char ≈ 1 token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def build_memory_hint(memory_blocks: Dict[str, Any]) -> str:
    """Memory bloklarından prompt hint'i oluşturur."""
    hints = []
    if memory_blocks.get("summary"):
        hints.append(f"Önceki konuşma özeti: {memory_blocks['summary']}")
    if memory_blocks.get("personal"):
        hints.append(f"Kişisel hafıza: {'; '.join(memory_blocks['personal'])}")
    if memory_blocks.get("recent"):
        hints.append(f"Son mesajlar: {memory_blocks['recent']}")
    return "\n".join(filter(None, hints)).strip()


def build_history_budget(
    username: str,
    conversation_id: Optional[str],
    *,
    token_budget: int,
) -> List[Dict[str, str]]:
    """
    Token budget'a göre sohbet geçmişi oluşturur.
    
    Importance-based selection kullanır: En önemli mesajları seçer.
    """
    if not conversation_id:
        return []

    _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, load_messages, _, _, _, _, _, _, _ = _get_imports()
    from app.services.context_truncation_manager import context_manager
    
    messages = load_messages(username, conversation_id)
    if not messages:
        return []

    # Mesajları dict formatına çevir
    cooked: List[Dict[str, str]] = []
    for msg in messages:
        text = getattr(msg, "content", getattr(msg, "text", ""))
        if not text:
            continue
        role = msg.role
        role = "assistant" if role == "bot" else role
        if role not in ("user", "assistant"):
            continue
        cooked.append({"role": role, "content": text})

    if not cooked:
        return []

    # Importance-based truncation
    selected, was_truncated = context_manager.truncate_messages_by_importance(
        cooked,
        token_budget,
        preserve_system=False
    )
    
    if was_truncated:
        logger.info(f"[HISTORY] {len(cooked)} mesaj → {len(selected)} mesaj (importance-based)")
    
    return selected


def normalize_groq_history(raw_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """History'yi Groq formatına normalize eder."""
    normalized: List[Dict[str, str]] = []
    for entry in raw_history:
        role = entry.get("role")
        content = entry.get("content")
        if not content:
            continue
        mapped_role = "assistant" if role == "bot" else role
        if mapped_role not in {"user", "assistant"}:
            continue
        normalized.append({"role": mapped_role, "content": content})
    return normalized


def _format_context_block(title: str, lines: List[str]) -> str:
    """Context bloğu formatlar."""
    return f"### {title}\n" + "\n".join(lines).strip()


def _truncate_context_text(content: str) -> str:
    """Context metnini akıllıca truncate eder."""
    from app.services.context_truncation_manager import context_manager
    
    if len(content) <= CONTEXT_CHAR_LIMIT:
        return content
    
    # Akıllı truncation (message boundary'lerde, critical info korunur)
    return context_manager.truncate_text_smart(
        content,
        char_limit=CONTEXT_CHAR_LIMIT,
        add_notice=True
    )


async def build_enhanced_context(
    username: str,
    message: str,
    conversation_id: Optional[str],
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Zenginleştirilmiş context oluşturur.
    
    İçerik:
    1. Sohbet özeti
    2. Kullanıcı profili (önemli hafızalar)
    3. İlgili hafızalar
    4. RAG dokümanları
    """
    (
        _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _,
        enhance_query_for_search, search_memories, _, _,
        _, _, search_documents, _, _, _, _, _
    ) = _get_imports()
    
    get_conversation_summary_text = _get_conversation_summary()
    
    sections: List[str] = []
    
    # 1. Sohbet özeti
    if conversation_id:
        try:
            summary = get_conversation_summary_text(conversation_id)
            if summary:
                summary_block = (
                    "📋 ÖNCEKİ SOHBET ÖZETİ:\n"
                    f"{summary}"
                )
                sections.append(summary_block)
        except Exception as exc:
            logger.error(f"[CONTEXT] Summary okunamadı: {exc}")

    # 2. Multi-query memory search
    try:
        search_queries = await enhance_query_for_search(message, max_queries=3)
    except Exception as e:
        logger.debug(f"[CONTEXT] Query enhancement failed, using original: {e}")
        search_queries = [message]
    
    all_memories = []
    seen_memory_texts = set()
    
    for query in search_queries:
        try:
            results = await search_memories(username, query, max_items=15)
            for mem in results:
                text = getattr(mem, "text", "")
                if text and text not in seen_memory_texts:
                    seen_memory_texts.add(text)
                    all_memories.append(mem)
        except Exception as exc:
            logger.error(f"[CONTEXT] Hafıza aranamadı: {exc}")
    
    # Importance'a göre sırala
    def get_memory_score(memory) -> float:
        importance = getattr(memory, "importance", 0.5)
        relevance = getattr(memory, "relevance", getattr(memory, "score", 0.5))
        return (importance * 0.6) + (relevance * 0.4)
    
    sorted_memories = sorted(all_memories, key=get_memory_score, reverse=True)
    
    all_texts = [getattr(m, "text", "").strip() for m in sorted_memories if getattr(m, "text", "")]
    critical_texts = all_texts[:8]
    other_texts = all_texts[8:]

    profile_lines = []
    if critical_texts:
        profile_lines.append("🧠 Kullanıcı hakkında bilinen önemli bilgiler:")
        profile_lines.extend(f"- {item}" for item in critical_texts)

    other_lines = []
    seen_texts = set(critical_texts)
    for stripped in other_texts:
        if stripped not in seen_texts:
            other_lines.append(f"- {stripped}")
            seen_texts.add(stripped)

    if profile_lines:
        sections.append(_format_context_block("KULLANICI PROFİLİ (ÖNEMLİ)", profile_lines))
    if other_lines:
        sections.append(_format_context_block("İLGİLİ HAFIZALAR", other_lines))

    # RAG dokümanları
    rag_lines = []
    try:
        rag_docs = search_documents(message, owner=username, max_items=3)
        for doc in rag_docs:
            text = getattr(doc, "text", "") or ""
            metadata = getattr(doc, "metadata", {}) or {}
            filename = metadata.get("filename", "Doküman")
            preview = (text[:400] + "...") if len(text) > 400 else text
            rag_lines.append(f"- {filename}: {preview}")
    except Exception as exc:
        logger.error(f"[CONTEXT] RAG dokümanları aranamadı: {exc}")

    if rag_lines:
        sections.append(_format_context_block("İLGİLİ BELGELER", rag_lines))

    if not sections:
        return None, []

    header = "📚 BAĞLAM BİLGİLERİ\n\n"
    full_context = header + "\n\n".join(sections)
    
    # Decider için memory listesi
    memories_for_decider = []
    for m in sorted_memories:
        memories_for_decider.append({
            "id": getattr(m, "id", "unknown"),
            "text": getattr(m, "text", ""),
            "importance": getattr(m, "importance", 0.5)
        })

    return _truncate_context_text(full_context), memories_for_decider


async def build_image_prompt(user_message: str, style_profile: Optional[Dict[str, Any]] = None) -> str:
    """
    Görsel üretimi için prompt oluşturur.
    
    Prefix Kuralları:
        - '!!' ile başlıyorsa: raw prompt + style guard KAPALI
        - '!' ile başlıyorsa: raw prompt + style guard AÇIK
        - Normal: translate/expand + style guard AÇIK
    
    NOT: Permissions/policy (censorship, can_use_image, nsfw) bu fonksiyondan
         ÖNCE kontrol edilir, burada değil.
    
    FORBIDDEN TOKEN GUARD:
        Kullanıcı istemediği sürece style tokenlar eklenmez.
        Bkz: app/ai/prompts/image_guard.py
    """
    (
        _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _
    ) = _get_imports()
    
    # Decider import'u
    from app.chat.decider import call_groq_api_safe_async
    
    # Forbidden token guard import'u
    from app.ai.prompts.image_guard import sanitize_image_prompt
    
    # DEBUG LOG - Ünlem kontrolü için
    logger.warning(f"[DEBUG_EXCLAIM] Gelen mesaj: '{user_message}' | starts with !: {user_message.strip().startswith('!')}")
    
    normalized = user_message.strip()
    prompt: str
    
    # Prefix kontrolü
    raw_prompt = False
    style_guard = True
    
    if normalized.startswith("!!"):
        # !! prefix: RAW + GUARD KAPALI
        raw_prompt = True
        style_guard = False
        prompt = normalized[2:].strip() or normalized[2:]
        logger.info(
            f"[IMAGE_PROMPT] raw_prompt=True, style_guard=False | "
            f"'{user_message}' -> '{prompt}'"
        )
        return prompt
    
    elif normalized.startswith("!"):
        # ! prefix: RAW + GUARD AÇIK
        raw_prompt = True
        style_guard = True
        prompt = normalized[1:].strip() or normalized[1:]
        # Style guard uygula (kullanıcının kendi yazdığı tokenlara dokunma)
        prompt = sanitize_image_prompt(prompt, prompt)  # user_original = prompt kendisi
        logger.info(
            f"[IMAGE_PROMPT] raw_prompt=True, style_guard=True | "
            f"'{user_message}' -> '{prompt}'"
        )
        return prompt
    
    # Normal akış: translate/expand + guard
    raw_prompt = False
    style_guard = True
    
    # Groq ile zenginleştir - MİNİMAL system prompt kullan
    detail_messages = [
        {
            "role": "system",
            "content": (
                    "You are an image prompt translator. "
                    "Translate and expand the user's request into a visual English prompt for Flux. "
                    "Describe the scene visually in 1-2 sentences. "
                    "Output ONLY the prompt text, no explanations or prefixes."
            ),
        },
        {"role": "user", "content": user_message},
    ]
    detailed, _ = await call_groq_api_safe_async(detail_messages, temperature=0.4)
    prompt = detailed.strip() if detailed else user_message.strip()
    
    # FORBIDDEN TOKEN GUARD: Groq'un eklediklerini temizle
    prompt = sanitize_image_prompt(prompt, user_message)

    # Stil ekle (sadece izin verilmişse)
    if style_profile:
        extras = []
        # "highly detailed" sadece kullanıcı "detaylı" dediyse ekle
        if style_profile.get("detail_level") == "long":
            detail_keywords = ["detay", "detail", "ayrıntı", "ayrinti"]
            if any(kw in user_message.lower() for kw in detail_keywords):
                extras.append("detailed")
        if style_profile.get("caution_level") == "high":
            extras.append("balanced framing")
        if extras:
            prompt = f"{prompt}, {'; '.join(extras)}"

    logger.info(
        f"[IMAGE_PROMPT] raw_prompt=False, style_guard=True | "
        f"'{user_message}' -> '{prompt}'"
    )
    return prompt


# =============================================================================
# ANA İŞLEMCİ
# =============================================================================

async def process_chat_message(
    username: str,
    message: str,
    user: Optional[Any] = None,
    force_local: bool = False,
    conversation_id: Optional[str] = None,
    requested_model: Optional[str] = None,
    stream: bool = False,
) -> Union[Tuple[str, Any], AsyncGenerator[str, None]]:
    """
    Ana sohbet işlemcisi.
    
    Args:
        username: Kullanıcı adı
        message: Kullanıcı mesajı
        user: User nesnesi
        force_local: Yerel modeli zorla
        conversation_id: Sohbet ID'si
        requested_model: İstenen model
        stream: Streaming modu
    
    Returns:
        Non-stream: (reply, semantic) tuple
        Stream: AsyncGenerator[str, None]
    """
    (
        get_settings, get_logger, feature_enabled, FeatureDisabledError, User,
        run_decider_async, decide_memory_storage_async, generate_answer, generate_answer_stream,
        handle_internet_action, route_message, RoutingTarget, ToolIntent, analyze_message_semantics,
        build_user_context, choose_model_for_request, should_update_summary, generate_and_save_summary,
        enhance_query_for_search, search_memories, add_memory, delete_memory,
        load_messages, append_message, search_documents, run_local_chat, run_local_chat_stream,
        get_ai_identity, request_image_generation, job_queue
    ) = _get_imports()
    
    logger = get_logger(__name__)
    settings = get_settings()

    # 1. Feature Flag Kontrolü
    if not feature_enabled("chat", True):
        raise FeatureDisabledError("chat")

    # 2. Semantic Analiz
    semantic = await analyze_message_semantics(message)
    semantic_dict = semantic.dict() if semantic else None

    user_context = await build_user_context(
        username, message, conversation_id, semantic_dict, user,
    )
    memory_blocks = user_context.get("memory_blocks", {})
    memory_hint = build_memory_hint(memory_blocks)

    # 3. SmartRouter ile Yönlendirme Kararı
    # Kullanıcının aktif persona'sını al (DB'den)
    active_persona = getattr(user, "active_persona", "standard") if user else "standard"
    
    routing_decision = route_message(
        message=message,
        user=user,
        persona_name=active_persona,
        requested_model=requested_model,
        force_local=force_local,
        semantic=semantic_dict,
    )
    
    # Routing loglaması
    logger.info(
        f"[ROUTER] User: {username} | Persona: {active_persona} | "
        f"Target: {routing_decision.target.value} | "
        f"Tool: {routing_decision.tool_intent.value} | "
        f"Reasons: {routing_decision.reason_codes} | "
        f"Censorship: {routing_decision.censorship_level} | Stream: {stream}"
    )
    
    # BLOCKED kontrolü - izin yoksa hata döndür
    if routing_decision.blocked:
        error_msg = routing_decision.block_reason or "Bu istek izniniz dahilinde değil."
        return f"[BLOCKED] {error_msg}", semantic
    
    # Routing hedefine göre action belirle
    action = "GROQ_REPLY"
    analysis: Dict[str, Any] = {"intent": "chat"}
    decision: Dict[str, Any] = {}
    
    if routing_decision.target == RoutingTarget.IMAGE:
        action = "IMAGE"
    elif routing_decision.target == RoutingTarget.INTERNET:
        action = "INTERNET"
        # Internet için decider'dan ek bilgi al
        decision = await run_decider_async(message)
        analysis = decision.get("analysis", analysis)
    elif routing_decision.target == RoutingTarget.LOCAL:
        action = "LOCAL_CHAT"
    else:
        # GROQ - router kararına güven, decider'ı bypass et
        action = "GROQ_REPLY"
        # analysis zaten semantic analizden geldi

    # A) GÖRSEL ÜRETİM
    # YENİ YAKLAŞIM: Mesajı SYNC oluştur, job'u async başlat
    # Frontend job_id ve message_id'yi almalı
    if action == "IMAGE":
        from uuid import uuid4
        
        # 1. Prompt'u SYNC hazırla
        prompt = await build_image_prompt(message)
        
        # 2. JOB_ID'yi ÖNCE oluştur
        job_id = str(uuid4())
        
        # 3. Mesajı SYNC oluştur (job_id dahil!)
        message_id = None
        if conversation_id:
            placeholder_msg = append_message(
                username=username,
                conv_id=conversation_id,
                role="bot",
                text="[IMAGE_PENDING] Görsel isteğiniz kuyruğa alındı...",
                extra_metadata={
                    "type": "image", 
                    "status": "queued", 
                    "job_id": job_id,
                    "prompt": prompt[:200]
                }
            )
            message_id = placeholder_msg.id
            logger.info(f"[IMAGE] Mesaj oluşturuldu (sync): {message_id}, job_id: {job_id[:8]}")
        
        # 4. Job'u ASYNC başlat (mesaj zaten oluşturuldu)
        async def _start_job():
            try:
                result_job_id = request_image_generation(
                    username=username,
                    prompt=prompt,
                    message_id=message_id,
                    job_id=job_id,
                    conversation_id=conversation_id,
                    user=user,
                )
                if result_job_id:
                    logger.info(f"[IMAGE] Job başlatıldı: {result_job_id} -> mesaj: {message_id}")
            except Exception as e:
                logger.error(f"[IMAGE] Job başlatma hatası: {e}")
                if message_id:
                    from app.memory.conversation import update_message
                    update_message(message_id, f"❌ Görsel oluşturulamadı: {str(e)}", {"status": "error"})
        
        asyncio.create_task(_start_job())
        
        # 5. Frontend'e JSON bilgisi döndür (special marker ile)
        # Format: [IMAGE_QUEUED:job_id:message_id]
        return f"[IMAGE_QUEUED:{job_id}:{message_id}]", semantic

    # B) İNTERNET ARAMASI
    if action == "INTERNET":
        res = await handle_internet_action(
            decision, username, message, semantic=semantic,
            conversation_id=conversation_id, user=user, user_context=user_context,
        )
        return f"[NET] {res}", semantic

    # C) YEREL MODEL
    if action == "LOCAL_CHAT":
        local_history = build_history_budget(username, conversation_id, token_budget=HISTORY_TOKEN_BUDGET_LOCAL)
        ctx_tuple = await build_enhanced_context(username, message, conversation_id)
        full_context = ctx_tuple[0] if ctx_tuple else ""

        if (local_history and local_history[-1].get("role") == "user" and
            (local_history[-1].get("content") or "").strip() == (message or "").strip()):
            local_history = local_history[:-1]

        if stream:
            async def local_stream_wrapper():
                async for chunk in run_local_chat_stream(
                    username, message, analysis, history=local_history, memory_hint=full_context
                ):
                    yield chunk
            return local_stream_wrapper()

        res = await run_local_chat(
            username, message, analysis, history=local_history, memory_hint=full_context
        )
        return f"[BELA] {res}", semantic

    # D) GROQ REPLY (Varsayılan)
    full_context_str, relevant_memories = await build_enhanced_context(username, message, conversation_id)
    full_context = full_context_str or ""

    raw_history = build_history_budget(username, conversation_id, token_budget=HISTORY_TOKEN_BUDGET_GROQ)
    if (raw_history and raw_history[-1].get("role") == "user" and
        (raw_history[-1].get("content") or "").strip() == (message or "").strip()):
        raw_history = raw_history[:-1]
    groq_history = normalize_groq_history(raw_history)

    # STREAMING
    if stream:
        async def groq_stream_wrapper():
            from app.services.streaming_memory_manager import streaming_memory_manager
            from app.chat.streaming_buffer import StreamingBuffer
            
            buffer = StreamingBuffer(max_chunks=1000)  # ~100KB max
            
            try:
                async for chunk in generate_answer_stream(
                    message=message, analysis=analysis, context=full_context, history=groq_history,
                ):
                    buffer.append(chunk)
                    yield chunk

                final_answer_streamed = buffer.finalize()
            finally:
                buffer.clear()  # Ensure cleanup
            if final_answer_streamed:
                # Streaming memory deduplication kontrolü
                import hashlib
                message_id = hashlib.md5(f"{conversation_id}:{message}:{final_answer_streamed[:100]}".encode()).hexdigest()
                
                if await streaming_memory_manager.can_process_memory(message_id):
                    try:
                        async with await streaming_memory_manager.get_lock(message_id):
                            decision_mem = await decide_memory_storage_async(message, final_answer_streamed, existing_memories=relevant_memories)
                            invalidate_ids = decision_mem.get("invalidate", [])
                            if invalidate_ids:
                                for old_id in invalidate_ids:
                                    await delete_memory(username, old_id)
                            if decision_mem.get("store") and decision_mem.get("memory"):
                                await add_memory(username, decision_mem["memory"], importance=decision_mem.get("importance", 0.5))
                        
                        await streaming_memory_manager.mark_completed(message_id)
                    except Exception as e:
                        logger.error(f"[ROUTER] Hafıza kayıt hatası: {e}")
                else:
                    logger.debug(f"[ROUTER] Memory already processed for message_id: {message_id}")
                
                if conversation_id:
                    try:
                        if await should_update_summary(conversation_id):
                            summary_coro = generate_and_save_summary(conversation_id)
                            if summary_coro:
                                asyncio.create_task(summary_coro)
                    except Exception as e:
                        logger.debug(f"[STREAM] Summary check/generate failed: {e}")

        return groq_stream_wrapper()

    # NON-STREAMING
    final_answer = await generate_answer(
        message=message, analysis=analysis, context=full_context, history=groq_history,
    )

    # Hafıza kayıt
    try:
        decision_mem = await decide_memory_storage_async(message, final_answer, existing_memories=relevant_memories)
        invalidate_ids = decision_mem.get("invalidate", [])
        if invalidate_ids:
            for old_id in invalidate_ids:
                await delete_memory(username, old_id)
        if decision_mem.get("store") and decision_mem.get("memory"):
            await add_memory(username, decision_mem["memory"], importance=decision_mem.get("importance", 0.5))
    except Exception as e:
        logger.error(f"[ROUTER] Hafıza kayıt hatası: {e}")

    # Özet tetikleme
    if conversation_id:
        try:
            if await should_update_summary(conversation_id):
                summary_coro = generate_and_save_summary(conversation_id)
                if summary_coro:
                    asyncio.create_task(summary_coro)
        except Exception as e:
            logger.debug(f"[ROUTER] Summary check/generate failed: {e}")

    return f"[GROQ] {final_answer}", semantic

