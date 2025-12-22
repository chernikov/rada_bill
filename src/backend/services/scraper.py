"""
Web scraper service for downloading bill HTML cards from Parliament website
Migrated from: src/legacy/pages_installer.py
"""
import asyncio
import aiohttp
import re
import structlog
from typing import Optional, Dict, List, Tuple
from bs4 import BeautifulSoup


logger = structlog.get_logger()


class ScraperService:
    """
    Service for scraping bill information from Parliament website
    """
    
    def __init__(self):
        self.base_url = "https://itd.rada.gov.ua/billinfo"
        self.search_url = "https://itd.rada.gov.ua/billinfo/Bills/searchResults"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url,
        }
        self.search_delay = 1.0  # seconds between search requests
        self.download_delay = 0.2  # seconds between card downloads
        self.max_retries = 3
        self.retry_delay = 5
    
    async def download_bill_card(self, bill_number: str, card_url: Optional[str] = None) -> Optional[str]:
        """
        Download HTML card for a specific bill
        
        Args:
            bill_number: Bill number (e.g., "12414")
            card_url: Direct URL to bill card (if known)
            
        Returns:
            HTML content or None if not found
        """
        logger.info("download_bill_card", bill_number=bill_number, url=card_url)
        
        # If URL not provided, search for the bill to get its card URL
        if not card_url:
            search_result = await self.search_bills(page=1, per_page=1, bill_number=bill_number)
            if not search_result.get("bills"):
                logger.warning("bill_not_found", bill_number=bill_number)
                return None
            card_url = search_result["bills"][0]["card_url"]
        
        await asyncio.sleep(self.download_delay)
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        card_url,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        response.raise_for_status()
                        html_content = await response.text()
                        logger.info("bill_card_downloaded", bill_number=bill_number, size=len(html_content))
                        return html_content
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "download_retry",
                        bill_number=bill_number,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(
                        "download_failed",
                        bill_number=bill_number,
                        error=str(e)
                    )
                    return None
        
        return None
    
    def _parse_bill_links_from_html(self, html: str) -> List[Tuple[str, str]]:
        """
        Parse bill links from search results HTML
        
        Args:
            html: HTML content of search results page
            
        Returns:
            List of tuples: [(bill_number, card_url), ...]
        """
        # Use regex to find bill links (now supports formats like "14270-1", "10000-д")
        pattern = re.compile(
            r'<a href="(https://itd\.rada\.gov\.ua/billinfo/Bills/Card/\d+)"[^>]*class="link-blue">([0-9]+-?[0-9а-яА-Яa-zA-Z]*)</a>'
        )
        matches = pattern.findall(html)
        
        # Return as [(bill_number, card_url), ...]
        return [(match[1], match[0]) for match in matches]
    
    async def search_bills(
        self, 
        page: int = 1, 
        per_page: int = 30,
        bill_number: Optional[str] = None,
        bill_name: Optional[str] = None,
        session: Optional[str] = "10",
        **filters
    ) -> Dict[str, any]:
        """
        Search for bills on Parliament website
        
        Args:
            page: Page number (1-indexed)
            per_page: Bills per page (30, 40, or 50)
            bill_number: Specific bill number to search for
            bill_name: Text search in bill name/title
            session: Parliament session number
            **filters: Additional search filters
            
        Returns:
            Dictionary with bills list and pagination info
        """
        logger.info("search_bills", page=page, per_page=per_page, bill_number=bill_number, bill_name=bill_name)
        
        await asyncio.sleep(self.search_delay)
        
        # Prepare search form data
        data = {
            'BillSearchModel.session': session,
            'BillSearchModel.registrationNumberCompareOperation': '2',
            'Paging.per_page': str(per_page),
            'Paging.page': str(page)
        }
        
        # Add bill number filter if provided
        if bill_number:
            data['BillSearchModel.registrationNumber'] = bill_number
        
        # Add bill name (text search) filter if provided
        if bill_name:
            data['BillSearchModel.name'] = bill_name
        
        # Add any additional filters
        data.update(filters)
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session_obj:
                    async with session_obj.post(
                        self.search_url,
                        data=data,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        response.raise_for_status()
                        html_content = await response.text()
                        
                        # Parse bill links from HTML
                        bill_links = self._parse_bill_links_from_html(html_content)
                        
                        # Format results
                        bills = [
                            {
                                "bill_number": bill_num,
                                "card_url": card_url
                            }
                            for bill_num, card_url in bill_links
                        ]
                        
                        logger.info(
                            "search_completed",
                            page=page,
                            found=len(bills)
                        )
                        
                        return {
                            "bills": bills,
                            "total": len(bills),
                            "page": page,
                            "per_page": per_page
                        }
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "search_retry",
                        page=page,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(
                        "search_failed",
                        page=page,
                        error=str(e)
                    )
                    return {
                        "bills": [],
                        "total": 0,
                        "page": page,
                        "per_page": per_page
                    }
        
        return {
            "bills": [],
            "total": 0,
            "page": page,
            "per_page": per_page
        }
    
    def extract_bill_title(self, html_content: str) -> Optional[str]:
        """
        Extract bill title from HTML content
        
        Args:
            html_content: HTML content of bill card
            
        Returns:
            Bill title or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try meta description first
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc['content'].strip()
            
            # Try title tag as fallback
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.text.strip()
                # Remove "Картка законопроекту - Законотворчість" part
                if ' - ' in title_text:
                    return title_text.split(' - ')[0].strip()
                return title_text
            
            return None
            
        except Exception as e:
            logger.error("title_extraction_failed", error=str(e))
            return None
