"""
Neo4j to Spark Schema Definitions - Version 2 (Specific Schemas Only)

This module provides type-safe Spark schemas for Neo4j node types and relationship
types. This version implements the Specific Relationship Schemas approach (Approach 2)
for maximum type safety and semantic clarity.

Platform-agnostic: Works with any Spark platform (Databricks, AWS EMR, Azure Synapse,
Google Dataproc, etc.). For Databricks-specific table names, see databricks_constants.py.

Design Philosophy:
    - Specific relationship schemas with business-meaningful column names
    - Type-safe schemas for compile-time validation
    - Self-documenting code with semantic field names
    - Optimized for ETL pipelines and business logic

Schemas are derived from the Neo4j importer model:
    fintech_demo/neo4j_importer_model_financial_demo.json

Usage:
    from neo4j_schemas import NODE_SCHEMAS, get_node_schema
    from neo4j_schemas import RELATIONSHIP_SCHEMAS, get_relationship_schema

    # Get node schema
    customer_schema = get_node_schema("Customer")
    df = spark.read.schema(customer_schema).format("parquet").load("path/to/customers")

    # Get relationship schema (includes rel_element_id, rel_type, node IDs)
    has_account_schema = get_relationship_schema("HAS_ACCOUNT")
    edges = spark.read.schema(has_account_schema).format("parquet").load("path/to/has_account")
    # Columns: customerId, accountId, rel_element_id, rel_type,
    #          src_neo4j_id, dst_neo4j_id, ingestion_timestamp

Version: 2.0.0 (Specific Schemas Only)
"""

from typing import Dict, List, Optional, Tuple

try:
    from pyspark.sql.types import (
        StructType,
        StructField,
        StringType,
        IntegerType,
        LongType,
        FloatType,
        DoubleType,
        DateType,
        TimestampType,
        ArrayType,
        BooleanType,
    )
except ImportError:
    raise ImportError(
        "PySpark is required. Install with: pip install pyspark"
    )

__version__ = "2.0.0"
__all__ = [
    # Node schemas
    "NODE_SCHEMAS",
    "BASE_NODE_SCHEMAS",
    # Relationship schemas
    "RELATIONSHIP_SCHEMAS",
    "RELATIONSHIP_METADATA",
    # Node helper functions
    "get_node_schema",
    "list_node_schemas",
    "print_node_schema",
    "validate_node_schema",
    # Relationship helper functions
    "get_relationship_schema",
    "list_relationship_schemas",
    "print_relationship_schema",
    "get_relationship_metadata",
    "validate_relationship_schema",
    # Documentation functions
    "print_graph_summary",
    "print_module_info",
    # Utility functions
    "get_version",
    # Neo4j Data Conversion Utilities (optional, requires neo4j driver)
    "convert_neo4j_value",
    "serialize_properties",
]


def get_version() -> str:
    """Return module version."""
    return __version__


def add_metadata_fields(base_schema: StructType) -> StructType:
    """
    Add standard metadata fields to a node schema.

    Metadata fields:
        - neo4j_id: Neo4j element ID (string, e.g., "4:abc123:1")
        - neo4j_labels: Node labels array (array<string>)
        - ingestion_timestamp: Data extraction timestamp (timestamp)

    Args:
        base_schema: Base StructType with entity-specific fields.

    Returns:
        StructType with metadata fields appended.
    """
    metadata_fields = [
        StructField("neo4j_id", StringType(), nullable=True),
        StructField("neo4j_labels", ArrayType(StringType()), nullable=True),
        StructField("ingestion_timestamp", TimestampType(), nullable=True),
    ]

    return StructType(base_schema.fields + metadata_fields)


def add_relationship_metadata_fields(base_schema: StructType) -> StructType:
    """
    Add standard metadata fields to a relationship schema.

    Metadata fields:
        - rel_element_id: Relationship element ID (string, e.g., "5:abc123:2")
        - rel_type: Relationship type name (string, e.g., "HAS_ACCOUNT")
        - src_neo4j_id: Source node element ID (string)
        - dst_neo4j_id: Destination node element ID (string)
        - ingestion_timestamp: Data extraction timestamp (timestamp)

    Args:
        base_schema: Base StructType with relationship-specific fields.

    Returns:
        StructType with metadata fields appended.
    """
    metadata_fields = [
        StructField("rel_element_id", StringType(), nullable=False),
        StructField("rel_type", StringType(), nullable=False),
        StructField("src_neo4j_id", StringType(), nullable=True),
        StructField("dst_neo4j_id", StringType(), nullable=True),
        StructField("ingestion_timestamp", TimestampType(), nullable=True),
    ]

    return StructType(base_schema.fields + metadata_fields)


# ============================================================================
# NODE SCHEMAS
# ============================================================================

# Customer Schema
# Based on: neo4j_importer_model_financial_demo.json -> Customer node (nl:1)
CUSTOMER_BASE_SCHEMA = StructType([
    # Key property
    StructField("customerId", StringType(), nullable=False),
    # Personal information
    StructField("firstName", StringType(), nullable=False),
    StructField("lastName", StringType(), nullable=False),
    StructField("dateOfBirth", DateType(), nullable=True),
    # Contact information
    StructField("email", StringType(), nullable=True),
    StructField("phone", StringType(), nullable=True),
    StructField("address", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("state", StringType(), nullable=True),
    StructField("zipCode", StringType(), nullable=True),
    # Account information
    StructField("registrationDate", DateType(), nullable=True),
    StructField("riskProfile", StringType(), nullable=True),
    StructField("employmentStatus", StringType(), nullable=True),
    # Financial information
    StructField("annualIncome", IntegerType(), nullable=True),
    StructField("creditScore", IntegerType(), nullable=True),
])

# Bank Schema
# Based on: neo4j_importer_model_financial_demo.json -> Bank node (nl:2)
BANK_BASE_SCHEMA = StructType([
    # Key property
    StructField("bankId", StringType(), nullable=False),
    # Institution information
    StructField("name", StringType(), nullable=True),
    StructField("headquarters", StringType(), nullable=True),
    StructField("bankType", StringType(), nullable=True),
    # Financial metrics
    StructField("totalAssetsBillions", FloatType(), nullable=True),
    StructField("establishedYear", IntegerType(), nullable=True),
    # Banking identifiers
    StructField("routingNumber", StringType(), nullable=True),
    StructField("swiftCode", StringType(), nullable=True),
])

# Account Schema
# Based on: neo4j_importer_model_financial_demo.json -> Account node (nl:3)
ACCOUNT_BASE_SCHEMA = StructType([
    # Key property
    StructField("accountId", StringType(), nullable=False),
    # Account details
    StructField("accountNumber", StringType(), nullable=True),
    StructField("accountType", StringType(), nullable=True),
    StructField("status", StringType(), nullable=True),
    # Financial information
    StructField("balance", FloatType(), nullable=False),
    StructField("currency", StringType(), nullable=True),
    StructField("interestRate", FloatType(), nullable=True),
    # Dates
    StructField("openedDate", DateType(), nullable=True),
])

# Company Schema
# Based on: neo4j_importer_model_financial_demo.json -> Company node (nl:4)
COMPANY_BASE_SCHEMA = StructType([
    # Key property
    StructField("companyId", StringType(), nullable=False),
    # Company information
    StructField("name", StringType(), nullable=True),
    StructField("tickerSymbol", StringType(), nullable=True),
    StructField("headquarters", StringType(), nullable=True),
    # Classification
    StructField("industry", StringType(), nullable=True),
    StructField("sector", StringType(), nullable=True),
    # Financial metrics
    StructField("marketCapBillions", FloatType(), nullable=True),
    StructField("annualRevenueBillions", FloatType(), nullable=True),
    # Company details
    StructField("foundedYear", IntegerType(), nullable=True),
    StructField("ceo", StringType(), nullable=True),
    StructField("employeeCount", IntegerType(), nullable=True),
])

# Stock Schema
# Based on: neo4j_importer_model_financial_demo.json -> Stock node (nl:5)
STOCK_BASE_SCHEMA = StructType([
    # Key property
    StructField("stockId", StringType(), nullable=False),
    # Stock identification
    StructField("ticker", StringType(), nullable=True),
    StructField("exchange", StringType(), nullable=True),
    # Current pricing
    StructField("currentPrice", FloatType(), nullable=True),
    StructField("previousClose", FloatType(), nullable=True),
    StructField("openingPrice", FloatType(), nullable=True),
    # Daily range
    StructField("dayHigh", FloatType(), nullable=True),
    StructField("dayLow", FloatType(), nullable=True),
    # Volume and market data
    StructField("volume", IntegerType(), nullable=True),
    StructField("marketCapBillions", FloatType(), nullable=True),
    # Metrics
    StructField("peRatio", FloatType(), nullable=True),
    StructField("dividendYield", FloatType(), nullable=True),
    # 52-week range
    StructField("fiftyTwoWeekHigh", FloatType(), nullable=True),
    StructField("fiftyTwoWeekLow", FloatType(), nullable=True),
])

# Transaction Schema
# Based on: neo4j_importer_model_financial_demo.json -> Transaction node (nl:6)
TRANSACTION_BASE_SCHEMA = StructType([
    # Key property
    StructField("transactionId", StringType(), nullable=False),
    # Transaction details
    StructField("amount", FloatType(), nullable=False),
    StructField("currency", StringType(), nullable=True),
    StructField("type", StringType(), nullable=True),
    StructField("status", StringType(), nullable=True),
    StructField("description", StringType(), nullable=True),
    # Temporal information
    StructField("transactionDate", DateType(), nullable=False),
    StructField("transactionTime", StringType(), nullable=True),
])

# Position Schema
# Based on: neo4j_importer_model_financial_demo.json -> Position node (nl:7)
#
# NOTE: CSV Field Mapping
# -----------------------
# The source CSV file (portfolio_holdings.csv) uses "holding_id" as the field name.
# This is mapped to "positionId" in the Neo4j schema for semantic clarity, as these
# nodes represent investment positions held by accounts.
#
POSITION_BASE_SCHEMA = StructType([
    # Key property
    StructField("positionId", StringType(), nullable=False),
    # Position details
    StructField("shares", FloatType(), nullable=True),
    StructField("purchasePrice", FloatType(), nullable=True),
    StructField("purchaseDate", DateType(), nullable=True),
    StructField("currentValue", FloatType(), nullable=True),
    StructField("percentageOfPortfolio", FloatType(), nullable=True),
])


# ============================================================================
# RELATIONSHIP (EDGE) SCHEMAS - SPECIFIC SCHEMAS ONLY
# ============================================================================

# HAS_ACCOUNT: (Customer)-[:HAS_ACCOUNT]->(Account)
# Source: accounts.csv (customer_id -> account_id)
HAS_ACCOUNT_BASE_SCHEMA = StructType([
    StructField("customerId", StringType(), nullable=False),
    StructField("accountId", StringType(), nullable=False),
])

# AT_BANK: (Account)-[:AT_BANK]->(Bank)
# Source: accounts.csv (account_id -> bank_id)
AT_BANK_BASE_SCHEMA = StructType([
    StructField("accountId", StringType(), nullable=False),
    StructField("bankId", StringType(), nullable=False),
])

# OF_COMPANY: (Stock)-[:OF_COMPANY]->(Company)
# Source: stocks.csv (stock_id -> company_id)
OF_COMPANY_BASE_SCHEMA = StructType([
    StructField("stockId", StringType(), nullable=False),
    StructField("companyId", StringType(), nullable=False),
])

# PERFORMS: (Account)-[:PERFORMS]->(Transaction)
# Source: transactions.csv (from_account_id -> transaction_id)
PERFORMS_BASE_SCHEMA = StructType([
    StructField("senderAccountId", StringType(), nullable=False),
    StructField("transactionId", StringType(), nullable=False),
])

# BENEFITS_TO: (Transaction)-[:BENEFITS_TO]->(Account)
# Source: transactions.csv (transaction_id -> to_account_id)
BENEFITS_TO_BASE_SCHEMA = StructType([
    StructField("transactionId", StringType(), nullable=False),
    StructField("receiverAccountId", StringType(), nullable=False),
])

# HAS_POSITION: (Account)-[:HAS_POSITION]->(Position)
# Source: portfolio_holdings.csv (account_id -> holding_id)
HAS_POSITION_BASE_SCHEMA = StructType([
    StructField("accountId", StringType(), nullable=False),
    StructField("positionId", StringType(), nullable=False),
])

# OF_SECURITY: (Position)-[:OF_SECURITY]->(Stock)
# Source: portfolio_holdings.csv (holding_id -> stock_id)
OF_SECURITY_BASE_SCHEMA = StructType([
    StructField("positionId", StringType(), nullable=False),
    StructField("stockId", StringType(), nullable=False),
])


# ============================================================================
# SCHEMA REGISTRY
# ============================================================================

# Dictionary mapping node labels to base schemas (without metadata)
BASE_NODE_SCHEMAS: Dict[str, StructType] = {
    "Customer": CUSTOMER_BASE_SCHEMA,
    "Bank": BANK_BASE_SCHEMA,
    "Account": ACCOUNT_BASE_SCHEMA,
    "Company": COMPANY_BASE_SCHEMA,
    "Stock": STOCK_BASE_SCHEMA,
    "Transaction": TRANSACTION_BASE_SCHEMA,
    "Position": POSITION_BASE_SCHEMA,
}

# Dictionary mapping node labels to schemas (with metadata)
NODE_SCHEMAS: Dict[str, StructType] = {
    label: add_metadata_fields(schema)
    for label, schema in BASE_NODE_SCHEMAS.items()
}

# Dictionary mapping relationship types to base schemas (without metadata)
BASE_RELATIONSHIP_SCHEMAS: Dict[str, StructType] = {
    "HAS_ACCOUNT": HAS_ACCOUNT_BASE_SCHEMA,
    "AT_BANK": AT_BANK_BASE_SCHEMA,
    "OF_COMPANY": OF_COMPANY_BASE_SCHEMA,
    "PERFORMS": PERFORMS_BASE_SCHEMA,
    "BENEFITS_TO": BENEFITS_TO_BASE_SCHEMA,
    "HAS_POSITION": HAS_POSITION_BASE_SCHEMA,
    "OF_SECURITY": OF_SECURITY_BASE_SCHEMA,
}

# Dictionary mapping relationship types to schemas (with metadata)
RELATIONSHIP_SCHEMAS: Dict[str, StructType] = {
    rel_type: add_relationship_metadata_fields(schema)
    for rel_type, schema in BASE_RELATIONSHIP_SCHEMAS.items()
}

# Relationship metadata describing source and destination node types
# This provides semantic information about each relationship
RELATIONSHIP_METADATA: Dict[str, Dict[str, str]] = {
    "HAS_ACCOUNT": {
        "source_label": "Customer",
        "destination_label": "Account",
        "source_key": "customerId",
        "destination_key": "accountId",
        "cardinality": "1:N",
        "description": "Customer has a bank account",
        "source_csv_field": "customer_id",
        "destination_csv_field": "account_id",
        "source_table": "accounts.csv",
    },
    "AT_BANK": {
        "source_label": "Account",
        "destination_label": "Bank",
        "source_key": "accountId",
        "destination_key": "bankId",
        "cardinality": "N:1",
        "description": "Account is held at a bank",
        "source_csv_field": "account_id",
        "destination_csv_field": "bank_id",
        "source_table": "accounts.csv",
    },
    "OF_COMPANY": {
        "source_label": "Stock",
        "destination_label": "Company",
        "source_key": "stockId",
        "destination_key": "companyId",
        "cardinality": "N:1",
        "description": "Stock is issued by a company",
        "source_csv_field": "stock_id",
        "destination_csv_field": "company_id",
        "source_table": "stocks.csv",
    },
    "PERFORMS": {
        "source_label": "Account",
        "destination_label": "Transaction",
        "source_key": "accountId",
        "destination_key": "transactionId",
        "cardinality": "1:N",
        "description": "Account performs a transaction (sender/debtor)",
        "source_csv_field": "from_account_id",
        "destination_csv_field": "transaction_id",
        "source_table": "transactions.csv",
    },
    "BENEFITS_TO": {
        "source_label": "Transaction",
        "destination_label": "Account",
        "source_key": "transactionId",
        "destination_key": "accountId",
        "cardinality": "1:1",
        "description": "Transaction benefits an account (receiver/creditor)",
        "source_csv_field": "transaction_id",
        "destination_csv_field": "to_account_id",
        "source_table": "transactions.csv",
    },
    "HAS_POSITION": {
        "source_label": "Account",
        "destination_label": "Position",
        "source_key": "accountId",
        "destination_key": "positionId",
        "cardinality": "1:N",
        "description": "Account holds an investment position",
        "source_csv_field": "account_id",
        "destination_csv_field": "holding_id",  # Maps to positionId in schema
        "source_table": "portfolio_holdings.csv",
    },
    "OF_SECURITY": {
        "source_label": "Position",
        "destination_label": "Stock",
        "source_key": "positionId",
        "destination_key": "stockId",
        "cardinality": "N:1",
        "description": "Position represents shares of a stock",
        "source_csv_field": "holding_id",  # Maps to positionId in schema
        "destination_csv_field": "stock_id",
        "source_table": "portfolio_holdings.csv",
    },
}


# ============================================================================
# NODE HELPER FUNCTIONS
# ============================================================================

def get_node_schema(node_label: str, include_metadata: bool = True) -> StructType:
    """
    Get Spark schema for a node label.

    Args:
        node_label: Neo4j node label (e.g., "Customer", "Bank").
        include_metadata: Include neo4j_id, neo4j_labels, ingestion_timestamp (default: True).

    Returns:
        StructType schema for the node type.

    Raises:
        ValueError: If node_label is not defined.

    Example:
        >>> schema = get_node_schema("Customer")
        >>> df = spark.read.schema(schema).table("neo4j_customer")
    """
    schema_dict = NODE_SCHEMAS if include_metadata else BASE_NODE_SCHEMAS

    if node_label not in schema_dict:
        available = ", ".join(sorted(schema_dict.keys()))
        raise ValueError(
            f"No schema defined for node label '{node_label}'. "
            f"Available schemas: {available}"
        )

    return schema_dict[node_label]


def list_node_schemas() -> List[str]:
    """
    List all available node schemas.

    Returns:
        Sorted list of node label strings.

    Example:
        >>> schemas = list_node_schemas()
        >>> print(schemas)
        ['Account', 'Bank', 'Company', 'Customer', 'Position', 'Stock', 'Transaction']
    """
    return sorted(NODE_SCHEMAS.keys())


def print_node_schema(node_label: str, include_metadata: bool = True) -> None:
    """
    Pretty-print schema for a node label.

    Args:
        node_label: Neo4j node label.
        include_metadata: Include metadata fields in output (default: True).

    Raises:
        ValueError: If node_label is not defined.

    Example:
        >>> print_node_schema("Customer")
        ============================================================
        Node Schema: Customer
        ============================================================
        root
         |-- customerId: string (nullable = false)
         |-- firstName: string (nullable = false)
         ...
    """
    schema = get_node_schema(node_label, include_metadata=include_metadata)
    print(f"\n{'=' * 60}")
    print(f"Node Schema: {node_label}")
    if include_metadata:
        print("(includes metadata fields)")
    print(f"{'=' * 60}")
    print(schema.treeString())
    print(f"{'=' * 60}\n")


def validate_node_schema(
    df,
    node_label: str,
    strict: bool = False
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate DataFrame schema matches expected node schema.

    Args:
        df: Spark DataFrame.
        node_label: Expected node label.
        strict: If True, extra fields cause validation failure (default: False).

    Returns:
        Tuple of (is_valid: bool, missing_fields: list, extra_fields: list).

    Raises:
        ValueError: If node_label is not defined.

    Example:
        >>> is_valid, missing, extra = validate_node_schema(df, "Customer")
        >>> if not is_valid:
        ...     print(f"Schema validation failed!")
        ...     print(f"Missing fields: {missing}")
        ...     print(f"Extra fields: {extra}")
    """
    expected_schema = get_node_schema(node_label, include_metadata=False)
    expected_fields = {f.name for f in expected_schema.fields}

    # Exclude metadata fields from actual fields
    metadata_fields = {"neo4j_id", "neo4j_labels", "ingestion_timestamp"}
    actual_fields = {
        f.name for f in df.schema.fields
        if f.name not in metadata_fields
    }

    missing_fields = sorted(expected_fields - actual_fields)
    extra_fields = sorted(actual_fields - expected_fields)

    if strict:
        is_valid = len(missing_fields) == 0 and len(extra_fields) == 0
    else:
        is_valid = len(missing_fields) == 0

    return is_valid, missing_fields, extra_fields


# ============================================================================
# RELATIONSHIP HELPER FUNCTIONS
# ============================================================================

def get_relationship_schema(
    relationship_type: str,
    include_metadata: bool = True
) -> StructType:
    """
    Get Spark schema for a relationship type.

    This function returns the specific relationship schema with business-meaningful
    column names (e.g., customerId, accountId) for type-safe ETL pipelines.

    Args:
        relationship_type: Relationship type (e.g., "HAS_ACCOUNT", "AT_BANK").
        include_metadata: Include rel_element_id, rel_type, src_neo4j_id, dst_neo4j_id, ingestion_timestamp (default: True).

    Returns:
        StructType schema for the relationship.

    Raises:
        ValueError: If relationship_type is not defined.

    Example:
        >>> schema = get_relationship_schema("HAS_ACCOUNT")
        >>> df = spark.read.schema(schema).table("neo4j_has_account")
        >>> # DataFrame has columns: customerId, accountId, rel_element_id,
        >>> # rel_type, src_neo4j_id, dst_neo4j_id, ingestion_timestamp
    """
    schema_dict = RELATIONSHIP_SCHEMAS if include_metadata else BASE_RELATIONSHIP_SCHEMAS

    if relationship_type not in schema_dict:
        available = ", ".join(sorted(schema_dict.keys()))
        raise ValueError(
            f"No schema defined for relationship type '{relationship_type}'. "
            f"Available relationships: {available}"
        )

    return schema_dict[relationship_type]


def list_relationship_schemas() -> List[str]:
    """
    List all available relationship types.

    Returns:
        Sorted list of relationship type strings.

    Example:
        >>> relationships = list_relationship_schemas()
        >>> print(relationships)
        ['AT_BANK', 'BENEFITS_TO', 'HAS_ACCOUNT', 'HAS_POSITION', 'OF_COMPANY', 'OF_SECURITY', 'PERFORMS']
    """
    return sorted(RELATIONSHIP_SCHEMAS.keys())


def print_relationship_schema(
    relationship_type: str,
    include_metadata: bool = True
) -> None:
    """
    Pretty-print schema for a relationship type.

    Args:
        relationship_type: Relationship type name.
        include_metadata: Include metadata fields in output (default: True).

    Raises:
        ValueError: If relationship_type is not defined.

    Example:
        >>> print_relationship_schema("HAS_ACCOUNT")
        ============================================================
        Relationship Schema: HAS_ACCOUNT
        Description: Customer has a bank account
        Cardinality: 1:N
        Source: Customer (customerId) -> Destination: Account (accountId)
        ============================================================
        root
         |-- customerId: string (nullable = false)
         |-- accountId: string (nullable = false)
         |-- rel_element_id: string (nullable = false)
         |-- rel_type: string (nullable = false)
         |-- src_neo4j_id: string (nullable = true)
         |-- dst_neo4j_id: string (nullable = true)
         |-- ingestion_timestamp: timestamp (nullable = true)
        ============================================================
    """
    schema = get_relationship_schema(relationship_type, include_metadata=include_metadata)
    metadata = get_relationship_metadata(relationship_type)

    print(f"\n{'=' * 60}")
    print(f"Relationship Schema: {relationship_type}")
    print(f"Description: {metadata['description']}")
    print(f"Cardinality: {metadata['cardinality']}")
    print(
        f"Source: {metadata['source_label']} ({metadata['source_key']}) -> "
        f"Destination: {metadata['destination_label']} ({metadata['destination_key']})"
    )
    if "properties" in metadata and metadata["properties"]:
        print(f"Properties: {', '.join(metadata['properties'])}")
    if include_metadata:
        print("(includes metadata fields)")
    print(f"{'=' * 60}")
    print(schema.treeString())
    print(f"{'=' * 60}\n")


def get_relationship_metadata(relationship_type: str) -> Dict[str, str]:
    """
    Get metadata for a relationship type.

    Args:
        relationship_type: Relationship type name.

    Returns:
        Dictionary with relationship metadata including:
        - source_label: Source node label
        - destination_label: Destination node label
        - source_key: Source node key property
        - destination_key: Destination node key property
        - cardinality: Relationship cardinality (e.g., "1:N", "N:1")
        - description: Human-readable description
        - source_csv_field: CSV field name for source
        - destination_csv_field: CSV field name for destination
        - source_table: Source CSV file name

    Raises:
        ValueError: If relationship_type is not defined.

    Example:
        >>> metadata = get_relationship_metadata("HAS_ACCOUNT")
        >>> print(f"{metadata['source_label']} -> {metadata['destination_label']}")
        Customer -> Account
        >>> print(f"Cardinality: {metadata['cardinality']}")
        Cardinality: 1:N
    """
    if relationship_type not in RELATIONSHIP_METADATA:
        available = ", ".join(sorted(RELATIONSHIP_METADATA.keys()))
        raise ValueError(
            f"No metadata defined for relationship type '{relationship_type}'. "
            f"Available relationships: {available}"
        )

    return RELATIONSHIP_METADATA[relationship_type]


def validate_relationship_schema(
    df,
    relationship_type: str,
    strict: bool = False
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate DataFrame schema matches expected relationship schema.

    Args:
        df: Spark DataFrame.
        relationship_type: Expected relationship type.
        strict: If True, extra fields cause validation failure (default: False).

    Returns:
        Tuple of (is_valid: bool, missing_fields: list, extra_fields: list).

    Raises:
        ValueError: If relationship_type is not defined.

    Example:
        >>> is_valid, missing, extra = validate_relationship_schema(df, "HAS_ACCOUNT")
        >>> if not is_valid:
        ...     print(f"Schema validation failed!")
        ...     print(f"Missing fields: {missing}")
        ...     print(f"Extra fields: {extra}")
    """
    expected_schema = get_relationship_schema(relationship_type, include_metadata=False)
    expected_fields = {f.name for f in expected_schema.fields}

    # Exclude metadata fields from actual fields
    metadata_fields = {"rel_element_id", "rel_type", "src_neo4j_id", "dst_neo4j_id", "ingestion_timestamp"}
    actual_fields = {
        f.name for f in df.schema.fields
        if f.name not in metadata_fields
    }

    missing_fields = sorted(expected_fields - actual_fields)
    extra_fields = sorted(actual_fields - expected_fields)

    if strict:
        is_valid = len(missing_fields) == 0 and len(extra_fields) == 0
    else:
        is_valid = len(missing_fields) == 0

    return is_valid, missing_fields, extra_fields


# ============================================================================
# DOCUMENTATION FUNCTIONS
# ============================================================================

def print_graph_summary() -> None:
    """
    Print comprehensive graph schema summary.

    This includes all node types, relationship types, and their connections,
    providing a complete overview of the financial graph model.

    Example:
        >>> print_graph_summary()
        ================================================================================
        Financial Graph Schema Summary (Specific Schemas)
        ================================================================================
        Version: 2.0.0

        Node Types (7):
        ---------------
          1. Account: 8 properties
          2. Bank: 8 properties
          3. Company: 11 properties
          4. Customer: 15 properties
          5. Position: 7 properties
          6. Stock: 14 properties
          7. Transaction: 8 properties

        Relationship Types (7):
        -----------------------
          1. AT_BANK [N:1]: Account -> Bank
             Schema: accountId, bankId
             Description: Account is held at a bank

          2. BENEFITS_TO [1:1]: Transaction -> Account
             Schema: transactionId, accountId
             Description: Transaction benefits an account (receiver/creditor)
        ...
    """
    print("=" * 80)
    print("Financial Graph Schema Summary (Specific Schemas)")
    print("=" * 80)
    print(f"Version: {__version__}\n")

    # Node types
    print(f"Node Types ({len(NODE_SCHEMAS)}):")
    print("-" * 15)
    for i, label in enumerate(sorted(NODE_SCHEMAS.keys()), 1):
        schema = BASE_NODE_SCHEMAS[label]
        prop_count = len(schema.fields)
        key_field = schema.fields[0].name  # First field is always the key
        print(f"  {i}. {label}: {prop_count} properties (key: {key_field})")

    print()

    # Relationship types with detailed information
    print(f"Relationship Types ({len(RELATIONSHIP_SCHEMAS)}):")
    print("-" * 23)
    for i, rel_type in enumerate(sorted(RELATIONSHIP_SCHEMAS.keys()), 1):
        metadata = RELATIONSHIP_METADATA[rel_type]
        schema = BASE_RELATIONSHIP_SCHEMAS[rel_type]
        field_names = ", ".join([f.name for f in schema.fields])

        print(f"  {i}. {rel_type} [{metadata['cardinality']}]: {metadata['source_label']} -> {metadata['destination_label']}")
        print(f"     Schema: {field_names}")
        print(f"     Description: {metadata['description']}")
        print()

    # Graph structure visualization
    print("Graph Structure:")
    print("-" * 16)
    for rel_type in sorted(RELATIONSHIP_SCHEMAS.keys()):
        metadata = RELATIONSHIP_METADATA[rel_type]
        print(
            f"({metadata['source_label']})-[:{rel_type}]->({metadata['destination_label']})"
        )

    print("=" * 80)


def print_module_info() -> None:
    """
    Print module information.

    Example:
        >>> print_module_info()
        ================================================================================
        Neo4j to Databricks Schema Module v2 (Specific Schemas Only)
        ================================================================================
        Version: 2.0.0
        Approach: Specific Relationship Schemas (Type-Safe)

        Node Types: 7
        Relationship Types: 7

        Available Node Schemas:
          Account, Bank, Company, Customer, Position, Stock, Transaction

        Available Relationship Schemas:
          AT_BANK, BENEFITS_TO, HAS_ACCOUNT, HAS_POSITION, OF_COMPANY, OF_SECURITY, PERFORMS

        Design Philosophy:
          - Business-meaningful column names (customerId, accountId, not src/dst)
          - Type-safe schemas for compile-time validation
          - Self-documenting code with semantic clarity
          - Optimized for ETL pipelines and business logic
        ================================================================================
    """
    print("=" * 80)
    print("Neo4j to Databricks Schema Module v2 (Specific Schemas Only)")
    print("=" * 80)
    print(f"Version: {__version__}")
    print("Approach: Specific Relationship Schemas (Type-Safe)")
    print()
    print(f"Node Types: {len(NODE_SCHEMAS)}")
    print(f"Relationship Types: {len(RELATIONSHIP_SCHEMAS)}")
    print()
    print("Available Node Schemas:")
    print(f"  {', '.join(list_node_schemas())}")
    print()
    print("Available Relationship Schemas:")
    print(f"  {', '.join(list_relationship_schemas())}")
    print()
    print("Design Philosophy:")
    print("  - Business-meaningful column names (customerId, accountId, not src/dst)")
    print("  - Type-safe schemas for compile-time validation")
    print("  - Self-documenting code with semantic clarity")
    print("  - Optimized for ETL pipelines and business logic")
    print("=" * 80)
