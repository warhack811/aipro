"""
Chat Modülü
===========

Sohbet işleme mantığını yönetir. Kullanıcı mesajlarını alır,
uygun aksiyonu belirler ve yanıt üretir.

Modüller:
    - processor: Ana sohbet işleme akışı (process_chat_message)
    - decider: Mesaj analizi ve aksiyon kararı (GROQ_REPLY, IMAGE, INTERNET vb.)
    - answerer: Groq API ile yanıt üretimi
    - search: İnternet araması işlemleri

Akış:
    1. Kullanıcı mesajı gelir
    2. Decider mesajı analiz eder (ne yapılacağına karar verir)
    3. Processor uygun servisi çağırır (Groq, Ollama, Image, Internet)
    4. Yanıt formatlanır ve döndürülür
"""
