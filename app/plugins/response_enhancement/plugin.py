"""
Response Enhancement Plugin - Ana Modül
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResponseEnhancementPlugin:
    """
    Profesyonel cevap formatlaması ve zenginleştirme plugin'i.
    
    Bu plugin, AI cevaplarını büyük chatbot'lar (ChatGPT, Claude, Gemini)
    seviyesine çıkarmak için gelişmiş formatlamalar uygular.
    """
    
    def __init__(self):
        self.name = "response_enhancement"
        self.version = "1.0.0"
        self.description = "Professional response formatting and enhancement"
        self._enabled = True
        
        # Modülleri lazy load edeceğiz
        self._prompt_enhancer = None
        self._answer_shaper = None
        self._visual_beautifier = None
        self._orchestrator = None
        
        logger.info(f"[{self.name.upper()}] Plugin initialized v{self.version}")
    
    def is_enabled(self) -> bool:
        """Plugin aktif mi?"""
        return self._enabled
    
    def enable(self):
        """Plugin'i aktif et"""
        self._enabled = True
        logger.info(f"[{self.name.upper()}] Plugin enabled")
    
    def disable(self):
        """Plugin'i devre dışı bırak"""
        self._enabled = False
        logger.info(f"[{self.name.upper()}] Plugin disabled")
    
    @property
    def prompt_enhancer(self):
        """Lazy load prompt enhancer"""
        if self._prompt_enhancer is None:
            from app.plugins.response_enhancement.prompt_enhancer import PromptEnhancer
            self._prompt_enhancer = PromptEnhancer()
        return self._prompt_enhancer
    
    @property
    def answer_shaper(self):
        """Lazy load answer shaper"""
        if self._answer_shaper is None:
            from app.plugins.response_enhancement.smart_shaper import SmartAnswerShaper
            self._answer_shaper = SmartAnswerShaper()
        return self._answer_shaper
    
    @property
    def visual_beautifier(self):
        """Lazy load visual beautifier"""
        if self._visual_beautifier is None:
            from app.plugins.response_enhancement.visual_beautifier import VisualBeautifier
            self._visual_beautifier = VisualBeautifier()
        return self._visual_beautifier
    
    @property
    def orchestrator(self):
        """Lazy load orchestrator"""
        if self._orchestrator is None:
            from app.plugins.response_enhancement.orchestrator import ResponseOrchestrator
            self._orchestrator = ResponseOrchestrator(self)
        return self._orchestrator
    
    def enhance_prompt(
        self,
        base_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Prompt'u zenginleştir - Modele daha iyi formatlama talimatları ekle.
        
        Args:
            base_prompt: Orijinal system prompt
            context: Bağlam bilgisi (user_message, persona, vb.)
            
        Returns:
            Zenginleştirilmiş prompt
        """
        if not self._enabled:
            return base_prompt
        
        return self.prompt_enhancer.enhance(base_prompt, context)
    
    def process_response(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Model cevabını işle ve zenginleştir.
        
        Args:
            text: Model'in ham cevabı
            context: Bağlam (user_message, persona, vb.)
            options: İşleme seçenekleri
            
        Returns:
            İşlenmiş ve zenginleştirilmiş cevap
        """
        if not self._enabled:
            return text
        
        return self.orchestrator.process(text, context, options)
    
    def get_info(self) -> Dict[str, Any]:
        """Plugin bilgilerini döndür"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self._enabled,
            "features": [
                "Advanced prompt engineering",
                "Smart answer structuring",
                "Visual beautification",
                "Code block enhancement",
                "Markdown automation",
                "Table generation",
                "Emoji & callout boxes"
            ]
        }