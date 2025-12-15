"""
Embeddings subpackage for Lab 3: Vector Embeddings and Hybrid Search.

This package provides embedding generation using:
- Sentence Transformers (local, 384 dimensions)
- Databricks Foundation Models (cloud, 1024 dimensions)
"""

from .provider import (
    DatabricksEmbeddings,
    create_embedder,
    embed_chunks,
    get_default_config_for_provider,
    validate_embeddings,
)

__all__ = [
    "DatabricksEmbeddings",
    "create_embedder",
    "embed_chunks",
    "get_default_config_for_provider",
    "validate_embeddings",
]
