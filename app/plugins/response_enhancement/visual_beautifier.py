"""
Visual Beautifier - Görsel Zenginleştirme
=========================================

Cevapları görsel olarak zenginleştirir:
- Emoji ekleme
- Callout box'lar
- Bölüm ayırıcılar
- Kod bloğu başlıkları
- Özet kutuları
"""
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class VisualBeautifier:
    """
    Profesyonel görsel zenginleştirme modülü.
    
    Büyük chatbot'ların kullandığı görsel teknikleri uygular.
    """
    
    # Emoji eşleştirmeleri
    EMOJI_MAP = {
        # Başlık tipleri
        'kurulum': '⚙️',
        'setup': '⚙️',
        'install': '⚙️',
        'başlangıç': '🚀',
        'giriş': '🚀',
        'introduction': '🚀',
        'örnek': '💡',
        'example': '💡',
        'demo': '💡',
        'sonuç': '✅',
        'result': '✅',
        'conclusion': '✅',
        'hata': '❌',
        'error': '❌',
        'problem': '❌',
        'uyarı': '⚠️',
        'warning': '⚠️',
        'dikkat': '⚠️',
        'ipucu': '💡',
        'tip': '💡',
        'hint': '💡',
        'özellik': '⭐',
        'feature': '⭐',
        'kullanım': '📚',
        'usage': '📚',
        'kod': '💻',
        'code': '💻',
        'script': '💻',
    }
    
    # Callout türleri
    CALLOUT_TYPES = {
        'ipucu': ('💡', 'İpucu'),
        'tip': ('💡', 'Tip'),
        'uyarı': ('⚠️', 'Uyarı'),
        'warning': ('⚠️', 'Warning'),
        'dikkat': ('🚨', 'Dikkat'),
        'danger': ('🚨', 'Danger'),
        'başarılı': ('✅', 'Başarılı'),
        'success': ('✅', 'Success'),
        'bilgi': ('ℹ️', 'Bilgi'),
        'info': ('ℹ️', 'Info'),
        'not': ('📝', 'Not'),
        'note': ('📝', 'Note'),
    }
    
    def __init__(self):
        self.enabled = True
        self.add_emojis = True
        self.add_callouts = True
        self.add_separators = True
        self.enhance_code_blocks = True
        self.create_summary_box = True
        
        logger.info("[VISUAL_BEAUTIFIER] Initialized")
    
    def beautify(
        self,
        text: str,
        options: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        Metni görsel olarak zenginleştir.
        
        Args:
            text: Ham metin
            options: Özelleştirme seçenekleri
            
        Returns:
            Zenginleştirilmiş metin
        """
        if not self.enabled:
            return text
        
        options = options or {}
        
        # Özet kutusu (en başta)
        if options.get('create_summary_box', self.create_summary_box):
            text = self._create_summary_box(text)
        
        # Başlıklara emoji ekle
        if options.get('add_emojis', self.add_emojis):
            text = self._add_heading_emojis(text)
        
        # Callout box'lar oluştur
        if options.get('add_callouts', self.add_callouts):
            text = self._create_callout_boxes(text)
        
        # Kod bloğu başlıkları
        if options.get('enhance_code_blocks', self.enhance_code_blocks):
            text = self._enhance_code_blocks(text)
        
        # Bölüm ayırıcıları (uzun cevaplarda)
        if options.get('add_separators', self.add_separators):
            text = self._add_visual_separators(text)
        
        return text
    
    def _create_summary_box(self, text: str) -> str:
        """İlk paragrafı özet kutusu yap"""
        lines = text.split('\n')
        
        # İlk paragrafı bul
        first_para = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                first_para.append(line)
            elif first_para:  # Boş satır geldi, paragraf bitti
                break
        
        if not first_para or len(first_para) > 5:  # Çok uzunsa yapma
            return text
        
        # İlk paragrafı özet kutusu yap
        summary = '\n'.join(first_para)
        remaining_lines = lines[len(first_para):]
        
        # Kalan metinde özeti çıkar
        remaining = '\n'.join(remaining_lines)
        
        return f'> 📌 **Özet:** {summary}\n\n{remaining}'
    
    def _add_heading_emojis(self, text: str) -> str:
        """Başlıklara uygun emoji ekle"""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            
            # Markdown başlık mı?
            if re.match(r'^#{1,6}\s+', stripped):
                # Zaten emoji var mı?
                if re.search(r'[😀-🙏🚀-🛿⚠-⚡💀-💿]', stripped):
                    result.append(line)
                    continue
                
                # Uygun emoji bul
                line_lower = stripped.lower()
                for keyword, emoji in self.EMOJI_MAP.items():
                    if keyword in line_lower:
                        # Başlığa emoji ekle
                        line = re.sub(r'^(#{1,6}\s+)', rf'\1{emoji} ', line)
                        break
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _create_callout_boxes(self, text: str) -> str:
        """Callout box'lar oluştur"""
        lines = text.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            matched = False
            
            # Callout pattern ara
            for key, (emoji, label) in self.CALLOUT_TYPES.items():
                # "İpucu: Bu önemli" veya "Tip: Important"
                pattern = rf'^({key}|{label})\s*:?\s*(.+)$'
                match = re.match(pattern, stripped, re.IGNORECASE)
                
                if match:
                    content = match.group(2)
                    # Zaten emoji yoksa ekle
                    if emoji not in stripped:
                        result.append(f'{emoji} **{label}:** {content}')
                    else:
                        result.append(line)
                    matched = True
                    break
            
            if not matched:
                result.append(line)
        
        return '\n'.join(result)
    
    def _enhance_code_blocks(self, text: str) -> str:
        """Kod bloklarına başlık ve açıklama ekle"""
        def add_title(match):
            lang = match.group(1) or 'code'
            code = match.group(2)
            
            # Dil etiketini güzelleştir
            lang_display = {
                'python': 'Python',
                'javascript': 'JavaScript',
                'js': 'JavaScript',
                'typescript': 'TypeScript',
                'ts': 'TypeScript',
                'java': 'Java',
                'cpp': 'C++',
                'c': 'C',
                'sql': 'SQL',
                'bash': 'Bash',
                'sh': 'Shell',
                'html': 'HTML',
                'css': 'CSS',
                'json': 'JSON',
                'yaml': 'YAML',
                'xml': 'XML',
            }.get(lang.lower(), lang.upper())
            
            # Başlık ekle
            title = f'**💻 {lang_display} Kodu:**\n'
            return f'{title}```{lang}\n{code}```'
        
        pattern = r'```(\w*)\n(.*?)```'
        return re.sub(pattern, add_title, text, flags=re.DOTALL)
    
    def _add_visual_separators(self, text: str) -> str:
        """Uzun cevaplara görsel ayırıcılar ekle"""
        lines = text.split('\n')
        
        # Çok uzun değilse gerek yok
        if len(lines) < 20:
            return text
        
        result = []
        empty_line_count = 0
        line_count = 0
        
        for line in lines:
            result.append(line)
            line_count += 1
            
            if not line.strip():
                empty_line_count += 1
            else:
                empty_line_count = 0
            
            # Her 15 satırda bir ayırıcı ekle (ama boş satırdan sonra)
            if line_count % 15 == 0 and empty_line_count == 1:
                result.append('')
                result.append('---')
                result.append('')
        
        return '\n'.join(result)
    
    def add_spacing(self, text: str) -> str:
        """Paragraf arası boşlukları optimize et"""
        lines = text.split('\n')
        result = []
        prev_type = None
        
        for line in lines:
            stripped = line.strip()
            
            # Satır tipini belirle
            if not stripped:
                line_type = 'empty'
            elif stripped.startswith('#'):
                line_type = 'heading'
            elif re.match(r'^[-*•]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                line_type = 'list'
            elif stripped.startswith('```'):
                line_type = 'code'
            elif stripped.startswith('|'):
                line_type = 'table'
            else:
                line_type = 'text'
            
            # Başlık öncesi boşluk
            if line_type == 'heading' and prev_type and prev_type != 'empty':
                result.append('')
            
            result.append(line)
            prev_type = line_type
        
        # Çoklu boş satırları azalt
        final = '\n'.join(result)
        final = re.sub(r'\n{4,}', '\n\n\n', final)
        
        return final