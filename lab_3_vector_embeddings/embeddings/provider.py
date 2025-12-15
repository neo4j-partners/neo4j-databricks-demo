"""
Embedding provider module for Lab 3: Vector Embeddings and Hybrid Search.

This module generates vector embeddings for text chunks, enabling semantic similarity
search. It implements the neo4j-graphrag Embedder interface for compatibility with
the library's retrievers.

Supported Providers:

1. **Sentence Transformers** (local, default for development):
   - Model: all-MiniLM-L6-v2
   - Dimensions: 384
   - No API key required, runs entirely on local CPU/GPU
   - Best for: Local development, testing, offline environments

2. **Databricks Foundation Models** (cloud, recommended for production):
   - Model: databricks-gte-large-en (recommended)
   - Dimensions: 1024
   - Context: 8192 tokens (handles longer text chunks)
   - Authentication: Uses Databricks SDK (token from .env or CLI profile)
   - Best for: Production workloads, higher quality embeddings

Key Functions:
    - create_embedder(): Factory function to instantiate the correct provider
    - embed_chunks(): Batch embed all chunks, returning chunks with embedding vectors
    - validate_embeddings(): Verify all chunks have valid embedding dimensions
    - get_default_config_for_provider(): Get recommended settings for each provider

Usage Example:
    config = get_default_config_for_provider(EmbeddingProvider.DATABRICKS)
    embedder = create_embedder(config)
    embedded_chunks = embed_chunks(chunks, embedder)

Reference: https://docs.databricks.com/en/machine-learning/model-serving/query-embedding-models
"""

from typing import Optional

from neo4j_graphrag.embeddings import Embedder, SentenceTransformerEmbeddings

from ..models import EmbeddingConfig, EmbeddingProvider, ProcessedChunk


class DatabricksEmbeddings(Embedder):
    """Embedder implementation for Databricks Foundation Model APIs.

    This embedder uses the databricks-langchain DatabricksEmbeddings class
    internally, which provides:
    - Automatic authentication via Databricks SDK
    - Support for Foundation Model embedding endpoints
    - OpenAI-compatible API format

    Available models:
    - databricks-gte-large-en: 1024 dims, 8192 token context (recommended)
    - databricks-bge-large-en: 1024 dims, 512 token context

    Reference: https://docs.databricks.com/en/machine-learning/model-serving/query-embedding-models
    """

    def __init__(
        self,
        endpoint: str = "databricks-gte-large-en",
    ) -> None:
        """Initialize Databricks embedder.

        Args:
            endpoint: Name of the Databricks embedding model endpoint.
                     Defaults to 'databricks-gte-large-en' for best context window.
        """
        super().__init__()
        self.endpoint = endpoint
        self._embedder: Optional[object] = None

    def _get_embedder(self) -> object:
        """Get or create the databricks-langchain embedder."""
        if self._embedder is None:
            try:
                from databricks_langchain import DatabricksEmbeddings as DBEmbeddings

                self._embedder = DBEmbeddings(endpoint=self.endpoint)
            except ImportError as e:
                raise ImportError(
                    "databricks-langchain is required for Databricks embeddings. "
                    "Install with: pip install databricks-langchain"
                ) from e
        return self._embedder

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector (1024 dimensions).
        """
        embedder = self._get_embedder()
        return embedder.embed_query(text)


def create_embedder(config: EmbeddingConfig) -> Embedder:
    """Create an embedder based on configuration.

    Factory function that creates the appropriate neo4j-graphrag Embedder
    implementation based on the configured provider.

    Args:
        config: Embedding configuration.

    Returns:
        Embedder instance ready for use.

    Raises:
        ValueError: If an unsupported provider is specified.
    """
    if config.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
        return SentenceTransformerEmbeddings(model=config.model_name)

    if config.provider == EmbeddingProvider.DATABRICKS:
        endpoint = config.endpoint or config.model_name
        return DatabricksEmbeddings(endpoint=endpoint)

    raise ValueError(f"Unsupported embedding provider: {config.provider}")


def embed_chunks(
    chunks: list[ProcessedChunk],
    embedder: Embedder,
    batch_size: int = 32,
) -> list[ProcessedChunk]:
    """Generate embeddings for a list of chunks.

    Args:
        chunks: List of chunks to embed.
        embedder: Embedder instance to use.
        batch_size: Number of chunks to process in each batch (for rate limiting).

    Returns:
        List of chunks with embeddings populated.
    """
    embedded_chunks: list[ProcessedChunk] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        for chunk in batch:
            embedding = embedder.embed_query(chunk.text)
            embedded_chunk = ProcessedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                index=chunk.index,
                embedding=embedding,
                metadata=chunk.metadata,
            )
            embedded_chunks.append(embedded_chunk)

    return embedded_chunks


def validate_embeddings(
    chunks: list[ProcessedChunk],
    expected_dimensions: int,
) -> tuple[bool, list[str]]:
    """Validate that all chunks have embeddings with correct dimensions.

    Args:
        chunks: List of chunks to validate.
        expected_dimensions: Expected embedding vector dimension.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors: list[str] = []

    for chunk in chunks:
        if chunk.embedding is None:
            errors.append(f"Chunk {chunk.chunk_id} has no embedding")
        elif len(chunk.embedding) != expected_dimensions:
            errors.append(
                f"Chunk {chunk.chunk_id} has {len(chunk.embedding)} dimensions, "
                f"expected {expected_dimensions}"
            )

    return len(errors) == 0, errors


def get_default_config_for_provider(provider: EmbeddingProvider) -> EmbeddingConfig:
    """Get default embedding configuration for a provider.

    Args:
        provider: Embedding provider to configure.

    Returns:
        EmbeddingConfig with appropriate defaults for the provider.
    """
    if provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
        return EmbeddingConfig(
            provider=provider,
            model_name="all-MiniLM-L6-v2",
            dimensions=384,
        )

    if provider == EmbeddingProvider.DATABRICKS:
        return EmbeddingConfig(
            provider=provider,
            model_name="databricks-gte-large-en",
            dimensions=1024,
            endpoint="databricks-gte-large-en",
        )

    raise ValueError(f"Unknown provider: {provider}")
