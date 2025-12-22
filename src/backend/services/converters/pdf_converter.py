"""
PDF to Markdown converter service
Migrated from: src/legacy/pdf_to_md_convertor.py
"""
import pdfplumber
import re
import structlog
from typing import Optional
from io import BytesIO


logger = structlog.get_logger()


class PDFConverter:
    """
    Service for converting PDF documents to Markdown format
    """
    
    def __init__(self):
        pass
    
    async def convert_to_markdown(self, pdf_content: bytes, filename: str) -> Optional[str]:
        """
        Convert PDF bytes to Markdown text
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for reference
            
        Returns:
            Markdown text or None if conversion fails
        """
        logger.info("convert_pdf_to_markdown", filename=filename, size=len(pdf_content))
        
        try:
            # Use BytesIO to read PDF from memory
            pdf_bytes = BytesIO(pdf_content)
            
            all_text = []
            
            with pdfplumber.open(pdf_bytes) as pdf:
                logger.info("pdf_opened", filename=filename, pages=len(pdf.pages))
                
                for i, page in enumerate(pdf.pages):
                    # Add page header
                    all_text.append(f"\n## Сторінка {i + 1}\n\n")
                    
                    # Extract text with layout preservation
                    page_text = page.extract_text(layout=True)
                    
                    if page_text:
                        # Clean up common issues: extra newlines and spaces
                        page_text = re.sub(r'(\n\s*){2,}', '\n\n', page_text)
                        all_text.append(page_text)
                    else:
                        all_text.append("*[Текст на цій сторінці не вдалося витягти]*\n")
            
            # Join all pages
            raw_text = "\n".join(all_text)
            
            # Additional cleanup for better Markdown appearance
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', raw_text)
            
            logger.info(
                "pdf_converted",
                filename=filename,
                output_length=len(markdown_content)
            )
            
            return markdown_content
            
        except Exception as e:
            logger.error(
                "pdf_conversion_failed",
                filename=filename,
                error=str(e)
            )
            return None
