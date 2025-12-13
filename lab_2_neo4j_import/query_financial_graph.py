"""
Financial Graph Query Application using Neo4j Spark Connector

Run sample Cypher queries against the Neo4j financial demo database using PySpark
and the Neo4j Spark Connector.

Usage:
    uv run python lab_2_neo4j_import/query_financial_graph.py [query_name]

Available queries:
    portfolio         - Top customers by portfolio value
    diversified       - Accounts with multiple holdings
    sectors           - Investment allocation by sector
    active_senders    - Most active sending accounts
    bidirectional     - Accounts with bidirectional flow
    high_value        - High-value transactions (>$1000)
    risk_profile      - Customer segmentation by risk
    all               - Run all queries

Prerequisites:
    - PySpark installed (uv add pyspark)
    - Neo4j Spark Connector JAR available
    - .env file with Neo4j credentials

Best Practices Applied:
    - Uses Spark DataSource V2 API (org.neo4j.spark.DataSource)
    - Uses 'query' option for complex Cypher with multiple MATCH clauses
    - Pushdown optimizations enabled by default
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Neo4j Spark Connector Maven coordinates
NEO4J_CONNECTOR_PACKAGE = "org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3"


QUERIES = {
    "portfolio": {
        "title": "Top 10 Customers by Portfolio Value",
        "query": """
            MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)-[:HAS_POSITION]->(p:Position)
            WITH c, round(SUM(p.current_value), 2) AS total_portfolio_value
            RETURN
                c.customer_id AS customer_id,
                c.first_name + ' ' + c.last_name AS customer_name,
                total_portfolio_value
            ORDER BY total_portfolio_value DESC
            LIMIT 10
        """,
    },
    "diversified": {
        "title": "Accounts with Multiple Holdings",
        "query": """
            MATCH (a:Account)-[:HAS_POSITION]->(p:Position)
            WITH a, COUNT(p) AS position_count, round(SUM(p.current_value), 2) AS total_value
            WHERE position_count > 1
            RETURN
                a.account_id AS account,
                a.account_type AS type,
                position_count AS num_positions,
                total_value AS portfolio_value
            ORDER BY position_count DESC
            LIMIT 10
        """,
    },
    "sectors": {
        "title": "Investment Allocation by Sector",
        "query": """
            MATCH (a:Account)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)-[:OF_COMPANY]->(c:Company)
            WHERE c.sector IS NOT NULL
            WITH c.sector AS sector, round(SUM(p.current_value), 2) AS sector_value
            WITH sector, sector_value, SUM(sector_value) OVER () AS total_value
            RETURN
                sector,
                sector_value,
                round(sector_value * 100.0 / total_value, 2) AS pct_of_total
            ORDER BY sector_value DESC
        """,
    },
    "active_senders": {
        "title": "Most Active Sending Accounts",
        "query": """
            MATCH (a:Account)-[:PERFORMS]->(t:Transaction)
            WITH a, COUNT(t) AS tx_count, round(SUM(t.amount), 2) AS total_sent
            ORDER BY tx_count DESC
            LIMIT 10
            MATCH (c:Customer)-[:HAS_ACCOUNT]->(a)
            RETURN
                c.first_name + ' ' + c.last_name AS customer_name,
                a.account_id AS account,
                a.account_type AS account_type,
                tx_count AS num_transactions,
                total_sent
        """,
    },
    "bidirectional": {
        "title": "Accounts with Bidirectional Transaction Flow",
        "query": """
            MATCH (a:Account)-[:PERFORMS]->(:Transaction)
            WITH a, COUNT(*) AS sent_count
            MATCH (a)<-[:BENEFITS_TO]-(:Transaction)
            WITH a, sent_count, COUNT(*) AS received_count
            MATCH (c:Customer)-[:HAS_ACCOUNT]->(a)
            RETURN
                c.first_name + ' ' + c.last_name AS customer_name,
                a.account_id AS account,
                a.account_type AS type,
                a.balance AS balance,
                sent_count,
                received_count
            ORDER BY sent_count + received_count DESC
            LIMIT 10
        """,
    },
    "high_value": {
        "title": "High-Value Transactions (> $1,000)",
        "query": """
            MATCH (from:Account)-[:PERFORMS]->(t:Transaction)-[:BENEFITS_TO]->(to:Account)
            WHERE t.amount > 1000
            RETURN
                from.account_id AS sender,
                to.account_id AS recipient,
                t.amount AS amount,
                t.transaction_date AS date,
                t.description AS description
            ORDER BY t.amount DESC
            LIMIT 10
        """,
    },
    "risk_profile": {
        "title": "Portfolio Characteristics by Risk Profile",
        "query": """
            MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)
            WHERE c.risk_profile IS NOT NULL
            OPTIONAL MATCH (a)-[:HAS_POSITION]->(p:Position)
            WITH c.risk_profile AS risk_profile,
                 COUNT(DISTINCT c) AS num_customers,
                 AVG(c.annual_income) AS avg_income,
                 AVG(c.credit_score) AS avg_credit_score,
                 AVG(a.balance) AS avg_account_balance,
                 SUM(p.current_value) AS total_investment_value
            RETURN
                risk_profile,
                num_customers,
                round(avg_income, 0) AS avg_income,
                round(avg_credit_score, 0) AS avg_credit_score,
                round(avg_account_balance, 2) AS avg_account_balance,
                round(total_investment_value, 2) AS total_investment_value
            ORDER BY risk_profile
        """,
    },
}


def create_spark_session():
    """Create a Spark session with Neo4j Connector configured."""
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName("Neo4j Financial Graph Queries")
        .config("spark.jars.packages", NEO4J_CONNECTOR_PACKAGE)
        # Configure Neo4j connection globally
        .config("neo4j.url", NEO4J_URI)
        .config("neo4j.authentication.type", "basic")
        .config("neo4j.authentication.basic.username", NEO4J_USERNAME)
        .config("neo4j.authentication.basic.password", NEO4J_PASSWORD)
        .config("neo4j.database", NEO4J_DATABASE)
        .getOrCreate()
    )

    # Reduce Spark logging noise
    spark.sparkContext.setLogLevel("WARN")

    return spark


def run_query(spark, query: str, partitions: int = 1):
    """
    Execute a Cypher query using the Neo4j Spark Connector.

    Best Practices:
        - Uses 'query' option for complex Cypher with multiple MATCH clauses
        - Pushdown optimizations enabled by default (filters, columns, aggregates, limits)
        - Use partitions > 1 for large result sets (disables limit pushdown)
    """
    return (
        spark.read
        .format("org.neo4j.spark.DataSource")
        .option("query", query)
        .option("partitions", str(partitions))
        .load()
    )


def display_results(title: str, df):
    """Display query results in a formatted table."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    if df.count() == 0:
        print("No results.")
        return

    df.show(truncate=False)
    print()


def main():
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        print("Error: Missing Neo4j credentials in .env file")
        print("Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        sys.exit(1)

    query_name = sys.argv[1] if len(sys.argv) > 1 else "all"

    if query_name not in QUERIES and query_name != "all":
        print(f"Unknown query: {query_name}")
        print(f"Available: {', '.join(QUERIES.keys())}, all")
        sys.exit(1)

    print(f"Initializing Spark with Neo4j Connector...")
    print(f"Neo4j URL: {NEO4J_URI}")
    print(f"Database: {NEO4J_DATABASE}")

    try:
        spark = create_spark_session()
    except Exception as e:
        print(f"Failed to create Spark session: {e}")
        print()
        print("Make sure PySpark is installed: uv add pyspark")
        sys.exit(1)

    # Test connection
    try:
        test_df = run_query(spark, "RETURN 'Connected!' AS status")
        status = test_df.collect()[0]["status"]
        print(f"Connection: {status}")
    except Exception as e:
        print(f"Connection failed: {e}")
        spark.stop()
        sys.exit(1)

    # Run queries
    queries_to_run = QUERIES.keys() if query_name == "all" else [query_name]

    for name in queries_to_run:
        q = QUERIES[name]
        df = run_query(spark, q["query"])
        display_results(q["title"], df)

    spark.stop()


if __name__ == "__main__":
    main()
