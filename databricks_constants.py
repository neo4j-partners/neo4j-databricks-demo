"""
Databricks-Specific Constants for Neo4j Graph Data

This module contains Unity Catalog table names and other Databricks-specific
configurations for the Neo4j to Databricks ETL pipeline.

These constants are separated from neo4j_schemas.py to keep the schema definitions
platform-agnostic and reusable across different Spark environments (AWS EMR, Azure
Synapse, Google Dataproc, etc.).

Usage:
    from databricks_constants import NODE_TABLE_NAMES, RELATIONSHIP_TABLE_NAMES

    table_name = NODE_TABLE_NAMES["Customer"]
    df = spark.read.table(table_name)

Version: 1.0.0
"""

from typing import Dict

__version__ = "1.0.0"
__all__ = [
    "NODE_TABLE_NAMES",
    "RELATIONSHIP_TABLE_NAMES",
    "CATALOG_NAME",
    "SCHEMA_NAME",
    "get_node_table_name",
    "get_relationship_table_name",
]

# Unity Catalog Configuration
CATALOG_NAME = "retail_investment"
SCHEMA_NAME = "retail_investment"


# Dictionary mapping node labels to Unity Catalog table names
# Format: catalog.schema.table (Unity Catalog three-level namespace)
NODE_TABLE_NAMES: Dict[str, str] = {
    "Customer": f"{CATALOG_NAME}.{SCHEMA_NAME}.customer",
    "Bank": f"{CATALOG_NAME}.{SCHEMA_NAME}.bank",
    "Account": f"{CATALOG_NAME}.{SCHEMA_NAME}.account",
    "Company": f"{CATALOG_NAME}.{SCHEMA_NAME}.company",
    "Stock": f"{CATALOG_NAME}.{SCHEMA_NAME}.stock",
    "Transaction": f"{CATALOG_NAME}.{SCHEMA_NAME}.transaction",
    "Position": f"{CATALOG_NAME}.{SCHEMA_NAME}.position",
}

# Dictionary mapping relationship types to Unity Catalog table names
# Format: catalog.schema.table (Unity Catalog three-level namespace)
RELATIONSHIP_TABLE_NAMES: Dict[str, str] = {
    "HAS_ACCOUNT": f"{CATALOG_NAME}.{SCHEMA_NAME}.has_account",
    "AT_BANK": f"{CATALOG_NAME}.{SCHEMA_NAME}.at_bank",
    "OF_COMPANY": f"{CATALOG_NAME}.{SCHEMA_NAME}.of_company",
    "PERFORMS": f"{CATALOG_NAME}.{SCHEMA_NAME}.performs",
    "BENEFITS_TO": f"{CATALOG_NAME}.{SCHEMA_NAME}.benefits_to",
    "HAS_POSITION": f"{CATALOG_NAME}.{SCHEMA_NAME}.has_position",
    "OF_SECURITY": f"{CATALOG_NAME}.{SCHEMA_NAME}.of_security",
}


def get_node_table_name(node_label: str) -> str:
    """
    Get Unity Catalog table name for a node label.

    Args:
        node_label: Neo4j node label (e.g., "Customer", "Bank").

    Returns:
        Unity Catalog table name (e.g., "retail_investment.retail_investment.customer").

    Raises:
        ValueError: If node_label is not defined.

    Example:
        >>> table = get_node_table_name("Customer")
        >>> print(table)
        retail_investment.retail_investment.customer
    """
    if node_label not in NODE_TABLE_NAMES:
        available = ", ".join(sorted(NODE_TABLE_NAMES.keys()))
        raise ValueError(
            f"No table name defined for node label '{node_label}'. "
            f"Available labels: {available}"
        )

    return NODE_TABLE_NAMES[node_label]


def get_relationship_table_name(relationship_type: str) -> str:
    """
    Get Unity Catalog table name for a relationship type.

    Args:
        relationship_type: Neo4j relationship type (e.g., "HAS_ACCOUNT", "AT_BANK").

    Returns:
        Unity Catalog table name (e.g., "retail_investment.retail_investment.has_account").

    Raises:
        ValueError: If relationship_type is not defined.

    Example:
        >>> table = get_relationship_table_name("HAS_ACCOUNT")
        >>> print(table)
        retail_investment.retail_investment.has_account
    """
    if relationship_type not in RELATIONSHIP_TABLE_NAMES:
        available = ", ".join(sorted(RELATIONSHIP_TABLE_NAMES.keys()))
        raise ValueError(
            f"No table name defined for relationship type '{relationship_type}'. "
            f"Available types: {available}"
        )

    return RELATIONSHIP_TABLE_NAMES[relationship_type]
