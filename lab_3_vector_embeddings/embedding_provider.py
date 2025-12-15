"""
Embedding provider module for Lab 3: Vector Embeddings and Hybrid Search.

This module provides embedding generation using neo4j-graphrag Embedder interface
with support for multiple providers: OpenAI, Sentence Transformers, and Databricks
Foundation Models.
"""

import os
from typing import Optional

from neo4j_graphrag.embeddings import Embedder, OpenAIEmbeddings, SentenceTransformerEmbeddings

from .schemas import EmbeddingConfig, EmbeddingProvider, ProcessedChunk


class DatabricksEmbeddings(Embedder):
    """Embedder implementation for Databricks Foundation Model endpoints.

    This embedder calls Databricks Foundation Model serving endpoints
    for embedding generation. Requires databricks-sdk to be installed.
    """

    def __init__(
        self,
        endpoint_name: str,
        host: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Initialize Databricks embedder.

        Args:
            endpoint_name: Name of the Foundation Model serving endpoint.
            host: Databricks workspace URL. Uses DATABRICKS_HOST env var if not provided.
            token: Databricks access token. Uses DATABRICKS_TOKEN env var if not provided.
        """
        super().__init__()
        self.endpoint_name = endpoint_name
        self.host = host or os.environ.get("DATABRICKS_HOST")
        self.token = token or os.environ.get("DATABRICKS_TOKEN")

        if not self.host:
            raise ValueError(
                "Databricks host not provided. Set DATABRICKS_HOST environment variable "
                "or pass host parameter."
            )
        if not self.token:
            raise ValueError(
                "Databricks token not provided. Set DATABRICKS_TOKEN environment variable "
                "or pass token parameter."
            )

        # Initialize client lazily to avoid import errors when not using Databricks
        self._client: Optional[object] = None

    def _get_client(self) -> object:
        """Get or create Databricks workspace client."""
        if self._client is None:
            try:
                from databricks.sdk import WorkspaceClient

                self._client = WorkspaceClient(host=self.host, token=self.token)
            except ImportError as e:
                raise ImportError(
                    "databricks-sdk is required for Databricks embeddings. "
                    "Install with: pip install databricks-sdk"
                ) from e
        return self._client

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        client = self._get_client()

        # Call the Foundation Model serving endpoint
        response = client.serving_endpoints.query(  # type: ignore[attr-defined]
            name=self.endpoint_name,
            input=text,
        )

        # Extract embedding from response
        if hasattr(response, "data") and response.data:
            return response.data[0].embedding
        if hasattr(response, "embedding"):
            return response.embedding

        raise ValueError(f"Unexpected response format from Databricks endpoint: {response}")


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

    if config.provider == EmbeddingProvider.OPENAI:
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key in EmbeddingConfig."
            )
        return OpenAIEmbeddings(model=config.model_name, api_key=api_key)

    if config.provider == EmbeddingProvider.DATABRICKS:
        if not config.endpoint:
            raise ValueError(
                "Databricks endpoint name required. Provide endpoint in EmbeddingConfig."
            )
        return DatabricksEmbeddings(endpoint_name=config.endpoint)

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

    if provider == EmbeddingProvider.OPENAI:
        return EmbeddingConfig(
            provider=provider,
            model_name="text-embedding-3-small",
            dimensions=1536,
        )

    if provider == EmbeddingProvider.DATABRICKS:
        return EmbeddingConfig(
            provider=provider,
            model_name="databricks-gte-large-en",
            dimensions=1024,
        )

    raise ValueError(f"Unknown provider: {provider}")
