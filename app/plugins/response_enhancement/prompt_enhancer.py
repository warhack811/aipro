"""
Prompt Enhancer - Gelişmiş Prompt Mühendisliği
================================================

Model'e daha iyi formatlama talimatları vererek cevap kalitesini artırır.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptEnhancer:
    """
    System prompt'lara profesyonel formatlama talimatları ekler.
    
    Büyük chatbot'ların (ChatGPT, Claude, Gemini) kullandığı teknikleri uygular:
    - Yapılandırılmış cevap formatı
    - Görsel zenginlik (emoji, tablo, liste)
    - Kod bloğu standartları
    - Kalite kontrol kuralları
    """
    
    FORMATTING_INSTRUCTIONS = """

📝 **CEVAP FORMATI VE KALİTE KURALLARI:**

1. **YAPILANDIRMA:**
   - Her cevabı düzenli yapılandır: giriş, ana içerik, sonuç
   - Karmaşık konularda başlıklar kullan (##, ###)
   - Önemli noktaları **kalın** ile vurgula
   - Uzun cevaplarda özet ile başla, sonra detaylandır

2. **KOD BLOKLARI:**
   - Tüm kod örnekleri MUTLAKA ```dil formatında
   - Dil etiketini belirt (python, javascript, sql, vb.)
   - Kod bloğu üstüne ne yaptığını kısaca yaz
   - İnline kod için `backtick` kullan

3. **LİSTELER VE TABLOLAR:**
   - Adım adım işlemler için numaralı liste (1., 2., 3.)
   - Özellikler/seçenekler için bullet list (-, *)
   - Karşılaştırmalarda markdown tablo kullan
   - İç içe listelerde girinti kullan (2 boşluk)

4. **GÖRSEL ZENGİNLİK:**
   - Uygun yerlerde emoji kullan ama abartma (max 5-6)
   - Önemli uyarılar için callout box: 💡, ⚠️, ✅
   - Uzun cevaplarda bölüm ayırıcı (---) ekle
   - Alıntı için > karakteri kullan

5. **KALİTE STANDARTLARI:**
   - İlk paragraf MUTLAKA soruyu özetle ve ana cevabı ver
   - Teknik terimleri açıkla ama basit tut
   - Soyut kalmak yerine ÖRNEK ver
   - 'Evet', 'Hayır' gibi tek kelimelik cevap yasak
   - Her cevap en az 3 cümle içermeli
   - Bilmediğinde dürüstçe söyle, uydurma

6. **ÖZEL DURUMLAR:**
   - Nasıl soruları → Adım adım numaralı liste
   - Karşılaştırma → Markdown tablo + özet
   - Kod istekleri → Kod önce, açıklama sonra
   - Liste istekleri → Düzenli bullet/numbered list
"""

    COMPARISON_FORMAT = """
   
**Karşılaştırmalarda tablo formatı kullan:**

| Özellik | Seçenek A | Seçenek B |
|---------|-----------|-----------|
| [Özellik 1] | [Değer] | [Değer] |
| [Özellik 2] | [Değer] | [Değer] |

Tablo altında kısa özet ekle.
"""

    STEP_FORMAT = """

**Adım adım açıklamalarda format:**

1. **[Başlık]**: Kısa açıklama
2. **[Başlık]**: Kısa açıklama
3. **[Başlık]**: Kısa açıklama

Her adımda ne yapılacağını net söyle.
"""

    CODE_FORMAT = """

**Kod örneklerinde format:**

**[Ne yaptığını açıkla]:**
```dil
[kod buraya]
```

Kod altında önemli noktaları açıkla.
"""

    def __init__(self):
        self.enabled = True
        logger.info("[PROMPT_ENHANCER] Initialized")
    
    def enhance(
        self,
        base_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Base prompt'a formatlama talimatları ekle.
        
        Args:
            base_prompt: Orijinal system prompt
            context: Bağlam bilgisi
            
        Returns:
            Zenginleştirilmiş prompt
        """
        if not self.enabled:
            return base_prompt
        
        context = context or {}
        user_message = context.get("user_message", "")
        
        # Temel formatlama talimatları
        enhanced = base_prompt + self.FORMATTING_INSTRUCTIONS
        
        # Kullanıcı mesajına göre özel format ekle
        if user_message:
            msg_lower = user_message.lower()
            
            # Karşılaştırma sorusu
            if any(x in msg_lower for x in ['karşılaştır', 'fark', 'hangisi', 'vs', 'versus']):
                enhanced += self.COMPARISON_FORMAT
            
            # Adım adım soru
            elif any(x in msg_lower for x in ['nasıl', 'adım adım', 'kurulum', 'yap']):
                enhanced += self.STEP_FORMAT
            
            # Kod sorusu
            elif any(x in msg_lower for x in ['kod', 'code', 'örnek', 'fonksiyon']):
                enhanced += self.CODE_FORMAT
        
        logger.debug(f"[PROMPT_ENHANCER] Enhanced prompt length: {len(enhanced)}")
        return enhanced
    
    def get_quality_rules(self) -> str:
        """Kalite kurallarını döndür (test amaçlı)"""
        return self.FORMATTING_INSTRUCTIONS