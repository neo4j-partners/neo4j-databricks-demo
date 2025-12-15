"""
Lab 3: Vector Embeddings and Hybrid Search

This lab processes HTML documents from the Databricks volume, generates vector
embeddings, stores them in Neo4j as a document graph, and enables both semantic
vector search and keyword-based full-text search through a hybrid search interface.

Subpackages:
    - models: Pydantic models for type-safe data handling
    - processing: HTML parsing, text extraction, and chunking
    - embeddings: Embedder implementations (Sentence Transformers, Databricks)
    - graph: Neo4j document graph writing operations
    - search: Vector, full-text, and hybrid search implementations
"""

# Models
from .models import (
    ChunkConfig,
    DocumentType,
    EmbeddingConfig,
    EmbeddingProvider,
    GraphTraversalResult,
    HybridRankerType,
    IndexConfig,
    Neo4jConfig,
    ProcessedChunk,
    ProcessedDocument,
    SearchConfig,
    SearchResult,
)

# Processing
from .processing import (
    chunk_document_sync,
    process_documents_sync,
    process_html_content,
    process_html_file,
)

# Embeddings
from .embeddings import (
    DatabricksEmbeddings,
    create_embedder,
    embed_chunks,
    get_default_config_for_provider,
    validate_embeddings,
)

# Graph
from .graph import (
    GraphWriter,
    write_document_graph,
)

# Search
from .search import (
    DocumentSearcher,
    create_searcher,
)

__all__ = [
    # Models
    "ChunkConfig",
    "DocumentType",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "GraphTraversalResult",
    "HybridRankerType",
    "IndexConfig",
    "Neo4jConfig",
    "ProcessedChunk",
    "ProcessedDocument",
    "SearchConfig",
    "SearchResult",
    # Processing
    "chunk_document_sync",
    "process_documents_sync",
    "process_html_content",
    "process_html_file",
    # Embeddings
    "DatabricksEmbeddings",
    "create_embedder",
    "embed_chunks",
    "get_default_config_for_provider",
    "validate_embeddings",
    # Graph
    "GraphWriter",
    "write_document_graph",
    # Search
    "DocumentSearcher",
    "create_searcher",
]
