"""
Graph subpackage for Lab 3: Vector Embeddings and Hybrid Search.

This package handles Neo4j graph operations including:
- Index and constraint creation
- Document and Chunk node writing
- Relationship creation (FROM_DOCUMENT, NEXT_CHUNK, DESCRIBES)
"""

from .writer import (
    GraphWriter,
    write_document_graph,
)

__all__ = [
    "GraphWriter",
    "write_document_graph",
]
