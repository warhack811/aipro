"""
Mami AI - İnternet Arama İşleyicisi
===================================

Bu modül, internet arama aksiyonlarını işler.

İşlem Akışı:
    1. Decider'dan gelen sorguları al
    2. Search manager ile arama yap
    3. Sonuçları yapılandırılmış formata dönüştür
    4. Groq ile özet cevap üret

Desteklenen Arama Türleri:
    - Genel web araması
    - Hava durumu (structured)
    - Döviz kurları (structured)
    - Spor sonuçları (structured)

Kullanım:
    from app.chat.search import handle_internet_action
    
    result = await handle_internet_action(
        decision={"internet": {"queries": [...]}},
        username="john",
        original_message="Dolar kaç TL?"
    )
"""

from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Dict, Optional

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# SABİTLER
# =============================================================================

SEARCH_SUMMARY_PROMPT = """
Sen uzman bir asistansın. Arama sonuçlarını kullanarak kullanıcıya yanıt ver.
- Asla "Arama sonuçlarına göre" deme. Doğal konuş.
- Bilgi yoksa dürüstçe "Bu konuda net bilgi bulamadım" de.
"""


# =============================================================================
# LAZY IMPORTS
# =============================================================================

def _get_imports():
    """Import döngüsünü önlemek için lazy import."""
    from app.chat.answerer import generate_answer
    from app.search.manager import search_queries_async
    from app.search.structured_parser import (
        parse_exchange_rate_result,
        parse_sports_fixture_result,
        parse_weather_result,
    )
    
    return (
        search_queries_async,
        generate_answer,
        parse_weather_result,
        parse_exchange_rate_result,
        parse_sports_fixture_result,
    )


# =============================================================================
# ANA İŞLEYİCİ
# =============================================================================

async def handle_internet_action(
    decision: Dict[str, Any],
    username: str,
    original_message: str,
    semantic: Optional[Any] = None,
    conversation_id: Optional[str] = None,
    user: Optional[Any] = None,
    user_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Decider'dan gelen internet aksiyonunu işler.
    
    Args:
        decision: Decider kararı (internet.queries içermeli)
        username: Kullanıcı adı
        original_message: Orijinal kullanıcı mesajı
        semantic: Semantic analiz sonuçları (Dict veya Pydantic model)
        conversation_id: Sohbet ID'si
        user: Kullanıcı nesnesi
        user_context: Kullanıcı bağlamı
    
    Returns:
        str: İşlenmiş ve özetlenmiş yanıt
    """
    (
        search_queries_async,
        generate_answer,
        parse_weather_result,
        parse_exchange_rate_result,
        parse_sports_fixture_result,
    ) = _get_imports()
    
    try:
        # 1. Sorguları al
        internet_info = decision.get("internet") or {}
        queries = internet_info.get("queries") or []

        if not queries:
            return "İnternet araması yapmam istendi ancak sorgu oluşturulamadı."

        logger.info(f"[INTERNET] user={username} için {len(queries)} sorgu işlenecek")

        # 2. Arama yap
        search_results = await search_queries_async(queries)

        # Sonuç kontrolü
        has_any_result = any(
            snippets for snippets in search_results.values()
        )
        
        if not has_any_result:
            return f"'{original_message}' ile ilgili güncel bir sonuç bulamadım."

        # 3. Context oluştur
        context_lines = []
        structured_data = None
        
        # Semantic değer okuyucu (Dict veya Object uyumlu)
        def get_sem_val(key, default=None):
            if isinstance(semantic, dict):
                return semantic.get(key, default)
            return getattr(semantic, key, default)

        sem_mode = get_sem_val("answer_mode", "web_factual")
        
        # Structured data parsing (hava, döviz, spor)
        if sem_mode == "strict_structured" and queries:
            try:
                first_q = queries[0]
                snippets = search_results.get(first_q.get("id", ""), [])
                qtext = first_q.get("query", "")
                domain = get_sem_val("domain")

                if domain == "weather":
                    structured_data = parse_weather_result(snippets)
                elif domain == "finance":
                    base = "USD"
                    if "dolar" in qtext.lower():
                        base = "USD"
                    elif "euro" in qtext.lower():
                        base = "EUR"
                    elif "altın" in qtext.lower():
                        base = "GOLD"
                    structured_data = parse_exchange_rate_result(snippets, base, "TRY")
                elif domain == "sports":
                    team = "Takım"
                    for t in ["Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor"]:
                        if t.lower() in qtext.lower():
                            team = t
                            break
                    structured_data = parse_sports_fixture_result(snippets, team)
            except Exception as e:
                logger.error(f"[INTERNET] Parser hatası: {e}")

        # Context oluştur
        if structured_data and not structured_data.get("error"):
            context_lines.append(
                f"STRUCTURED_DATA_JSON:\n{json.dumps(structured_data, ensure_ascii=False)}"
            )
        else:
            for q in queries:
                qid = q.get("id", "?")
                snippets = search_results.get(qid, [])
                if not snippets:
                    continue
                
                context_lines.append(f"--- Sorgu: {q.get('query')} ---")
                for snip in snippets[:4]:
                    context_lines.append(f"Başlık: {snip.title}\nÖzet: {snip.snippet}\n")

        full_context = "\n".join(context_lines)

        # 4. Kaynakları topla (formatter için)
        sources = []
        for q in queries:
            qid = q.get("id", "?")
            snippets = search_results.get(qid, [])
            for snip in snippets[:3]:  # Max 3 kaynak per sorgu
                sources.append({
                    "title": snip.title,
                    "url": snip.url,
                    "snippet": snip.snippet,
                })

        # 5. Cevap üret
        answer = await generate_answer(
            message=original_message,
            analysis=decision.get("analysis"),
            context=full_context,
            system_prompt=SEARCH_SUMMARY_PROMPT,
            source="internet",
        )

        # 6. Formatter ile kaynakları ekle
        try:
            from app.services.tool_output_formatter import format_web_result
            formatted_answer = format_web_result(answer, sources)
            return formatted_answer
        except ImportError:
            logger.warning("[INTERNET] tool_output_formatter bulunamadı, ham cevap döndürülüyor")
            return answer

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"[INTERNET] Crash: {error_trace}")
        return f"İnternet modülünde teknik bir hata: {str(e)}"







