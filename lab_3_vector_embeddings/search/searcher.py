"""
Search module for Lab 3: Vector Embeddings and Hybrid Search.

This module provides multiple search strategies over the document graph, using
neo4j-graphrag retrievers to find relevant text chunks. It demonstrates the
power of combining vector similarity with graph traversal for enhanced retrieval.

Search Types Available:

1. **Vector Search** (vector_search):
   - Pure semantic similarity using embedding vectors
   - Best for: Natural language queries, conceptual questions
   - Example: "What are good investment strategies for retirement?"

2. **Full-text Search** (fulltext_search):
   - Keyword-based search using Neo4j's Lucene full-text index
   - Best for: Exact term matching, specific entity names, technical terms
   - Example: "renewable energy" or "John Smith"

3. **Hybrid Search** (hybrid_search):
   - Combines vector and full-text search with configurable ranking
   - Rankers: NAIVE (interleaved results) or LINEAR (weighted combination)
   - Best for: General-purpose search balancing semantics and keywords

4. **Graph-Aware Search** (vector_search_with_graph_traversal, hybrid_search_with_graph_traversal):
   - Extends search results by traversing graph relationships
   - Returns related Customer, Company, and Stock nodes connected to found chunks
   - Uses VectorCypherRetriever/HybridCypherRetriever with custom retrieval queries
   - Best for: Context enrichment, finding related entities

How neo4j-graphrag Hybrid Search Works:
    The library performs result fusion entirely in Cypher at the database level:

    1. Vector search runs, scores normalized by max: score / max_vector_score
    2. Fulltext search runs, scores normalized by max: score / max_fulltext_score
    3. Results combined via UNION (keeps all rows from both searches)
    4. Deduplication via aggregation:
       - NAIVE:  WITH node, max(score) AS score  (takes best score from either index)
       - LINEAR: WITH node, sum(score) AS score  (combines weighted scores)
    5. Final ORDER BY score DESC LIMIT top_k

    This means no Python-side deduplication is needed - the library handles it.

Key Classes:
    - DocumentSearcher: Main search interface with lazy-initialized retrievers
    - create_searcher(): Factory function for creating searcher instances

Usage Example:
    searcher = create_searcher(neo4j_config, embedder, index_config)
    results = searcher.hybrid_search("portfolio diversification", SearchConfig(top_k=10))
    graph_results = searcher.vector_search_with_graph_traversal("customer investments")
    searcher.close()
"""

from typing import Optional

import neo4j
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.retrievers import (
    HybridCypherRetriever,
    HybridRetriever,
    VectorCypherRetriever,
    VectorRetriever,
)
from neo4j_graphrag.types import HybridSearchRanker

from ..models import (
    GraphTraversalResult,
    HybridRankerType,
    IndexConfig,
    Neo4jConfig,
    SearchConfig,
    SearchResult,
)


def _ranker_from_config(ranker: HybridRankerType) -> HybridSearchRanker:
    """Convert schema HybridRankerType to neo4j-graphrag HybridSearchRanker.

    Ranker determines how vector and fulltext scores are combined:
    - NAIVE: max(vector_score, fulltext_score) - best single score wins
    - LINEAR: alpha * vector_score + (1-alpha) * fulltext_score - weighted blend
    """
    if ranker == HybridRankerType.LINEAR:
        return HybridSearchRanker.LINEAR
    return HybridSearchRanker.NAIVE


def _record_to_search_result(record: neo4j.Record) -> SearchResult:
    """Convert a neo4j Record to SearchResult."""
    node = record.get("node", {})
    if hasattr(node, "items"):
        node_dict = dict(node.items())
    else:
        node_dict = node if isinstance(node, dict) else {}

    return SearchResult(
        chunk_id=node_dict.get("chunk_id", ""),
        document_id=node_dict.get("document_id", ""),
        text=node_dict.get("text", ""),
        score=record.get("score", 0.0),
        document_title=node_dict.get("document_title"),
        document_type=node_dict.get("document_type"),
        metadata={k: v for k, v in node_dict.items() if k not in ("chunk_id", "document_id", "text", "embedding")},
    )


def _collect_entities(
    record: neo4j.Record,
    seen_customers: set[str],
    seen_companies: set[str],
    seen_stocks: set[str],
    all_customers: list[dict],
    all_companies: list[dict],
    all_stocks: list[dict],
) -> None:
    """Collect unique entities from a record using set-based deduplication.

    Modifies the lists and sets in place for efficiency.
    """
    # Collect customers (via Document -> DESCRIBES -> Customer path)
    for customer in record.get("customers", []):
        if customer and hasattr(customer, "items"):
            customer_dict = dict(customer.items())
            customer_id = customer_dict.get("customer_id", "")
            if customer_id and customer_id not in seen_customers:
                seen_customers.add(customer_id)
                all_customers.append(customer_dict)

    # Collect companies (via Customer -> Account -> Position -> Stock -> Company path)
    for company in record.get("companies", []):
        if company and hasattr(company, "items"):
            company_dict = dict(company.items())
            company_id = company_dict.get("company_id", "")
            if company_id and company_id not in seen_companies:
                seen_companies.add(company_id)
                all_companies.append(company_dict)

    # Collect stocks (via Customer -> Account -> Position -> Stock path)
    for stock in record.get("stocks", []):
        if stock and hasattr(stock, "items"):
            stock_dict = dict(stock.items())
            stock_id = stock_dict.get("stock_id", "")
            if stock_id and stock_id not in seen_stocks:
                seen_stocks.add(stock_id)
                all_stocks.append(stock_dict)


class DocumentSearcher:
    """Unified search interface for document chunks.

    Provides vector, full-text, and hybrid search using neo4j-graphrag
    retrievers with support for graph-aware retrieval patterns.
    """

    def __init__(
        self,
        neo4j_config: Neo4jConfig,
        embedder: Embedder,
        index_config: Optional[IndexConfig] = None,
    ) -> None:
        """Initialize DocumentSearcher.

        Args:
            neo4j_config: Neo4j connection configuration.
            embedder: Embedder for query embedding generation.
            index_config: Index configuration.
        """
        self.neo4j_config = neo4j_config
        self.embedder = embedder
        self.index_config = index_config or IndexConfig()
        self._driver: Optional[neo4j.Driver] = None
        self._vector_retriever: Optional[VectorRetriever] = None
        self._hybrid_retriever: Optional[HybridRetriever] = None

    @property
    def driver(self) -> neo4j.Driver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.neo4j_config.uri,
                auth=(self.neo4j_config.username, self.neo4j_config.password),
            )
        return self._driver

    @property
    def vector_retriever(self) -> VectorRetriever:
        """Get or create VectorRetriever."""
        if self._vector_retriever is None:
            self._vector_retriever = VectorRetriever(
                driver=self.driver,
                index_name=self.index_config.vector_index_name,
                embedder=self.embedder,
                return_properties=[
                    "chunk_id",
                    "document_id",
                    self.index_config.text_property,
                    "document_title",
                    "document_type",
                    "index",
                ],
                neo4j_database=self.neo4j_config.database,
            )
        return self._vector_retriever

    @property
    def hybrid_retriever(self) -> HybridRetriever:
        """Get or create HybridRetriever.

        HybridRetriever combines vector and fulltext search in a single Cypher query.
        Score fusion and deduplication happen at the database level, not in Python.
        """
        if self._hybrid_retriever is None:
            self._hybrid_retriever = HybridRetriever(
                driver=self.driver,
                vector_index_name=self.index_config.vector_index_name,
                fulltext_index_name=self.index_config.fulltext_index_name,
                embedder=self.embedder,
                return_properties=[
                    "chunk_id",
                    "document_id",
                    self.index_config.text_property,
                    "document_title",
                    "document_type",
                    "index",
                ],
                neo4j_database=self.neo4j_config.database,
            )
        return self._hybrid_retriever

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def vector_search(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
    ) -> list[SearchResult]:
        """Perform vector similarity search.

        Args:
            query: Natural language query text.
            config: Search configuration.

        Returns:
            List of SearchResult objects ordered by similarity score.
        """
        config = config or SearchConfig()

        raw_result = self.vector_retriever.get_search_results(
            query_text=query,
            top_k=config.top_k,
            effective_search_ratio=config.effective_search_ratio,
        )

        results: list[SearchResult] = []
        for record in raw_result.records:
            result = _record_to_search_result(record)
            results.append(result)

        return results

    def fulltext_search(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
    ) -> list[SearchResult]:
        """Perform full-text keyword search.

        Args:
            query: Keyword query (supports Lucene syntax).
            config: Search configuration.

        Returns:
            List of SearchResult objects ordered by relevance score.
        """
        config = config or SearchConfig()

        # Direct Cypher query for full-text search
        # Note: Full-text index already constrains to the correct label (Chunk)
        cypher = """
        CALL db.index.fulltext.queryNodes($index_name, $query)
        YIELD node, score
        WITH node, score
        ORDER BY score DESC
        LIMIT $top_k
        RETURN node, score
        """

        with self.driver.session(database=self.neo4j_config.database) as session:
            result = session.run(
                cypher,
                {
                    "index_name": self.index_config.fulltext_index_name,
                    "query": query,
                    "top_k": config.top_k,
                },
            )

            results: list[SearchResult] = []
            for record in result:
                results.append(_record_to_search_result(record))

        return results

    def hybrid_search(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
    ) -> list[SearchResult]:
        """Perform hybrid search combining vector and full-text.

        Uses neo4j-graphrag HybridRetriever which fuses results at the database level:
        - NAIVE ranker: Normalizes scores per-index, returns max(score) for duplicates
        - LINEAR ranker: Weighted combination using alpha (vector weight) and 1-alpha (fulltext)

        The library handles deduplication via Cypher aggregation, so no Python-side
        deduplication is needed.

        Args:
            query: Query text for both vector and keyword search.
            config: Search configuration including ranker and alpha.
                - ranker: NAIVE (default) or LINEAR
                - alpha: Required for LINEAR ranker (0.0-1.0, weight for vector score)
                - effective_search_ratio: Candidate pool multiplier for better fusion

        Returns:
            List of SearchResult objects ordered by combined score.
        """
        config = config or SearchConfig()
        ranker = _ranker_from_config(config.ranker)

        # The library handles deduplication at the database level via UNION + aggregation
        raw_result = self.hybrid_retriever.get_search_results(
            query_text=query,
            top_k=config.top_k,
            effective_search_ratio=config.effective_search_ratio,
            ranker=ranker,
            alpha=config.alpha,
        )

        return [_record_to_search_result(record) for record in raw_result.records]

    def vector_search_with_graph_traversal(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
    ) -> GraphTraversalResult:
        """Perform vector search with graph traversal to related entities.

        Uses VectorCypherRetriever which:
        1. Finds similar chunks via vector similarity search
        2. Applies the retrieval_query to traverse from chunks to related entities

        The retrieval query follows the investment graph path:
        Chunk -> Document -> Customer -> Account -> Position -> Stock -> Company

        Args:
            query: Natural language query text.
            config: Search configuration (top_k, effective_search_ratio).

        Returns:
            GraphTraversalResult with search results and related entities.
        """
        config = config or SearchConfig()

        # Retrieval query that traverses to related entities through graph paths:
        # Path: Chunk -> Document -> Customer -> Account -> Position -> Stock -> Company
        # This finds what stocks/companies the customer (from the document) actually invests in
        retrieval_query = """
        WITH node, score
        OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
        OPTIONAL MATCH (d)-[:DESCRIBES]->(customer:Customer)
        OPTIONAL MATCH (customer)-[:HAS_ACCOUNT]->(acct:Account)
                       -[:HAS_POSITION]->(pos:Position)
                       -[:OF_SECURITY]->(stock:Stock)
        OPTIONAL MATCH (stock)-[:OF_COMPANY]->(company:Company)
        RETURN node, score,
               d AS document,
               collect(DISTINCT customer) AS customers,
               collect(DISTINCT company) AS companies,
               collect(DISTINCT stock) AS stocks
        """

        retriever = VectorCypherRetriever(
            driver=self.driver,
            index_name=self.index_config.vector_index_name,
            retrieval_query=retrieval_query,
            embedder=self.embedder,
            neo4j_database=self.neo4j_config.database,
        )

        raw_result = retriever.get_search_results(
            query_text=query,
            top_k=config.top_k,
            effective_search_ratio=config.effective_search_ratio,
        )

        search_results: list[SearchResult] = []
        all_customers: list[dict] = []
        all_companies: list[dict] = []
        all_stocks: list[dict] = []
        seen_customers: set[str] = set()
        seen_companies: set[str] = set()
        seen_stocks: set[str] = set()

        for record in raw_result.records:
            result = _record_to_search_result(record)
            search_results.append(result)
            _collect_entities(
                record, seen_customers, seen_companies, seen_stocks,
                all_customers, all_companies, all_stocks,
            )

        return GraphTraversalResult(
            search_results=search_results,
            related_customers=all_customers,
            related_companies=all_companies,
            related_stocks=all_stocks,
        )

    def hybrid_search_with_graph_traversal(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
    ) -> GraphTraversalResult:
        """Perform hybrid search with graph traversal to related entities.

        Uses HybridCypherRetriever which:
        1. Performs hybrid search with database-level deduplication via UNION + aggregation
        2. Applies the retrieval_query to traverse from chunks to related entities

        The retrieval query follows the investment graph path:
        Chunk -> Document -> Customer -> Account -> Position -> Stock -> Company

        Args:
            query: Query text.
            config: Search configuration (ranker, alpha, effective_search_ratio).

        Returns:
            GraphTraversalResult with search results and related entities.
        """
        config = config or SearchConfig()
        ranker = _ranker_from_config(config.ranker)

        # Retrieval query appended after hybrid search deduplication
        # Traverses: Chunk -> Document -> Customer -> Account -> Position -> Stock -> Company
        retrieval_query = """
        WITH node, score
        OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
        OPTIONAL MATCH (d)-[:DESCRIBES]->(customer:Customer)
        OPTIONAL MATCH (customer)-[:HAS_ACCOUNT]->(acct:Account)
                       -[:HAS_POSITION]->(pos:Position)
                       -[:OF_SECURITY]->(stock:Stock)
        OPTIONAL MATCH (stock)-[:OF_COMPANY]->(company:Company)
        RETURN node, score,
               d AS document,
               collect(DISTINCT customer) AS customers,
               collect(DISTINCT company) AS companies,
               collect(DISTINCT stock) AS stocks
        """

        retriever = HybridCypherRetriever(
            driver=self.driver,
            vector_index_name=self.index_config.vector_index_name,
            fulltext_index_name=self.index_config.fulltext_index_name,
            retrieval_query=retrieval_query,
            embedder=self.embedder,
            neo4j_database=self.neo4j_config.database,
        )

        # Library handles deduplication at search level; retrieval_query runs after
        raw_result = retriever.get_search_results(
            query_text=query,
            top_k=config.top_k,
            effective_search_ratio=config.effective_search_ratio,
            ranker=ranker,
            alpha=config.alpha,
        )

        search_results: list[SearchResult] = []
        all_customers: list[dict] = []
        all_companies: list[dict] = []
        all_stocks: list[dict] = []
        seen_customers: set[str] = set()
        seen_companies: set[str] = set()
        seen_stocks: set[str] = set()

        for record in raw_result.records:
            result = _record_to_search_result(record)
            search_results.append(result)
            _collect_entities(
                record, seen_customers, seen_companies, seen_stocks,
                all_customers, all_companies, all_stocks,
            )

        return GraphTraversalResult(
            search_results=search_results,
            related_customers=all_customers,
            related_companies=all_companies,
            related_stocks=all_stocks,
        )


def create_searcher(
    neo4j_config: Neo4jConfig,
    embedder: Embedder,
    index_config: Optional[IndexConfig] = None,
) -> DocumentSearcher:
    """Factory function to create a DocumentSearcher.

    Args:
        neo4j_config: Neo4j connection configuration.
        embedder: Embedder for query embedding.
        index_config: Index configuration.

    Returns:
        Configured DocumentSearcher instance.
    """
    return DocumentSearcher(
        neo4j_config=neo4j_config,
        embedder=embedder,
        index_config=index_config,
    )
