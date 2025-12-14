"""
Smart Answer Shaper - Akıllı Cevap Yapılandırıcı
================================================

Model cevaplarını kullanıcı niyetine göre yapılandırır.
Mevcut answer_shaper.py'den çok daha gelişmiş.
"""
import re
import logging
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SmartAnswerShaper:
    """
    Gelişmiş cevap yapılandırıcı.
    
    Desteklenen modlar:
    - steps: Adım adım numaralı format
    - comparison: Karşılaştırma tablosu
    - table: Liste/özet tablosu
    - code_first: Kod önce, açıklama sonra
    - direct: Minimal yapılandırma
    """
    
    def __init__(self):
        self.enabled = True
        logger.info("[SMART_SHAPER] Initialized")
    
    def detect_intent(self, user_message: str) -> str:
        """
        Kullanıcı niyetini tespit et.
        
        Returns:
            'steps', 'comparison', 'table', 'code_first', 'direct'
        """
        msg_lower = user_message.lower()
        
        # COMPARISON - En yüksek öncelik
        comparison_keywords = [
            'karşılaştır', 'fark', 'farklar', 'farkı', 
            'vs', 'versus', 'veya', 'mi yoksa',
            'hangisi', 'hangisi daha', 'tercih',
            'artı eksi', 'avantaj dezavantaj',
            'pros cons', 'compare', 'difference'
        ]
        if any(kw in msg_lower for kw in comparison_keywords):
            return 'comparison'
        
        # STEPS - İkinci öncelik
        steps_keywords = [
            'nasıl', 'adım adım', 'adımlar', 'adımları',
            'kurulum', 'install', 'setup', 'kur',
            'yap', 'yapalım', 'oluştur', 'oluşturalım',
            'plan', 'planlama', 'roadmap', 'yol haritası',
            'sıra', 'sırayla', 'önce', 'sonra',
            'süreç', 'tutorial', 'guide'
        ]
        if any(kw in msg_lower for kw in steps_keywords):
            return 'steps'
        
        # TABLE - Liste/özet istekleri
        table_keywords = [
            'liste', 'listele', 'say', 'sırala',
            'tablo', 'özet', 'özetle',
            'list', 'summarize', 'top'
        ]
        word_count = len(msg_lower.split())
        if any(kw in msg_lower for kw in table_keywords):
            # Kısa sorular muhtemelen basit liste istiyor
            if word_count <= 15:
                return 'table'
        
        # CODE_FIRST - Kod istekleri
        code_keywords = [
            'kod', 'code', 'script', 'program',
            'örnek', 'example', 'demo',
            'fonksiyon', 'function', 'method',
            'class', 'sınıf', 'modül',
            'implement', 'uygula', 'yaz',
            'regex', 'sql', 'query'
        ]
        if any(kw in msg_lower for kw in code_keywords):
            return 'code_first'
        
        # Default
        return 'direct'
    
    def shape(
        self,
        text: str,
        user_message: str,
        mode: str = "auto"
    ) -> Tuple[str, str, str]:
        """
        Cevabı yapılandır.
        
        Args:
            text: Model'in ham cevabı
            user_message: Kullanıcının sorusu
            mode: 'auto' veya manuel mod
            
        Returns:
            (shaped_text, applied_mode, reason)
        """
        if not self.enabled:
            logger.debug("[SHAPER] Disabled")
            return text, 'none', 'disabled'
        
        # Debug: Gelen metin hakkında bilgi
        logger.info(f"[SHAPER] Input: len={len(text)}, user_msg={user_message[:50] if user_message else 'N/A'}...")
        
        # Zaten iyi yapılandırılmış mı kontrol et
        if self._is_well_structured(text):
            logger.info("[SHAPER] Skipped: already well structured")
            return text, 'none', 'already_structured'
        
        # Çok kısa cevaplar için minimal yapı (paragraf + bold)
        if len(text) < 50:
            logger.info(f"[SHAPER] Short response ({len(text)} chars), applying minimal")
            return self._shape_minimal(text), 'minimal', 'short_formatted'
        
        # Mod tespiti
        if mode == 'auto':
            detected_mode = self.detect_intent(user_message)
        else:
            detected_mode = mode
        
        # Kod bloklarını ayır (korumak için)
        code_blocks, text_without_code = self._extract_code_blocks(text)
        
        # Yapılandır
        if detected_mode == 'steps':
            shaped = self._shape_steps(text_without_code)
        elif detected_mode == 'comparison':
            shaped = self._shape_comparison(text_without_code, user_message)
        elif detected_mode == 'table':
            shaped = self._shape_table(text_without_code)
        elif detected_mode == 'code_first':
            if code_blocks:
                shaped = self._shape_code_first(text_without_code, code_blocks)
                return shaped, detected_mode, 'shaped'  # Kod zaten eklendi
            else:
                return text, 'none', 'no_code'
        elif detected_mode == 'direct':
            shaped = self._shape_direct(text_without_code)
        else:
            shaped = text_without_code
        
        # Kod bloklarını geri ekle
        final = self._restore_code_blocks(shaped, code_blocks)
        
        return final, detected_mode, 'shaped'
    
    def _is_well_structured(self, text: str) -> bool:
        """
        Cevap zaten iyi yapılandırılmış mı?
        
        Not: Daha gevşek kontrol - sadece gerçekten iyi yapılandırılmış cevapları atla.
        """
        # Başlık sayısı - sadece çok iyi yapılandırılmış ise
        headings = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
        if headings >= 3:  # 3+ başlık gerekli (eskiden 2 idi)
            logger.debug(f"[SHAPER] Well structured: {headings} headings")
            return True
        
        # Liste sayısı - daha yüksek eşik
        lists = len(re.findall(r'^\s*[-*•]\s|\s*\d+\.\s', text, re.MULTILINE))
        if lists >= 7:  # 7+ liste gerekli (eskiden 5 idi)
            logger.debug(f"[SHAPER] Well structured: {lists} list items")
            return True
        
        # Tablo var mı - daha yüksek eşik
        if text.count('|') >= 12:  # 12+ pipe karakteri (eskiden 8 idi)
            logger.debug(f"[SHAPER] Well structured: has table")
            return True
        
        # Kod bloğu sayısı - daha yüksek eşik
        code_blocks = text.count('```')
        if code_blocks >= 6:  # 3+ tam blok (eskiden 4 idi yani 2 blok)
            logger.debug(f"[SHAPER] Well structured: {code_blocks//2} code blocks")
            return True
        
        return False
    
    def _extract_code_blocks(self, text: str) -> Tuple[List[Tuple[str, str]], str]:
        """Kod bloklarını ayır"""
        pattern = r'```(\w*)\n(.*?)```'
        blocks = []
        
        for match in re.finditer(pattern, text, re.DOTALL):
            lang = match.group(1) or ''
            code = match.group(2)
            blocks.append((lang, code))
        
        # Placeholder ekle
        text_clean = re.sub(pattern, '[CODE_BLOCK_{}]', text, flags=re.DOTALL)
        return blocks, text_clean
    
    def _restore_code_blocks(self, text: str, blocks: List[Tuple[str, str]]) -> str:
        """Kod bloklarını geri koy"""
        # Tüm placeholder formatlarını bul ve düzelt
        placeholder_patterns = [
            r'\[CODE_BLOCK_\{?\}?\]',  # [CODE_BLOCK_{}] veya [CODE_BLOCK_{}]
            r'\[CODE_BLOCK_\d+\]',     # [CODE_BLOCK_0], [CODE_BLOCK_1], vb.
        ]
        
        # Önce numaralı placeholder'ları düzelt
        for i, (lang, code) in enumerate(blocks):
            placeholder = f'[CODE_BLOCK_{i}]'
            block = f'```{lang}\n{code}```' if lang else f'```\n{code}```'
            text = text.replace(placeholder, block, 1)
        
        # Kalan placeholder'ları (model tarafından eklenen) temizle
        for pattern in placeholder_patterns:
            text = re.sub(pattern, '', text)
        
        return text
    
    def _shape_steps(self, text: str) -> str:
        """Adım adım format"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) <= 2:
            return text
        
        # İlk satır özet
        summary = lines[0]
        
        # Diğerleri adım (max 10)
        steps = lines[1:11]
        
        result = [f"**Özet:** {summary}", ""]
        for i, step in enumerate(steps, 1):
            # Mevcut numarayı temizle
            step_clean = re.sub(r'^\d+[\.\)]\s*', '', step)
            result.append(f'{i}. **{step_clean}**')
        
        return '\n'.join(result)
    
    def _shape_comparison(self, text: str, user_message: str) -> str:
        """Karşılaştırma tablosu"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) < 4:
            return text
        
        # Seçenek isimlerini çıkar
        msg_lower = user_message.lower()
        options = []
        
        # "A vs B" pattern
        vs_match = re.search(r'(\w+)\s+(?:vs|versus|veya)\s+(\w+)', msg_lower)
        if vs_match:
            options = [vs_match.group(1).title(), vs_match.group(2).title()]
        else:
            options = ['Seçenek A', 'Seçenek B']
        
        # Tablo oluştur
        result = [
            f'### Karşılaştırma: {options[0]} vs {options[1]}',
            '',
            f'| Özellik | {options[0]} | {options[1]} |',
            '|---------|' + '-' * len(options[0]) + '|' + '-' * len(options[1]) + '|'
        ]
        
        # Satırları 2'şer ayır (ilk yarı A, ikinci yarı B)
        mid = len(lines) // 2
        for i in range(min(mid, 5)):  # Max 5 özellik
            feature = f'Özellik {i+1}'
            val_a = lines[i] if i < len(lines) else ''
            val_b = lines[mid + i] if mid + i < len(lines) else ''
            result.append(f'| {feature} | {val_a[:30]}... | {val_b[:30]}... |')
        
        return '\n'.join(result)
    
    def _shape_table(self, text: str) -> str:
        """Liste/özet tablosu"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) < 3:
            return text
        
        # Basit bullet list
        result = [lines[0], '']  # İlk satır başlık
        for line in lines[1:]:
            # Mevcut bullet'i temizle
            line_clean = re.sub(r'^[-*•]\s*', '', line)
            result.append(f'- {line_clean}')
        
        return '\n'.join(result)
    
    def _shape_code_first(self, text: str, code_blocks: List[Tuple[str, str]]) -> str:
        """Kod önce, açıklama sonra"""
        if not code_blocks:
            return text
        
        lang, code = code_blocks[0]
        
        # Açıklamayı al
        lines = [l.strip() for l in text.split('\n') if l.strip() and '[CODE_BLOCK' not in l]
        explanation = ' '.join(lines[:3])  # İlk 3 cümle
        
        # Format
        code_block = f'```{lang}\n{code}```' if lang else f'```\n{code}```'
        return f'**Kod Örneği:**\n\n{code_block}\n\n**Açıklama:** {explanation}'
    
    def _shape_direct(self, text: str) -> str:
        """Minimal format - intro + key points"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if len(lines) <= 2:
            return text
        
        intro = lines[0]
        points = lines[1:4]  # Max 3 nokta
        
        result = [intro, '']
        for point in points:
            point_clean = re.sub(r'^[-*•]\s*', '', point)
            result.append(f'- {point_clean}')
        
        return '\n'.join(result)
    
    def _shape_minimal(self, text: str) -> str:
        """
        Çok kısa cevaplar için minimal yapılandırma.
        
        Basit selamlama veya kısa cevaplar için bile düzgün paragraf yapısı sağlar.
        """
        text = text.strip()
        
        # Zaten bold/italik varsa dokunma
        if '**' in text or '*' in text:
            return text
        
        # Birden fazla cümle varsa ilk cümleyi bold yap
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) >= 2:
            # İlk cümleyi bold yap
            sentences[0] = f"**{sentences[0]}**"
            return ' '.join(sentences)
        
        # Tek cümle ise düzgün paragraf olarak döndür
        return text