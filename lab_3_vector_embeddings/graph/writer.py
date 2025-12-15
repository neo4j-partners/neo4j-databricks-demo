"""
Graph writer module for Lab 3: Vector Embeddings and Hybrid Search.

This module persists processed documents and embedded chunks to Neo4j, creating
the graph structure required for vector and hybrid search. It follows neo4j-graphrag
LexicalGraphConfig conventions for compatibility with the library's retrievers.

Graph Structure Created:

    Nodes:
        - (Document) - Metadata about source HTML files
        - (Chunk) - Text segments with embedding vectors

    Relationships:
        - (Chunk)-[:FROM_DOCUMENT]->(Document) - Links chunks to their source
        - (Chunk)-[:NEXT_CHUNK]->(Chunk) - Maintains document reading order
        - (Document)-[:DESCRIBES]->(Customer) - Connects customer profiles to Customer nodes

    Indexes:
        - Vector index on Chunk.embedding (cosine similarity)
        - Full-text index on Chunk.text (Lucene-based keyword search)

Key Classes:
    - GraphWriter: Low-level Neo4j operations (create indexes, write nodes, etc.)
    - write_document_graph(): High-level convenience function for full pipeline

GraphWriter Methods:
    - create_indexes(): Set up vector and full-text indexes
    - create_constraints(): Ensure unique document_id and chunk_id
    - write_documents(): Create/update Document nodes
    - write_chunks(): Create/update Chunk nodes with embeddings
    - create_document_chunk_relationships(): Link chunks to documents
    - create_next_chunk_relationships(): Link sequential chunks
    - create_describes_relationships(): Link customer profiles to Customer nodes
    - get_graph_stats(): Count nodes and relationships
    - clear_document_graph(): Remove all document/chunk data for re-processing

Usage Example:
    results = write_document_graph(
        neo4j_config=neo4j_config,
        documents=documents,
        chunks=embedded_chunks,
        embedding_dimensions=1024,
        clear_existing=True,
    )
"""

import time
from typing import Any, Optional

import neo4j
from neo4j import GraphDatabase
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index

from ..models import (
    EntityMention,
    IndexConfig,
    Neo4jConfig,
    ProcessedChunk,
    ProcessedDocument,
)


class GraphWriter:
    """Handles Neo4j graph operations for document storage and retrieval.

    This class manages the document graph structure following neo4j-graphrag
    LexicalGraphConfig conventions with Document and Chunk nodes connected
    by FROM_DOCUMENT and NEXT_CHUNK relationships.
    """

    def __init__(
        self,
        neo4j_config: Neo4jConfig,
        index_config: Optional[IndexConfig] = None,
    ) -> None:
        """Initialize GraphWriter with Neo4j connection.

        Args:
            neo4j_config: Neo4j connection configuration.
            index_config: Index configuration. Uses defaults if not provided.
        """
        self.config = neo4j_config
        self.index_config = index_config or IndexConfig()
        self._driver: Optional[neo4j.Driver] = None

    @property
    def driver(self) -> neo4j.Driver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
            )
        return self._driver

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def verify_connection(self) -> bool:
        """Verify Neo4j connection is working.

        Returns:
            True if connection is successful.
        """
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            return True
        except Exception:
            return False

    def create_indexes(self, dimensions: int) -> dict[str, str]:
        """Create vector and full-text indexes for chunks.

        Args:
            dimensions: Embedding vector dimensions.

        Returns:
            Dictionary with index names and status.
        """
        results: dict[str, str] = {}

        # Create vector index using neo4j-graphrag function
        try:
            create_vector_index(
                driver=self.driver,
                name=self.index_config.vector_index_name,
                label=self.index_config.chunk_label,
                embedding_property=self.index_config.embedding_property,
                dimensions=dimensions,
                similarity_fn=self.index_config.similarity_fn,  # type: ignore[arg-type]
                neo4j_database=self.config.database,
            )
            results[self.index_config.vector_index_name] = "created"
        except Exception as e:
            if "already exists" in str(e).lower():
                results[self.index_config.vector_index_name] = "exists"
            else:
                results[self.index_config.vector_index_name] = f"error: {e}"

        # Create full-text index using neo4j-graphrag function
        try:
            create_fulltext_index(
                driver=self.driver,
                name=self.index_config.fulltext_index_name,
                label=self.index_config.chunk_label,
                node_properties=[self.index_config.text_property],
                neo4j_database=self.config.database,
            )
            results[self.index_config.fulltext_index_name] = "created"
        except Exception as e:
            if "already exists" in str(e).lower():
                results[self.index_config.fulltext_index_name] = "exists"
            else:
                results[self.index_config.fulltext_index_name] = f"error: {e}"

        return results

    def create_constraints(self) -> dict[str, str]:
        """Create uniqueness constraints for Document and Chunk nodes.

        Returns:
            Dictionary with constraint names and status.
        """
        results: dict[str, str] = {}
        constraints = [
            ("document_id_unique", "Document", "document_id"),
            ("chunk_id_unique", self.index_config.chunk_label, "chunk_id"),
        ]

        with self.driver.session(database=self.config.database) as session:
            for constraint_name, label, prop in constraints:
                query = f"""
                CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                FOR (n:{label})
                REQUIRE n.{prop} IS UNIQUE
                """
                try:
                    session.run(query)
                    results[constraint_name] = "created"
                except Exception as e:
                    if "already exists" in str(e).lower():
                        results[constraint_name] = "exists"
                    else:
                        results[constraint_name] = f"error: {e}"

        return results

    def write_documents(
        self, documents: list[ProcessedDocument]
    ) -> dict[str, int]:
        """Write Document nodes to Neo4j.

        Args:
            documents: List of processed documents to write.

        Returns:
            Dictionary with counts of created/updated nodes.
        """
        query = """
        UNWIND $documents AS doc
        MERGE (d:Document {document_id: doc.document_id})
        SET d.filename = doc.filename,
            d.document_type = doc.document_type,
            d.title = doc.title,
            d.source_path = doc.source_path,
            d.processed_at = datetime(doc.processed_at),
            d.char_count = doc.char_count
        RETURN count(d) AS count
        """

        doc_data = [
            {
                "document_id": doc.document_id,
                "filename": doc.filename,
                "document_type": doc.document_type.value,
                "title": doc.title,
                "source_path": doc.source_path,
                "processed_at": doc.processed_at.isoformat(),
                "char_count": doc.metadata.get("char_count", len(doc.raw_text)),
            }
            for doc in documents
        ]

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, {"documents": doc_data})
            record = result.single()
            count = record["count"] if record else 0

        return {"documents_written": count}

    def write_chunks(
        self, chunks: list[ProcessedChunk]
    ) -> dict[str, int]:
        """Write Chunk nodes with embeddings to Neo4j.

        Args:
            chunks: List of processed chunks with embeddings.

        Returns:
            Dictionary with counts of created/updated nodes.
        """
        chunk_label = self.index_config.chunk_label
        embedding_prop = self.index_config.embedding_property
        text_prop = self.index_config.text_property

        query = f"""
        UNWIND $chunks AS chunk
        MERGE (c:{chunk_label} {{chunk_id: chunk.chunk_id}})
        SET c.{text_prop} = chunk.text,
            c.document_id = chunk.document_id,
            c.`index` = chunk.index,
            c.document_title = chunk.document_title,
            c.document_type = chunk.document_type,
            c.{embedding_prop} = chunk.embedding
        RETURN count(c) AS count
        """

        chunk_data = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "document_id": chunk.document_id,
                "index": chunk.index,
                "document_title": chunk.metadata.get("document_title"),
                "document_type": chunk.metadata.get("document_type"),
                "embedding": chunk.embedding,
            }
            for chunk in chunks
        ]

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, {"chunks": chunk_data})
            record = result.single()
            count = record["count"] if record else 0

        return {"chunks_written": count}

    def create_document_chunk_relationships(self) -> dict[str, int]:
        """Create FROM_DOCUMENT relationships between Chunks and Documents.

        Returns:
            Dictionary with count of relationships created.
        """
        chunk_label = self.index_config.chunk_label
        query = f"""
        MATCH (c:{chunk_label})
        WHERE c.document_id IS NOT NULL
        MATCH (d:Document {{document_id: c.document_id}})
        MERGE (c)-[r:FROM_DOCUMENT]->(d)
        RETURN count(r) AS count
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            record = result.single()
            count = record["count"] if record else 0

        return {"from_document_relationships": count}

    def create_next_chunk_relationships(self) -> dict[str, int]:
        """Create NEXT_CHUNK relationships between sequential chunks.

        Returns:
            Dictionary with count of relationships created.
        """
        chunk_label = self.index_config.chunk_label
        query = f"""
        MATCH (c1:{chunk_label})
        MATCH (c2:{chunk_label})
        WHERE c1.document_id = c2.document_id
          AND c2.index = c1.index + 1
        MERGE (c1)-[r:NEXT_CHUNK]->(c2)
        RETURN count(r) AS count
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            record = result.single()
            count = record["count"] if record else 0

        return {"next_chunk_relationships": count}

    def create_entity_mentions(
        self, mentions: list[EntityMention]
    ) -> dict[str, int]:
        """Create MENTIONS relationships between Chunks and entities.

        Args:
            mentions: List of entity mentions to create relationships for.

        Returns:
            Dictionary with counts by entity type.
        """
        results: dict[str, int] = {}
        chunk_label = self.index_config.chunk_label

        for mention in mentions:
            entity_label = mention.entity_type  # Customer, Company, or Stock

            # Match entity by common ID patterns
            if mention.entity_type == "Customer":
                match_clause = f"""
                MATCH (e:{entity_label})
                WHERE e.customer_id = $entity_id
                   OR e.first_name + ' ' + e.last_name = $entity_name
                """
            elif mention.entity_type == "Company":
                match_clause = f"""
                MATCH (e:{entity_label})
                WHERE e.company_id = $entity_id
                   OR e.name = $entity_name
                """
            elif mention.entity_type == "Stock":
                match_clause = f"""
                MATCH (e:{entity_label})
                WHERE e.stock_id = $entity_id
                   OR e.ticker = $entity_name
                """
            else:
                continue

            query = f"""
            {match_clause}
            UNWIND $chunk_ids AS chunk_id
            MATCH (c:{chunk_label} {{chunk_id: chunk_id}})
            MERGE (c)-[r:MENTIONS]->(e)
            RETURN count(r) AS count
            """

            with self.driver.session(database=self.config.database) as session:
                result = session.run(
                    query,
                    {
                        "entity_id": mention.entity_id,
                        "entity_name": mention.entity_name,
                        "chunk_ids": mention.chunk_ids,
                    },
                )
                record = result.single()
                count = record["count"] if record else 0
                results[f"{entity_label}_mentions"] = (
                    results.get(f"{entity_label}_mentions", 0) + count
                )

        return results

    def create_describes_relationships(self) -> dict[str, int]:
        """Create DESCRIBES relationships for customer profile documents.

        Links Document nodes of type customer_profile to Customer nodes
        based on name matching in the document title.

        Returns:
            Dictionary with count of relationships created.
        """
        query = """
        MATCH (d:Document)
        WHERE d.document_type = 'customer_profile'
        WITH d,
             replace(replace(d.title, 'Customer Profile - ', ''), 'Customer Profile: ', '') AS customer_name
        MATCH (c:Customer)
        WHERE c.first_name + ' ' + c.last_name = customer_name
        MERGE (d)-[r:DESCRIBES]->(c)
        RETURN count(r) AS count
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            record = result.single()
            count = record["count"] if record else 0

        return {"describes_relationships": count}

    def get_graph_stats(self) -> dict[str, int]:
        """Get counts of document graph nodes and relationships.

        Returns:
            Dictionary with node and relationship counts.
        """
        stats: dict[str, int] = {}
        chunk_label = self.index_config.chunk_label

        # Count nodes
        node_queries = [
            ("document_count", "MATCH (d:Document) RETURN count(d) AS count"),
            ("chunk_count", f"MATCH (c:{chunk_label}) RETURN count(c) AS count"),
        ]

        # Count relationships
        rel_queries = [
            (
                "from_document_count",
                f"MATCH (:{chunk_label})-[r:FROM_DOCUMENT]->(:Document) RETURN count(r) AS count",
            ),
            (
                "next_chunk_count",
                f"MATCH (:{chunk_label})-[r:NEXT_CHUNK]->(:{chunk_label}) RETURN count(r) AS count",
            ),
            # Note: MENTIONS relationships (Chunk->Company/Stock) not created in this lab
            (
                "describes_count",
                "MATCH (:Document)-[r:DESCRIBES]->(:Customer) RETURN count(r) AS count",
            ),
        ]

        with self.driver.session(database=self.config.database) as session:
            for stat_name, query in node_queries + rel_queries:
                result = session.run(query)
                record = result.single()
                stats[stat_name] = record["count"] if record else 0

        return stats

    def verify_indexes(self) -> dict[str, dict[str, str]]:
        """Verify that required indexes exist and are online.

        Returns:
            Dictionary with index status information.
        """
        query = """
        SHOW INDEXES
        YIELD name, type, state, labelsOrTypes, properties
        WHERE name IN [$vector_index, $fulltext_index]
        RETURN name, type, state, labelsOrTypes, properties
        """

        results: dict[str, dict[str, str]] = {}

        with self.driver.session(database=self.config.database) as session:
            records = session.run(
                query,
                {
                    "vector_index": self.index_config.vector_index_name,
                    "fulltext_index": self.index_config.fulltext_index_name,
                },
            )

            for record in records:
                results[record["name"]] = {
                    "type": record["type"],
                    "state": record["state"],
                    "labels": str(record["labelsOrTypes"]),
                    "properties": str(record["properties"]),
                }

        return results

    def clear_document_graph(self) -> dict[str, int]:
        """Remove all Document and Chunk nodes, relationships, and indexes.

        This also drops vector and full-text indexes so they can be recreated
        with the correct dimensions.

        Returns:
            Dictionary with counts of deleted nodes and indexes.
        """
        chunk_label = self.index_config.chunk_label
        results: dict[str, int] = {}

        # Drop indexes first (so they can be recreated with correct dimensions)
        with self.driver.session(database=self.config.database) as session:
            indexes_dropped = 0
            for index_name in [self.index_config.vector_index_name, self.index_config.fulltext_index_name]:
                try:
                    session.run(f"DROP INDEX {index_name} IF EXISTS")
                    indexes_dropped += 1
                except Exception:
                    pass  # Index might not exist
            results["indexes_dropped"] = indexes_dropped

        # Delete nodes
        query = f"""
        MATCH (n)
        WHERE n:Document OR n:{chunk_label}
        DETACH DELETE n
        RETURN count(n) AS count
        """

        with self.driver.session(database=self.config.database) as session:
            result = session.run(query)
            record = result.single()
            results["nodes_deleted"] = record["count"] if record else 0

        return results


def write_document_graph(
    neo4j_config: Neo4jConfig,
    documents: list[ProcessedDocument],
    chunks: list[ProcessedChunk],
    embedding_dimensions: int,
    index_config: Optional[IndexConfig] = None,
    clear_existing: bool = False,
) -> dict[str, Any]:
    """Write complete document graph to Neo4j.

    Convenience function that handles the full pipeline of creating
    indexes, constraints, nodes, and relationships.

    Args:
        neo4j_config: Neo4j connection configuration.
        documents: Processed documents to write.
        chunks: Processed chunks with embeddings.
        embedding_dimensions: Vector dimensions for index creation.
        index_config: Index configuration.
        clear_existing: Whether to clear existing document graph first.

    Returns:
        Dictionary with operation results and statistics.
    """
    writer = GraphWriter(neo4j_config, index_config)
    results: dict[str, Any] = {"timing": {}}

    try:
        # Verify connection
        start = time.time()
        if not writer.verify_connection():
            raise ConnectionError("Failed to connect to Neo4j")
        results["timing"]["connection_verify"] = time.time() - start

        # Clear existing if requested
        if clear_existing:
            start = time.time()
            results["clear"] = writer.clear_document_graph()
            results["timing"]["clear"] = time.time() - start

        # Create constraints
        start = time.time()
        results["constraints"] = writer.create_constraints()
        results["timing"]["constraints"] = time.time() - start

        # Create indexes
        start = time.time()
        results["indexes"] = writer.create_indexes(embedding_dimensions)
        results["timing"]["indexes"] = time.time() - start

        # Write documents
        start = time.time()
        results["documents"] = writer.write_documents(documents)
        results["timing"]["documents"] = time.time() - start

        # Write chunks
        start = time.time()
        results["chunks"] = writer.write_chunks(chunks)
        results["timing"]["chunks"] = time.time() - start

        # Create relationships
        start = time.time()
        results["from_document"] = writer.create_document_chunk_relationships()
        results["timing"]["from_document"] = time.time() - start

        start = time.time()
        results["next_chunk"] = writer.create_next_chunk_relationships()
        results["timing"]["next_chunk"] = time.time() - start

        start = time.time()
        results["describes"] = writer.create_describes_relationships()
        results["timing"]["describes"] = time.time() - start

        # Get final stats
        results["stats"] = writer.get_graph_stats()
        results["index_status"] = writer.verify_indexes()

    finally:
        writer.close()

    return results
