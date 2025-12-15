"""
Pydantic schemas for Lab 3: Vector Embeddings and Hybrid Search.

This module defines type-safe data models for document processing, chunking,
embedding generation, and search operations following neo4j-graphrag best practices.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class DocumentType(str, Enum):
    """Classification of document types based on filename patterns."""

    CUSTOMER_PROFILE = "customer_profile"
    COMPANY_ANALYSIS = "company_analysis"
    COMPANY_REPORT = "company_report"
    BANK_PROFILE = "bank_profile"
    BANK_BRANCH = "bank_branch"
    INVESTMENT_GUIDE = "investment_guide"
    MARKET_ANALYSIS = "market_analysis"
    REGULATORY = "regulatory"
    UNKNOWN = "unknown"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers.

    - SENTENCE_TRANSFORMERS: Local embeddings, no API key required (384 dims)
    - DATABRICKS: Databricks Foundation Model APIs (1024 dims)
    """

    SENTENCE_TRANSFORMERS = "sentence_transformers"
    DATABRICKS = "databricks"


class HybridRankerType(str, Enum):
    """Hybrid search ranking strategies matching neo4j-graphrag HybridSearchRanker."""

    NAIVE = "naive"
    LINEAR = "linear"


class DocumentConfig(BaseModel):
    """Configuration for document processing.

    Attributes:
        volume_path: Databricks Unity Catalog volume path containing HTML files.
        html_subdirectory: Subdirectory within volume containing HTML files.
    """

    volume_path: str = Field(description="Databricks Unity Catalog volume path")
    html_subdirectory: str = Field(default="html", description="HTML subdirectory name")

    @property
    def html_path(self) -> str:
        """Full path to HTML files."""
        return f"{self.volume_path}/{self.html_subdirectory}"


class ChunkConfig(BaseModel):
    """Configuration for text chunking following neo4j-graphrag FixedSizeSplitter.

    Attributes:
        chunk_size: Number of characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.
        approximate: Whether to avoid splitting words mid-token.
    """

    chunk_size: int = Field(default=4000, gt=0, description="Characters per chunk")
    chunk_overlap: int = Field(
        default=200, ge=0, description="Overlapping characters between chunks"
    )
    approximate: bool = Field(
        default=True, description="Avoid splitting words mid-token"
    )

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info: ValidationInfo) -> int:
        """Ensure chunk_overlap is less than chunk_size."""
        data = info.data or {}
        chunk_size = data.get("chunk_size", 4000)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation.

    Attributes:
        provider: Embedding provider to use.
        model_name: Model name for the embedding provider.
        dimensions: Expected embedding vector dimensions.
        endpoint: Databricks Foundation Model endpoint name.

    Databricks Models:
        - databricks-gte-large-en: 1024 dims, 8192 token context (recommended)
        - databricks-bge-large-en: 1024 dims, 512 token context
    """

    provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        description="Embedding provider",
    )
    model_name: str = Field(
        default="all-MiniLM-L6-v2", description="Model name for embedding generation"
    )
    dimensions: int = Field(default=384, gt=0, description="Embedding vector dimensions")
    endpoint: Optional[str] = Field(
        default=None, description="Databricks Foundation Model endpoint name"
    )


class Neo4jConfig(BaseModel):
    """Configuration for Neo4j connection.

    Attributes:
        uri: Neo4j connection URI.
        username: Neo4j username.
        password: Neo4j password.
        database: Neo4j database name.
    """

    uri: str = Field(description="Neo4j connection URI")
    username: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")


class IndexConfig(BaseModel):
    """Configuration for Neo4j indexes following neo4j-graphrag conventions.

    Attributes:
        vector_index_name: Name for the vector index.
        fulltext_index_name: Name for the full-text index.
        chunk_label: Node label for chunks.
        embedding_property: Property name for embedding vectors.
        text_property: Property name for chunk text.
        similarity_fn: Similarity function for vector index.
    """

    vector_index_name: str = Field(
        default="chunk_embedding_index", description="Vector index name"
    )
    fulltext_index_name: str = Field(
        default="chunk_text_index", description="Full-text index name"
    )
    chunk_label: str = Field(default="Chunk", description="Node label for chunks")
    embedding_property: str = Field(
        default="embedding", description="Property for embedding vectors"
    )
    text_property: str = Field(default="text", description="Property for chunk text")
    similarity_fn: str = Field(
        default="cosine", description="Similarity function (cosine or euclidean)"
    )


class SearchConfig(BaseModel):
    """Configuration for search operations.

    Attributes:
        top_k: Number of results to return.
        effective_search_ratio: Candidate pool size multiplier.
        ranker: Hybrid search ranking strategy.
        alpha: Weight for vector score in linear ranker (0-1).
    """

    top_k: int = Field(default=5, gt=0, description="Number of results to return")
    effective_search_ratio: int = Field(
        default=1, gt=0, description="Candidate pool multiplier"
    )
    ranker: HybridRankerType = Field(
        default=HybridRankerType.NAIVE, description="Hybrid ranking strategy"
    )
    alpha: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Vector weight for linear ranker"
    )

    @field_validator("alpha")
    @classmethod
    def validate_alpha_for_linear(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        """Ensure alpha is provided when using linear ranker."""
        data = info.data or {}
        ranker = data.get("ranker")
        if ranker == HybridRankerType.LINEAR and v is None:
            raise ValueError("alpha is required when using linear ranker")
        return v


class ProcessedDocument(BaseModel):
    """A processed HTML document ready for graph storage.

    Attributes:
        document_id: Unique identifier for the document.
        filename: Original HTML filename.
        document_type: Classified document type.
        title: Extracted document title.
        raw_text: Extracted text content.
        source_path: Original file path in Databricks.
        processed_at: Timestamp of processing.
        metadata: Additional metadata.
    """

    document_id: str = Field(description="Unique document identifier")
    filename: str = Field(description="Original HTML filename")
    document_type: DocumentType = Field(description="Classified document type")
    title: str = Field(description="Document title")
    raw_text: str = Field(description="Extracted text content")
    source_path: str = Field(description="Original file path")
    processed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Processing timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProcessedChunk(BaseModel):
    """A text chunk with embedding ready for graph storage.

    Attributes:
        chunk_id: Unique identifier for the chunk.
        document_id: Parent document identifier.
        text: Chunk text content.
        index: Position in the original document.
        embedding: Vector embedding (populated after embedding generation).
        metadata: Additional metadata.
    """

    chunk_id: str = Field(description="Unique chunk identifier")
    document_id: str = Field(description="Parent document identifier")
    text: str = Field(description="Chunk text content")
    index: int = Field(ge=0, description="Position in document")
    embedding: Optional[list[float]] = Field(
        default=None, description="Vector embedding"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EntityMention(BaseModel):
    """An entity mention found in document text.

    Attributes:
        entity_id: Identifier of the mentioned entity.
        entity_type: Type of entity (Customer, Company, Stock).
        entity_name: Display name of the entity.
        chunk_ids: Chunks where this entity is mentioned.
    """

    entity_id: str = Field(description="Entity identifier")
    entity_type: str = Field(description="Entity type (Customer, Company, Stock)")
    entity_name: str = Field(description="Entity display name")
    chunk_ids: list[str] = Field(default_factory=list, description="Mentioning chunk IDs")


class SearchResult(BaseModel):
    """A search result from vector, full-text, or hybrid search.

    Attributes:
        chunk_id: Chunk identifier.
        document_id: Parent document identifier.
        text: Chunk text content.
        score: Relevance score.
        document_title: Title of parent document.
        document_type: Type of parent document.
        metadata: Additional result metadata.
    """

    chunk_id: str = Field(description="Chunk identifier")
    document_id: str = Field(description="Parent document identifier")
    text: str = Field(description="Chunk text")
    score: float = Field(description="Relevance score")
    document_title: Optional[str] = Field(default=None, description="Document title")
    document_type: Optional[str] = Field(default=None, description="Document type")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Result metadata")


class GraphTraversalResult(BaseModel):
    """Result from graph-aware retrieval with entity traversal.

    Attributes:
        search_results: Initial search results.
        related_customers: Customer nodes connected via graph traversal.
        related_companies: Company nodes connected via graph traversal.
        related_stocks: Stock nodes connected via graph traversal.
    """

    search_results: list[SearchResult] = Field(description="Initial search results")
    related_customers: list[dict[str, Any]] = Field(
        default_factory=list, description="Related customer nodes"
    )
    related_companies: list[dict[str, Any]] = Field(
        default_factory=list, description="Related company nodes"
    )
    related_stocks: list[dict[str, Any]] = Field(
        default_factory=list, description="Related stock nodes"
    )
