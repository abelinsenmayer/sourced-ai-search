"""
Web search package initialization.
"""

from .brave_search import BraveSearchClient, SearchResult, format_results
from .web_crawler import WebCrawler, WebPageContent

__all__ = ['BraveSearchClient', 'SearchResult', 'format_results', 'WebCrawler', 'WebPageContent']
