# Databricks Embedding Models and Neo4j GraphRAG Compatibility

## Research Summary

This document examines the embedding models offered by Databricks and their compatibility with the Neo4j GraphRAG Python library.

---

## Databricks Embedding Models

Databricks offers two embedding models through their Foundation Model APIs:

### databricks-gte-large-en

- Provider: Alibaba NLP
- Dimensions: 1024
- Context window: 8,192 tokens
- Does not generate normalized embeddings
- Use cases: Retrieval, classification, question-answering, clustering, semantic search, and RAG applications

### databricks-bge-large-en

- Provider: BAAI (Beijing Academy of Artificial Intelligence)
- Dimensions: 1024
- Context window: 512 tokens
- Generates normalized embeddings
- Supports optional instruction parameters for improved retrieval performance
- Use cases: Vector indexing for LLMs, retrieval augmented generation, and semantic search

### API Access

Both models are accessible via an OpenAI-compatible API format. Databricks provides multiple query methods including an OpenAI client wrapper, REST API, and LangChain integration.

Reference: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/query-embedding-models

---

## Neo4j GraphRAG Embedder Architecture

### Core Interface

The Neo4j GraphRAG library defines an abstract base class for all embedders.

Location: `src/neo4j_graphrag/embeddings/base.py` (lines 26-50)

The interface requires only one method to be implemented: `embed_query(text: str) -> list[float]`. This method takes a string and returns a list of floating point numbers representing the embedding vector.

### Existing OpenAI Implementation

The library includes an OpenAI embeddings implementation that demonstrates the pattern for API-based embedders.

Location: `src/neo4j_graphrag/embeddings/openai.py` (lines 29-109)

Key observations:
- The OpenAI implementation uses the standard OpenAI Python client
- It accepts additional keyword arguments that are passed through to the client initialization (line 40)
- The embed_query method calls `client.embeddings.create()` with the input text and model name (lines 71-76)

### Custom Embedder Pattern

The library provides an example of how to create a custom embedder implementation.

Location: `examples/customize/embeddings/custom_embeddings.py` (lines 7-13)

The pattern is straightforward: inherit from the Embedder class, call the parent constructor, and implement the embed_query method.

---

## Compatibility Analysis

### Why Databricks Models Are Compatible

Databricks embedding models expose an OpenAI-compatible API. This means any client that can communicate with OpenAI's embedding endpoint can also communicate with Databricks by changing the base URL and authentication.

The Neo4j GraphRAG OpenAIEmbeddings class accepts keyword arguments that are passed to the OpenAI client. The OpenAI Python client accepts a `base_url` parameter that can be pointed at any OpenAI-compatible endpoint, including Databricks Model Serving endpoints.

### Integration Approach: Using OpenAI Client with Databricks

The existing OpenAIEmbeddings class in Neo4j GraphRAG can potentially be configured to work with Databricks by providing the Databricks serving endpoint URL and authentication token through the constructor's keyword arguments.

Reference: `src/neo4j_graphrag/embeddings/openai.py` line 94 shows how kwargs are passed to the OpenAI client

### Integration Approach: Custom Embedder

A dedicated Databricks embedder could be created following the pattern shown in `examples/customize/embeddings/custom_embeddings.py`. This would:

1. Inherit from the Embedder base class
2. Initialize a Databricks SDK client or HTTP client in the constructor
3. Implement embed_query to call the Databricks Model Serving endpoint
4. Return the 1024-dimensional embedding vector as a list of floats

### Dimension Compatibility

Both Databricks embedding models produce 1024-dimensional vectors. This is compatible with Neo4j vector indexes, which support configurable dimensions. When creating a vector index in Neo4j, the dimension should be set to 1024 to match the Databricks embedding output.

---

## Summary

Databricks provides two enterprise-grade embedding models (GTE Large and BGE Large) with OpenAI-compatible APIs. The Neo4j GraphRAG Python library has a simple and extensible embedder interface that can accommodate Databricks embeddings either through configuration of the existing OpenAI embedder or through a minimal custom implementation. The 1024-dimensional output from both Databricks models is well-suited for use with Neo4j vector search capabilities.

---

## References

- Databricks Embedding Models: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/query-embedding-models
- Databricks Foundation Models: https://docs.databricks.com/en/machine-learning/foundation-models/supported-models.html
- Neo4j GraphRAG Embedder Base Class: `src/neo4j_graphrag/embeddings/base.py`
- Neo4j GraphRAG OpenAI Embedder: `src/neo4j_graphrag/embeddings/openai.py`
- Neo4j GraphRAG Custom Embedder Example: `examples/customize/embeddings/custom_embeddings.py`
