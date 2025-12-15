"""
Debug utility for Lab 3 graph structure.

Connects to Neo4j and investigates why graph-aware search
isn't finding related customers/companies/stocks.

Usage:
    uv run python lab_3_vector_embeddings/debug_graph.py
"""

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods
for var in ["DATABRICKS_CONFIG_PROFILE", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET"]:
    os.environ.pop(var, None)


def get_neo4j_config() -> tuple[str, str, str]:
    """Get Neo4j credentials from Databricks secrets."""
    from databricks.sdk import WorkspaceClient

    def decode_secret(encoded: str) -> str:
        return base64.b64decode(encoded).decode("utf-8")

    client = WorkspaceClient()
    uri = decode_secret(client.secrets.get_secret(scope="neo4j-creds", key="url").value)
    user = decode_secret(client.secrets.get_secret(scope="neo4j-creds", key="username").value)
    pwd = decode_secret(client.secrets.get_secret(scope="neo4j-creds", key="password").value)
    return uri, user, pwd


def main():
    print("=" * 70)
    print("LAB 3 GRAPH STRUCTURE DIAGNOSTIC")
    print("=" * 70)

    # Connect to Neo4j
    uri, user, pwd = get_neo4j_config()
    print(f"\nConnecting to: {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))

    with driver.session(database="neo4j") as session:
        # 1. Check node counts
        print("\n" + "-" * 50)
        print("1. NODE COUNTS")
        print("-" * 50)
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] AS label, count(n) AS count
            RETURN label, count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"   {record['label']}: {record['count']}")

        # 2. Check relationship counts
        print("\n" + "-" * 50)
        print("2. RELATIONSHIP COUNTS")
        print("-" * 50)
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"   {record['type']}: {record['count']}")

        # 3. Check Document -> Customer (DESCRIBES) relationships
        print("\n" + "-" * 50)
        print("3. DOCUMENT -> CUSTOMER (DESCRIBES) RELATIONSHIPS")
        print("-" * 50)
        result = session.run("""
            MATCH (d:Document)-[r:DESCRIBES]->(c:Customer)
            RETURN d.title AS doc_title, d.document_type AS doc_type,
                   c.first_name + ' ' + c.last_name AS customer_name
            LIMIT 10
        """)
        records = list(result)
        if records:
            for record in records:
                print(f"   '{record['doc_title']}' -> {record['customer_name']}")
        else:
            print("   [NONE FOUND] - This is why related_customers is empty!")

        # 4. Check Chunk -> Document (FROM_DOCUMENT) relationships
        print("\n" + "-" * 50)
        print("4. CHUNK -> DOCUMENT (FROM_DOCUMENT) RELATIONSHIPS")
        print("-" * 50)
        result = session.run("""
            MATCH (c:Chunk)-[r:FROM_DOCUMENT]->(d:Document)
            RETURN count(r) AS count
        """)
        count = result.single()["count"]
        print(f"   Total FROM_DOCUMENT relationships: {count}")

        # 5. Check if customer profiles exist and their document_type
        print("\n" + "-" * 50)
        print("5. CUSTOMER PROFILE DOCUMENTS")
        print("-" * 50)
        result = session.run("""
            MATCH (d:Document)
            WHERE d.document_type = 'customer_profile'
            RETURN d.title AS title, d.document_type AS type
            LIMIT 10
        """)
        records = list(result)
        if records:
            for record in records:
                print(f"   {record['title']} (type: {record['type']})")
        else:
            print("   [NONE FOUND] - No documents with type 'customer_profile'")

        # 6. Check all document types
        print("\n" + "-" * 50)
        print("6. ALL DOCUMENT TYPES")
        print("-" * 50)
        result = session.run("""
            MATCH (d:Document)
            RETURN d.document_type AS type, count(d) AS count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"   {record['type']}: {record['count']}")

        # 7. Check Customer nodes
        print("\n" + "-" * 50)
        print("7. CUSTOMER NODES (sample)")
        print("-" * 50)
        result = session.run("""
            MATCH (c:Customer)
            RETURN c.first_name + ' ' + c.last_name AS name
            LIMIT 5
        """)
        records = list(result)
        if records:
            for record in records:
                print(f"   {record['name']}")
        else:
            print("   [NONE FOUND] - No Customer nodes in graph!")

        # 8. Debug: Check if DESCRIBES could be created
        print("\n" + "-" * 50)
        print("8. DEBUG: POTENTIAL DESCRIBES MATCHES")
        print("-" * 50)
        result = session.run("""
            MATCH (d:Document)
            WHERE d.document_type = 'customer_profile'
            WITH d,
                 replace(replace(d.title, 'Customer Profile - ', ''), 'Customer Profile: ', '') AS extracted_name
            OPTIONAL MATCH (c:Customer)
            WHERE c.first_name + ' ' + c.last_name = extracted_name
            RETURN d.title AS doc_title, extracted_name,
                   c.first_name + ' ' + c.last_name AS matched_customer
            LIMIT 10
        """)
        records = list(result)
        if records:
            for record in records:
                match_status = "MATCHED" if record['matched_customer'] else "NO MATCH"
                print(f"   Doc: '{record['doc_title']}'")
                print(f"       Extracted name: '{record['extracted_name']}' -> {match_status}")
        else:
            print("   No customer_profile documents to check")

        # 9. Check actual Document titles
        print("\n" + "-" * 50)
        print("9. DOCUMENT TITLES (sample)")
        print("-" * 50)
        result = session.run("""
            MATCH (d:Document)
            RETURN d.title AS title, d.document_type AS type
            LIMIT 10
        """)
        for record in result:
            print(f"   [{record['type']}] {record['title']}")

        # 10. TEST: Simulate the graph traversal query
        print("\n" + "-" * 50)
        print("10. SIMULATE GRAPH TRAVERSAL QUERY")
        print("-" * 50)
        result = session.run("""
            MATCH (chunk:Chunk)
            WITH chunk LIMIT 5
            OPTIONAL MATCH (chunk)-[:FROM_DOCUMENT]->(d:Document)
            OPTIONAL MATCH (d)-[:DESCRIBES]->(customer:Customer)
            RETURN chunk.chunk_id AS chunk_id,
                   d.title AS doc_title,
                   d.document_type AS doc_type,
                   collect(DISTINCT customer.first_name + ' ' + customer.last_name) AS customers
        """)
        for record in result:
            print(f"   Chunk: {record['chunk_id'][:20]}...")
            print(f"       Doc: {record['doc_title']} ({record['doc_type']})")
            print(f"       Customers: {record['customers']}")

        # 11. Check which chunks have customer connections
        print("\n" + "-" * 50)
        print("11. CHUNKS WITH CUSTOMER CONNECTIONS")
        print("-" * 50)
        result = session.run("""
            MATCH (chunk:Chunk)-[:FROM_DOCUMENT]->(d:Document)-[:DESCRIBES]->(c:Customer)
            RETURN count(DISTINCT chunk) AS chunks_with_customers,
                   count(DISTINCT c) AS unique_customers
        """)
        record = result.single()
        print(f"   Chunks connected to customers: {record['chunks_with_customers']}")
        print(f"   Unique customers reachable: {record['unique_customers']}")

        # 12. Test full path from Chunk to Customer
        print("\n" + "-" * 50)
        print("12. SAMPLE FULL PATH: CHUNK -> DOCUMENT -> CUSTOMER")
        print("-" * 50)
        result = session.run("""
            MATCH path = (chunk:Chunk)-[:FROM_DOCUMENT]->(d:Document)-[:DESCRIBES]->(c:Customer)
            RETURN chunk.text AS chunk_text,
                   d.title AS doc_title,
                   c.first_name + ' ' + c.last_name AS customer
            LIMIT 3
        """)
        records = list(result)
        if records:
            for i, record in enumerate(records, 1):
                print(f"   Path {i}:")
                print(f"       Chunk: {record['chunk_text'][:80]}...")
                print(f"       Document: {record['doc_title']}")
                print(f"       Customer: {record['customer']}")
        else:
            print("   [NO PATHS FOUND] - Missing relationship chain!")

        # 13. Test enhanced retrieval query (company matching)
        print("\n" + "-" * 50)
        print("13. TEST ENHANCED RETRIEVAL QUERY")
        print("-" * 50)
        result = session.run("""
            MATCH (d:Document)
            WITH d LIMIT 10
            OPTIONAL MATCH (company:Company)
            WHERE d.title CONTAINS company.name
            OPTIONAL MATCH (stock:Stock)-[:OF_COMPANY]->(company)
            RETURN d.title AS doc_title,
                   collect(DISTINCT company.name) AS companies,
                   collect(DISTINCT stock.ticker) AS stocks
        """)
        for record in result:
            if record['companies']:
                print(f"   Doc: {record['doc_title']}")
                print(f"       Companies: {record['companies']}")
                print(f"       Stocks: {record['stocks']}")

    driver.close()
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
