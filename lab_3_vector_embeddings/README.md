# Lab 3: Vector Embeddings and Hybrid Search

This lab processes HTML documents from the Databricks volume, generates vector embeddings, stores them in Neo4j as a document graph, and enables both semantic vector search and keyword-based full-text search through a hybrid search interface.

## Prerequisites

1. **Neo4j database** running (Aura or self-hosted, version 5.11+ for vector index support)
2. **Databricks Secrets** configured with `neo4j-creds` scope (for notebook)
3. **Unity Catalog Volume** with HTML files uploaded (from Lab 1)
4. **Lab 2 completed** - financial entity graph populated in Neo4j

## Databricks Cluster Libraries

Install the following PyPI libraries on your Databricks cluster (Compute > Libraries > Install new):

| Library | Version | Purpose |
|---------|---------|---------|
| `neo4j-graphrag` | `>=1.0.0` (latest: 1.10.1) | GraphRAG components: chunking, embeddings, retrievers |
| `beautifulsoup4` | `>=4.12.0` (latest: 4.14.3) | HTML document parsing |
| `pydantic` | `>=2.0.0` | Data validation and schemas |

**Note**: The `neo4j` driver package should already be installed if you completed Lab 2.

## neo4j-graphrag Library Components

This lab uses the official [neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python) library:

| Component | Module | Purpose |
|-----------|--------|---------|
| `FixedSizeSplitter` | `neo4j_graphrag.experimental.components.text_splitters` | Text chunking with overlap |
| `SentenceTransformerEmbeddings` | `neo4j_graphrag.embeddings` | Local embedding generation |
| `create_vector_index` | `neo4j_graphrag.indexes` | Vector index creation |
| `create_fulltext_index` | `neo4j_graphrag.indexes` | Full-text index creation |
| `VectorRetriever` | `neo4j_graphrag.retrievers` | Semantic similarity search |
| `HybridRetriever` | `neo4j_graphrag.retrievers` | Combined vector + keyword search |
| `VectorCypherRetriever` | `neo4j_graphrag.retrievers` | Graph-aware vector search |
| `HybridCypherRetriever` | `neo4j_graphrag.retrievers` | Graph-aware hybrid search |

## Databricks Embedding Models

This lab also supports Databricks Foundation Model APIs for cloud-based embeddings:

| Model | Dimensions | Context | Notes |
|-------|------------|---------|-------|
| `databricks-gte-large-en` | 1024 | 8,192 tokens | **Recommended** - larger context window |
| `databricks-bge-large-en` | 1024 | 512 tokens | Normalized embeddings |

Reference: [Databricks Embedding Models](https://docs.databricks.com/en/machine-learning/model-serving/query-embedding-models)

## Graph Schema

The lab creates the following document graph structure:

```
(:Document)
    - document_id, filename, document_type, title, source_path, processed_at

(:Chunk)
    - chunk_id, text, embedding, index, document_id, document_title, document_type

(:Document)<-[:FROM_DOCUMENT]-(:Chunk)
(:Chunk)-[:NEXT_CHUNK]->(:Chunk)
(:Document)-[:DESCRIBES]->(:Customer)  // for customer_profile documents
```

## Indexes Created

- **Vector Index** (`chunk_embedding_index`): For semantic similarity search on Chunk.embedding
- **Full-text Index** (`chunk_text_index`): For keyword search on Chunk.text

## Project Structure

```
lab_3_vector_embeddings/
├── __init__.py              # Package exports
├── schemas.py               # Pydantic models for type safety
├── document_processor.py    # HTML parsing and text chunking
├── embedding_provider.py    # Embedding generation (multiple providers)
├── graph_writer.py          # Neo4j graph operations
├── search.py                # Search implementations
├── vector_embeddings.py     # Main CLI script
├── vector_embeddings.ipynb  # Databricks notebook
└── README.md               # This file
```

## Usage

### Databricks Secrets Configuration

Before running, configure secrets in the `neo4j-creds` scope using the Databricks CLI:

```bash
# Create the secrets scope (if not already created)
databricks secrets create-scope neo4j-creds

# Add required secrets
databricks secrets put-secret neo4j-creds username --string-value "neo4j"
databricks secrets put-secret neo4j-creds password --string-value "your_password"
databricks secrets put-secret neo4j-creds url --string-value "neo4j+s://your-instance.databases.neo4j.io"
databricks secrets put-secret neo4j-creds volume_path --string-value "/Volumes/your_catalog/your_schema/your_volume"
```

### Databricks Notebook

1. Upload `vector_embeddings.ipynb` to your Databricks workspace
2. Ensure Databricks Secrets are configured in `neo4j-creds` scope (see above)
3. Install required libraries on cluster or use `%pip install`
4. Run cells sequentially

### Local Development (via Databricks SDK)

For local development, the CLI uses Databricks SDK to fetch secrets from your workspace:

```bash
# Install dependencies
uv sync

# Configure Databricks authentication (one of these methods):
# Option 1: Databricks CLI profile (recommended)
databricks auth login --host https://your-workspace.cloud.databricks.com

# Option 2: Environment variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your_token"

# Run with default settings (sentence-transformers, local, 384 dims)
uv run python -m lab_3_vector_embeddings.vector_embeddings

# Run with Databricks Foundation Model embeddings (cloud, 1024 dims)
uv run python -m lab_3_vector_embeddings.vector_embeddings --provider databricks

# Clear existing document graph first
uv run python -m lab_3_vector_embeddings.vector_embeddings --clear

# Skip search demonstration
uv run python -m lab_3_vector_embeddings.vector_embeddings --skip-demo
```

## Search Capabilities

### Vector Search

Semantic similarity search using embedding cosine similarity:

```python
from neo4j_graphrag.retrievers import VectorRetriever

retriever = VectorRetriever(
    driver=driver,
    index_name="chunk_embedding_index",
    embedder=embedder,
)

results = retriever.get_search_results(
    query_text="investment strategies for moderate risk",
    top_k=5,
)
```

### Full-text Search

Keyword-based search using Lucene:

```cypher
CALL db.index.fulltext.queryNodes("chunk_text_index", "renewable energy")
YIELD node, score
RETURN node, score
ORDER BY score DESC
LIMIT 5
```

### Hybrid Search

Combined vector and keyword search with configurable ranking:

```python
from neo4j_graphrag.retrievers import HybridRetriever
from neo4j_graphrag.types import HybridSearchRanker

retriever = HybridRetriever(
    driver=driver,
    vector_index_name="chunk_embedding_index",
    fulltext_index_name="chunk_text_index",
    embedder=embedder,
)

# NAIVE ranker: max of normalized scores
results = retriever.get_search_results(
    query_text="technology investments",
    top_k=5,
    ranker=HybridSearchRanker.NAIVE,
)

# LINEAR ranker: weighted combination
results = retriever.get_search_results(
    query_text="technology investments",
    top_k=5,
    ranker=HybridSearchRanker.LINEAR,
    alpha=0.7,  # 70% vector, 30% keyword
)
```

### Graph-Aware Search

Search with graph traversal to related entities:

```python
from neo4j_graphrag.retrievers import VectorCypherRetriever

retrieval_query = """
WITH node, score
OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
OPTIONAL MATCH (d)-[:DESCRIBES]->(customer:Customer)
RETURN node, score,
       d.title AS document_title,
       collect(DISTINCT customer) AS related_customers
"""

retriever = VectorCypherRetriever(
    driver=driver,
    index_name="chunk_embedding_index",
    retrieval_query=retrieval_query,
    embedder=embedder,
)
```

## Configuration

### Chunking Configuration

```python
from lab_3_vector_embeddings.schemas import ChunkConfig

config = ChunkConfig(
    chunk_size=4000,       # Characters per chunk
    chunk_overlap=200,     # Overlap between chunks
    approximate=True,      # Avoid mid-word splits
)
```

### Embedding Providers

| Provider | Model | Dimensions | Context | Notes |
|----------|-------|------------|---------|-------|
| `sentence_transformers` | all-MiniLM-L6-v2 | 384 | 512 tokens | Local, no API key needed |
| `databricks` | databricks-gte-large-en | 1024 | 8,192 tokens | **Recommended for production** |

For production workloads, the Databricks `databricks-gte-large-en` model is recommended due to its larger context window (8K tokens) which handles longer text chunks better.

## Troubleshooting

### Index Not Found

Ensure indexes are created before searching:

```cypher
SHOW INDEXES
YIELD name, type, state
WHERE name IN ['chunk_embedding_index', 'chunk_text_index']
```

### Embedding Dimension Mismatch

Vector index dimensions must match embedding model output. Recreate index if needed:

```cypher
DROP INDEX chunk_embedding_index IF EXISTS
```

### Connection Issues

Verify Neo4j URI format:
- Aura: `neo4j+s://xxxxx.databases.neo4j.io`
- Self-hosted with TLS: `neo4j+s://host:7687`
- Self-hosted no TLS: `bolt://host:7687`
