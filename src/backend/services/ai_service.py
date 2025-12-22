"""
AI analysis service using Google Gemini
Migrated from: src/legacy/ai_analyzer.py
"""
import asyncio
import re
import structlog
from google import genai
from typing import Optional, Dict

from backend.config import config


logger = structlog.get_logger()


class AIService:
    """
    Service for AI-powered document analysis using Google Gemini
    """
    
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model = "gemini-2.5-flash"
        self.max_text_length = 30000  # Limit text for API
        
        if not self.api_key or "ВАШ" in self.api_key:
            logger.warning("gemini_api_key_not_configured")
    
    async def analyze_document(
        self,
        text: str,
        document_type: str,
        filename: str = ""
    ) -> Optional[Dict[str, str]]:
        """
        Analyze document text using Gemini AI
        
        Args:
            text: Document text content
            document_type: Type of document (bill, amendment, etc.)
            filename: Original filename for reference
            
        Returns:
            Dictionary with analysis text and generated filename
        """
        logger.info(
            "analyze_document",
            filename=filename,
            text_length=len(text),
            document_type=document_type
        )
        
        if not self.api_key or "ВАШ" in self.api_key:
            logger.error("api_key_not_configured")
            return None
        
        if not text or len(text) < 50:
            logger.warning("insufficient_text", filename=filename)
            return None
        
        try:
            # Create Gemini client
            client = genai.Client(api_key=self.api_key)
            
            # Truncate text if too long
            analysis_text = text[:self.max_text_length]
            
            # 1. Perform deep analysis
            analysis_prompt = self._build_analysis_prompt(analysis_text, filename)
            
            logger.info("sending_to_gemini", model=self.model)
            
            analysis_response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=analysis_prompt
            )
            
            if not analysis_response or not analysis_response.text:
                logger.error("empty_analysis_response")
                return None
            
            # 2. Generate filename based on analysis
            naming_prompt = self._build_naming_prompt(analysis_response.text)
            
            naming_response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=naming_prompt
            )
            
            if not naming_response or not naming_response.text:
                logger.warning("filename_generation_failed")
                generated_filename = "VISNOVOK_ANALYSIS.txt"
            else:
                # Clean filename
                clean_filename = naming_response.text.strip().replace(' ', '_')
                clean_filename = re.sub(r'[^\w\._-]', '', clean_filename).upper()
                generated_filename = f"VISNOVOK_{clean_filename}.txt"
            
            logger.info(
                "analysis_completed",
                filename=filename,
                generated_filename=generated_filename,
                analysis_length=len(analysis_response.text)
            )
            
            return {
                "analysis_text": analysis_response.text,
                "generated_filename": generated_filename
            }
            
        except Exception as e:
            logger.error(
                "analysis_failed",
                filename=filename,
                error=str(e)
            )
            return None
    
    def _build_analysis_prompt(self, text: str, filename: str) -> str:
        """Build comprehensive analysis prompt"""
        return (
            f"Проаналізуй наступний законопроєкт (файл: {filename}). "
            "Твій висновок має бути коротким, логічним і структурованим за пунктами:"
            "\n1. **Суть:** Коротка суть законопроєкту та його ціль."
            "\n2. **Автор та Репутація:** Яка особа/орган подала ідею закону? "
            "Стисла репутаційна довідка про цього автора (позитивна/негативна)."
            "\n3. **Корупційні ризики:** Чи може бути цей закон пов'язаний з корупцією? "
            "Поясни, чому (включаючи потенційні лазівки)."
            "\n4. **Вплив на Україну:** Наскільки сильно цей закон може вплинути на "
            "економіку/соціальну сферу України (високий, середній, низький) і чому."
            "\n5. **Плюси та Мінуси:** Головні переваги (Плюси) та недоліки (Мінуси)."
            f"\n\n--- ТЕКСТ ЗАКОНОПРОЄКТУ ---\n\n{text}"
        )
    
    def _build_naming_prompt(self, analysis_text: str) -> str:
        """Build filename generation prompt"""
        return (
            "Проаналізуй наданий висновок по законопроєкту. Створи коротку, змістовну назву для файлу. "
            "Назва має бути транслітерацією (українськими літерами латинкою), без пробілів, без спецсимволів. "
            "Почни відповідь ОДРАЗУ з назви файлу без розширення. Не пиши ніяких пояснень."
            f"\n\n--- АНАЛІЗ ---\n\n{analysis_text}"
        )
    
    async def analyze_bill(
        self,
        bill_number: str,
        documents_text: str
    ) -> Optional[Dict[str, str]]:
        """
        Analyze entire bill with all its documents
        
        Args:
            bill_number: Bill registration number
            documents_text: Combined text from all bill documents
            
        Returns:
            Analysis result dictionary
        """
        logger.info("analyze_bill", bill_number=bill_number)
        
        return await self.analyze_document(
            text=documents_text,
            document_type="bill",
            filename=f"Bill_{bill_number}"
        )
    
    async def summarize_document(
        self,
        text: str,
        max_words: int = 300
    ) -> Optional[str]:
        """
        Generate a brief summary of document
        
        Args:
            text: Document text
            max_words: Maximum words in summary
            
        Returns:
            Summary text
        """
        logger.info("summarize_document", text_length=len(text))
        
        if not self.api_key or "ВАШ" in self.api_key:
            logger.error("api_key_not_configured")
            return None
        
        try:
            client = genai.Client(api_key=self.api_key)
            
            prompt = (
                f"Створи стислий висновок наступного тексту законопроєкту. "
                f"Використовуй максимум {max_words} слів. "
                f"Висвітли лише найважливіші моменти.\n\n{text[:self.max_text_length]}"
            )
            
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=prompt
            )
            
            if response and response.text:
                logger.info("summary_generated", length=len(response.text))
                return response.text
            
            return None
            
        except Exception as e:
            logger.error("summarization_failed", error=str(e))
            return None
