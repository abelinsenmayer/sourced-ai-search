import os
import json
from datetime import datetime
from pydoc import text
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIWebSearch:
    """A class to perform web searches using OpenAI's API with web search tool."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def search(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search using OpenAI's responses API with web search tool.
        
        Args:
            query: The search query
            max_results: Maximum number of results to retrieve
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            response = self.client.responses.create(
                model="gpt-5-mini",
                tools=[
                    {"type": "web_search"},
                ],
                input=query,
                include=["web_search_call.action.sources"],
                tool_choice="required",
                reasoning={"effort": "medium"},
                instructions="""
                    You are a helpful assistant that can perform web searches. Answer the user's question using the web search tool. 
                    Proivide up to 3 sentences of context for each part of your answer. Cite your sources using annotations.
                    Keep your answer grounded in the web search results; do not add any information not found in the web search results.
                    Do not ask follow questions or suggest further actions. Do not provide any additional information other than the answer.
                    If you cannot find any information to answer the user's question, state that you cannot find any information.
                """
            )

            output_text = response.output_text
            
            # Extract sources from the response
            sources_list = []
            for item in response.output:
                if hasattr(item, 'action') and hasattr(item.action, 'sources'):
                    for source in item.action.sources:
                        sources_list.append({
                            "type": source.type,
                            "url": source.url
                        })
            
            return {
                "query": query,
                "output_text": output_text,
                "sources": sources_list,
                "model_used": "gpt-5-mini",
                "timestamp": datetime.now().isoformat(),
            }
                
        except Exception as e:
            print('Exception: ', e)
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Main function to demonstrate the OpenAI web search."""
    # Initialize the searcher
    searcher = OpenAIWebSearch()
    
    # Clear sample_data directory if it exists
    sample_data_dir = "sample_data"
    if os.path.exists(sample_data_dir):
        import shutil
        shutil.rmtree(sample_data_dir)
        print(f"Cleared all contents of {sample_data_dir}")
    
    # Prompt user for query
    query = input("\nEnter your search query: ").strip()
    
    if not query:
        print("No query provided. Exiting.")
        return
    
    # Create sample_data directory if it doesn't exist
    os.makedirs(sample_data_dir, exist_ok=True)
    
    # Perform search and save results
    print(f"\nSearching for: {query}")
    results = searcher.search(query)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    # Print the output text to console
    print("\n" + "="*80)
    print("SEARCH RESULTS:")
    print("="*80)
    print(results['output_text'])
    print("="*80)
    
    # Create a subfolder for this search
    search_folder = f"sample_data/{''.join(c for c in query if c.isalnum())[:20]}"
    os.makedirs(search_folder, exist_ok=True)
    
    # Save sources to a separate file
    sources_filename = f"{search_folder}/sources.json"
    with open(sources_filename, 'w', encoding='utf-8') as f:
        json.dump(results.get('sources', []), f, indent=2, ensure_ascii=False)
    
    # Save other data (excluding sources) to a separate file
    other_data = {k: v for k, v in results.items() if k != 'sources'}
    other_filename = f"{search_folder}/search_data.json"
    with open(other_filename, 'w', encoding='utf-8') as f:
        json.dump(other_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {search_folder}/")
    print(f"  - sources.json: {len(results.get('sources', []))} sources")
    print(f"  - search_data.json: query and output text")
    
    print("\nSearch completed!")


if __name__ == "__main__":
    main()
