"""
Main workflow for combining web search and crawling.
This script searches for a query, crawls the top results, and saves the data.
"""

import asyncio
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from src.web_search import BraveSearchClient, SearchResult, WebCrawler, WebPageContent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearchAndCrawlWorkflow:
    """
    Main workflow for searching and crawling web content.
    """
    
    def __init__(self, sample_data_dir: str = "sample_data"):
        """
        Initialize the workflow.
        
        Args:
            sample_data_dir: Directory to store crawled data
        """
        self.sample_data_dir = Path(sample_data_dir)
        self.sample_data_dir.mkdir(exist_ok=True)
        
        # Initialize search client
        try:
            self.search_client = BraveSearchClient()
        except ValueError as e:
            logger.error(f"Failed to initialize search client: {e}")
            raise
    
    def clear_sample_data(self):
        """Clear all files in the sample data directory."""
        logger.info("Clearing sample data directory...")
        
        for item in self.sample_data_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        logger.info("Sample data directory cleared")
    
    async def crawl_results(self, search_results: List[SearchResult]) -> List[Dict[str, Any]]:
        """
        Crawl the search results and extract content.
        
        Args:
            search_results: List of search results to crawl
            
        Returns:
            List of crawled content data
        """
        crawled_data = []
        
        async with WebCrawler(headless=True) as crawler:
            for i, result in enumerate(search_results, 1):
                logger.info(f"Crawling result {i}/{len(search_results)}: {result.url}")
                
                try:
                    # Crawl the page
                    content = await crawler.get_page_content(
                        result.url,
                        clean_content=True,
                        remove_selectors=['script', 'style', 'nav', 'footer', 'header', 'aside']
                    )
                    
                    # # Also get the raw HTML without cleaning for debugging
                    # raw_content = await crawler.get_page_content(
                    #     result.url,
                    #     clean_content=False,
                    #     remove_selectors=[]
                    # )
                    
                    # Combine search result with crawled content
                    data = {
                        "search_result": {
                            "title": result.title,
                            "url": result.url,
                            "snippet": result.snippet,
                            "published_date": result.published_date,
                            "language": result.language
                        },
                        "crawled_content": {
                            "title": content.title,
                            "content": content.content,
                            "metadata": content.metadata,
                            "links_count": len(content.links),
                            "images_count": len(content.images)
                        },
                        # "debug": {
                        #     "full_html_content": raw_content.content,
                        #     "raw_title": raw_content.title,
                        #     "raw_metadata": raw_content.metadata
                        # },
                        "crawled_at": datetime.utcnow().isoformat()
                    }
                    
                    crawled_data.append(data)
                    logger.info(f"Successfully crawled {result.url}")
                    
                except Exception as e:
                    logger.error(f"Failed to crawl {result.url}: {e}")
                    
                    # Save failed attempt
                    data = {
                        "search_result": {
                            "title": result.title,
                            "url": result.url,
                            "snippet": result.snippet,
                            "published_date": result.published_date,
                            "language": result.language
                        },
                        "error": str(e),
                        "crawled_at": datetime.utcnow().isoformat()
                    }
                    
                    crawled_data.append(data)
        
        return crawled_data
    
    def save_crawled_data(self, crawled_data: List[Dict[str, Any]], query: str):
        """
        Save crawled data to JSON files.
        
        Args:
            crawled_data: List of crawled content data
            query: The search query for naming
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        query_safe = query_safe.replace(' ', '_')[:50]  # Limit length
        
        # Save individual files
        for i, data in enumerate(crawled_data):
            filename = f"{timestamp}_{query_safe}_result_{i+1}.json"
            filepath = self.sample_data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved: {filepath}")
        
        # Save summary file
        summary = {
            "query": query,
            "timestamp": timestamp,
            "total_results": len(crawled_data),
            "successful_crawls": sum(1 for d in crawled_data if "crawled_content" in d),
            "failed_crawls": sum(1 for d in crawled_data if "error" in d),
            "results": [
                {
                    "title": d["search_result"]["title"],
                    "url": d["search_result"]["url"],
                    "status": "success" if "crawled_content" in d else "failed"
                }
                for d in crawled_data
            ]
        }
        
        summary_filename = f"{timestamp}_{query_safe}_summary.json"
        summary_filepath = self.sample_data_dir / summary_filename
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved summary: {summary_filepath}")
    
    async def run_search_and_crawl(self, query: str, num_results: int = 5):
        """
        Run the complete search and crawl workflow.
        
        Args:
            query: Search query
            num_results: Number of results to crawl
        """
        logger.info(f"Starting search and crawl workflow for query: '{query}'")
        
        # Clear previous data
        self.clear_sample_data()
        
        # Perform search
        logger.info(f"Searching for '{query}'...")
        search_results = self.search_client.search(query, count=num_results)
        
        if not search_results:
            logger.warning("No search results found")
            return
        
        logger.info(f"Found {len(search_results)} search results")
        
        # Crawl the results
        crawled_data = await self.crawl_results(search_results)
        
        # Save the data
        self.save_crawled_data(crawled_data, query)
        
        # Print summary
        successful = sum(1 for d in crawled_data if "crawled_content" in d)
        logger.info(f"Workflow completed: {successful}/{len(crawled_data)} pages successfully crawled")
        
        return crawled_data


async def main():
    """
    Main function to run the workflow with a dummy question.
    """
    # Dummy question for testing
    dummy_query = "What is artificial intelligence and how does it work?"
    
    # Create and run workflow
    workflow = SearchAndCrawlWorkflow()
    
    try:
        crawled_data = await workflow.run_search_and_crawl(dummy_query, num_results=5)
        
        # Print a sample of the results
        if crawled_data:
            print("\n" + "=" * 60)
            print("SAMPLE CRAWLED CONTENT")
            print("=" * 60)
            
            for i, data in enumerate(crawled_data[:2], 1):  # Show first 2 results
                print(f"\nResult {i}:")
                print(f"Title: {data['search_result']['title']}")
                print(f"URL: {data['search_result']['url']}")
                
                if "crawled_content" in data:
                    content = data["crawled_content"]["content"]
                    preview = content[:300] + "..." if len(content) > 300 else content
                    print(f"Content preview:\n{preview}")
                else:
                    print(f"Error: {data.get('error', 'Unknown error')}")
                
                print("-" * 40)
    
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        raise


if __name__ == "__main__":
    # Run the workflow
    asyncio.run(main())
