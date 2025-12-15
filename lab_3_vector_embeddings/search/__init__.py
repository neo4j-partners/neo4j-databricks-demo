"""
Search subpackage for Lab 3: Vector Embeddings and Hybrid Search.

This package provides search capabilities using neo4j-graphrag retrievers:
- VectorRetriever for semantic similarity search
- HybridRetriever for combined vector + keyword search
- VectorCypherRetriever for graph-aware vector search
- HybridCypherRetriever for graph-aware hybrid search
"""

from .searcher import (
    DocumentSearcher,
    create_searcher,
)

__all__ = [
    "DocumentSearcher",
    "create_searcher",
]
