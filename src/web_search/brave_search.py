"""
Web search utility using Brave Search API.
"""

import os
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Data class representing a single search result."""
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    language: Optional[str] = None


class BraveSearchClient:
    """
    Client for interacting with the Brave Search API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Brave Search client.
        
        Args:
            api_key: Brave Search API key. If not provided, will try to get from environment variable.
        """
        self.api_key = api_key or os.getenv('BRAVE_SEARCH_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Brave Search API key not provided. "
                "Set BRAVE_SEARCH_API_KEY environment variable or pass api_key parameter."
            )
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
    
    def search(self, 
               query: str, 
               count: int = 10, 
               offset: int = 0,
               lang: str = "en-US",
               country: str = "US",
               search_lang: str = "en",
               ui_lang: str = "en-US",
               text_decorations: bool = False,
               spellcheck: bool = True,
               result_filter: str = None,
               safesearch: str = "moderate",
               search_type: str = "web",
               freshness: str = None) -> List[SearchResult]:
        """
        Perform a web search using Brave Search API.
        
        Args:
            query: Search query string
            count: Number of results to return (max 20)
            offset: Number of results to skip
            lang: Language locale for search results (e.g., "en-US", "en-GB", "fr-FR")
            country: Country code for search results
            search_lang: Language code of the search query (e.g., "en", "en-gb", "fr", "de")
            ui_lang: Language locale for UI elements (e.g., "en-US", "en-GB", "fr-FR")
            text_decorations: Whether to include text decorations
            spellcheck: Whether to enable spellcheck
            result_filter: Filter results (e.g., "news", "images", "videos")
            safesearch: Safe search level ("strict", "moderate", "off")
            search_type: Type of search ("web", "news", "images", "videos")
            freshness: Filter by freshness ("pd", "pw", "pm", "py")
        
        Returns:
            List of SearchResult objects
        """
        params = {
            "q": query,
            "count": min(count, 20),  # API limit is 20
            "offset": offset
        }
        
        # Add optional parameters if provided
        optional_params = {
            "lang": lang,
            "country": country,
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "text_decorations": str(text_decorations).lower(),
            "spellcheck": str(spellcheck).lower(),
            "safesearch": safesearch,
            "search_type": search_type
        }
        
        for key, value in optional_params.items():
            if value is not None:
                params[key] = value
        
        if result_filter:
            params["result_filter"] = result_filter
        
        if freshness:
            params["freshness"] = freshness
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_results(data)
            
        except requests.exceptions.RequestException as e:
            print(f"Error performing search: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            return []
    
    def _parse_results(self, data: Dict) -> List[SearchResult]:
        """
        Parse the API response into SearchResult objects.
        
        Args:
            data: Raw API response data
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        if 'web' in data and 'results' in data['web']:
            for item in data['web']['results']:
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('description', ''),
                    published_date=item.get('age'),
                    language=item.get('language')
                )
                results.append(result)
        
        return results
    
    def search_news(self, query: str, count: int = 10, freshness: str = None) -> List[SearchResult]:
        """
        Perform a news search.
        
        Args:
            query: Search query string
            count: Number of results to return
            freshness: Filter by freshness ("pd", "pw", "pm", "py")
        
        Returns:
            List of SearchResult objects
        """
        return self.search(
            query=query,
            count=count,
            search_type="news",
            freshness=freshness
        )
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions for a query.
        
        Args:
            query: Partial query string
            
        Returns:
            List of suggestion strings
        """
        suggestions_url = "https://api.search.brave.com/res/v1/suggestions"
        params = {"q": query}
        
        try:
            response = requests.get(
                suggestions_url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [item.get('q', '') for item in data.get('suggestions', [])]
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting suggestions: {e}")
            return []


def format_results(results: List[SearchResult], show_snippets: bool = True) -> str:
    """
    Format search results for display.
    
    Args:
        results: List of SearchResult objects
        show_snippets: Whether to include snippets in output
        
    Returns:
        Formatted string of results
    """
    if not results:
        return "No results found."
    
    output = []
    for i, result in enumerate(results, 1):
        output.append(f"{i}. {result.title}")
        output.append(f"   URL: {result.url}")
        
        if show_snippets and result.snippet:
            output.append(f"   {result.snippet}")
        
        if result.published_date:
            output.append(f"   Published: {result.published_date}")
        
        output.append("")  # Empty line for readability
    
    return "\n".join(output)


def main():
    """
    Example usage of the Brave Search client.
    """
    # Initialize the client (will use BRAVE_SEARCH_API_KEY environment variable)
    try:
        client = BraveSearchClient()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the BRAVE_SEARCH_API_KEY environment variable.")
        print("Example: export BRAVE_SEARCH_API_KEY='your-api-key-here'")
        return
    
    # Perform a sample search
    query = "artificial intelligence latest developments"
    print(f"Searching for: {query}")
    print("-" * 50)
    
    results = client.search(query, count=5)
    
    if results:
        print(format_results(results))
        
        # Demonstrate news search
        print("\n" + "=" * 50)
        print("News Search Example:")
        print("=" * 50)
        
        news_results = client.search_news(query, count=3)
        if news_results:
            print(format_results(news_results))
        
        # Demonstrate search suggestions
        print("\n" + "=" * 50)
        print("Search Suggestions Example:")
        print("=" * 50)
        
        suggestions = client.get_search_suggestions("artificial int")
        if suggestions:
            print("Suggestions for 'artificial int':")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
    
    else:
        print("No results found for the query.")


if __name__ == "__main__":
    main()
