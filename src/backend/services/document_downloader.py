"""
Document downloader service for downloading PDF/DOCX files from Parliament website
Migrated from: src/legacy/doc_loader.py
"""
import asyncio
import aiohttp
import re
import structlog
from typing import List, Dict, Optional


logger = structlog.get_logger()


class DocumentDownloaderService:
    """
    Service for downloading bill documents (PDF, DOCX) from Parliament website
    """
    
    def __init__(self):
        self.download_url = "https://itd.rada.gov.ua/billinfo/api/file/download/"
        self.download_delay = 0.5  # seconds between downloads
        self.headers = {
            'accept': '*/*',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'x-current-chunk': '0',
            # Note: Cookie should be provided or refreshed for authenticated downloads
            # If downloads fail, update this cookie from browser DevTools
            'Cookie': 'sid=a2e5a4963-13a5-48b4-8116-a36942321854; api=c70996c2-ad94-4e59-8879-482127b84631'
        }
    
    def _parse_file_metadata_from_html(self, html_content: str) -> List[Dict]:
        """
        Parse HTML card to extract file metadata (ID, extension, name)
        
        Args:
            html_content: HTML content of bill card
            
        Returns:
            List of file metadata dictionaries
        """
        pattern = re.compile(
            r'<a[^>]*class="downloadFile"[^>]*'
            r'data-id="(?P<id>\d+)"[^>]*'
            r'data-ext="(?P<ext>\.\w+)"[^>]*'
            r'data-file-name="(?P<name>[^"]+)"[^>]*>'
        )
        
        metadata_list = []
        
        for match in pattern.finditer(html_content):
            ext = match.group('ext').lower()
            if ext in ('.pdf', '.docx'):
                metadata_list.append({
                    'id': match.group('id'),
                    'ext': ext,
                    'name': match.group('name')
                })
        
        logger.info(
            "parsed_file_metadata",
            found_files=len(metadata_list)
        )
        
        return metadata_list
    
    async def download_document(
        self,
        file_id: str,
        file_ext: str,
        file_name: str
    ) -> Optional[bytes]:
        """
        Download a single document by file ID
        
        Args:
            file_id: File ID from Parliament website
            file_ext: File extension (.pdf or .docx)
            file_name: Original file name
            
        Returns:
            File content as bytes or None if failed
        """
        logger.info(
            "download_document",
            file_id=file_id,
            file_ext=file_ext,
            file_name=file_name
        )
        
        await asyncio.sleep(self.download_delay)
        
        # Add file ID to headers
        headers = self.headers.copy()
        headers['x-file-id'] = file_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.download_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    content = await response.read()
                    
                    if content:
                        logger.info(
                            "document_downloaded",
                            file_id=file_id,
                            size=len(content)
                        )
                        return content
                    else:
                        logger.warning(
                            "empty_document",
                            file_id=file_id
                        )
                        return None
                        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(
                "download_failed",
                file_id=file_id,
                error=str(e)
            )
            return None
    
    async def download_bill_documents(
        self,
        bill_number: str,
        html_content: str
    ) -> List[Dict]:
        """
        Download all documents for a bill from its HTML card
        
        Args:
            bill_number: Bill registration number
            html_content: HTML content of bill card
            
        Returns:
            List of downloaded documents with metadata
        """
        logger.info(
            "download_bill_documents",
            bill_number=bill_number
        )
        
        # Parse file metadata from HTML
        file_metadata = self._parse_file_metadata_from_html(html_content)
        
        if not file_metadata:
            logger.info(
                "no_documents_found",
                bill_number=bill_number
            )
            return []
        
        logger.info(
            "found_documents",
            bill_number=bill_number,
            count=len(file_metadata)
        )
        
        # Download all documents
        downloaded_documents = []
        
        for i, meta in enumerate(file_metadata, 1):
            file_id = meta['id']
            file_ext = meta['ext']
            file_name = meta['name']
            
            # Download document
            content = await self.download_document(file_id, file_ext, file_name)
            
            if content:
                # Generate filename: bill_number_file_id_sequence.ext
                generated_filename = f"{bill_number}_{file_id}_{i}{file_ext}"
                
                downloaded_documents.append({
                    'file_id': file_id,
                    'file_ext': file_ext,
                    'original_name': file_name,
                    'generated_filename': generated_filename,
                    'content': content,
                    'size': len(content),
                    'sequence': i
                })
        
        logger.info(
            "download_completed",
            bill_number=bill_number,
            downloaded=len(downloaded_documents),
            total=len(file_metadata)
        )
        
        return downloaded_documents
