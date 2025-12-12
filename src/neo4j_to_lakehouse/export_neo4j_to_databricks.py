"""
Export Neo4j Graph Data to Databricks Unity Catalog

This script extracts nodes and relationships from Neo4j and writes them
as Delta tables in Unity Catalog.

Prerequisites:
    1. Neo4j database with financial demo data loaded
    2. Databricks Secrets scope 'neo4j-creds' with: url, username, password
    3. Databricks cluster with Neo4j Spark Connector installed
    4. Cluster access mode: Dedicated (not Shared)

Usage:
    Run this script in a Databricks notebook or as a job.
"""

import time


# =============================================================================
# CONFIGURATION
# =============================================================================

# Unity Catalog destination (loaded from volume_path secret)
# These are defaults if secrets are not available
CATALOG = "neo4j_augmentation_demo"
SCHEMA = "graph_data"

# Node labels to extract
NODE_LABELS = [
    "Customer",
    "Bank",
    "Account",
    "Company",
    "Stock",
    "Position",
    "Transaction",
]

# Relationships to extract: (type, source_label, target_label)
RELATIONSHIPS = [
    ("HAS_ACCOUNT", "Customer", "Account"),
    ("AT_BANK", "Account", "Bank"),
    ("OF_COMPANY", "Stock", "Company"),
    ("PERFORMS", "Account", "Transaction"),
    ("BENEFITS_TO", "Transaction", "Account"),
    ("HAS_POSITION", "Account", "Position"),
    ("OF_SECURITY", "Position", "Stock"),
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_config():
    """Load Neo4j credentials from Databricks Secrets."""
    global CATALOG, SCHEMA

    print("=" * 70)
    print("CONFIGURATION")
    print("=" * 70)

    config = {
        "url": dbutils.secrets.get(scope="neo4j-creds", key="url"),
        "username": dbutils.secrets.get(scope="neo4j-creds", key="username"),
        "password": dbutils.secrets.get(scope="neo4j-creds", key="password"),
        "database": "neo4j",
    }

    # Extract catalog/schema from volume_path secret
    # Format: /Volumes/{catalog}/{schema}/{volume}
    try:
        volume_path = dbutils.secrets.get(scope="neo4j-creds", key="volume_path")
        parts = volume_path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "Volumes":
            CATALOG = parts[1]
            SCHEMA = parts[2]
            print(f"[OK] Catalog from volume_path: {CATALOG}")
            print(f"[OK] Schema from volume_path: {SCHEMA}")
        else:
            print(f"[WARN] Could not parse volume_path: {volume_path}")
            print(f"[INFO] Using defaults: {CATALOG}.{SCHEMA}")
    except Exception:
        print(f"[INFO] volume_path secret not found, using defaults")
        print(f"[INFO] Catalog: {CATALOG}, Schema: {SCHEMA}")

    # Configure Spark session
    spark.conf.set("neo4j.url", config["url"])
    spark.conf.set("neo4j.authentication.basic.username", config["username"])
    spark.conf.set("neo4j.authentication.basic.password", config["password"])
    spark.conf.set("neo4j.database", config["database"])

    print(f"Neo4j URL: {config['url']}")
    print(f"Database:  {config['database']}")
    print(f"Catalog:   {CATALOG}")
    print(f"Schema:    {SCHEMA}")
    print("=" * 70)

    return config


def test_connection(config: dict) -> bool:
    """Test Neo4j connectivity."""
    print("\n[Testing Neo4j connection...]")

    try:
        df = (
            spark.read.format("org.neo4j.spark.DataSource")
            .option("query", "RETURN 1 AS test")
            .load()
        )
        df.collect()
        print("[OK] Connected to Neo4j")
        return True
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return False


def setup_catalog():
    """Verify catalog exists and create schema if needed."""
    print("\n[Setting up Unity Catalog...]")

    # Check if catalog exists (don't try to create - requires special permissions)
    try:
        catalogs = [row.catalog for row in spark.sql("SHOW CATALOGS").collect()]
        if CATALOG not in catalogs:
            print(f"[ERROR] Catalog '{CATALOG}' does not exist.")
            print(f"        Available catalogs: {catalogs}")
            print(f"        Please create the catalog first or update CATALOG variable.")
            raise ValueError(f"Catalog '{CATALOG}' not found")
        print(f"[OK] Catalog exists: {CATALOG}")
    except Exception as e:
        if "not found" in str(e).lower() or "Catalog" in str(e):
            raise
        # If SHOW CATALOGS fails, try to use the catalog directly
        print(f"[INFO] Could not list catalogs, attempting to use '{CATALOG}' directly")

    # Create schema if it doesn't exist
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
    print(f"[OK] Schema ready: {CATALOG}.{SCHEMA}")


def read_nodes(label: str):
    """Read all nodes with a given label from Neo4j."""
    return (
        spark.read.format("org.neo4j.spark.DataSource")
        .option("labels", label)
        .load()
    )


def read_relationship(rel_type: str, source_label: str, target_label: str):
    """Read all relationships of a given type from Neo4j."""
    return (
        spark.read.format("org.neo4j.spark.DataSource")
        .option("relationship", rel_type)
        .option("relationship.source.labels", source_label)
        .option("relationship.target.labels", target_label)
        .option("relationship.nodes.map", "false")
        .load()
    )


def write_table(df, table_name: str) -> int:
    """Write DataFrame as a Delta table in Unity Catalog."""
    full_name = f"{CATALOG}.{SCHEMA}.{table_name}"

    df.write.format("delta").mode("overwrite").saveAsTable(full_name)

    return df.count()


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_nodes() -> dict:
    """Export all node types to Delta tables."""
    print("\n" + "=" * 70)
    print("EXPORTING NODES")
    print("=" * 70)

    results = {}

    for i, label in enumerate(NODE_LABELS, 1):
        table_name = label.lower()
        print(f"\n[{i}/{len(NODE_LABELS)}] {label} -> {table_name}")

        start = time.time()
        df = read_nodes(label)
        count = write_table(df, table_name)
        elapsed = time.time() - start

        results[label] = {"count": count, "time": elapsed}
        print(f"    {count} rows in {elapsed:.2f}s")

    return results


def export_relationships() -> dict:
    """Export all relationship types to Delta tables."""
    print("\n" + "=" * 70)
    print("EXPORTING RELATIONSHIPS")
    print("=" * 70)

    results = {}

    for i, (rel_type, source, target) in enumerate(RELATIONSHIPS, 1):
        table_name = rel_type.lower()
        print(f"\n[{i}/{len(RELATIONSHIPS)}] {rel_type} -> {table_name}")
        print(f"    Pattern: (:{source})-[:{rel_type}]->(:{target})")

        start = time.time()
        df = read_relationship(rel_type, source, target)
        count = write_table(df, table_name)
        elapsed = time.time() - start

        results[rel_type] = {"count": count, "time": elapsed}
        print(f"    {count} rows in {elapsed:.2f}s")

    return results


# =============================================================================
# VALIDATION
# =============================================================================

def validate_export(node_results: dict, rel_results: dict) -> bool:
    """Validate exported data by checking row counts."""
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    # Expected counts
    expected_nodes = {
        "Customer": 102,
        "Bank": 102,
        "Account": 123,
        "Company": 102,
        "Stock": 102,
        "Position": 110,
        "Transaction": 123,
    }

    expected_rels = {
        "HAS_ACCOUNT": 123,
        "AT_BANK": 123,
        "OF_COMPANY": 102,
        "PERFORMS": 123,
        "BENEFITS_TO": 123,
        "HAS_POSITION": 110,
        "OF_SECURITY": 110,
    }

    all_valid = True

    print("\nNode Tables:")
    print(f"{'Table':<15} {'Expected':>10} {'Actual':>10} {'Status':>10}")
    print("-" * 50)

    for label, expected in expected_nodes.items():
        actual = node_results.get(label, {}).get("count", 0)
        status = "[OK]" if actual == expected else "[MISMATCH]"
        if actual != expected:
            all_valid = False
        print(f"{label.lower():<15} {expected:>10} {actual:>10} {status:>10}")

    print("\nRelationship Tables:")
    print(f"{'Table':<15} {'Expected':>10} {'Actual':>10} {'Status':>10}")
    print("-" * 50)

    for rel_type, expected in expected_rels.items():
        actual = rel_results.get(rel_type, {}).get("count", 0)
        status = "[OK]" if actual == expected else "[MISMATCH]"
        if actual != expected:
            all_valid = False
        print(f"{rel_type.lower():<15} {expected:>10} {actual:>10} {status:>10}")

    return all_valid


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("NEO4J TO DATABRICKS EXPORT")
    print("=" * 70)

    total_start = time.time()

    # Setup
    config = load_config()

    if not test_connection(config):
        return False

    setup_catalog()

    # Export
    node_results = export_nodes()
    rel_results = export_relationships()

    # Validate
    valid = validate_export(node_results, rel_results)

    # Summary
    total_time = time.time() - total_start
    total_nodes = sum(r["count"] for r in node_results.values())
    total_rels = sum(r["count"] for r in rel_results.values())

    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"Total nodes:         {total_nodes}")
    print(f"Total relationships: {total_rels}")
    print(f"Total tables:        {len(node_results) + len(rel_results)}")
    print(f"Total time:          {total_time:.2f}s")
    print(f"Status:              {'SUCCESS' if valid else 'COMPLETED WITH WARNINGS'}")
    print("=" * 70)

    return valid


if __name__ == "__main__":
    main()
