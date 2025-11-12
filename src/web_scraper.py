"""
Web Scraper Service for Layer 2 - Investment Analyst Research Tool
Uses Playwright for robust web scraping with JavaScript support
"""

import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraperService:
    """
    Async web scraping service using Playwright for robust content extraction
    """

    def __init__(self, max_concurrent: int = 5, timeout: int = 30000):
        """
        Initialize the web scraper service

        Args:
            max_concurrent: Maximum number of concurrent scraping tasks
            timeout: Timeout in milliseconds for each page load
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start the Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        logger.info("Playwright browser started")

    async def close(self):
        """Close the Playwright browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")

    async def scrape_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single URL and extract clean text content

        Args:
            url: The URL to scrape

        Returns:
            Dict with 'url', 'content', and 'success' keys, or None if failed
        """
        if not self.browser:
            logger.error("Browser not started. Call start() first.")
            return None

        page: Optional[Page] = None
        try:
            # Create a new page
            page = await self.browser.new_page()

            # Set a reasonable viewport
            await page.set_viewport_size({"width": 1280, "height": 720})

            # Navigate to the URL with timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

            # Wait a bit for any dynamic content to load
            await page.wait_for_timeout(2000)

            # Get the HTML content
            html_content = await page.content()

            # Extract clean text using BeautifulSoup
            clean_text = self._extract_clean_text(html_content)

            if clean_text and len(clean_text.strip()) > 100:  # Minimum viable content
                logger.info(f"Successfully scraped: {url[:60]}... ({len(clean_text)} chars)")
                return {
                    "url": url,
                    "content": clean_text,
                    "success": True
                }
            else:
                logger.warning(f"Insufficient content from: {url[:60]}...")
                return None

        except PlaywrightTimeoutError:
            logger.warning(f"Timeout scraping: {url[:60]}...")
            return None

        except Exception as e:
            logger.warning(f"Failed to scrape {url[:60]}...: {str(e)[:100]}")
            return None

        finally:
            if page:
                await page.close()

    def _extract_clean_text(self, html: str) -> str:
        """
        Extract clean text from HTML using BeautifulSoup

        Args:
            html: Raw HTML content

        Returns:
            Clean text content
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=' ', strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Limit to reasonable size (100K chars max)
            if len(text) > 100000:
                text = text[:100000]

            return text

        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""

    async def scrape_urls_batch(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        Scrape multiple URLs concurrently with rate limiting

        Args:
            urls: List of URLs to scrape

        Returns:
            List of successfully scraped content dictionaries
        """
        if not self.browser:
            await self.start()

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape_url(url)

        # Scrape all URLs concurrently (but rate-limited)
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        successful_results = []
        for result in results:
            if isinstance(result, dict) and result.get("success"):
                successful_results.append(result)

        logger.info(f"Scraped {len(successful_results)}/{len(urls)} URLs successfully")
        return successful_results


async def scrape_urls(urls: List[str], max_concurrent: int = 5, timeout: int = 30000) -> List[Dict[str, str]]:
    """
    Convenience function to scrape multiple URLs

    Args:
        urls: List of URLs to scrape
        max_concurrent: Maximum concurrent scraping tasks
        timeout: Timeout in milliseconds for each page

    Returns:
        List of successfully scraped content dictionaries
    """
    async with WebScraperService(max_concurrent=max_concurrent, timeout=timeout) as scraper:
        return await scraper.scrape_urls_batch(urls)
