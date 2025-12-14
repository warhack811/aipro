"""
Response Orchestrator - İşlem Koordinatörü
==========================================

Tüm enhancement modüllerini doğru sırayla çalıştırır.
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResponseOrchestrator:
    """
    Response enhancement pipeline'ı yöneten orkestratör.
    
    İşlem sırası (DOĞRU SIRA ÇOK ÖNEMLİ!):
    1. Temel temizlik (thinking blocks, fazla boşluk)
    2. Kod bloğu düzeltmeleri
    3. Markdown formatlaması
    4. Smart shaping (yapılandırma)
    5. Visual beautification (emoji, callout)
    6. Final cleanup
    """
    
    def __init__(self, plugin):
        self.plugin = plugin
        logger.info("[ORCHESTRATOR] Initialized")
    
    def process(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cevabı tam pipeline'dan geçir.
        
        Args:
            text: Ham model cevabı
            context: Bağlam (user_message, persona, vb.)
            options: İşlem seçenekleri
            
        Returns:
            İşlenmiş ve zenginleştirilmiş cevap
        """
        if not text:
            return ""
        
        context = context or {}
        options = options or {}
        
        original_len = len(text)
        user_message = context.get('user_message', '')
        
        logger.debug(f"[ORCHESTRATOR] Processing response, length={original_len}")
        
        # === STAGE 0: ORIGINAL ===
        logger.info(f"[POST_STAGE] stage=0_original preview={text[:200] if text else 'N/A'}...")
        
        # === STAGE 1: TEMEL TEMİZLİK ===
        text = self._basic_cleanup(text)
        logger.info(f"[POST_STAGE] stage=1_cleanup preview={text[:200] if text else 'N/A'}...")
        
        # === STAGE 2: KOD BLOĞU DÜZELTMELERİ ===
        text = self._fix_code_blocks(text)
        logger.info(f"[POST_STAGE] stage=2_code_fix preview={text[:200] if text else 'N/A'}...")
        
        # === STAGE 3: MARKDOWN FORMATLAMASI ===
        if options.get('enable_markdown', True):
            text = self._apply_markdown_formatting(text)
            logger.info(f"[POST_STAGE] stage=3_markdown preview={text[:200] if text else 'N/A'}...")
        
        # === STAGE 4: SMART SHAPING (Markdown'dan SONRA!) ===
        shape_mode = 'none'
        if options.get('enable_smart_shaping', True) and user_message:
            text, shape_mode, shape_reason = self.plugin.answer_shaper.shape(
                text, user_message, mode='auto'
            )
            logger.info(f"[POST_STAGE] stage=4_shaping mode={shape_mode} reason={shape_reason} preview={text[:200] if text else 'N/A'}...")
        
        # === STAGE 5: VISUAL BEAUTIFICATION ===
        if options.get('enable_beautification', True):
            text = self.plugin.visual_beautifier.beautify(text, options)
            logger.info(f"[POST_STAGE] stage=5_beautify preview={text[:200] if text else 'N/A'}...")
        
        # === STAGE 6: FINAL CLEANUP ===
        text = self._final_cleanup(text)
        logger.info(f"[POST_STAGE] stage=6_final preview={text[:200] if text else 'N/A'}...")
        
        final_len = len(text)
        logger.info(
            f"[ORCHESTRATOR] Complete: {original_len} -> {final_len} chars, "
            f"shape={shape_mode}"
        )
        
        return text
    
    def _basic_cleanup(self, text: str) -> str:
        """Temel temizlik işlemleri"""
        import re

        # Thinking bloklarını kaldır
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Fazla boşlukları temizle
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Satır başı/sonu boşlukları
        lines = text.split('\n')
        cleaned = [line.strip() for line in lines]
        text = '\n'.join(cleaned)
        
        # Tekrarlayan noktalama
        text = re.sub(r'\.{4,}', '...', text)
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)
        
        return text
    
    def _fix_code_blocks(self, text: str) -> str:
        """Kod bloğu düzeltmeleri"""
        import re

        # [CODE_BLOCK_{}] placeholder'larını temizle (model bazen bunu kullanıyor)
        placeholder_patterns = [
            r'\[CODE_BLOCK_\{?\}?\]',  # [CODE_BLOCK_{}] veya [CODE_BLOCK_{}]
            r'\[CODE_BLOCK_\d+\]',     # [CODE_BLOCK_0], [CODE_BLOCK_1], vb.
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, text):
                text = re.sub(pattern, '', text)
                logger.warning("[CODE_BLOCK] Placeholder bulundu ve kaldırıldı")
        
        # === KRİTİK: Code fence format düzeltmeleri ===
        
        # 1. ```python ile kod aynı satırdaysa ayır: ```pythonprint() -> ```python\nprint()
        text = re.sub(
            r'```(\w+)([^\n`])',
            r'```\1\n\2',
            text
        )
        
        # 2. Kapanış ``` önünde newline yoksa ekle
        text = re.sub(
            r'([^\n])```',
            r'\1\n```',
            text
        )
        
        # 3. ```plaintext gibi garip dil etiketlerini düzelt
        text = re.sub(r'```plaintext', '```text', text)
        
        # Açık kalan kod bloklarını kapat
        code_block_count = text.count('```')
        if code_block_count % 2 != 0:
            text = text + '\n```'
        
        # Eksik dil etiketlerini tespit et ve ekle
        def detect_language(code):
            patterns = {
                'python': [r'\bdef\s+\w+', r'\bimport\s+', r'print\('],
                'javascript': [r'\bfunction\s+', r'\bconst\s+', r'console\.log'],
                'sql': [r'\bSELECT\s+', r'\bFROM\s+', r'\bWHERE\s+'],
                'bash': [r'#!/bin/bash', r'\bif\s+\['],
            }
            
            for lang, patterns_list in patterns.items():
                for pattern in patterns_list:
                    if re.search(pattern, code, re.IGNORECASE):
                        return lang
            return 'text'
        
        # Dil etiketi olmayan blokları düzelt
        pattern = r'```\n(.*?)```'
        def add_lang(match):
            code = match.group(1)
            lang = detect_language(code)
            return f'```{lang}\n{code}```'
        
        text = re.sub(pattern, add_lang, text, flags=re.DOTALL)
        
        logger.debug(f"[CODE_FIX] Code blocks normalized")
        return text
    
    def _apply_markdown_formatting(self, text: str) -> str:
        """Markdown formatlaması uygula"""
        import re

        # Başlıkları formatla
        lines = text.split('\n')
        formatted = []
        
        for line in lines:
            stripped = line.strip()
            
            # Zaten başlık
            if stripped.startswith('#'):
                formatted.append(line)
                continue
            
            # Büyük harf ve kısa satırlar (olası başlık)
            if (stripped.isupper() and 
                3 < len(stripped) < 60 and 
                not stripped.endswith(':')):
                formatted.append(f'## {stripped.title()}')
                continue
            
            formatted.append(line)
        
        text = '\n'.join(formatted)
        
        # Liste formatlaması
        text = re.sub(r'^([-*•])\s*', r'\1 ', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+\.)\s*', r'\1 ', text, flags=re.MULTILINE)
        
        # Inline formatlaması
        text = re.sub(r'\*\*\s+', '**', text)
        text = re.sub(r'\s+\*\*', '**', text)
        text = re.sub(r'`\s+', '`', text)
        text = re.sub(r'\s+`', '`', text)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Son düzeltmeler"""
        import re

        # Çoklu boş satırları azalt
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Boş parantezleri temizle
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\[\s*\]', '', text)
        
        # Noktalama öncesi gereksiz boşluk
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Noktalama sonrası boşluk ekle (eğer yoksa)
        text = re.sub(r'([.,!?;:])([A-ZÇĞİÖŞÜa-zçğıöşü])', r'\1 \2', text)
        
        return text.strip()