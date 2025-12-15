"""
Vector Embeddings and Hybrid Search - Main Processing Script

This is the main entry point for Lab 3, orchestrating the complete document
processing pipeline from HTML ingestion through search demonstration. It ties
together all the modular components (processing, embeddings, graph, search)
into a cohesive workflow.

Pipeline Overview:
    Step 1 - Document Processing:
        - Load HTML files from local directory or Databricks volume
        - Parse HTML, extract text, classify document types
        - Split documents into overlapping chunks using FixedSizeSplitter

    Step 2 - Embedding Generation:
        - Initialize embedding provider (SentenceTransformers or Databricks)
        - Generate vector embeddings for all chunks
        - Validate embedding dimensions match configuration

    Step 3 - Neo4j Graph Writing:
        - Create vector and full-text indexes
        - Write Document and Chunk nodes with embeddings
        - Create relationships (FROM_DOCUMENT, NEXT_CHUNK, DESCRIBES)

    Step 4 - Search Demonstration:
        - Run sample queries showing vector, full-text, and hybrid search
        - Demonstrate graph-aware retrieval with entity traversal

Usage:
    # Local development (reads from local data/html directory)
    uv run python lab_3_vector_embeddings/vector_embeddings.py

    # Use local embeddings (no Databricks API needed, 384 dims)
    uv run python lab_3_vector_embeddings/vector_embeddings.py --provider sentence_transformers

    # Use Databricks embeddings (requires auth, 1024 dims, better quality)
    uv run python lab_3_vector_embeddings/vector_embeddings.py --provider databricks

    # Clear existing document graph before processing
    uv run python lab_3_vector_embeddings/vector_embeddings.py --clear

    # Skip the search demo at the end
    uv run python lab_3_vector_embeddings/vector_embeddings.py --skip-demo

    # Use custom HTML directory
    uv run python lab_3_vector_embeddings/vector_embeddings.py --html-dir /path/to/html

Authentication:
    Neo4j credentials are retrieved from Databricks Secrets (scope: neo4j-creds).
    Configure Databricks authentication via .env file:
        DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
        DATABRICKS_TOKEN=your-token

    Required secrets in 'neo4j-creds' scope:
        - url: Neo4j connection URI (neo4j+s://...)
        - username: Neo4j username (typically 'neo4j')
        - password: Neo4j password
"""

import argparse
import os
import sys
import time
from pathlib import Path

# =============================================================================
# INDEX CONFIGURATION CONSTANTS
# =============================================================================
# These index names must match across all components (graph writer, searcher)
# Change these values if you need different index names in your Neo4j database
VECTOR_INDEX_NAME = "chunk_embedding_index"
FULLTEXT_INDEX_NAME = "chunk_text_index"

# Handle Databricks environment where __file__ is not defined
try:
    PROJECT_ROOT = Path(__file__).parent.parent
except NameError:
    # In Databricks notebooks, use current working directory
    PROJECT_ROOT = Path.cwd()

# Load .env from project root for Databricks authentication (same as lab 1)
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods - use only HOST + TOKEN from .env
for var in ["DATABRICKS_CONFIG_PROFILE", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET", "DATABRICKS_ACCOUNT_ID"]:
    os.environ.pop(var, None)

# Support both direct script execution and module execution
try:
    # When run as a module (python -m lab_3_vector_embeddings.vector_embeddings)
    from .processing import (
        process_html_content,
        chunk_document_sync,
    )
    from .embeddings import (
        create_embedder,
        embed_chunks,
        get_default_config_for_provider,
        validate_embeddings,
    )
    from .graph import write_document_graph, GraphWriter
    from .models import (
        ChunkConfig,
        EmbeddingConfig,
        EmbeddingProvider,
        IndexConfig,
        Neo4jConfig,
        ProcessedChunk,
        ProcessedDocument,
    )
    from .search import DocumentSearcher, create_searcher
except ImportError:
    # When run directly (python vector_embeddings.py) or in Databricks
    from lab_3_vector_embeddings.processing import (
        process_html_content,
        chunk_document_sync,
    )
    from lab_3_vector_embeddings.embeddings import (
        create_embedder,
        embed_chunks,
        get_default_config_for_provider,
        validate_embeddings,
    )
    from lab_3_vector_embeddings.graph import write_document_graph, GraphWriter
    from lab_3_vector_embeddings.models import (
        ChunkConfig,
        EmbeddingConfig,
        EmbeddingProvider,
        IndexConfig,
        Neo4jConfig,
        ProcessedChunk,
        ProcessedDocument,
    )
    from lab_3_vector_embeddings.search import DocumentSearcher, create_searcher


def load_neo4j_config() -> Neo4jConfig:
    """Load Neo4j configuration from Databricks Secrets.

    Uses the Databricks SDK to retrieve secrets from the 'neo4j-creds' scope.
    Requires Databricks authentication to be configured (CLI profile or env vars).

    Note: The Databricks SDK returns secret values as base64-encoded strings,
    which must be decoded before use.
    """
    import base64
    from databricks.sdk import WorkspaceClient

    def decode_secret(encoded_value: str) -> str:
        """Decode a base64-encoded secret value from Databricks SDK."""
        return base64.b64decode(encoded_value).decode("utf-8")

    print("[DEBUG] Retrieving secrets from Databricks scope 'neo4j-creds'...")

    try:
        client = WorkspaceClient()
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Databricks client: {e}\n"
            "Configure authentication via:\n"
            "  - Databricks CLI: databricks auth login --host <workspace-url>\n"
            "  - Environment: DATABRICKS_HOST and DATABRICKS_TOKEN"
        ) from e

    try:
        uri_encoded = client.secrets.get_secret(scope="neo4j-creds", key="url").value
        uri = decode_secret(uri_encoded)
        print(f"  [OK] url: {uri}")
    except Exception as e:
        raise ValueError(f"Failed to get 'url' from neo4j-creds scope: {e}") from e

    try:
        username_encoded = client.secrets.get_secret(scope="neo4j-creds", key="username").value
        username = decode_secret(username_encoded)
        print(f"  [OK] username: retrieved ({len(username)} chars)")
    except Exception as e:
        raise ValueError(f"Failed to get 'username' from neo4j-creds scope: {e}") from e

    try:
        password_encoded = client.secrets.get_secret(scope="neo4j-creds", key="password").value
        password = decode_secret(password_encoded)
        print(f"  [OK] password: retrieved ({len(password)} chars, masked)")
    except Exception as e:
        raise ValueError(f"Failed to get 'password' from neo4j-creds scope: {e}") from e

    return Neo4jConfig(
        uri=uri,
        username=username,
        password=password,
        database="neo4j",
    )


def load_html_files_local(html_dir: Path) -> list[tuple[str, str, str]]:
    """Load HTML files from local directory.

    Args:
        html_dir: Path to directory containing HTML files.

    Returns:
        List of tuples (html_content, filename, source_path).
    """
    html_files: list[tuple[str, str, str]] = []

    for html_path in sorted(html_dir.glob("*.html")):
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        html_files.append((content, html_path.name, str(html_path)))

    return html_files


def step1_process_documents(
    html_files: list[tuple[str, str, str]],
    chunk_config: ChunkConfig,
) -> tuple[list[ProcessedDocument], list[ProcessedChunk], float]:
    """Step 1: Process HTML files into documents and chunks.

    Args:
        html_files: List of (content, filename, source_path) tuples.
        chunk_config: Chunking configuration.

    Returns:
        Tuple of (documents, chunks, elapsed_time).
    """
    print("\n" + "=" * 70)
    print("STEP 1: Document Processing")
    print("=" * 70)

    start = time.time()
    documents: list[ProcessedDocument] = []
    all_chunks: list[ProcessedChunk] = []

    for i, (content, filename, source_path) in enumerate(html_files):
        print(f"  [{i+1}/{len(html_files)}] Processing: {filename}")

        doc = process_html_content(content, filename, source_path)
        documents.append(doc)
        print(f"           Type: {doc.document_type.value}, Chars: {len(doc.raw_text)}")

        chunks = chunk_document_sync(doc, chunk_config)
        all_chunks.extend(chunks)
        print(f"           Chunks: {len(chunks)}")

    elapsed = time.time() - start

    print(f"\n  [OK] Processed {len(documents)} documents into {len(all_chunks)} chunks")
    print(f"       Time: {elapsed:.2f}s")

    return documents, all_chunks, elapsed


def step2_generate_embeddings(
    chunks: list[ProcessedChunk],
    embedding_config: EmbeddingConfig,
) -> tuple[list[ProcessedChunk], float]:
    """Step 2: Generate embeddings for all chunks.

    Args:
        chunks: List of processed chunks without embeddings.
        embedding_config: Embedding configuration.

    Returns:
        Tuple of (embedded_chunks, elapsed_time).
    """
    print("\n" + "=" * 70)
    print("STEP 2: Embedding Generation")
    print("=" * 70)
    print(f"  Provider: {embedding_config.provider.value}")
    print(f"  Model: {embedding_config.model_name}")
    print(f"  Dimensions: {embedding_config.dimensions}")

    start = time.time()
    embedder = create_embedder(embedding_config)
    print(f"\n  [OK] Embedder initialized")

    print(f"  Embedding {len(chunks)} chunks...")
    embedded_chunks = embed_chunks(chunks, embedder)

    # Validate embeddings
    is_valid, errors = validate_embeddings(embedded_chunks, embedding_config.dimensions)
    if not is_valid:
        print(f"  [WARNING] Embedding validation errors: {errors[:5]}")
    else:
        print(f"  [OK] All embeddings validated ({embedding_config.dimensions} dimensions)")

    elapsed = time.time() - start
    print(f"       Time: {elapsed:.2f}s")

    return embedded_chunks, elapsed


def step3_write_to_neo4j(
    neo4j_config: Neo4jConfig,
    documents: list[ProcessedDocument],
    embedded_chunks: list[ProcessedChunk],
    embedding_dimensions: int,
    index_config: IndexConfig,
    clear_existing: bool = False,
) -> tuple[dict, float]:
    """Step 3: Write documents and chunks to Neo4j graph database.

    Args:
        neo4j_config: Neo4j connection configuration.
        documents: List of processed documents.
        embedded_chunks: List of chunks with embeddings.
        embedding_dimensions: Dimension of embeddings for index creation.
        index_config: Index configuration.
        clear_existing: Whether to clear existing document graph.

    Returns:
        Tuple of (graph_results, elapsed_time).
    """
    print("\n" + "=" * 70)
    print("STEP 3: Neo4j Graph Writing")
    print("=" * 70)
    print(f"  URI: {neo4j_config.uri}")
    print(f"  Database: {neo4j_config.database}")

    start = time.time()
    graph_results = write_document_graph(
        neo4j_config=neo4j_config,
        documents=documents,
        chunks=embedded_chunks,
        embedding_dimensions=embedding_dimensions,
        index_config=index_config,
        clear_existing=clear_existing,
    )
    elapsed = time.time() - start

    print(f"\n  [OK] Graph writing complete")
    print(f"       Documents written: {graph_results['documents'].get('documents_written', 0)}")
    print(f"       Chunks written: {graph_results['chunks'].get('chunks_written', 0)}")
    print(f"       FROM_DOCUMENT relationships: {graph_results['from_document'].get('from_document_relationships', 0)}")
    print(f"       NEXT_CHUNK relationships: {graph_results['next_chunk'].get('next_chunk_relationships', 0)}")
    print(f"       DESCRIBES relationships: {graph_results['describes'].get('describes_relationships', 0)}")
    print(f"       Time: {elapsed:.2f}s")

    # Index status
    print("\n  Index Status:")
    for index_name, status in graph_results.get("index_status", {}).items():
        print(f"    {index_name}: {status.get('state', 'unknown')}")

    return graph_results, elapsed


def process_pipeline(
    html_files: list[tuple[str, str, str]],
    embedding_config: EmbeddingConfig,
    chunk_config: ChunkConfig,
    neo4j_config: Neo4jConfig,
    index_config: IndexConfig,
    clear_existing: bool = False,
) -> dict:
    """Run the complete document processing pipeline.

    Args:
        html_files: List of (content, filename, source_path) tuples.
        embedding_config: Embedding configuration.
        chunk_config: Chunking configuration.
        neo4j_config: Neo4j connection configuration.
        index_config: Index configuration.
        clear_existing: Whether to clear existing document graph.

    Returns:
        Dictionary with pipeline results and statistics.
    """
    results: dict = {"timing": {}, "counts": {}}
    total_start = time.time()

    # Step 1: Process documents
    documents, all_chunks, doc_time = step1_process_documents(
        html_files=html_files,
        chunk_config=chunk_config,
    )
    results["timing"]["document_processing"] = doc_time
    results["counts"]["documents"] = len(documents)
    results["counts"]["chunks"] = len(all_chunks)

    # Step 2: Generate embeddings
    embedded_chunks, embed_time = step2_generate_embeddings(
        chunks=all_chunks,
        embedding_config=embedding_config,
    )
    results["timing"]["embedding"] = embed_time

    # Step 3: Write to Neo4j
    graph_results, graph_time = step3_write_to_neo4j(
        neo4j_config=neo4j_config,
        documents=documents,
        embedded_chunks=embedded_chunks,
        embedding_dimensions=embedding_config.dimensions,
        index_config=index_config,
        clear_existing=clear_existing,
    )
    results["timing"]["graph_writing"] = graph_time
    results["graph"] = graph_results

    results["timing"]["total"] = time.time() - total_start

    return results


def run_search_demo(
    neo4j_config: Neo4jConfig,
    embedding_config: EmbeddingConfig,
    index_config: IndexConfig,
) -> None:
    """Run search demonstration queries.

    Args:
        neo4j_config: Neo4j connection configuration.
        embedding_config: Embedding configuration.
        index_config: Index configuration.
    """
    print("\n" + "=" * 70)
    print("STEP 4: Search Demonstration")
    print("=" * 70)

    embedder = create_embedder(embedding_config)
    searcher = create_searcher(neo4j_config, embedder, index_config)

    try:
        # Demo query 1: Vector search
        print("\n[Demo 1] Vector Search: 'investment strategies for moderate risk'")
        print("-" * 50)
        results = searcher.vector_search("investment strategies for moderate risk")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. Score: {result.score:.4f}")
            print(f"     Document: {result.document_title}")
            print(f"     Text: {result.text[:150]}...")
            print()

        # Demo query 2: Full-text search
        print("\n[Demo 2] Full-text Search: 'renewable energy'")
        print("-" * 50)
        results = searcher.fulltext_search("renewable energy")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. Score: {result.score:.4f}")
            print(f"     Document: {result.document_title}")
            print(f"     Text: {result.text[:150]}...")
            print()

        # Demo query 3: Hybrid search
        print("\n[Demo 3] Hybrid Search: 'customer technology investments'")
        print("-" * 50)
        results = searcher.hybrid_search("customer technology investments")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. Score: {result.score:.4f}")
            print(f"     Document: {result.document_title}")
            print(f"     Text: {result.text[:150]}...")
            print()

        # Demo query 4: Graph-aware search
        print("\n[Demo 4] Graph-Aware Search: 'portfolio diversification'")
        print("-" * 50)
        graph_result = searcher.vector_search_with_graph_traversal(
            "portfolio diversification"
        )
        print(f"  Found {len(graph_result.search_results)} chunks")
        print(f"  Related customers: {len(graph_result.related_customers)}")
        print(f"  Related companies: {len(graph_result.related_companies)}")
        print(f"  Related stocks: {len(graph_result.related_stocks)}")

        if graph_result.related_customers:
            print("\n  Connected Customers:")
            for customer in graph_result.related_customers[:3]:
                name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}"
                print(f"    - {name.strip()}")

    finally:
        searcher.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process HTML documents and create vector embeddings in Neo4j"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["sentence_transformers", "databricks"],
        default="databricks",
        help="Embedding provider: sentence_transformers (local, 384 dims) or databricks (cloud, 1024 dims)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing document graph before processing",
    )
    parser.add_argument(
        "--skip-demo",
        action="store_true",
        help="Skip search demonstration",
    )
    parser.add_argument(
        "--html-dir",
        type=str,
        default=None,
        help="Path to HTML directory (default: data/html)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Lab 3: Vector Embeddings and Hybrid Search")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Load configurations
    print("\n[1/4] Loading configuration...")
    try:
        neo4j_config = load_neo4j_config()
        print(f"  [OK] Neo4j config loaded: {neo4j_config.uri}")
    except ValueError as e:
        print(f"  [FAIL] {e}")
        print("\n  Make sure Databricks Secrets are configured:")
        print("    databricks secrets put-secret neo4j-creds url --string-value 'neo4j+s://...'")
        print("    databricks secrets put-secret neo4j-creds username --string-value 'neo4j'")
        print("    databricks secrets put-secret neo4j-creds password --string-value '...'")
        sys.exit(1)

    # Get embedding config for provider
    provider_map = {
        "sentence_transformers": EmbeddingProvider.SENTENCE_TRANSFORMERS,
        "databricks": EmbeddingProvider.DATABRICKS,
    }
    embedding_config = get_default_config_for_provider(provider_map[args.provider])
    print(f"  [OK] Embedding config: {embedding_config.provider.value}")

    chunk_config = ChunkConfig()
    print(f"  [OK] Chunk config: size={chunk_config.chunk_size}, overlap={chunk_config.chunk_overlap}")

    index_config = IndexConfig(
        vector_index_name=VECTOR_INDEX_NAME,
        fulltext_index_name=FULLTEXT_INDEX_NAME,
    )
    print(f"  [OK] Index config: vector={index_config.vector_index_name}, fulltext={index_config.fulltext_index_name}")

    # Load HTML files
    print("\n[2/4] Loading HTML files...")
    html_dir = Path(args.html_dir) if args.html_dir else PROJECT_ROOT / "data" / "html"

    if not html_dir.exists():
        print(f"  [FAIL] HTML directory not found: {html_dir}")
        sys.exit(1)

    html_files = load_html_files_local(html_dir)
    print(f"  [OK] Loaded {len(html_files)} HTML files from {html_dir}")

    if not html_files:
        print("  [FAIL] No HTML files found")
        sys.exit(1)

    # Run pipeline
    print("\n[3/4] Running processing pipeline...")
    results = process_pipeline(
        html_files=html_files,
        embedding_config=embedding_config,
        chunk_config=chunk_config,
        neo4j_config=neo4j_config,
        index_config=index_config,
        clear_existing=args.clear,
    )

    # Run search demo
    if not args.skip_demo:
        print("\n[4/4] Running search demonstration...")
        run_search_demo(neo4j_config, embedding_config, index_config)
    else:
        print("\n[4/4] Skipping search demonstration (--skip-demo)")

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Documents processed: {results['counts']['documents']}")
    print(f"  Chunks created: {results['counts']['chunks']}")
    print(f"  Total time: {results['timing']['total']:.2f}s")
    print("\n  Timing breakdown:")
    print(f"    Document processing: {results['timing']['document_processing']:.2f}s")
    print(f"    Embedding generation: {results['timing']['embedding']:.2f}s")
    print(f"    Graph writing: {results['timing']['graph_writing']:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
