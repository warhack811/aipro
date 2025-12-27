"""
Memory Modülü
=============

Hafıza ve bilgi depolama sistemlerini yönetir.

Modüller:
    - store: Kullanıcı hafızası (kişisel bilgiler, tercihler)
    - rag: RAG (Retrieval Augmented Generation) doküman deposu
    - conversation: Sohbet geçmişi yönetimi

Teknoloji:
    - ChromaDB: Vektör veritabanı (semantik arama)
    - SQLite: İlişkisel veri (kullanıcılar, sohbetler)

Hafıza Türleri:
    - Kısa vadeli: Aktif sohbet bağlamı
    - Uzun vadeli: Kalıcı kullanıcı bilgileri (ChromaDB)
    - RAG: Yüklenen dokümanlar (PDF, TXT)
"""
