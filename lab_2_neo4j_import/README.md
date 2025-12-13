# Lab 2: Import Data to Neo4j

This lab reads CSV files from the Databricks volume and imports them into your Neo4j graph database.

## Prerequisites

Before running this lab, ensure you have:

1. Completed the setup steps in the main [README.md](../README.md)
2. Completed [Lab 1](../lab_1_databricks_upload/README.md) to upload data files
3. A running Neo4j instance (AuraDB or Neo4j Desktop)

## Data Model

The import creates a retail investment graph with the following structure:

**Node Types (7)**:
- **Customer** - Customer profile data (demographics, risk profile, credit scores)
- **Bank** - Financial institution data
- **Account** - Customer account information (checking, savings, investment)
- **Company** - Corporate entity information
- **Stock** - Stock and security data
- **Position** - Investment portfolio holdings
- **Transaction** - Financial transaction records

**Relationship Types (7)**:
- `(Customer)-[:HAS_ACCOUNT]->(Account)` - Customer owns accounts
- `(Account)-[:AT_BANK]->(Bank)` - Account held at a bank
- `(Stock)-[:OF_COMPANY]->(Company)` - Stock issued by company
- `(Account)-[:PERFORMS]->(Transaction)` - Account performs transaction
- `(Transaction)-[:BENEFITS_TO]->(Account)` - Transaction benefits account
- `(Account)-[:HAS_POSITION]->(Position)` - Account holds investment position
- `(Position)-[:OF_SECURITY]->(Stock)` - Position represents stock shares

## Running the Import

### Option A: Databricks Notebook (Recommended)

1. In Databricks, go to **Workspace** → **Import**
2. Upload `import_financial_data_to_neo4j.ipynb`
3. Attach to a cluster with the Neo4j Spark Connector installed
4. Run all cells

### Option B: Local Python Script

```bash
uv run python lab_2_neo4j_import/import_financial_data.py
```

## Query Samples

After importing data, explore the graph with sample queries using the Neo4j Spark Connector.

### Option A: Databricks Notebook (Recommended)

Upload `query_samples.ipynb` to Databricks and run it. This notebook:
- Uses Neo4j Spark Connector with pushdown optimizations
- Includes portfolio analysis, transaction network, and risk profiling queries

### Option B: Local PySpark Script

```bash
# Run all queries (requires PySpark)
uv run python lab_2_neo4j_import/query_financial_graph.py

# Run specific query
uv run python lab_2_neo4j_import/query_financial_graph.py portfolio
uv run python lab_2_neo4j_import/query_financial_graph.py sectors
uv run python lab_2_neo4j_import/query_financial_graph.py risk_profile
```

**Available queries**: `portfolio`, `diversified`, `sectors`, `active_senders`, `bidirectional`, `high_value`, `risk_profile`

## Spark Connector Best Practices

All notebooks and scripts follow Neo4j Spark Connector best practices:

- **DataSource V2 API** - Uses `org.neo4j.spark.DataSource` for all operations
- **Pushdown optimizations** - Filters, columns, aggregates, and limits pushed to Neo4j
- **coalesce(1) for relationships** - Prevents deadlocks during parallel writes
- **Indexes before loading** - Constraints created before bulk writes for performance

## Verification

After import, verify the data in Neo4j Browser:

```cypher
-- Count nodes by label
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {})
YIELD value
RETURN label, value.count as count;

-- Count relationships by type
CALL db.relationshipTypes() YIELD relationshipType
CALL apoc.cypher.run('MATCH ()-[r:`' + relationshipType + '`]->() RETURN count(r) as count', {})
YIELD value
RETURN relationshipType, value.count as count;
```

## Next Steps

Continue to [Lab 3: Export Neo4j to Lakehouse](../lab_3_neo4j_to_lakehouse/README.md) to export graph data back to Databricks Delta tables.
