"""
Mami AI - RAG (Retrieval Augmented Generation) Deposu
=====================================================

Bu modül, yüklenen dokümanları (PDF, TXT) semantik arama için depolar.

Özellikler:
    - Metin chunking (parçalama)
    - ChromaDB vektör depolama
    - Scope bazlı erişim (global, user, conversation)
    - Semantik arama

Kullanım:
    from app.memory.rag import add_document, search_documents

    # Doküman ekle
    add_document(text, scope="user", owner="john", metadata={"filename": "doc.pdf"})

    # Arama yap
    results = search_documents("Python nedir?", owner="john", max_items=5)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# TİP TANIMLAMALARI
# =============================================================================

Scope = Literal["global", "user", "conversation", "web"]
"""Doküman erişim kapsamı."""

# =============================================================================
# CHUNKING AYARLARI
# =============================================================================

DEFAULT_CHUNK_SIZE = 500
"""Varsayılan chunk boyutu (karakter)."""

DEFAULT_CHUNK_OVERLAP = 50
"""Chunk'lar arası örtüşme."""


# =============================================================================
# DATA CLASS
# =============================================================================


@dataclass
class RagDocument:
    """RAG doküman veri sınıfı."""

    id: str
    scope: Scope
    owner: Optional[str]
    text: str
    created_at: str
    metadata: Dict[str, Any]


# =============================================================================
# LAZY IMPORTS
# =============================================================================


def _get_chroma_client():
    """ChromaDB client lazy import."""
    try:
        from app.core.database import get_chroma_client
    except ImportError:
        from app.core.database import get_chroma_client
    return get_chroma_client()


def _get_rag_collection():
    """RAG koleksiyonunu döndürür."""
    client = _get_chroma_client()

    try:
        # Try to get existing collection
        collection = client.get_collection(name="rag_docs")  # type: ignore

        # Test if collection works by attempting a simple query
        try:
            collection.peek(limit=1)  # type: ignore
        except Exception as e:
            # Collection exists but is corrupted, delete and recreate
            logger.warning(f"[RAG] Collection corrupted ({e}), recreating...")
            try:
                client.delete_collection(name="rag_docs")  # type: ignore
            except:
                pass
            collection = client.create_collection(name="rag_docs", metadata={"hnsw:space": "cosine"})  # type: ignore
            logger.info("[RAG] Collection recreated successfully")
    except:
        # Collection doesn't exist, create it
        collection = client.create_collection(name="rag_docs", metadata={"hnsw:space": "cosine"})  # type: ignore
        logger.info("[RAG] New collection created")

    return collection


# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    """
    Metni örtüşen parçalara böler.

    Args:
        text: Bölünecek metin
        chunk_size: Maksimum chunk boyutu
        overlap: Parçalar arası örtüşme

    Returns:
        List[str]: Metin parçaları
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Kelime ortasında bölmemek için son boşluğu bul
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Sonraki başlangıç
        start = end - overlap if end < len(text) else len(text)

        # Sonsuz döngü koruması
        if start >= end:
            break

    return chunks


# =============================================================================
# PUBLIC API
# =============================================================================


def add_document(
    text: str,
    scope: Scope = "global",
    owner: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    chunk: bool = True,
) -> List[str]:
    """
    Doküman ekler (opsiyonel chunking ile).

    Args:
        text: Eklenecek metin
        scope: Erişim kapsamı
        owner: Sahip kullanıcı adı
        metadata: Ek metadata
        chunk: Metni parçalara böl

    Returns:
        List[str]: Eklenen doküman ID'leri
    """
    collection = _get_rag_collection()

    # Chunking
    if chunk and len(text) > DEFAULT_CHUNK_SIZE:
        texts = chunk_text(text)
    else:
        texts = [text]

    doc_ids = []
    now = datetime.utcnow().isoformat()

    for i, chunk_text_item in enumerate(texts):
        doc_id = str(uuid.uuid4())
        doc_ids.append(doc_id)

        doc_metadata = {
            "scope": scope,
            "owner": owner or "",
            "created_at": now,
            "chunk_index": i,
            "total_chunks": len(texts),
            **(metadata or {}),
        }

        try:
            collection.add(ids=[doc_id], documents=[chunk_text_item], metadatas=[doc_metadata])
        except Exception as e:
            logger.error(f"[RAG] Ekleme hatası: {e}")

    logger.info(f"[RAG] {len(doc_ids)} chunk eklendi (scope={scope})")
    return doc_ids


def search_documents(
    query: str, owner: Optional[str] = None, scope: Optional[Scope] = None, max_items: int = 5
) -> List[RagDocument]:
    """
    Dokümanlarda semantik arama yapar.

    Args:
        query: Arama sorgusu
        owner: Filtreleme için sahip
        scope: Filtreleme için kapsam
        max_items: Maksimum sonuç

    Returns:
        List[RagDocument]: Eşleşen dokümanlar
    """
    try:
        collection = _get_rag_collection()
    except Exception as e:
        # ChromaDB schema corruption detected
        if "no such column" in str(e):
            logger.error(f"[RAG] ChromaDB schema corrupted: {e}")
            logger.error("[RAG] Please delete data/chroma_db directory and restart")
            return []
        raise

    # Filtre oluştur
    where_filter = {}
    if owner:
        where_filter["owner"] = owner
    if scope:
        where_filter["scope"] = scope

    try:
        # WHERE filtresi ile native filtering (ChromaDB >=0.4.22 gerekli)
        # Performance improvement: Manual filtreleme kaldırıldı
        where_filter = {}
        if owner:
            where_filter["owner"] = owner
        if scope:
            where_filter["scope"] = scope

        results = collection.query(
            query_texts=[query],
            n_results=max_items,  # Sadece gerekli kadar (2x değil!)
            where=where_filter if where_filter else None,
        )

        documents = []
        if results and results.get("ids"):
            ids_list = results.get("ids")
            metadatas_list = results.get("metadatas")
            documents_list = results.get("documents")

            if ids_list and metadatas_list and documents_list:
                for i, doc_id in enumerate(ids_list[0]):
                    if i >= len(metadatas_list[0]) or i >= len(documents_list[0]):
                        continue

                    meta = metadatas_list[0][i]
                    # Extract and cast metadata values to proper types
                    scope_val = meta.get("scope", "global")
                    doc_scope: Scope = str(scope_val) if scope_val in ["global", "user", "conversation", "web"] else "global"  # type: ignore

                    owner_val = meta.get("owner")
                    doc_owner: Optional[str] = (
                        str(owner_val) if owner_val and isinstance(owner_val, (str, int, float)) else None
                    )

                    created_val = meta.get("created_at", "")
                    doc_created_at: str = str(created_val) if created_val else ""

                    # Convert metadata to proper Dict[str, Any]
                    metadata_dict: Dict[str, Any] = dict(meta) if meta else {}

                    doc = RagDocument(
                        id=doc_id,
                        scope=doc_scope,
                        owner=doc_owner,
                        text=documents_list[0][i],
                        created_at=doc_created_at,
                        metadata=metadata_dict,
                    )
                    documents.append(doc)

        return documents

    except Exception as e:
        logger.error(f"[RAG] Arama hatası: {e}")
        return []


def delete_document(doc_id: str) -> bool:
    """
    Doküman siler.

    Args:
        doc_id: Silinecek doküman ID'si

    Returns:
        bool: Silme başarılı ise True
    """
    collection = _get_rag_collection()

    try:
        collection.delete(ids=[doc_id])
        logger.info(f"[RAG] Silindi: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"[RAG] Silme hatası: {e}")
        return False


def delete_by_owner(owner: str) -> int:
    """
    Bir kullanıcıya ait tüm dokümanları siler.

    Args:
        owner: Kullanıcı adı

    Returns:
        int: Silinen doküman sayısı
    """
    collection = _get_rag_collection()

    try:
        # where filtresi kullanmıyoruz (ChromaDB SQLite backend hatası)
        # Tüm kayıtları al, owner'a göre manuel filtrele
        results = collection.get(limit=10000)  # Yeterince büyük limit

        if not results or not results.get("ids"):
            return 0

        # Manuel filtrele: owner kontrolü
        ids_to_delete = []
        ids_list = results.get("ids")
        metadatas = results.get("metadatas")

        if ids_list and metadatas:
            for i, doc_id in enumerate(ids_list):
                meta = metadatas[i] if i < len(metadatas) else {}
                if meta.get("owner") == owner:
                    ids_to_delete.append(doc_id)

        if not ids_to_delete:
            return 0

        collection.delete(ids=ids_to_delete)

        logger.info(f"[RAG] {len(ids_to_delete)} doküman silindi (owner={owner})")
        return len(ids_to_delete)

    except Exception as e:
        logger.error(f"[RAG] Toplu silme hatası: {e}")
        return 0
