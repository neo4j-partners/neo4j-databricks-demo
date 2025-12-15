"""
Clear Neo4j Database Utility

This script connects to Neo4j and clears all data including:
- All nodes and relationships
- All constraints
- All indexes

Uses APOC procedures for efficient batch deletion.

Prerequisites:
    - APOC plugin installed in Neo4j
    - Databricks secrets configured with neo4j-creds scope
    - .env file with DATABRICKS_HOST and DATABRICKS_TOKEN

Usage:
    uv run python lab_1_databricks_upload/clear_neo4j_database.py

    # Dry run (show what would be deleted without deleting)
    uv run python lab_1_databricks_upload/clear_neo4j_database.py --dry-run

    # Skip confirmation prompt
    uv run python lab_1_databricks_upload/clear_neo4j_database.py --yes
"""

import argparse
import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods
for var in ["DATABRICKS_CONFIG_PROFILE", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET"]:
    os.environ.pop(var, None)


def get_neo4j_credentials() -> tuple[str, str, str]:
    """Get Neo4j credentials from Databricks secrets.

    Returns:
        Tuple of (uri, username, password).
    """
    from databricks.sdk import WorkspaceClient

    def decode_secret(encoded: str) -> str:
        return base64.b64decode(encoded).decode("utf-8")

    print("[1/5] Retrieving Neo4j credentials from Databricks secrets...")

    try:
        client = WorkspaceClient()
        uri = decode_secret(client.secrets.get_secret(scope="neo4j-creds", key="url").value)
        user = decode_secret(client.secrets.get_secret(scope="neo4j-creds", key="username").value)
        pwd = decode_secret(client.secrets.get_secret(scope="neo4j-creds", key="password").value)
        print(f"  [OK] URI: {uri}")
        return uri, user, pwd
    except Exception as e:
        print(f"  [FAIL] {e}")
        sys.exit(1)


def get_database_stats(session) -> dict:
    """Get current database statistics."""
    stats = {}

    # Count nodes by label
    result = session.run("""
        MATCH (n)
        WITH labels(n)[0] AS label, count(n) AS count
        RETURN label, count
        ORDER BY count DESC
    """)
    stats["nodes"] = {r["label"]: r["count"] for r in result}
    stats["total_nodes"] = sum(stats["nodes"].values())

    # Count relationships by type
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(r) AS count
        ORDER BY count DESC
    """)
    stats["relationships"] = {r["type"]: r["count"] for r in result}
    stats["total_relationships"] = sum(stats["relationships"].values())

    # Get constraints
    result = session.run("SHOW CONSTRAINTS")
    stats["constraints"] = [r["name"] for r in result]

    # Get indexes
    result = session.run("SHOW INDEXES")
    stats["indexes"] = [r["name"] for r in result]

    return stats


def print_stats(stats: dict, header: str) -> None:
    """Print database statistics."""
    print(f"\n{header}")
    print("-" * 50)

    print(f"  Nodes: {stats['total_nodes']}")
    for label, count in stats["nodes"].items():
        print(f"    - {label}: {count}")

    print(f"  Relationships: {stats['total_relationships']}")
    for rel_type, count in stats["relationships"].items():
        print(f"    - {rel_type}: {count}")

    print(f"  Constraints: {len(stats['constraints'])}")
    for name in stats["constraints"]:
        print(f"    - {name}")

    print(f"  Indexes: {len(stats['indexes'])}")
    for name in stats["indexes"]:
        print(f"    - {name}")


def clear_database(session, dry_run: bool = False) -> dict:
    """Clear all data from the database using APOC.

    Args:
        session: Neo4j session.
        dry_run: If True, only show what would be deleted.

    Returns:
        Dictionary with deletion results.
    """
    results = {
        "nodes_deleted": 0,
        "relationships_deleted": 0,
        "constraints_dropped": 0,
        "indexes_dropped": 0,
    }

    if dry_run:
        print("\n[DRY RUN] Would perform the following operations:")
        print("  - Delete all nodes and relationships using APOC")
        print("  - Drop all constraints")
        print("  - Drop all indexes")
        return results

    # Step 1: Delete all nodes and relationships using APOC
    print("\n[3/5] Deleting all nodes and relationships...")
    try:
        # Use APOC for batch deletion (more efficient for large graphs)
        result = session.run("""
            CALL apoc.periodic.iterate(
                'MATCH (n) RETURN n',
                'DETACH DELETE n',
                {batchSize: 10000, parallel: false}
            )
            YIELD batches, total, errorMessages
            RETURN batches, total, errorMessages
        """)
        record = result.single()
        results["nodes_deleted"] = record["total"]
        print(f"  [OK] Deleted {record['total']} nodes in {record['batches']} batches")
        if record["errorMessages"]:
            print(f"  [WARN] Errors: {record['errorMessages']}")
    except Exception as e:
        # Fallback if APOC is not available
        if "apoc" in str(e).lower():
            print("  [INFO] APOC not available, using standard deletion...")
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) AS deleted")
            record = result.single()
            results["nodes_deleted"] = record["deleted"]
            print(f"  [OK] Deleted {record['deleted']} nodes")
        else:
            print(f"  [FAIL] {e}")
            raise

    # Step 2: Drop all constraints
    print("\n[4/5] Dropping all constraints...")
    result = session.run("SHOW CONSTRAINTS")
    constraints = [r["name"] for r in result]
    for name in constraints:
        try:
            session.run(f"DROP CONSTRAINT {name} IF EXISTS")
            results["constraints_dropped"] += 1
            print(f"  [OK] Dropped constraint: {name}")
        except Exception as e:
            print(f"  [WARN] Failed to drop constraint {name}: {e}")

    if not constraints:
        print("  [OK] No constraints to drop")

    # Step 3: Drop all indexes (except system indexes)
    print("\n[5/5] Dropping all indexes...")
    result = session.run("SHOW INDEXES")
    indexes = [(r["name"], r.get("type", "")) for r in result]
    for name, idx_type in indexes:
        # Skip system indexes (lookup indexes)
        if idx_type == "LOOKUP" or name.startswith("__"):
            continue
        try:
            session.run(f"DROP INDEX {name} IF EXISTS")
            results["indexes_dropped"] += 1
            print(f"  [OK] Dropped index: {name}")
        except Exception as e:
            print(f"  [WARN] Failed to drop index {name}: {e}")

    if results["indexes_dropped"] == 0:
        print("  [OK] No user indexes to drop")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Clear all data from Neo4j database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("NEO4J DATABASE CLEAR UTILITY")
    print("=" * 60)

    # Get credentials
    uri, user, pwd = get_neo4j_credentials()

    # Connect to Neo4j
    print("\n[2/5] Connecting to Neo4j...")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))

    try:
        with driver.session(database="neo4j") as session:
            # Verify connection
            session.run("RETURN 1")
            print("  [OK] Connected successfully")

            # Get current stats
            stats = get_database_stats(session)
            print_stats(stats, "Current Database State:")

            # Check if anything to delete
            if stats["total_nodes"] == 0 and not stats["constraints"] and not stats["indexes"]:
                print("\n[OK] Database is already empty!")
                return

            # Confirm deletion
            if not args.dry_run and not args.yes:
                print("\n" + "!" * 60)
                print("WARNING: This will permanently delete ALL data!")
                print("!" * 60)
                response = input("\nType 'yes' to confirm: ")
                if response.lower() != "yes":
                    print("\n[CANCELLED] No changes made.")
                    return

            # Clear database
            results = clear_database(session, dry_run=args.dry_run)

            if not args.dry_run:
                # Verify deletion
                final_stats = get_database_stats(session)
                print_stats(final_stats, "\nFinal Database State:")

                print("\n" + "=" * 60)
                print("SUMMARY")
                print("=" * 60)
                print(f"  Nodes deleted: {results['nodes_deleted']}")
                print(f"  Constraints dropped: {results['constraints_dropped']}")
                print(f"  Indexes dropped: {results['indexes_dropped']}")
                print("=" * 60)

    finally:
        driver.close()
        print("\n[OK] Connection closed")


if __name__ == "__main__":
    main()
