import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel

# ChromaDB importu
from app.core.database import get_chroma_client

logger = logging.getLogger(__name__)

# --- SABÄ°TLER ---
COLLECTION_NAME = "memories"
DEFAULT_IMPORTANCE = 0.5
DEFAULT_TOPIC = "general"


class MemoryRecord(BaseModel):
    """ChromaDB Ã¼zerinde tutulan bir hafÄ±za kaydÄ±nÄ±n uygulama iÃ§i temsili."""
    id: str
    user_id: int
    text: str
    type: str # fact, goal, preference
    importance: float
    topic: str
    source: str
    
    is_active: bool
    created_at: str
    last_accessed: str

    score: Optional[float] = None
    vector_similarity: Optional[float] = None

    metadata: Dict[str, Any] = {}


class MemoryService:
    """Uzun vadeli, semantik hafÄ±za servisi."""

    # -------------------------------------------------------------------------
    # Ä°Ã§ yardÄ±mcÄ±lar
    # -------------------------------------------------------------------------
    @staticmethod
    def _get_collection():
        """ChromaDB koleksiyonunu getirir."""
        client = cast(Any, get_chroma_client())
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Cosine similarity
        )

    @staticmethod
    def _get_current_time() -> str:
        return datetime.utcnow().isoformat()

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_str(value: Any, default: str) -> str:
        return default if value is None else str(value)

    @staticmethod
    def _to_metadata(meta: Any) -> Dict[str, Any]:
        if isinstance(meta, dict):
            return dict(meta)
        try:
            return dict(meta or {})
        except Exception:
            return {}

    # -------------------------------------------------------------------------
    # API: Ekleme
    # -------------------------------------------------------------------------
    @classmethod
    async def add_memory(
        cls,
        user_id: int,
        text: str,
        memory_type: str = "fact",
        importance: float = DEFAULT_IMPORTANCE,
        topic: str = DEFAULT_TOPIC,
        source: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Yeni bir anÄ± ekler."""
        if not text: raise ValueError("HafÄ±za metni boÅŸ olamaz.")

        collection = cls._get_collection()
        now = cls._get_current_time()

        # --- HYBRID DUPLICATE CHECK (SEMANTIC + TEXT + ENTITY) ---
        from app.services.memory_duplicate_detector import detector
        
        try:
            # Benzer iÃ§erikli aktif bir kayÄ±t var mÄ±?
            # WHERE filter ile native filtering (ChromaDB >=0.4.22)
            check_res: Dict[str, Any] = await asyncio.to_thread(
                collection.query,
                query_texts=[text],
                n_results=10,  # Top-10 semantically similar
                where={"$and": [{"user_id": user_id}, {"is_active": True}]}  # ChromaDB $and filter
            )
            
            ids_block = check_res.get("ids") or []
            docs_block = check_res.get("documents") or []
            dists_block = check_res.get("distances") or []
            metas_block = check_res.get("metadatas") or []

            # Hybrid duplicate detection
            if ids_block and len(ids_block) > 0 and ids_block[0]:
                doc_ids: List[Any] = ids_block[0]
                docs: List[Any] = docs_block[0] if docs_block else []
                dists: List[Any] = dists_block[0] if dists_block else []
                metas: List[Any] = metas_block[0] if metas_block else []

                for i, doc_id in enumerate(doc_ids):
                    if i >= len(docs) or i >= len(dists):
                        continue

                    meta = cls._to_metadata(metas[i]) if i < len(metas) else {}
                    existing_text = cls._to_str(docs[i], "")
                    existing_dist = cls._to_float(dists[i], 0.0)

                    # Hybrid duplicate detection
                    is_dup, reason = detector.is_duplicate(
                        new_text=text,
                        existing_text=existing_text,
                        semantic_distance=existing_dist,
                        importance=importance,
                        use_entity_check=True
                    )

                    if is_dup:
                        logger.info(
                            f"[MEMORY] Duplicate detected: {reason} | "
                            f"ID: {doc_id} | dist={existing_dist:.4f}"
                        )

                        # Mevcut kaydZñ dÇôndÇ¬r
                        return MemoryRecord(
                            id=cls._to_str(doc_id, ""),
                            user_id=user_id,
                            text=existing_text,
                            type=cls._to_str(meta.get("type"), "fact"),
                            importance=cls._to_float(meta.get("importance"), 0.5),
                            topic=cls._to_str(meta.get("topic"), DEFAULT_TOPIC),
                            source=cls._to_str(meta.get("source"), "chat"),
                            is_active=True,
                            created_at=cls._to_str(meta.get("created_at"), now),
                            last_accessed=cls._to_str(meta.get("last_accessed"), now),
                            metadata=meta,
                        )
                    else:
                        logger.debug(f"[MEMORY] Not duplicate: {reason}")
                        break  # Zølk kontrolde duplicate deZYilse diZYerlerine gerek yok
        except Exception as e:
            logger.warning(f"[MEMORY] Duplicate check hatasÄ±: {e}")

        # EÄŸer duplicate deÄŸilse yeni oluÅŸtur
        memory_id = str(uuid.uuid4())

        final_metadata: Dict[str, Any] = {
            "user_id": user_id,
            "type": memory_type,
            "importance": float(importance),
            "topic": topic,
            "source": source,
            "is_active": True,
            "created_at": now,
            "last_accessed": now,
        }

        if metadata:
            for k, v in metadata.items():
                if k not in final_metadata: final_metadata[k] = v if v is not None else "" # None kontrolÃ¼

        # Chroma iÅŸlemi bloklayÄ±cÄ± olabilir, thread'e atÄ±yoruz
        await asyncio.to_thread(
            collection.add,
            documents=[text],
            metadatas=[final_metadata],
            ids=[memory_id],
        )

        logger.info(f"[MEMORY] Yeni kayÄ±t eklendi: {memory_id} (User: {user_id})")

        return MemoryRecord(
            id=memory_id, user_id=user_id, text=text, type=memory_type,
            importance=float(importance), topic=topic, source=source,
            is_active=True, created_at=now, last_accessed=now,
            score=None, vector_similarity=None, metadata=final_metadata,
        )

    # -------------------------------------------------------------------------
    # API: Sorgulama (Semantic Search + Scoring)
    # -------------------------------------------------------------------------
    @classmethod
    async def retrieve_relevant_memories(
        cls,
        user_id: int,
        query: str,
        limit: int = 5,
        min_relevance: float = 0.4,
    ) -> List[MemoryRecord]:
        """Sorguyla alakalÄ± anÄ±larÄ± getirir ve Yeniden Puanlama (Re-Ranking) uygular."""
        collection = cls._get_collection()

        fetch_k = max(limit * 3, limit)

        try:
            results = await asyncio.to_thread(
                collection.query,
                query_texts=[query],
                n_results=fetch_k,  # Sadece gerekli kadar
                where={"$and": [{"user_id": user_id}, {"is_active": True}]}  # ChromaDB $and filter
            )
        except Exception as e:
            logger.error(f"[MEMORY] Arama hatasZñ: {e}")
            return []

        ids_block = results.get("ids") or []
        docs_block = results.get("documents") or []
        metas_block = results.get("metadatas") or []
        dists_block = results.get("distances") or []

        if not ids_block or not ids_block[0]: return []

        ids: List[Any] = ids_block[0]
        documents: List[Any] = docs_block[0] if docs_block else []
        metadatas: List[Any] = metas_block[0] if metas_block else []
        distances: List[Any] = dists_block[0] if dists_block else []

        max_len = min(len(ids), len(documents), len(metadatas), len(distances))
        if max_len == 0: return []

        scored_memories: List[MemoryRecord] = []
        now = datetime.utcnow()

        # 2. Re-Ranking (Yeniden Puanlama)
        for i in range(max_len):
            meta = cls._to_metadata(metadatas[i])

            # VektÇôr BenzerliZYi (Similarity = 1 - Distance)
            dist = cls._to_float(distances[i], 1.0)
            vector_sim = max(0.0, 1.0 - dist)

            # Importance (Ç-nem)
            importance = cls._to_float(meta.get("importance"), DEFAULT_IMPORTANCE)

            # Recency (Yenilik / Tazelik)
            try:
                created_raw = cls._to_str(meta.get("created_at"), cls._get_current_time())
                created_at_dt = datetime.fromisoformat(created_raw)
                days_old = (now - created_at_dt).days
                recency = 1.0 / (1.0 + (days_old / 30.0)) # Basit decay formÇ¬lÇ¬
            except Exception:
                created_raw = cls._get_current_time()
                recency = 0.5

            # --- NZøHAZø SKOR FORMÇoLÇo (PROFESYONEL) ---
            # Benzerlik %60, Ç-nem %30, Yenilik %10
            final_score = (vector_sim * 0.6) + (importance * 0.3) + (recency * 0.1)

            if final_score < min_relevance: continue

            last_accessed_raw = cls._to_str(meta.get("last_accessed"), created_raw)

            record = MemoryRecord(
                id=cls._to_str(ids[i], ""), user_id=cls._to_int(meta.get("user_id"), user_id), text=cls._to_str(documents[i], ""),
                type=cls._to_str(meta.get("type"), "fact"), importance=importance,
                topic=cls._to_str(meta.get("topic"), DEFAULT_TOPIC), source=cls._to_str(meta.get("source"), "chat"),
                is_active=bool(meta.get("is_active", True)), created_at=created_raw,
                last_accessed=last_accessed_raw, score=final_score,
                vector_similarity=vector_sim, metadata=meta,
            )
            scored_memories.append(record)

        # 3. SÄ±ralama ve Kesme
        scored_memories.sort(key=lambda r: (r.score or 0.0), reverse=True)
        top_memories = scored_memories[:limit]

        # 4. Yan Etki: SeÃ§ilenlerin 'last_accessed' tarihini gÃ¼ncelle
        if top_memories:
            collection = cls._get_collection()
            update_ids = [m.id for m in top_memories]
            new_metas = []

            for m in top_memories:
                updated_meta = dict(m.metadata)
                updated_meta["last_accessed"] = cls._get_current_time()
                new_metas.append(updated_meta)

            await asyncio.to_thread(collection.update, ids=update_ids, metadatas=new_metas)

        return top_memories

    # -------------------------------------------------------------------------
    # API: Soft delete
    # -------------------------------------------------------------------------
    @classmethod
    async def soft_delete_memory(cls, user_id: int, memory_id: str) -> bool:
        """AnÄ±yÄ± silmez, 'is_active=False' olarak iÅŸaretler (Soft Delete)."""
        collection = cls._get_collection()

        # where filtresi kullanmZñyoruz (ChromaDB SQLite backend hatasZñ)
        existing = await asyncio.to_thread(
            collection.get, ids=[memory_id], include=["metadatas"]
        )

        if not existing.get("ids"):
            logger.warning(f"[MEMORY] Silinecek kayZñt bulunamadZñ: {memory_id}")
            return False

        # Manuel user_id kontrolÇ¬
        metadatas = existing.get("metadatas") or []
        current_meta = cls._to_metadata(metadatas[0]) if metadatas else {}
        if cls._to_int(current_meta.get("user_id"), -1) != user_id:
            logger.warning(f"[MEMORY] Yetkisiz silme denemesi: {memory_id} (user_id={user_id})")
            return False

        current_meta["is_active"] = False

        await asyncio.to_thread(collection.update, ids=[memory_id], metadatas=[current_meta])
        logger.info(f"[MEMORY] KayZñt arYivlendi: {memory_id}")
        return True

    @classmethod
    async def update_memory(
        cls,
        user_id: int,
        memory_id: str,
        text: str,
        importance: Optional[float] = None,
        topic: Optional[str] = None,
    ) -> Optional[MemoryRecord]:
        """Varolan hafÄ±za kaydÄ±nÄ± gÃ¼nceller."""
        collection = cls._get_collection()

        # where filtresi kullanmZñyoruz (ChromaDB SQLite backend hatasZñ)
        existing = await asyncio.to_thread(
            collection.get,
            ids=[memory_id],
            include=["metadatas"]
        )
        if not existing.get("ids"):
            logger.warning(f"[MEMORY] GÇ¬ncellenecek kayit bulunamadi: {memory_id}")
            return None

        # Manuel user_id kontrolÇ¬
        metadatas = existing.get("metadatas") or []
        current_meta = cls._to_metadata(metadatas[0]) if metadatas else {}
        if cls._to_int(current_meta.get("user_id"), -1) != user_id:
            logger.warning(f"[MEMORY] Yetkisiz gÇ¬ncelleme denemesi: {memory_id} (user_id={user_id})")
            return None
        new_importance = importance if importance is not None else cls._to_float(current_meta.get("importance"), DEFAULT_IMPORTANCE)
        new_topic = topic or cls._to_str(current_meta.get("topic"), DEFAULT_TOPIC)
        current_meta["importance"] = float(new_importance)
        current_meta["topic"] = new_topic
        current_meta["last_accessed"] = cls._get_current_time()

        await asyncio.to_thread(
            collection.update,
            ids=[memory_id],
            documents=[text],
            metadatas=[current_meta],
        )

        return MemoryRecord(
            id=memory_id,
            user_id=user_id,
            text=text,
            type=str(current_meta.get("type", "fact")),
            importance=float(new_importance),
            topic=str(new_topic),
            source=str(current_meta.get("source", "chat")),
            is_active=bool(current_meta.get("is_active", True)),
            created_at=cls._to_str(current_meta.get("created_at"), cls._get_current_time()),
            last_accessed=cls._to_str(current_meta.get("last_accessed"), cls._get_current_time()),
            score=None,
            vector_similarity=None,
            metadata=current_meta,
        )

