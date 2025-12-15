"""
Search module for Lab 3: Vector Embeddings and Hybrid Search.

This module provides vector, full-text, and hybrid search capabilities
using neo4j-graphrag retrievers (VectorRetriever, HybridRetriever,
VectorCypherRetriever, HybridCypherRetriever).
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
    """Convert schema HybridRankerType to neo4j-graphrag HybridSearchRanker."""
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
        """Get or create HybridRetriever."""
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
        chunk_label = self.index_config.chunk_label

        # Direct Cypher query for full-text search
        cypher = f"""
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

        Args:
            query: Query text for both vector and keyword search.
            config: Search configuration including ranker and alpha.

        Returns:
            List of SearchResult objects ordered by combined score.
        """
        config = config or SearchConfig()
        ranker = _ranker_from_config(config.ranker)

        raw_result = self.hybrid_retriever.get_search_results(
            query_text=query,
            top_k=config.top_k,
            effective_search_ratio=config.effective_search_ratio,
            ranker=ranker,
            alpha=config.alpha,
        )

        results: list[SearchResult] = []
        for record in raw_result.records:
            result = _record_to_search_result(record)
            results.append(result)

        return results

    def vector_search_with_graph_traversal(
        self,
        query: str,
        config: Optional[SearchConfig] = None,
    ) -> GraphTraversalResult:
        """Perform vector search with graph traversal to related entities.

        Uses VectorCypherRetriever to find similar chunks and traverse
        relationships to connected Customer, Company, and Stock nodes.

        Args:
            query: Natural language query text.
            config: Search configuration.

        Returns:
            GraphTraversalResult with search results and related entities.
        """
        config = config or SearchConfig()
        chunk_label = self.index_config.chunk_label

        # Retrieval query that traverses to related entities
        retrieval_query = f"""
        WITH node, score
        OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
        OPTIONAL MATCH (d)-[:DESCRIBES]->(customer:Customer)
        OPTIONAL MATCH (node)-[:MENTIONS]->(company:Company)
        OPTIONAL MATCH (node)-[:MENTIONS]->(stock:Stock)
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

        for record in raw_result.records:
            # Extract search result
            result = _record_to_search_result(record)
            search_results.append(result)

            # Collect related entities
            customers = record.get("customers", [])
            companies = record.get("companies", [])
            stocks = record.get("stocks", [])

            for customer in customers:
                if customer and hasattr(customer, "items"):
                    customer_dict = dict(customer.items())
                    if customer_dict not in all_customers:
                        all_customers.append(customer_dict)

            for company in companies:
                if company and hasattr(company, "items"):
                    company_dict = dict(company.items())
                    if company_dict not in all_companies:
                        all_companies.append(company_dict)

            for stock in stocks:
                if stock and hasattr(stock, "items"):
                    stock_dict = dict(stock.items())
                    if stock_dict not in all_stocks:
                        all_stocks.append(stock_dict)

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

        Uses HybridCypherRetriever to find chunks using both vector and
        full-text search, then traverses to connected entities.

        Args:
            query: Query text.
            config: Search configuration.

        Returns:
            GraphTraversalResult with search results and related entities.
        """
        config = config or SearchConfig()
        ranker = _ranker_from_config(config.ranker)

        # Retrieval query that traverses to related entities
        retrieval_query = """
        WITH node, score
        OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(d:Document)
        OPTIONAL MATCH (d)-[:DESCRIBES]->(customer:Customer)
        OPTIONAL MATCH (node)-[:MENTIONS]->(company:Company)
        OPTIONAL MATCH (node)-[:MENTIONS]->(stock:Stock)
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

        for record in raw_result.records:
            # Extract search result
            result = _record_to_search_result(record)
            search_results.append(result)

            # Collect related entities
            customers = record.get("customers", [])
            companies = record.get("companies", [])
            stocks = record.get("stocks", [])

            for customer in customers:
                if customer and hasattr(customer, "items"):
                    customer_dict = dict(customer.items())
                    if customer_dict not in all_customers:
                        all_customers.append(customer_dict)

            for company in companies:
                if company and hasattr(company, "items"):
                    company_dict = dict(company.items())
                    if company_dict not in all_companies:
                        all_companies.append(company_dict)

            for stock in stocks:
                if stock and hasattr(stock, "items"):
                    stock_dict = dict(stock.items())
                    if stock_dict not in all_stocks:
                        all_stocks.append(stock_dict)

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
