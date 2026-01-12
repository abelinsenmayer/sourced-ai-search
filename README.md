# Sourced AI Search

A vector search implementation using OpenSearch with ML capabilities for semantic document search and retrieval.

## Overview

This project sets up a complete vector search pipeline with:
- OpenSearch cluster with ML plugin support
- Sentence transformers model for text embeddings
- Ingestion pipeline for automatic vector generation
- Helper utilities for document ingestion

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Poetry (for dependency management)
- PowerShell (on Windows) or Bash (on Linux/Mac)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Start OpenSearch Cluster

```powershell
# On Windows
.\scripts\start-opensearch.ps1

# On Linux/Mac
./scripts/start-opensearch.sh
```

This will:
- Start OpenSearch and OpenSearch Dashboards containers
- Wait for the cluster to be ready
- OpenSearch will be available at http://localhost:9200
- Dashboards will be available at http://localhost:5601

### 3. Set Up Vector Index and ML Pipeline

```powershell
# On Windows
.\scripts\setup-opensearch.ps1

# On Linux/Mac
./scripts/setup-opensearch.sh
```

This will:
- Configure ML cluster settings
- Register and deploy the sentence-transformers model
- Create an ingest pipeline with text embedding
- Create the vector index with k-NN support

## Usage

### Document Ingestion

Use the `DocumentIngestor` class to ingest documents:

```python
from src.document_ingestion import DocumentIngestor

# Create ingestor instance
ingestor = DocumentIngestor()

# Ingest a single text file
ingestor.ingest_text_file("document.txt", title="My Document", source="local")

# Ingest a JSON file with multiple documents
ingestor.ingest_json_file("documents.json", text_field="content", title_field="title")

# Ingest all text files in a directory
ingestor.ingest_directory("./documents", pattern="*.txt", recursive=True)

# Ingest custom data
documents = [
    {
        "text": "This is a sample document.",
        "title": "Sample",
        "source": "example",
        "id": "doc_1"
    }
]
ingestor.ingest_custom_data(documents)
```

### Querying the Index

```python
from opensearchpy import OpenSearch

# Create OpenSearch client
client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=None,
    use_ssl=False,
    verify_certs=False,
)

# Perform a k-NN search
query = {
    "size": 5,
    "query": {
        "knn": {
            "text_embedding": {
                "vector": [0.1, 0.2, ...],  # Your query vector
                "k": 5
            }
        }
    }
}

response = client.search(index="sourced-ai-index", body=query)
```

## Project Structure

```
sourced-ai-search/
├── scripts/                    # PowerShell/Bash scripts
│   ├── start-opensearch.ps1    # Start OpenSearch cluster
│   ├── stop-opensearch.ps1     # Stop OpenSearch cluster
│   └── setup-opensearch.ps1    # Setup vector index and ML pipeline
├── src/                        # Python source code
│   ├── opensearch_setup.py     # OpenSearch index and ML setup
│   └── document_ingestion.py   # Document ingestion utilities
├── opensearch-cluster/         # Docker Compose configuration
│   └── docker-compose.yml      # OpenSearch cluster definition
├── pyproject.toml              # Python dependencies
└── README.md                   # This file
```

## Configuration

### OpenSearch Settings

The cluster is configured with:
- Single-node deployment (for development)
- 1GB heap size
- Security disabled
- ML plugin enabled

### Model Configuration

Default model: `huggingface/sentence-transformers/all-MiniLM-L6-v2`
- Embedding dimension: 384
- Suitable for general-purpose semantic search

## API Endpoints

Once running:
- OpenSearch REST API: http://localhost:9200
- OpenSearch Dashboards: http://localhost:5601

## Cleanup

To stop and remove all containers:

```powershell
# On Windows
.\scripts\stop-opensearch.ps1

# On Linux/Mac
./scripts/stop-opensearch.sh
```

To remove the Docker volumes (warning: this deletes all data):

```bash
cd opensearch-cluster
docker compose down -v
```

## Troubleshooting

### OpenSearch fails to start
- Check if ports 9200, 9600, and 5601 are available
- Ensure Docker has enough memory allocated (recommended 4GB+)

### Model deployment fails
- Check cluster health: `curl http://localhost:9200/_cluster/health`
- Verify ML plugin is enabled: `curl http://localhost:9200/_cat/plugins`

### Memory issues
- Increase Docker memory allocation
- Adjust heap size in docker-compose.yml

## License

This project is licensed under the MIT License - see the LICENSE file for details.
