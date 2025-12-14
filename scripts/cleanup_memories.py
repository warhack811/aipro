"""
Hafıza Temizleme ve Kalite Kontrol Scripti
==========================================

Bu script:
1. Mevcut hafızaları analiz eder
2. Genel bilgi içeren yanlış hafızaları tespit eder
3. İsteğe bağlı olarak temizler

Kullanım:
    python scripts/cleanup_memories.py --dry-run  # Sadece göster
    python scripts/cleanup_memories.py --clean    # Temizle
"""

import re
import sys
from pathlib import Path

# Proje root'unu ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.memory_service import MemoryService

# Genel bilgi pattern'leri - bunları içeren hafızalar şüpheli
GENERAL_KNOWLEDGE_PATTERNS = [
    # Başkentler
    r"başkenti?\s+(ankara|istanbul|londra|paris|berlin|washington)",
    r"türkiye.{0,20}başkent",
    r"capital\s+of",
    
    # Matematik/Sayılar
    r"\d+\s*[\+\-\*/]\s*\d+\s*=\s*\d+",
    r"pi\s+sayısı",
    
    # Tanımlar
    r"(python|javascript|java)\s+(bir\s+)?(programlama\s+dili)",
    r"(ai|yapay zeka|artificial intelligence)\s+(nedir|demek)",
    
    # Tarihsel
    r"(atatürk|fatih)\s+.*(doğdu|öldü|fetih)",
    r"\d{4}[\'\']?(de|da|te|ta)\s+(fethedildi|doğdu|öldü)",
    
    # Güncel bilgi
    r"(dolar|euro|altın)\s+\d+",
    r"hava\s+(durumu|güneşli|yağmurlu|bulutlu)",
    
    # Çok genel - başlangıç pattern'leri
    r"^dünya\s+",
    r"^güneş\s+",
    r"^ay\s+bir",
]

# Kişisel bilgi pattern'leri - bunlar olumlu işaretler
PERSONAL_PATTERNS = [
    r"kullanıcı",  # "Kullanıcının adı..." formatı - EN ÖNEMLİ
    r"(benim\s+)?ad[ıi]m?\s+",
    r"(ben\s+)?\d+\s+yaşındayım",
    r"yaşıyorum|oturuyorum",
    r"(ben\s+)?(evli|bekar|nişanlı|boşanmış)",
    r"çocuğum\s+var",
    r"(kedim|köpeğim|kuşum|hayvanım)",
    r"(severim|sevmem|hoşlanırım|hoşlanmam)",
    r"(öğreniyorum|çalışıyorum|okuyorum)",
    r"mesleğ",
    r"hobil",
]


def is_general_knowledge(text: str) -> tuple[bool, str]:
    """
    Metnin genel bilgi olup olmadığını kontrol eder.
    
    Returns:
        (is_general, reason)
    """
    text_lower = text.lower()
    
    # Önce kişisel pattern kontrolü - bunlar varsa kesinlikle kaydet
    for pattern in PERSONAL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, "Kişisel bilgi içeriyor"
    
    # Genel bilgi pattern kontrolü
    for pattern in GENERAL_KNOWLEDGE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True, f"Pattern: {pattern[:40]}"
    
    # Uzunluk kontrolü - çok kısa hafızalar muhtemelen kişisel
    if len(text) < 30:
        return False, "Kısa metin"
    
    return False, "OK"


def analyze_all_memories(dry_run: bool = True):
    """Tüm hafızaları analiz et."""
    
    print("=" * 70)
    print("                     HAFIZA ANALİZİ")
    print("=" * 70)
    
    memory_service = MemoryService()
    
    # Tüm kullanıcıların hafızalarını al
    # ChromaDB'den direkt okuma
    collection = memory_service._get_collection()
    
    # Tüm kayıtları al
    result = collection.get(
        where={"is_active": True},
        include=["metadatas", "documents"]
    )
    
    if not result or not result.get("ids"):
        print("\n📭 Hiç hafıza kaydı bulunamadı.")
        return
    
    ids = result["ids"]
    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])
    
    suspicious_count = 0
    personal_count = 0
    total_count = len(ids)
    to_delete = []
    
    print(f"\n📊 Toplam {total_count} hafıza kaydı bulundu.\n")
    
    for i, (mem_id, text, meta) in enumerate(zip(ids, documents, metadatas)):
        if not text:
            continue
            
        is_general, reason = is_general_knowledge(text)
        
        if is_general:
            suspicious_count += 1
            to_delete.append(mem_id)
            
            user_id = meta.get("user_id", "?")
            category = meta.get("topic", meta.get("category", "?"))
            importance = meta.get("importance", "?")
            
            print(f"🔴 ŞÜPHELİ [{suspicious_count}]")
            print(f"   ID: {mem_id}")
            print(f"   User: {user_id}")
            print(f"   Metin: {text[:80]}{'...' if len(text) > 80 else ''}")
            print(f"   Sebep: {reason}")
            print(f"   Kategori: {category} | Önem: {importance}")
            print()
        else:
            personal_count += 1
            if not dry_run:
                # Sadece clean modunda göster
                pass
    
    print("=" * 70)
    print(f"📊 SONUÇ:")
    print(f"   ✅ Kişisel (geçerli): {personal_count}")
    print(f"   🔴 Şüpheli (genel bilgi): {suspicious_count}")
    print(f"   📝 Toplam: {total_count}")
    print("=" * 70)
    
    if not dry_run and to_delete:
        print(f"\n⚠️  {len(to_delete)} hafıza SİLİNECEK...")
        confirm = input("Devam etmek istiyor musunuz? (evet/hayır): ")
        
        if confirm.lower() == "evet":
            deleted = 0
            
            for mem_id in to_delete:
                try:
                    memory_service.delete_memory(mem_id)
                    deleted += 1
                    print(f"✅ Silindi: {mem_id}")
                except Exception as e:
                    print(f"❌ Hata: {mem_id} - {e}")
            
            print(f"\n✅ {deleted} hafıza silindi!")
        else:
            print("İptal edildi.")
    elif dry_run and to_delete:
        print(f"\n💡 Dry-run modu. {len(to_delete)} hafızayı silmek için:")
        print("   python scripts/cleanup_memories.py --clean")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Hafıza temizleme scripti")
    parser.add_argument("--dry-run", action="store_true", help="Sadece analiz yap, silme")
    parser.add_argument("--clean", action="store_true", help="Şüpheli hafızaları sil")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.clean:
        args.dry_run = True  # Varsayılan dry-run
    
    analyze_all_memories(dry_run=not args.clean)


if __name__ == "__main__":
    main()
