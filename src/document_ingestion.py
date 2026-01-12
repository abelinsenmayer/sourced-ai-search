"""
Document ingestion utilities for Sourced AI Search.
"""

import json
import os
from typing import List, Dict, Optional
from opensearchpy import OpenSearch
from opensearch_setup import ingest_document, ingest_documents_batch


class DocumentIngestor:
    """
    Helper class for ingesting documents into OpenSearch.
    """
    
    def __init__(self, host: str = "localhost", port: int = 9200):
        """
        Initialize the document ingestor.
        
        Args:
            host: OpenSearch host address
            port: OpenSearch port number
        """
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=None,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        
        # Load model ID if it exists
        model_id_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.opensearch_model_id')
        if os.path.exists(model_id_file):
            with open(model_id_file, 'r') as f:
                self.model_id = f.read().strip()
            print(f"Loaded model ID: {self.model_id}")
        else:
            print("Warning: No model ID file found. Please run opensearch_setup.py first.")
            self.model_id = None
    
    def ingest_text_file(self, file_path: str, title: str = None, source: str = None):
        """
        Ingest a text file into OpenSearch.
        
        Args:
            file_path: Path to the text file
            title: Optional title for the document
            source: Optional source identifier
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Use filename as title if not provided
            if not title:
                title = os.path.basename(file_path)
            
            # Use file path as source if not provided
            if not source:
                source = file_path
            
            # Use filename as document ID
            doc_id = os.path.splitext(os.path.basename(file_path))[0]
            
            response = ingest_document(
                self.client,
                text=text,
                title=title,
                source=source,
                doc_id=doc_id
            )
            
            print(f"Successfully ingested file: {file_path}")
            return response
            
        except Exception as e:
            print(f"Error ingesting file {file_path}: {e}")
            raise
    
    def ingest_json_file(self, file_path: str, text_field: str = "text", title_field: str = None, source_field: str = None):
        """
        Ingest a JSON file containing documents into OpenSearch.
        
        Args:
            file_path: Path to the JSON file
            text_field: Field name containing the text content
            title_field: Optional field name containing the title
            source_field: Optional field name containing the source
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle single document or array of documents
            if isinstance(data, dict):
                documents = [data]
            elif isinstance(data, list):
                documents = data
            else:
                raise ValueError("JSON file must contain a dictionary or array of dictionaries")
            
            # Process documents
            processed_docs = []
            for i, doc in enumerate(documents):
                if text_field not in doc:
                    print(f"Warning: Document {i} missing required field '{text_field}', skipping...")
                    continue
                
                processed_doc = {
                    "text": doc[text_field],
                    "title": doc.get(title_field) if title_field else None,
                    "source": doc.get(source_field) if source_field else None,
                    "id": doc.get("id") or f"doc_{i}"
                }
                
                processed_docs.append(processed_doc)
            
            if processed_docs:
                response = ingest_documents_batch(self.client, processed_docs)
                print(f"Successfully ingested {len(processed_docs)} documents from {file_path}")
                return response
            else:
                print(f"No valid documents found in {file_path}")
                return None
                
        except Exception as e:
            print(f"Error ingesting JSON file {file_path}: {e}")
            raise
    
    def ingest_directory(self, directory_path: str, pattern: str = "*.txt", recursive: bool = True, source_prefix: str = None):
        """
        Ingest all text files in a directory into OpenSearch.
        
        Args:
            directory_path: Path to the directory
            pattern: File pattern to match (e.g., "*.txt", "*.md")
            recursive: Whether to search subdirectories
            source_prefix: Optional prefix for source field
        """
        import glob
        
        if recursive:
            search_pattern = os.path.join(directory_path, "**", pattern)
            files = glob.glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(directory_path, pattern)
            files = glob.glob(search_pattern)
        
        if not files:
            print(f"No files found matching pattern '{pattern}' in directory '{directory_path}'")
            return
        
        print(f"Found {len(files)} files to ingest")
        
        documents = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Use relative path as source
                if source_prefix:
                    source = os.path.join(source_prefix, os.path.relpath(file_path, directory_path))
                else:
                    source = os.path.relpath(file_path, directory_path)
                
                doc = {
                    "text": text,
                    "title": os.path.basename(file_path),
                    "source": source,
                    "id": os.path.splitext(os.path.basename(file_path))[0]
                }
                
                documents.append(doc)
                
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
        
        if documents:
            response = ingest_documents_batch(self.client, documents)
            print(f"Successfully ingested {len(documents)} files from directory")
            return response
    
    def ingest_custom_data(self, documents: List[Dict]):
        """
        Ingest custom document data into OpenSearch.
        
        Args:
            documents: List of document dictionaries with keys: text (required), title (optional), source (optional), id (optional)
        """
        # Validate documents
        for i, doc in enumerate(documents):
            if "text" not in doc:
                raise ValueError(f"Document {i} missing required field 'text'")
        
        response = ingest_documents_batch(self.client, documents)
        print(f"Successfully ingested {len(documents)} custom documents")
        return response


def main():
    """
    Example usage of the DocumentIngestor class.
    """
    # Create ingestor instance
    ingestor = DocumentIngestor()
    
    # Example 1: Ingest a single text file
    # ingestor.ingest_text_file("example.txt", title="Example Document", source="local")
    
    # Example 2: Ingest a JSON file with documents
    # ingestor.ingest_json_file("documents.json", text_field="content", title_field="title")
    
    # Example 3: Ingest all text files in a directory
    # ingestor.ingest_directory("./documents", pattern="*.txt", recursive=True)
    
    # Example 4: Ingest custom data
    custom_docs = [
        {
            "text": "This is a sample document about artificial intelligence.",
            "title": "AI Sample",
            "source": "example",
            "id": "doc_1"
        },
        {
            "text": "Machine learning is a subset of artificial intelligence.",
            "title": "ML Definition",
            "source": "example",
            "id": "doc_2"
        }
    ]
    
    ingestor.ingest_custom_data(custom_docs)


if __name__ == "__main__":
    main()
