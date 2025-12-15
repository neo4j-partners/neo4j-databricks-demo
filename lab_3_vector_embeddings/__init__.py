"""
Lab 3: Vector Embeddings and Hybrid Search

This lab processes HTML documents from the Databricks volume, generates vector
embeddings, stores them in Neo4j as a document graph, and enables both semantic
vector search and keyword-based full-text search through a hybrid search interface.

Components:
    - schemas: Pydantic models for type-safe data handling
    - document_processor: HTML parsing and text extraction
    - embedding_provider: Embedder implementations for multiple providers
    - graph_writer: Neo4j document graph writing
    - search: Vector, full-text, and hybrid search implementations
"""

from .schemas import (
    DocumentConfig,
    ChunkConfig,
    EmbeddingConfig,
    SearchConfig,
    ProcessedDocument,
    ProcessedChunk,
    SearchResult,
)

__all__ = [
    "DocumentConfig",
    "ChunkConfig",
    "EmbeddingConfig",
    "SearchConfig",
    "ProcessedDocument",
    "ProcessedChunk",
    "SearchResult",
]
