"""
Unified document converter service
"""
import structlog
from typing import Optional
from backend.services.converters.pdf_converter import PDFConverter
from backend.services.converters.docx_converter import DOCXConverter

logger = structlog.get_logger()

class DocumentConverter:
    """
    Unified service for converting various document formats to Markdown
    """
    
    def __init__(self):
        self.pdf_converter = PDFConverter()
        self.docx_converter = DOCXConverter()
    
    async def convert_to_markdown(self, content: bytes, filename: str, file_ext: str) -> Optional[str]:
        """
        Convert document bytes to Markdown text based on file extension
        
        Args:
            content: File content as bytes
            filename: Original filename for reference
            file_ext: File extension (e.g., '.pdf', '.docx')
            
        Returns:
            Markdown text or None if conversion fails
        """
        logger.info("convert_document_to_markdown", filename=filename, ext=file_ext)
        
        if file_ext.lower() == '.pdf':
            return await self.pdf_converter.convert_to_markdown(content, filename)
        elif file_ext.lower() == '.docx':
            return await self.docx_converter.convert_to_markdown(content, filename)
        else:
            logger.warning("unsupported_file_format", filename=filename, ext=file_ext)
            return None
