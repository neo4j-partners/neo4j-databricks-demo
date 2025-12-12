"""
Financial Demo Data Import to Neo4j

This script imports the retail banking and investment portfolio demonstration
data from Databricks Unity Catalog into Neo4j.

Prerequisites:
    1. Neo4j database running (Aura or self-hosted)
    2. Databricks Secrets configured with 'neo4j-creds' scope
    3. Unity Catalog Volume with CSV files uploaded
    4. Neo4j Spark Connector installed on cluster

Usage:
    Run this script in a Databricks notebook or as a job.
"""

import time
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, DateType


# =============================================================================
# CONFIGURATION
# =============================================================================

def load_config():
    """Load configuration from Databricks Secrets."""
    print("=" * 70)
    print("CONFIGURATION - Loading secrets from Databricks")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    config = {}

    print("[DEBUG] Retrieving secrets from scope 'neo4j-creds'...")

    try:
        config["neo4j_user"] = dbutils.secrets.get(scope="neo4j-creds", key="username")
        print(f"  [OK] username: retrieved ({len(config['neo4j_user'])} chars)")
    except Exception as e:
        print(f"  [FAIL] username: {str(e)}")
        raise

    try:
        config["neo4j_pass"] = dbutils.secrets.get(scope="neo4j-creds", key="password")
        print(f"  [OK] password: retrieved ({len(config['neo4j_pass'])} chars, masked)")
    except Exception as e:
        print(f"  [FAIL] password: {str(e)}")
        raise

    try:
        config["neo4j_url"] = dbutils.secrets.get(scope="neo4j-creds", key="url")
        print(f"  [OK] url: {config['neo4j_url']}")
    except Exception as e:
        print(f"  [FAIL] url: {str(e)}")
        raise

    try:
        config["volume_path"] = dbutils.secrets.get(scope="neo4j-creds", key="volume_path")
        print(f"  [OK] volume_path: {config['volume_path']}")
    except Exception as e:
        print(f"  [FAIL] volume_path: {str(e)}")
        raise

    config["neo4j_database"] = "neo4j"

    print("")
    print("[DEBUG] Configuring Spark session for Neo4j connector...")
    try:
        spark.conf.set("neo4j.url", config["neo4j_url"])
        spark.conf.set("neo4j.authentication.basic.username", config["neo4j_user"])
        spark.conf.set("neo4j.authentication.basic.password", config["neo4j_pass"])
        spark.conf.set("neo4j.database", config["neo4j_database"])
        print("  [OK] Spark session configured")
    except Exception as e:
        print(f"  [FAIL] Spark configuration: {str(e)}")
        raise

    print("")
    print("=" * 70)
    print("CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"  Neo4j URL:    {config['neo4j_url']}")
    print(f"  Database:     {config['neo4j_database']}")
    print(f"  Username:     {config['neo4j_user']}")
    print(f"  Volume Path:  {config['volume_path']}")
    print("=" * 70)

    return config


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def read_csv(config: dict, filename: str) -> DataFrame:
    """Read a CSV file from the Unity Catalog Volume."""
    path = f"{config['volume_path']}/{filename}"
    return spark.read.option("header", "true").csv(path)


def write_nodes(config: dict, df: DataFrame, label: str, node_key: str) -> dict:
    """Write DataFrame rows as nodes to Neo4j."""
    count = df.count()
    print(f"[DEBUG] write_nodes(label={label}, key={node_key}, count={count})")

    try:
        start_time = time.time()
        (
            df.write.format("org.neo4j.spark.DataSource")
            .mode("Append")
            .option("labels", f":{label}")
            .option("node.keys", node_key)
            .save()
        )
        elapsed = time.time() - start_time
        print(f"  [OK] {count} {label} nodes written in {elapsed:.2f}s")
        return {"status": "OK", "count": count, "elapsed": elapsed}
    except Exception as e:
        print(f"  [FAIL] Error writing {label} nodes: {type(e).__name__}")
        print(f"         {str(e)[:200]}")
        raise


def write_relationship(
    config: dict,
    df: DataFrame,
    rel_type: str,
    source_label: str,
    source_key: str,
    target_label: str,
    target_key: str
) -> dict:
    """Write DataFrame rows as relationships to Neo4j."""
    count = df.count()
    print(f"[DEBUG] write_relationship(type={rel_type})")
    print(f"        Pattern: (:{source_label})-[:{rel_type}]->(:{target_label})")
    print(f"        Keys: {source_key} -> {target_key}, count={count}")

    try:
        start_time = time.time()
        (
            df.write.format("org.neo4j.spark.DataSource")
            .mode("Append")
            .option("relationship", rel_type)
            .option("relationship.save.strategy", "keys")
            .option("relationship.source.save.mode", "Match")
            .option("relationship.source.labels", f":{source_label}")
            .option("relationship.source.node.keys", f"{source_key}:{source_key}")
            .option("relationship.target.save.mode", "Match")
            .option("relationship.target.labels", f":{target_label}")
            .option("relationship.target.node.keys", f"{target_key}:{target_key}")
            .save()
        )
        elapsed = time.time() - start_time
        print(f"  [OK] {count} {rel_type} relationships written in {elapsed:.2f}s")
        return {"status": "OK", "count": count, "elapsed": elapsed}
    except Exception as e:
        print(f"  [FAIL] Error writing {rel_type} relationships: {type(e).__name__}")
        print(f"         {str(e)[:200]}")
        raise


def run_cypher(config: dict, query: str) -> DataFrame:
    """Execute a Cypher query and return results as DataFrame."""
    return (
        spark.read.format("org.neo4j.spark.DataSource")
        .option("url", config["neo4j_url"])
        .option("authentication.basic.username", config["neo4j_user"])
        .option("authentication.basic.password", config["neo4j_pass"])
        .option("database", config["neo4j_database"])
        .option("query", query)
        .load()
    )


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def verify_csv_files(config: dict) -> bool:
    """Verify CSV files exist in Unity Catalog Volume."""
    print("=" * 70)
    print("FILE VERIFICATION - Checking CSV files in Unity Catalog Volume")
    print("=" * 70)

    # CSV files are in the /csv subdirectory of the volume
    csv_path = f"{config['volume_path']}/csv"
    print(f"CSV path: {csv_path}")
    print("")

    expected_files = [
        "customers.csv",
        "banks.csv",
        "accounts.csv",
        "companies.csv",
        "stocks.csv",
        "portfolio_holdings.csv",
        "transactions.csv"
    ]

    print(f"[DEBUG] Expected files: {len(expected_files)}")
    for f in expected_files:
        print(f"  - {f}")
    print("")

    try:
        files = dbutils.fs.ls(csv_path)
        print(f"  [OK] Listed {len(files)} items")
        print("")

        # Show raw file info
        print("[DEBUG] Raw file listing:")
        print("-" * 70)
        for i, f in enumerate(files):
            print(f"  [{i}] name: {f.name}, size: {f.size} bytes")
        print("-" * 70)
        print("")

        # Extract filenames
        found_files = [f.name.rstrip('/').split('/')[-1] for f in files]

        # Check for expected files
        print("[DEBUG] Checking for expected files:")
        all_present = True
        for expected in expected_files:
            found = expected in found_files
            status = "[OK]  " if found else "[MISSING]"
            if not found:
                all_present = False
            print(f"  {status} {expected}")

        if all_present:
            print("\n[OK] All required CSV files are present!")
        else:
            print("\n[WARNING] Some files are missing!")

        return all_present

    except Exception as e:
        print(f"  [FAIL] Error listing files: {type(e).__name__}: {str(e)}")
        return False


def verify_neo4j_connection(config: dict) -> bool:
    """Verify Neo4j connectivity."""
    print("=" * 70)
    print("NEO4J CONNECTION TEST")
    print("=" * 70)
    print(f"URL: {config['neo4j_url']}")
    print(f"Database: {config['neo4j_database']}")
    print("")

    try:
        print("[DEBUG] Executing connection test...")
        start_time = time.time()

        test_df = run_cypher(config, "RETURN 'Connected' AS status")
        result = test_df.collect()
        elapsed = time.time() - start_time

        print(f"  [OK] Query executed in {elapsed:.2f}s")
        print(f"  [OK] Result: {result}")
        print("")
        print("=" * 70)
        print("[OK] NEO4J CONNECTION SUCCESSFUL!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"  [FAIL] Connection failed: {type(e).__name__}")
        print(f"         {str(e)}")
        return False


def clear_database(config: dict) -> bool:
    """Clear all nodes and relationships from the Neo4j database."""
    from neo4j import GraphDatabase

    print("=" * 70)
    print("DATABASE CLEANUP - Removing existing nodes and relationships")
    print("=" * 70)
    print("")

    print("[DEBUG] Deleting all nodes and relationships...")
    print("        Query: MATCH (n) DETACH DELETE n")
    print("")

    try:
        start_time = time.time()

        # Use neo4j Python driver for direct Cypher execution
        driver = GraphDatabase.driver(
            config["neo4j_url"],
            auth=(config["neo4j_user"], config["neo4j_pass"])
        )

        with driver.session(database=config["neo4j_database"]) as session:
            result = session.run("MATCH (n) DETACH DELETE n")
            summary = result.consume()
            nodes_deleted = summary.counters.nodes_deleted
            rels_deleted = summary.counters.relationships_deleted

        driver.close()

        elapsed = time.time() - start_time
        print(f"  [OK] Deleted {nodes_deleted} nodes and {rels_deleted} relationships")
        print(f"  [OK] Completed in {elapsed:.2f}s")
        print("")
        print("=" * 70)
        print("[OK] DATABASE CLEANUP COMPLETE!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"  [FAIL] Cleanup failed: {type(e).__name__}")
        print(f"         {str(e)[:200]}")
        return False


# =============================================================================
# DATA LOADING AND TRANSFORMATION
# =============================================================================

def load_csv_files(config: dict) -> dict:
    """Load all CSV files from Unity Catalog Volume."""
    print("=" * 70)
    print("DATA LOADING - Reading CSV files from Unity Catalog Volume")
    print("=" * 70)

    # CSV files are in the /csv subdirectory of the volume
    csv_path = f"{config['volume_path']}/csv"
    print(f"Base path: {csv_path}")
    print("")

    data = {}
    files_to_load = [
        ("customers", "customers.csv"),
        ("banks", "banks.csv"),
        ("accounts", "accounts.csv"),
        ("companies", "companies.csv"),
        ("stocks", "stocks.csv"),
        ("positions", "portfolio_holdings.csv"),
        ("transactions", "transactions.csv"),
    ]

    print("-" * 70)
    for key, filename in files_to_load:
        path = f"{csv_path}/{filename}"
        print(f"[DEBUG] Loading: {filename}")
        print(f"        Path: {path}")

        try:
            start_time = time.time()
            df = spark.read.option("header", "true").csv(path)
            count = df.count()
            elapsed = time.time() - start_time
            print(f"  [OK] Loaded {count} rows in {elapsed:.2f}s")
            data[key] = df
        except Exception as e:
            print(f"  [FAIL] Error: {type(e).__name__}: {str(e)[:100]}")
            raise
        print("")
    print("-" * 70)

    print("")
    print("=" * 70)
    print("[OK] ALL CSV FILES LOADED SUCCESSFULLY!")
    print("=" * 70)

    return data


def transform_data(data: dict) -> dict:
    """Apply data type conversions to all DataFrames."""
    print("=" * 70)
    print("DATA TRANSFORMATION - Applying data type conversions")
    print("=" * 70)
    print("")

    transformed = {}

    # Transform Customers
    print("[DEBUG] Transforming: Customers")
    transformed["customers"] = (
        data["customers"]
        .withColumn("annual_income", F.col("annual_income").cast(IntegerType()))
        .withColumn("credit_score", F.col("credit_score").cast(IntegerType()))
        .withColumn("registration_date", F.to_date(F.col("registration_date")))
        .withColumn("date_of_birth", F.to_date(F.col("date_of_birth")))
    )
    print("  [OK] annual_income, credit_score -> INT; dates -> DATE")

    # Transform Banks
    print("[DEBUG] Transforming: Banks")
    transformed["banks"] = (
        data["banks"]
        .withColumn("total_assets_billions", F.col("total_assets_billions").cast(DoubleType()))
        .withColumn("established_year", F.col("established_year").cast(IntegerType()))
    )
    print("  [OK] total_assets_billions -> DOUBLE; established_year -> INT")

    # Transform Accounts
    print("[DEBUG] Transforming: Accounts")
    transformed["accounts"] = (
        data["accounts"]
        .withColumn("balance", F.col("balance").cast(DoubleType()))
        .withColumn("interest_rate", F.col("interest_rate").cast(DoubleType()))
        .withColumn("opened_date", F.to_date(F.col("opened_date")))
    )
    print("  [OK] balance, interest_rate -> DOUBLE; opened_date -> DATE")

    # Transform Companies
    print("[DEBUG] Transforming: Companies")
    transformed["companies"] = (
        data["companies"]
        .withColumn("market_cap_billions", F.col("market_cap_billions").cast(DoubleType()))
        .withColumn("annual_revenue_billions", F.col("annual_revenue_billions").cast(DoubleType()))
        .withColumn("founded_year", F.col("founded_year").cast(IntegerType()))
        .withColumn("employee_count", F.col("employee_count").cast(IntegerType()))
    )
    print("  [OK] market_cap, revenue -> DOUBLE; founded_year, employees -> INT")

    # Transform Stocks
    print("[DEBUG] Transforming: Stocks")
    transformed["stocks"] = (
        data["stocks"]
        .withColumn("current_price", F.col("current_price").cast(DoubleType()))
        .withColumn("previous_close", F.col("previous_close").cast(DoubleType()))
        .withColumn("opening_price", F.col("opening_price").cast(DoubleType()))
        .withColumn("day_high", F.col("day_high").cast(DoubleType()))
        .withColumn("day_low", F.col("day_low").cast(DoubleType()))
        .withColumn("volume", F.col("volume").cast(IntegerType()))
        .withColumn("market_cap_billions", F.col("market_cap_billions").cast(DoubleType()))
        .withColumn("pe_ratio", F.col("pe_ratio").cast(DoubleType()))
        .withColumn("dividend_yield", F.col("dividend_yield").cast(DoubleType()))
        .withColumn("fifty_two_week_high", F.col("fifty_two_week_high").cast(DoubleType()))
        .withColumn("fifty_two_week_low", F.col("fifty_two_week_low").cast(DoubleType()))
    )
    print("  [OK] prices, ratios -> DOUBLE; volume -> INT")

    # Transform Positions
    print("[DEBUG] Transforming: Positions")
    transformed["positions"] = (
        data["positions"]
        .withColumnRenamed("holding_id", "position_id")
        .withColumn("shares", F.col("shares").cast(IntegerType()))
        .withColumn("purchase_price", F.col("purchase_price").cast(DoubleType()))
        .withColumn("current_value", F.col("current_value").cast(DoubleType()))
        .withColumn("percentage_of_portfolio", F.col("percentage_of_portfolio").cast(DoubleType()))
        .withColumn("purchase_date", F.to_date(F.col("purchase_date")))
    )
    print("  [OK] holding_id -> position_id; shares -> INT; values -> DOUBLE")

    # Transform Transactions
    print("[DEBUG] Transforming: Transactions")
    transformed["transactions"] = (
        data["transactions"]
        .withColumn("amount", F.col("amount").cast(DoubleType()))
        .withColumn("transaction_date", F.to_date(F.col("transaction_date")))
    )
    print("  [OK] amount -> DOUBLE; transaction_date -> DATE")

    print("")
    print("=" * 70)
    print("[OK] ALL DATA TRANSFORMATIONS COMPLETE!")
    print("=" * 70)

    return transformed


# =============================================================================
# SCHEMA SETUP
# =============================================================================

def create_constraints(config: dict):
    """Create indexes and constraints in Neo4j."""
    from neo4j import GraphDatabase

    print("=" * 70)
    print("SCHEMA SETUP - Creating indexes and constraints in Neo4j")
    print("=" * 70)
    print("")

    constraints = [
        ("customer_id_unique", "Customer", "customer_id"),
        ("bank_id_unique", "Bank", "bank_id"),
        ("account_id_unique", "Account", "account_id"),
        ("company_id_unique", "Company", "company_id"),
        ("stock_id_unique", "Stock", "stock_id"),
        ("position_id_unique", "Position", "position_id"),
        ("transaction_id_unique", "Transaction", "transaction_id"),
    ]

    # Use neo4j Python driver for DDL operations
    driver = GraphDatabase.driver(
        config["neo4j_url"],
        auth=(config["neo4j_user"], config["neo4j_pass"])
    )

    success_count = 0
    with driver.session(database=config["neo4j_database"]) as session:
        for constraint_name, label, property_name in constraints:
            query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.{property_name} IS UNIQUE
            """
            print(f"[DEBUG] Creating: {constraint_name}")

            try:
                start_time = time.time()
                session.run(query)
                elapsed = time.time() - start_time
                print(f"  [OK] Created/verified in {elapsed:.2f}s")
                success_count += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  [SKIP] Already exists")
                    success_count += 1
                else:
                    print(f"  [FAIL] {type(e).__name__}: {str(e)[:100]}")

    driver.close()

    print("")
    print(f"[OK] {success_count}/{len(constraints)} constraints ready!")
    print("=" * 70)


# =============================================================================
# NODE CREATION
# =============================================================================

def write_all_nodes(config: dict, data: dict) -> dict:
    """Write all nodes to Neo4j."""
    print("=" * 70)
    print("NODE CREATION - Writing nodes to Neo4j")
    print("=" * 70)
    print("")

    results = {}
    total_start = time.time()

    # Customer nodes
    print("[1/7] CUSTOMER NODES")
    print("-" * 40)
    results["Customer"] = write_nodes(config, data["customers"], "Customer", "customer_id")
    print("")

    # Bank nodes
    print("[2/7] BANK NODES")
    print("-" * 40)
    results["Bank"] = write_nodes(config, data["banks"], "Bank", "bank_id")
    print("")

    # Account nodes
    print("[3/7] ACCOUNT NODES")
    print("-" * 40)
    account_props = data["accounts"].select(
        "account_id", "account_number", "account_type",
        "balance", "currency", "opened_date", "status", "interest_rate"
    )
    results["Account"] = write_nodes(config, account_props, "Account", "account_id")
    print("")

    # Company nodes
    print("[4/7] COMPANY NODES")
    print("-" * 40)
    results["Company"] = write_nodes(config, data["companies"], "Company", "company_id")
    print("")

    # Stock nodes
    print("[5/7] STOCK NODES")
    print("-" * 40)
    stock_props = data["stocks"].select(
        "stock_id", "ticker", "current_price", "previous_close", "opening_price",
        "day_high", "day_low", "volume", "market_cap_billions", "pe_ratio",
        "dividend_yield", "fifty_two_week_high", "fifty_two_week_low", "exchange"
    )
    results["Stock"] = write_nodes(config, stock_props, "Stock", "stock_id")
    print("")

    # Position nodes
    print("[6/7] POSITION NODES")
    print("-" * 40)
    position_props = data["positions"].select(
        "position_id", "shares", "purchase_price", "purchase_date",
        "current_value", "percentage_of_portfolio"
    )
    results["Position"] = write_nodes(config, position_props, "Position", "position_id")
    print("")

    # Transaction nodes
    print("[7/7] TRANSACTION NODES")
    print("-" * 40)
    transaction_props = data["transactions"].select(
        "transaction_id", "amount", "currency", "transaction_date",
        "transaction_time", "type", "status", "description"
    )
    results["Transaction"] = write_nodes(config, transaction_props, "Transaction", "transaction_id")

    total_elapsed = time.time() - total_start

    print("")
    print("=" * 70)
    print("NODE CREATION SUMMARY")
    print("=" * 70)
    print("")
    print(f"{'Label':<15} {'Count':>10} {'Time':>10} {'Status':>10}")
    print("-" * 50)
    for label, result in results.items():
        print(f"{label:<15} {result['count']:>10} {result['elapsed']:>9.2f}s {'[OK]':>10}")
    print("-" * 50)
    total_nodes = sum(r['count'] for r in results.values())
    print(f"{'TOTAL':<15} {total_nodes:>10} {total_elapsed:>9.2f}s")
    print("")
    print("[OK] ALL NODES WRITTEN SUCCESSFULLY!")
    print("=" * 70)

    return results


# =============================================================================
# RELATIONSHIP CREATION
# =============================================================================

def write_all_relationships(config: dict, data: dict) -> dict:
    """Write all relationships to Neo4j."""
    print("=" * 70)
    print("RELATIONSHIP CREATION - Writing relationships to Neo4j")
    print("=" * 70)
    print("")

    results = {}
    total_start = time.time()

    # HAS_ACCOUNT: Customer -> Account
    print("[1/7] HAS_ACCOUNT RELATIONSHIPS")
    print("-" * 40)
    has_account_df = data["accounts"].select("customer_id", "account_id")
    results["HAS_ACCOUNT"] = write_relationship(
        config, has_account_df, "HAS_ACCOUNT",
        "Customer", "customer_id", "Account", "account_id"
    )
    print("")

    # AT_BANK: Account -> Bank
    print("[2/7] AT_BANK RELATIONSHIPS")
    print("-" * 40)
    at_bank_df = data["accounts"].select("account_id", "bank_id")
    results["AT_BANK"] = write_relationship(
        config, at_bank_df, "AT_BANK",
        "Account", "account_id", "Bank", "bank_id"
    )
    print("")

    # OF_COMPANY: Stock -> Company
    print("[3/7] OF_COMPANY RELATIONSHIPS")
    print("-" * 40)
    of_company_df = data["stocks"].select("stock_id", "company_id")
    results["OF_COMPANY"] = write_relationship(
        config, of_company_df, "OF_COMPANY",
        "Stock", "stock_id", "Company", "company_id"
    )
    print("")

    # PERFORMS: Account -> Transaction
    print("[4/7] PERFORMS RELATIONSHIPS")
    print("-" * 40)
    performs_df = data["transactions"].select(
        F.col("from_account_id").alias("account_id"),
        "transaction_id"
    )
    results["PERFORMS"] = write_relationship(
        config, performs_df, "PERFORMS",
        "Account", "account_id", "Transaction", "transaction_id"
    )
    print("")

    # BENEFITS_TO: Transaction -> Account
    print("[5/7] BENEFITS_TO RELATIONSHIPS")
    print("-" * 40)
    benefits_df = data["transactions"].select(
        "transaction_id",
        F.col("to_account_id").alias("account_id")
    )
    results["BENEFITS_TO"] = write_relationship(
        config, benefits_df, "BENEFITS_TO",
        "Transaction", "transaction_id", "Account", "account_id"
    )
    print("")

    # HAS_POSITION: Account -> Position
    print("[6/7] HAS_POSITION RELATIONSHIPS")
    print("-" * 40)
    has_position_df = data["positions"].select("account_id", "position_id")
    results["HAS_POSITION"] = write_relationship(
        config, has_position_df, "HAS_POSITION",
        "Account", "account_id", "Position", "position_id"
    )
    print("")

    # OF_SECURITY: Position -> Stock
    print("[7/7] OF_SECURITY RELATIONSHIPS")
    print("-" * 40)
    of_security_df = data["positions"].select("position_id", "stock_id")
    results["OF_SECURITY"] = write_relationship(
        config, of_security_df, "OF_SECURITY",
        "Position", "position_id", "Stock", "stock_id"
    )

    total_elapsed = time.time() - total_start

    print("")
    print("=" * 70)
    print("RELATIONSHIP CREATION SUMMARY")
    print("=" * 70)
    print("")
    print(f"{'Type':<20} {'Count':>10} {'Time':>10} {'Status':>10}")
    print("-" * 55)
    for rel_type, result in results.items():
        print(f"{rel_type:<20} {result['count']:>10} {result['elapsed']:>9.2f}s {'[OK]':>10}")
    print("-" * 55)
    total_rels = sum(r['count'] for r in results.values())
    print(f"{'TOTAL':<20} {total_rels:>10} {total_elapsed:>9.2f}s")
    print("")
    print("[OK] ALL RELATIONSHIPS WRITTEN SUCCESSFULLY!")
    print("=" * 70)

    return results


# =============================================================================
# VALIDATION
# =============================================================================

def validate_import(config: dict) -> bool:
    """Validate the import by checking node and relationship counts."""
    print("=" * 70)
    print("VALIDATION - Checking node and relationship counts")
    print("=" * 70)
    print("")

    expected_nodes = {
        "Customer": 102,
        "Bank": 102,
        "Account": 123,
        "Company": 102,
        "Stock": 102,
        "Position": 110,
        "Transaction": 123
    }

    expected_rels = {
        "HAS_ACCOUNT": 123,
        "AT_BANK": 123,
        "OF_COMPANY": 102,
        "PERFORMS": 123,
        "BENEFITS_TO": 123,
        "HAS_POSITION": 110,
        "OF_SECURITY": 110
    }

    all_valid = True

    # Validate nodes
    print("[DEBUG] Validating node counts...")
    node_query = """
    MATCH (n)
    RETURN labels(n)[0] AS label, count(n) AS count
    ORDER BY label
    """

    try:
        node_counts = run_cypher(config, node_query).collect()
        print("")
        print(f"{'Label':<15} {'Expected':>10} {'Actual':>10} {'Status':>10}")
        print("-" * 50)

        for row in node_counts:
            label = row["label"]
            actual = row["count"]
            expected = expected_nodes.get(label, "N/A")
            if expected == "N/A":
                status = "[?]"
            elif actual == expected:
                status = "[OK]"
            else:
                status = "[MISMATCH]"
                all_valid = False
            print(f"{label:<15} {expected:>10} {actual:>10} {status:>10}")
        print("-" * 50)
    except Exception as e:
        print(f"  [FAIL] Node validation failed: {e}")
        all_valid = False

    print("")

    # Validate relationships
    print("[DEBUG] Validating relationship counts...")
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) AS relationship_type, count(r) AS count
    ORDER BY relationship_type
    """

    try:
        rel_counts = run_cypher(config, rel_query).collect()
        print("")
        print(f"{'Relationship':<20} {'Expected':>10} {'Actual':>10} {'Status':>10}")
        print("-" * 55)

        for row in rel_counts:
            rel_type = row["relationship_type"]
            actual = row["count"]
            expected = expected_rels.get(rel_type, "N/A")
            if expected == "N/A":
                status = "[?]"
            elif actual == expected:
                status = "[OK]"
            else:
                status = "[MISMATCH]"
                all_valid = False
            print(f"{rel_type:<20} {expected:>10} {actual:>10} {status:>10}")
        print("-" * 55)
    except Exception as e:
        print(f"  [FAIL] Relationship validation failed: {e}")
        all_valid = False

    print("")
    if all_valid:
        print("[OK] VALIDATION PASSED!")
    else:
        print("[WARNING] VALIDATION FAILED - check mismatched counts")
    print("=" * 70)

    return all_valid


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for the import script."""
    print("")
    print("=" * 70)
    print("FINANCIAL DEMO DATA IMPORT TO NEO4J")
    print("=" * 70)
    print("")

    total_start = time.time()

    # Step 1: Load configuration
    config = load_config()
    print("")

    # Step 2: Verify prerequisites
    if not verify_csv_files(config):
        print("[ERROR] CSV file verification failed!")
        return False
    print("")

    if not verify_neo4j_connection(config):
        print("[ERROR] Neo4j connection failed!")
        return False
    print("")

    # Step 3: Clear existing database
    if not clear_database(config):
        print("[ERROR] Database cleanup failed!")
        return False
    print("")

    # Step 4: Load and transform data
    raw_data = load_csv_files(config)
    print("")

    data = transform_data(raw_data)
    print("")

    # Step 5: Create constraints
    create_constraints(config)
    print("")

    # Step 6: Write nodes
    write_all_nodes(config, data)
    print("")

    # Step 7: Write relationships
    write_all_relationships(config, data)
    print("")

    # Step 8: Validate
    success = validate_import(config)
    print("")

    total_elapsed = time.time() - total_start

    print("=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"Total time: {total_elapsed:.2f}s")
    print(f"Status: {'SUCCESS' if success else 'COMPLETED WITH WARNINGS'}")
    print("=" * 70)

    return success


if __name__ == "__main__":
    main()
