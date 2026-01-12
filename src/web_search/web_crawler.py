"""
Web crawling utility using Playwright for extracting web page content.
"""

import asyncio
import re
from typing import Optional, Dict, List
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from readabilipy import simple_json_from_html_string
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WebPageContent:
    """Data class representing extracted web page content."""
    url: str
    title: str
    content: str
    metadata: Dict[str, str]
    links: List[str]
    images: List[str]


class WebCrawler:
    """
    Web crawler using Playwright to extract clean content from web pages.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the web crawler.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the browser and create context."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        logger.info("Browser started successfully")
    
    async def close(self):
        """Close the browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def get_page_content(self, 
                              url: str, 
                              wait_for: str = None,
                              remove_selectors: List[str] = None,
                              clean_content: bool = True) -> WebPageContent:
        """
        Get the content of a web page.
        
        Args:
            url: URL of the page to fetch
            wait_for: CSS selector to wait for before extracting content
            remove_selectors: List of CSS selectors to remove before extraction
            clean_content: Whether to clean the HTML content
        
        Returns:
            WebPageContent object with extracted data
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() or use async context manager.")
        
        page = await self.context.new_page()
        
        try:
            # Navigate to the page
            logger.info(f"Navigating to: {url}")
            response = await page.goto(url, wait_until='networkidle')
            
            if response.status != 200:
                raise Exception(f"Failed to load page: HTTP {response.status}")
            
            # Wait for specific element if requested
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=10000)
            
            # Remove unwanted elements
            if remove_selectors:
                for selector in remove_selectors:
                    await page.evaluate(f"""
                        document.querySelectorAll('{selector}').forEach(el => el.remove());
                    """)
            
            # Extract page data
            title = await page.title()
            
            # Get the HTML content
            html_content = await page.content()
            
            # Extract links
            links = await page.evaluate("""
                Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href.startsWith('http'))
            """)
            
            # Extract images
            images = await page.evaluate("""
                Array.from(document.querySelectorAll('img[src]'))
                    .map(img => img.src)
                    .filter(src => src.startsWith('http'))
            """)
            
            # Get metadata
            metadata = await page.evaluate("""
                () => {
                    const meta = {};
                    document.querySelectorAll('meta').forEach(tag => {
                        if (tag.name) meta[tag.name] = tag.content;
                        if (tag.property) meta[tag.property] = tag.content;
                    });
                    return meta;
                }
            """)
            
            # Clean content if requested
            if clean_content:
                content = self._extract_readable_content(html_content)
            else:
                content = html_content
            
            return WebPageContent(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                links=links,
                images=images
            )
            
        finally:
            await page.close()
    
    def _extract_readable_content(self, html_content: str) -> str:
        """
        Extract readable content from HTML.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        try:
            # Use readability to extract the main content
            result = simple_json_from_html_string(html_content, use_readability=True)
            
            # Combine all text entries with newlines
            if isinstance(result['plain_text'], list):
                return '\n'.join(item.get('text', '') for item in result['plain_text'] if item.get('text'))
            else:
                return str(result['plain_text'])
            
        except Exception as e:
            logger.warning(f"Error using readability: {e}")
            return ""

    
    async def get_multiple_pages(self, urls: List[str], **kwargs) -> List[WebPageContent]:
        """
        Get content from multiple pages concurrently.
        
        Args:
            urls: List of URLs to fetch
            **kwargs: Additional arguments for get_page_content
            
        Returns:
            List of WebPageContent objects
        """
        tasks = [self.get_page_content(url, **kwargs) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)


async def test_crawler():
    """
    Test the web crawler with a sample page.
    """
    # Test URL - using a simple page that should be accessible
    test_url = "https://example.com"
    
    print(f"Testing web crawler with: {test_url}")
    print("=" * 60)
    
    async with WebCrawler(headless=True) as crawler:
        try:
            # Get page content
            content = await crawler.get_page_content(
                test_url,
                remove_selectors=['script', 'style', 'nav', 'footer'],
                clean_content=True
            )
            
            # Print results
            print(f"URL: {content.url}")
            print(f"Title: {content.title}")
            print("\nContent:")
            print("-" * 40)
            print(content.content[:1000] + "..." if len(content.content) > 1000 else content.content)
            
            print("\nMetadata:")
            print("-" * 40)
            for key, value in list(content.metadata.items())[:5]:  # Show first 5 metadata items
                print(f"{key}: {value}")
            
            print(f"\nFound {len(content.links)} links")
            print(f"Found {len(content.images)} images")
            
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """
    Main function to run the crawler test.
    """
    await test_crawler()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
