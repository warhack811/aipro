from __future__ import annotations
from typing import Optional, Dict, Any, List, AsyncGenerator
import httpx, json
from app.ai.prompts.identity import get_ai_identity, enforce_model_identity
from app.core.logger import get_logger
from app.config import get_settings
from app.core.gpu_manager import GPUManager # YENİ IMPORT
from app.services.response_processor import full_post_process  # YENİ: Response Enhancement
import re
logger = get_logger(__name__)
settings = get_settings()
_THINK_BLOCK_RE = re.compile(r"(?is)<\s*think(?:ing)?\s*>.*?<\s*/\s*think(?:ing)?\s*>")

def strip_think_blocks(text: str) -> str:
    if not text:
        return text
    return _THINK_BLOCK_RE.sub("", text)


_THINK_OPEN_RE = re.compile(r"(?is)<\s*think(?:ing)?\s*>")
_THINK_CLOSE_RE = re.compile(r"(?is)<\s*/\s*think(?:ing)?\s*>")

def strip_think_stateful(text: str, *, in_think: bool) -> tuple[str, bool]:
    """
    Kapanış etiketi gelmese bile düşünce bloklarını kesin biçimde engeller.
    - in_think=True iken kapanış gelene kadar her şeyi atar.
    - Açılış etiketi görürse in_think=True yapar ve devamını atar.
    """
    if not text:
        return "", in_think

    out = []
    i = 0
    n = len(text)

    while i < n:
        if in_think:
            # Kapanış arıyoruz
            m_close = _THINK_CLOSE_RE.search(text, i)
            if not m_close:
                # Kapanış yok: kalan her şey düşünce, komple at
                return "".join(out), True
            # Kapanışa kadar atla, kapanış etiketini de tüket
            i = m_close.end()
            in_think = False
            continue

        # in_think değilken açılış arıyoruz
        m_open = _THINK_OPEN_RE.search(text, i)
        if not m_open:
            out.append(text[i:])
            break

        # Açılışa kadar olan normal kısmı ekle
        out.append(text[i:m_open.start()])
        # Açılışı tüket, think moduna gir
        i = m_open.end()
        in_think = True

    return "".join(out), in_think



async def run_local_chat(
    username: str,
    message: str,
    analysis: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    memory_hint: Optional[str] = None
) -> str:
    """Yerel model (Bela / Gemma) ile sohbet."""
    
    # 1. GPU Erişim İzni İste (Bu satır sistemi kilitlenmekten kurtarır)
    await GPUManager.request_gemma_access()

    base_url = settings.OLLAMA_BASE_URL.rstrip("/")
    model_name = settings.OLLAMA_GEMMA_MODEL
    
 
    identity = get_ai_identity()
    system_prompt = f""" Senin ismin {identity.display_name}. – {identity.product_family}.
KİMLİK: Senin ile konuşan kişinin ismi {identity.developer_name}. {identity.short_intro}

AMAÇ:
Kullanıcıya doğru, pratik, uygulanabilir ve bağlama sadık şekilde yardım et.

TEMEL KURALLAR:
1) İç düşünce, akıl yürütme, analiz, plan veya “think/thinking” içeriği yazma. Sadece nihai cevabı yaz.
2) Yanıt dili Türkçe. Kullanıcıya “sen” diye hitap et.
3) Uydurma bilgi üretme. Emin değilsen “emin değilim” de ve net olarak hangi bilgiye ihtiyaç olduğunu söyle.
4) Gereksiz uzatma yapma; ama kullanıcı teknik soru soruyorsa eksiksiz ve hatasız, çalışır çözüm ver.
5) Aynı soruyu kullanıcıya tekrar tekrar sorma. Eksik bilgi gerekiyorsa tek seferde, maddeler halinde iste.
6) Kullanıcıdaki bağlamı (geçmiş mesajlar + aşağıdaki bağlam blokları) dikkate al; çelişki varsa bunu belirt.

ÇIKTI STANDARTLARI (Kalite):
- Önce sonucu söyle, sonra kısa gerekçe/uygulama adımlarını ver.
- Kod veriyorsan: minimal ama production-uygun, hata yakalama içeren, net isimlendirmeli olsun.
- Liste gerekiyorsa maddelerle yaz; tablo gerektiğinde tablo kullan.

SOHBET GEÇMİŞİ VE BAĞLAM:
Aşağıdaki konuşma geçmişini ve sağlanan bağlamı hatırla; kullanıcı mesajını bu bağlama göre yanıtla.
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content") or msg.get("text") or ""
            if content:
                messages.append({"role": role, "content": content})
    
    user_content = message
    if memory_hint:
        user_content = f"{memory_hint}\n\n{message}"

    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model_name,
        "stream": False,  # Akış istiyorsanız True yapın, API yanıtı için False
        "messages": messages,
        "options": {
            # --- BELLEK YÖNETİMİ (8GB VRAM OPTİMİZASYONU) ---
            # Q4 model ~5.2GB yer kaplar. 8192 context ~2GB harcar.
            # Toplam ~7.2GB ile kartınıza tam sığar.
            "num_ctx": 8192, 

            # --- YARATICILIK VE ZEKA (QWEN TUNING) ---
            # Qwen 0.8'de bazen saçmalar. 0.7 en dengeli (Stable/Creative) noktadır.
            "temperature": 0.7, 
            
            # Kelime havuzunu 40 ile sınırlamak, Türkçe'deki anlamsız heceleri eler.
            "top_k": 40,        
            "top_p": 0.90,      
            
            # --- TEKRAR VE DİL BİLGİSİ ---
            # Qwen Türkçe ekleri sever ama bazen takılır. 1.15 bunu keser.
            # Daha düşüğü (1.1) döngüye sokabilir, daha yükseği (1.2) yaratıcılığı öldürür.
            "repeat_penalty": 1.15, 
            
            # Gereksiz/düşük olasılıklı tokenları budamak için modern standart.
            "min_p": 0.05,      

            # --- KRİTİK QWEN MİMARİSİ AYARI (OLMAZSA OLMAZ) ---
            # Gemma'da buna gerek yoktu ama Qwen "ChatML" formatındadır.
            # Eğer bu STOP tokenları eklemezseniz, model cevabı bitirir bitirmez
            # "<|im_start|>user" yazıp kendi kendine sizin yerinize konuşmaya başlar.
            "stop": ["<|im_start|>", "<|im_end|>"] 
        },
    }

    try:
        logger.info(f"[LOCAL_CHAT] Async istek: {model_name} user={username}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        msg = data.get("message", {}) if isinstance(data, dict) else {}
        content = msg.get("content") or ""

        if not content:
            return "(BELA) Sessizlik..."

        cleaned, _ = strip_think_stateful(content, in_think=False)
        cleaned = strip_think_blocks(cleaned).strip()
        
        # YENİ: Gelişmiş formatlama uygula
        formatted = full_post_process(cleaned)
        
        # DEBUG: Formatlanmış cevabı log'la
        logger.info(f"[OLLAMA_FORMATTED] First 200 chars: {formatted[:200]}")
        
        return enforce_model_identity("local", formatted)


    except httpx.TimeoutException:
        logger.error("[LOCAL_CHAT] Zaman aşımı (Timeout).")
        return "(BELA) Çok düşündüm ama toparlayamadım. Tekrar eder misin?"
    except Exception as e:
        logger.error(f"[LOCAL_CHAT] Bağlantı hatası: {e}")
        return "(BELA) Beynim (GPU) şu an yanıt vermiyor. Lütfen Ollama'yı kontrol et."


async def run_local_chat_stream(
    username: str,
    message: str,
    analysis: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    memory_hint: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Yerel model (Bela / Gemma) ile streaming sohbet."""

    await GPUManager.request_gemma_access()

    base_url = settings.OLLAMA_BASE_URL.rstrip("/")
    model_name = settings.OLLAMA_GEMMA_MODEL

    identity = get_ai_identity()
    system_prompt = f""" Senin ismin {identity.display_name}. – {identity.product_family}.
KİMLİK: Senin sahibinin ismi{identity.developer_name}. {identity.short_intro}

AMAÇ:
Kullanıcıya doğru, pratik, uygulanabilir ve bağlama sadık şekilde yardım et.

TEMEL KURALLAR:
1) İç düşünce, akıl yürütme, analiz, plan veya “think/thinking” içeriği yazma. Sadece nihai cevabı yaz.
2) Yanıt dili Türkçe. Kullanıcıya “sen” diye hitap et.
3) Uydurma bilgi üretme. Emin değilsen “emin değilim” de ve net olarak hangi bilgiye ihtiyaç olduğunu söyle.
4) Gereksiz uzatma yapma; ama kullanıcı teknik soru soruyorsa eksiksiz ve hatasız, çalışır çözüm ver.
5) Aynı soruyu kullanıcıya tekrar tekrar sorma. Eksik bilgi gerekiyorsa tek seferde, maddeler halinde iste.
6) Kullanıcıdaki bağlamı (geçmiş mesajlar + aşağıdaki bağlam blokları) dikkate al; çelişki varsa bunu belirt.

ÇIKTI STANDARTLARI (Kalite):
- Önce sonucu söyle, sonra kısa gerekçe/uygulama adımlarını ver.
- Kod veriyorsan: minimal ama production-uygun, hata yakalama içeren, net isimlendirmeli olsun.
- Liste gerekiyorsa maddelerle yaz; tablo gerektiğinde tablo kullan.

SOHBET GEÇMİŞİ VE BAĞLAM:
Aşağıdaki konuşma geçmişini ve sağlanan bağlamı hatırla; kullanıcı mesajını bu bağlama göre yanıtla.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content") or msg.get("text") or ""
            if content:
                messages.append({"role": role, "content": content})
    user_content = message
    if memory_hint:
        user_content = f"{memory_hint}\n\n{message}"

    messages.append({"role": "user", "content": user_content})


    payload = {
        "model": model_name,
        "stream": True,  # Akış istiyorsanız True yapın, API yanıtı için False
        "messages": messages,
        "options": {
            # --- BELLEK YÖNETİMİ (8GB VRAM OPTİMİZASYONU) ---
            # Q4 model ~5.2GB yer kaplar. 8192 context ~2GB harcar.
            # Toplam ~7.2GB ile kartınıza tam sığar.
            "num_ctx": 8192, 

            # --- YARATICILIK VE ZEKA (QWEN TUNING) ---
            # Qwen 0.8'de bazen saçmalar. 0.7 en dengeli (Stable/Creative) noktadır.
            "temperature": 0.7, 
            
            # Kelime havuzunu 40 ile sınırlamak, Türkçe'deki anlamsız heceleri eler.
            "top_k": 40,        
            "top_p": 0.90,      
            
            # --- TEKRAR VE DİL BİLGİSİ ---
            # Qwen Türkçe ekleri sever ama bazen takılır. 1.15 bunu keser.
            # Daha düşüğü (1.1) döngüye sokabilir, daha yükseği (1.2) yaratıcılığı öldürür.
            "repeat_penalty": 1.15, 
            
            # Gereksiz/düşük olasılıklı tokenları budamak için modern standart.
            "min_p": 0.05,      

            # --- KRİTİK QWEN MİMARİSİ AYARI (OLMAZSA OLMAZ) ---
            # Gemma'da buna gerek yoktu ama Qwen "ChatML" formatındadır.
            # Eğer bu STOP tokenları eklemezseniz, model cevabı bitirir bitirmez
            # "<|im_start|>user" yazıp kendi kendine sizin yerinize konuşmaya başlar.
            "stop": ["<|im_start|>", "<|im_end|>"] 
        },
    }
    try:
        logger.info(f"[LOCAL_CHAT_STREAM] Async stream istek: {model_name} user={username}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                
                # YENİ HİBRİT YAKLAŞIM: Önce tüm cevabı topla
                full_response = ""
                in_think = False
                
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    
                    msg = data.get("message") or {}
                    content = msg.get("content") or ""

                    if content:
                        # Düşünce bloklarını filtrele
                        cleaned_chunk, in_think = strip_think_stateful(content, in_think=in_think)
                        cleaned_chunk = strip_think_blocks(cleaned_chunk)
                        
                        if cleaned_chunk:
                            full_response += cleaned_chunk

                    if data.get("done"):
                        break
                
                # Tüm cevap toplandı, şimdi formatla
                formatted_response = full_post_process(full_response.strip())
                final_response = enforce_model_identity("local", formatted_response)
                
                # Kelime bazlı stream et (hızlı ve akıcı)
                words = final_response.split(' ')
                for i, word in enumerate(words):
                    if i < len(words) - 1:
                        yield word + ' '
                    else:
                        yield word

    except httpx.TimeoutException:
        yield "(BELA) Zaman aşımı: Ollama yanıt vermedi."
    except Exception as e:
        logger.error(f"[LOCAL_CHAT_STREAM] Bağlantı hatası: {e}")
        yield "(BELA) Beynim (GPU) şu an yanıt vermiyor. Lütfen Ollama'yı kontrol et."

