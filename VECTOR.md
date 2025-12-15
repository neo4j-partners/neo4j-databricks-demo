# Lab 3 Proposal: Vector Embeddings and Hybrid Search

## Problem Statement

Labs 1 and 2 establish a foundation for structured financial data: Lab 1 uploads CSV files containing transactional records and HTML documents containing rich narrative content to Databricks Unity Catalog. Lab 2 imports the structured CSV data into Neo4j as a connected graph of Customers, Banks, Accounts, Companies, Stocks, Positions, and Transactions.

However, the HTML documents remain unutilized in Neo4j. These documents contain valuable unstructured information including customer profiles with investment preferences and life circumstances, investment strategy guides, market analysis reports, company quarterly reports, regulatory compliance documentation, and sector trend analysis. This narrative content cannot be queried through traditional Cypher pattern matching.

Without vector embeddings and semantic search capabilities, users cannot ask natural language questions like "Which customers are interested in renewable energy investments?" or "What does our compliance documentation say about risk disclosure requirements?" The structured graph data and unstructured document knowledge exist in isolation, limiting the analytical power of the combined system.

## Proposed Solution

Create a new Lab 3 that processes HTML documents from the Databricks volume, generates vector embeddings, stores them in Neo4j as a document graph, and enables both semantic vector search and keyword-based full-text search through a hybrid search interface.

The solution leverages the neo4j-graphrag-python library, which provides production-ready components for text chunking, embedding generation, index management, and hybrid retrieval. This library is the official Neo4j library for building GraphRAG applications and follows best practices established by the Neo4j engineering team.

The solution connects the document graph to the existing financial entity graph, allowing graph-aware retrieval that combines semantic similarity with relationship traversal. For example, a semantic search for "technology investment strategies" can return relevant document chunks and then traverse relationships to find which customers have profiles mentioning those strategies and what technology stocks they currently hold.

## Neo4j GraphRAG Python Library Components

The implementation uses specific components from the neo4j-graphrag-python library organized across several modules.

### Text Splitting Components

The FixedSizeSplitter from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter provides the primary chunking implementation. This splitter accepts configuration for chunk_size, chunk_overlap, and an approximate parameter that avoids splitting words mid-token by adjusting chunk boundaries to whitespace. The library also provides LangChainTextSplitterAdapter and LlamaIndexTextSplitterAdapter in the same module for integration with alternative chunking strategies when needed.

The TextChunk and TextChunks types from neo4j_graphrag.experimental.components.types define the data structures for chunked text. Each TextChunk contains the text content, an index indicating position within the source document, optional metadata including the embedding vector, and a unique identifier for tracking through the pipeline.

### Embedding Components

The Embedder abstract base class from neo4j_graphrag.embeddings.base defines the interface all embedding implementations follow. The embed_query method accepts text and returns a list of floats representing the embedding vector. The base class includes built-in rate limiting with exponential backoff through an optional RateLimitHandler.

The OpenAIEmbeddings class from neo4j_graphrag.embeddings.openai provides integration with OpenAI embedding models including text-embedding-ada-002 and text-embedding-3-large. This class also supports Azure OpenAI deployments through additional configuration parameters.

The SentenceTransformerEmbeddings class from neo4j_graphrag.embeddings.sentence_transformers enables local embedding generation using models from the Sentence Transformers library such as all-MiniLM-L6-v2. This option avoids API calls and keeps data on-premises for privacy-sensitive deployments.

The TextChunkEmbedder component from neo4j_graphrag.experimental.components.embedder wraps any Embedder implementation and processes TextChunks in batch, storing the resulting embedding vector in each chunk's metadata under the "embedding" key.

### Index Management Functions

The create_vector_index function from neo4j_graphrag.indexes creates a semantic vector index in Neo4j. Parameters include the Neo4j driver, index name, node label, embedding property name, vector dimensions, and similarity function which accepts either "cosine" or "euclidean" values.

The create_fulltext_index function from neo4j_graphrag.indexes creates a Lucene-based full-text index for keyword search. Parameters include the Neo4j driver, index name, node label, and a list of node properties to index.

The upsert_vectors function from neo4j_graphrag.indexes provides batch operations for writing embedding vectors to existing nodes, supporting both node and relationship embeddings through the EntityType parameter.

### Retriever Components

The VectorRetriever class from neo4j_graphrag.retrievers.vector performs semantic similarity search against a vector index. Configuration includes the Neo4j driver, index name, an optional Embedder for automatic query embedding, and return_properties specifying which node properties to include in results. The get_search_results method accepts query text or a pre-computed query vector, top_k for result count, effective_search_ratio for candidate pool sizing, and optional filters for pre-filtering.

The VectorCypherRetriever class from neo4j_graphrag.retrievers.vector extends vector search with graph traversal by accepting a retrieval_query parameter containing Cypher that executes after finding similar nodes. This enables graph-aware retrieval patterns where vector search results traverse relationships to gather additional context.

The HybridRetriever class from neo4j_graphrag.retrievers.hybrid combines vector similarity search with full-text keyword search. Configuration includes both vector_index_name and fulltext_index_name parameters. The get_search_results method accepts a ranker parameter that selects the score combination strategy.

The HybridCypherRetriever class from neo4j_graphrag.retrievers.hybrid combines hybrid search with graph traversal, applying a custom Cypher query after the combined vector and full-text search.

The HybridSearchRanker enumeration from neo4j_graphrag.retrievers defines two ranking strategies. The NAIVE ranker normalizes scores from each index independently and takes the maximum score when a node appears in both result sets. The LINEAR ranker applies configurable weights through an alpha parameter where alpha controls the balance between vector similarity at alpha equals one and full-text relevance at alpha equals zero.

### Pipeline Components

The SimpleKGPipeline class from neo4j_graphrag.experimental.pipeline.kg_builder orchestrates the complete workflow from text input through chunking, embedding, optional entity extraction, and graph writing. The pipeline supports async execution for concurrent processing.

The LexicalGraphConfig class from neo4j_graphrag.experimental.components.types defines the graph schema configuration including node labels for documents and chunks, property names for text and embeddings, and relationship types connecting the document graph structure.

## Document Processing Pipeline

The pipeline reads HTML files from the Databricks volume and extracts clean text content by removing HTML markup while preserving document structure and semantic meaning. Each document is associated with metadata including the original filename, document type derived from naming conventions, and any entity references identified in the content.

Text chunking uses the FixedSizeSplitter with a chunk_size of four thousand characters and chunk_overlap of two hundred characters. The approximate parameter is enabled to avoid mid-word splits by adjusting boundaries to whitespace. This configuration balances semantic coherence with embedding model input limits while ensuring relevant passages are not split at critical points.

The chunking process produces TextChunk objects that maintain references to position within the source document. The NEXT_CHUNK relationships between adjacent chunks enable retrieval systems to expand context when needed.

## Embedding Generation

Vector embeddings transform text chunks into dense numerical representations that capture semantic meaning. The implementation uses the Embedder interface to support multiple providers.

For Databricks deployments, the lab provides a custom Embedder implementation that calls Databricks Foundation Model endpoints. For local development, SentenceTransformerEmbeddings with the all-MiniLM-L6-v2 model provides 384-dimensional embeddings without external API dependencies. For production deployments requiring higher quality embeddings, OpenAIEmbeddings with text-embedding-3-large provides 3072-dimensional embeddings.

The TextChunkEmbedder component wraps the selected Embedder and processes all chunks, storing embedding vectors in the metadata dictionary. The pipeline validates that all chunks receive embeddings before proceeding to graph writing.

Embedding dimensions must match the Neo4j vector index configuration passed to create_vector_index. The lab documents this dependency clearly and provides configuration options for different embedding providers.

## Neo4j Graph Structure

The document graph introduces two new node types following the LexicalGraphConfig defaults: Document nodes representing source HTML files and Chunk nodes representing embedded text segments.

Document nodes store metadata including the original filename, document type classification, upload timestamp, and source path in Databricks. Each Document node connects to its Chunk nodes through a FROM_DOCUMENT relationship as defined in the chunk_to_document_relationship_type configuration.

Chunk nodes store the text content in a property named by chunk_text_property, the embedding vector in a property named by chunk_embedding_property, the chunk index within its parent document, and metadata about chunk boundaries. Adjacent chunks within the same document connect through NEXT_CHUNK relationships as defined in next_chunk_relationship_type, enabling sequential traversal when expanded context is needed.

The document graph connects to the existing financial entity graph through typed relationships. Customer profile documents link to their corresponding Customer nodes through a DESCRIBES relationship. Company analysis documents link to Company nodes. Investment strategy documents link to risk profile categories that can match Customer risk tolerance attributes.

Entity extraction during document processing identifies mentions of known entities such as customer names, company names, and stock tickers. These extracted references create additional MENTIONS relationships between Chunk nodes and the entity nodes they reference, enabling graph traversal from semantic search results to structured data.

## Index Configuration

The lab uses create_vector_index to create a semantic vector index on Chunk nodes. The configuration specifies the embedding property name matching chunk_embedding_property, vector dimensions matching the embedding model output, and cosine as the similarity function for normalized embedding vectors.

The lab uses create_fulltext_index to create a keyword search index on Chunk nodes. The configuration targets the text content property matching chunk_text_property. The full-text index uses Neo4j's native Lucene integration to support term matching, phrase queries, and fuzzy matching.

Both indexes support the hybrid search pattern implemented by HybridRetriever where results from vector similarity and keyword matching combine to produce final rankings.

## Search Capabilities

The lab demonstrates three search patterns using the retriever components.

Vector search uses VectorRetriever configured with the vector index name and an Embedder instance matching the embedding model used during ingestion. The get_search_results method accepts a query_text parameter which the retriever embeds automatically, then queries the vector index for the top_k most similar chunks ranked by cosine similarity. This search pattern excels at finding conceptually related content even when exact terminology differs between query and document.

Full-text search queries the full-text index directly through Cypher using the db.index.fulltext.queryNodes procedure. This search pattern uses the full-text index to match terms directly, supporting exact matches, phrase matching, and wildcard patterns. Full-text search excels when users know specific terminology or need to find exact references.

Hybrid search uses HybridRetriever configured with both vector_index_name and fulltext_index_name. The get_search_results method accepts a ranker parameter selecting either HybridSearchRanker.NAIVE or HybridSearchRanker.LINEAR. The NAIVE ranker normalizes scores independently and takes the maximum when a chunk appears in both result sets. The LINEAR ranker accepts an alpha parameter to weight vector similarity against full-text relevance, where alpha of 0.7 weights vector search at seventy percent and full-text at thirty percent.

## Graph-Aware Retrieval

Beyond basic search, the lab demonstrates retrieval patterns using VectorCypherRetriever and HybridCypherRetriever that leverage graph relationships after finding relevant chunks.

The VectorCypherRetriever accepts a retrieval_query parameter containing Cypher that executes after vector search. A search for customer investment preferences includes a retrieval query that traverses from matching Chunk nodes through FROM_DOCUMENT to Document nodes, then through DESCRIBES relationships to Customer nodes. Further traversal through HAS_ACCOUNT, HAS_POSITION, and OF_SECURITY relationships reveals the actual portfolio holdings of customers matching the search criteria.

The HybridCypherRetriever combines hybrid search with graph traversal. A search for company analysis documents uses a retrieval query that traverses from matching chunks through MENTIONS relationships to Company nodes and then through OF_COMPANY relationships to Stock nodes, revealing current market data for companies discussed in the matched content.

These graph-aware patterns demonstrate the power of combining semantic search with structured graph traversal, enabling queries that neither pure vector search nor pure graph queries could answer alone.

## Requirements

### Prerequisite Requirements

Lab 3 requires successful completion of Lab 1 with HTML files uploaded to the Databricks volume.

Lab 3 requires successful completion of Lab 2 with the financial entity graph populated in Neo4j.

The Neo4j instance must support vector indexes, requiring Neo4j version 5.11 or later, or Neo4j Aura with vector search capability enabled.

An embedding model must be accessible, either through Databricks Foundation Model endpoints, OpenAI API, or a locally running sentence transformer model.

The neo4j-graphrag-python library version 1.0.0 or later must be installed.

### Functional Requirements

The system must read HTML files from the Databricks Unity Catalog volume specified in the environment configuration.

The system must extract text content from HTML documents while preserving meaningful structure and removing markup.

The system must chunk text content using FixedSizeSplitter with configurable chunk_size and chunk_overlap parameters.

The system must generate vector embeddings for each text chunk using an Embedder implementation.

The system must use TextChunkEmbedder to process chunks in batch and store embeddings in chunk metadata.

The system must create Document nodes in Neo4j with properties for filename, document type, and processing timestamp.

The system must create Chunk nodes in Neo4j with properties for text content, embedding vector, chunk index, and metadata following LexicalGraphConfig conventions.

The system must create FROM_DOCUMENT relationships between Chunk nodes and their parent Document nodes.

The system must create NEXT_CHUNK relationships between adjacent Chunk nodes within the same document.

The system must use create_vector_index to create a vector index on the Chunk embedding property with appropriate dimension and similarity configuration.

The system must use create_fulltext_index to create a full-text index on the Chunk text property.

The system must provide vector search using VectorRetriever that accepts a text query and returns matching chunks with similarity scores.

The system must provide full-text search that accepts a keyword query and returns matching chunks with relevance scores.

The system must provide hybrid search using HybridRetriever that combines vector and full-text results with configurable HybridSearchRanker.

### Entity Linking Requirements

The system must identify customer name mentions in document text and create DESCRIBES relationships between Customer profile Document nodes and corresponding Customer nodes.

The system must identify company name mentions in document text and create MENTIONS relationships between Chunk nodes and corresponding Company nodes.

The system must identify stock ticker mentions in document text and create MENTIONS relationships between Chunk nodes and corresponding Stock nodes.

### Verification Requirements

The system must verify that the document count in Neo4j matches the HTML file count in the Databricks volume.

The system must verify that chunk counts are reasonable given document lengths and chunk size configuration.

The system must verify that all chunks have embedding vectors with the expected dimension.

The system must verify that the vector index is online and queryable.

The system must verify that the full-text index is online and queryable.

The system must demonstrate successful vector search with VectorRetriever returning relevant results for sample queries.

The system must demonstrate successful full-text search returning relevant results for sample queries.

The system must demonstrate successful hybrid search with HybridRetriever using both NAIVE and LINEAR rankers.

The system must demonstrate graph traversal from search results to connected financial entities using VectorCypherRetriever.

## Implementation Plan

### Phase 1: Analysis

Review the neo4j-graphrag-python library source code in the experimental.components.text_splitters, embeddings, indexes, and retrievers modules.

Document the HTML file structure and content types present in the data directory.

Identify entity mentions in sample documents to inform the entity extraction approach.

List all files requiring creation including the main processing script, utility modules, and Jupyter notebook.

Identify dependencies including neo4j-graphrag, beautifulsoup4 for HTML parsing, sentence-transformers for local embeddings, and openai for cloud embeddings.

### Phase 2: Implementation

Create the document processing module with HTML parsing and text extraction functions.

Create the text chunking module using FixedSizeSplitter with configurable parameters.

Create the embedding module implementing the Embedder interface for Databricks Foundation Model endpoints and using SentenceTransformerEmbeddings and OpenAIEmbeddings for alternative providers.

Create the Neo4j graph writing module for Document nodes, Chunk nodes, and relationships following LexicalGraphConfig conventions.

Create the index management module using create_vector_index and create_fulltext_index functions.

Create the search module implementing VectorRetriever, HybridRetriever, VectorCypherRetriever, and HybridCypherRetriever configurations.

Create the entity linking module for identifying entity mentions and creating relationships.

Create the main processing script that orchestrates the complete pipeline.

Create the Jupyter notebook with step-by-step execution and explanatory documentation.

Update pyproject.toml with neo4j-graphrag and related dependencies.

Update the project README with Lab 3 documentation.

### Phase 3: Verification

Run the complete processing pipeline against the full HTML document set.

Verify all node and relationship counts match expectations.

Verify index creation using Neo4j browser to confirm indexes are online.

Test VectorRetriever with diverse queries covering different document types.

Test full-text search with keyword queries.

Test HybridRetriever with HybridSearchRanker.NAIVE and HybridSearchRanker.LINEAR configurations.

Demonstrate VectorCypherRetriever queries that traverse from search results to financial entities.

Verify code follows project patterns established in Labs 1 and 2.

Run any existing tests and ensure no regression.

## Expected Outcomes

Lab 3 provides workshop participants with hands-on experience implementing a document embedding pipeline using the neo4j-graphrag-python library components including FixedSizeSplitter, TextChunkEmbedder, and the index management functions.

Participants learn how to configure FixedSizeSplitter chunk_size and chunk_overlap parameters for optimal embedding quality and how these settings affect retrieval performance.

Participants understand the Embedder interface and how to swap between SentenceTransformerEmbeddings for local development and OpenAIEmbeddings or custom implementations for production deployments.

Participants gain practical experience with VectorRetriever and HybridRetriever configurations and learn how to tune the HybridSearchRanker.LINEAR alpha parameter to balance semantic and keyword signals.

Participants see how VectorCypherRetriever and HybridCypherRetriever enable graph-aware retrieval patterns that combine semantic search with structured graph traversal through custom retrieval queries.

The completed lab demonstrates a realistic pattern for augmenting existing graph databases with semantic search capabilities using the official Neo4j GraphRAG library, applicable to customer service knowledge bases, compliance document retrieval, and investment research applications.
