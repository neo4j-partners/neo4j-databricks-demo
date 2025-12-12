# Import Neo4j Data to Databricks Unity Catalog

Extract graph data from Neo4j and load it into Databricks Unity Catalog tables.

## Status: IMPLEMENTED

| Task | Status |
|------|--------|
| Create module directory | Done |
| Write Python script | Done |
| Create Databricks notebook | Done |

## Files Created

```
src/neo4j_to_lakehouse/
├── __init__.py
├── export_neo4j_to_databricks.py    # Standalone script
└── export_neo4j_to_databricks.ipynb # Databricks notebook
```

## What It Does

1. Connects to Neo4j using the Spark Connector
2. Reads all 7 node types and 7 relationship types
3. Writes them as Delta tables in Unity Catalog

## Data Extracted

**7 Node Tables:**
- customer (102 rows)
- bank (102 rows)
- account (123 rows)
- company (102 rows)
- stock (102 rows)
- position (110 rows)
- transaction (123 rows)

**7 Relationship Tables:**
- has_account (Customer → Account, 123 rows)
- at_bank (Account → Bank, 123 rows)
- of_company (Stock → Company, 102 rows)
- performs (Account → Transaction, 123 rows)
- benefits_to (Transaction → Account, 123 rows)
- has_position (Account → Position, 110 rows)
- of_security (Position → Stock, 110 rows)

## How to Run

### Option 1: Databricks Notebook

1. Import `src/neo4j_to_lakehouse/export_neo4j_to_databricks.ipynb` to Databricks
2. Attach to a cluster with Neo4j Spark Connector installed
3. Run all cells

### Option 2: Python Script

1. Upload `src/neo4j_to_lakehouse/export_neo4j_to_databricks.py` to Databricks
2. Run as a job or execute in a notebook with `%run`

## Prerequisites

### Databricks Secrets

Use the existing setup script to create secrets:
```bash
./scripts/setup_databricks_secrets.sh
```

This creates the `neo4j-creds` scope with:
- `url` - Neo4j connection URL
- `username` - Neo4j username
- `password` - Neo4j password
- `volume_path` - Unity Catalog volume path (catalog/schema extracted from this)

**Note:** The catalog must already exist. The script will only create the schema.

### Cluster Requirements

- Neo4j Spark Connector installed (Maven: `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3`)
- Access mode: **Dedicated** (not Shared)
- Databricks Runtime 13.3 LTS or higher

### Permissions

- CREATE CATALOG (or use existing catalog)
- CREATE SCHEMA
- CREATE TABLE

## Configuration

The script extracts catalog and schema from the `volume_path` secret automatically.

If you need to override, edit the defaults in the script:

```python
CATALOG = "neo4j_augmentation_demo"
SCHEMA = "graph_data"
```

**Important:** The catalog must already exist. The script only creates the schema.

## Output

After running, Unity Catalog will have:

```
neo4j_augmentation_demo.graph_data/
├── customer           (102 rows)
├── bank               (102 rows)
├── account            (123 rows)
├── company            (102 rows)
├── stock              (102 rows)
├── position           (110 rows)
├── transaction        (123 rows)
├── has_account        (123 rows)
├── at_bank            (123 rows)
├── of_company         (102 rows)
├── performs           (123 rows)
├── benefits_to        (123 rows)
├── has_position       (110 rows)
└── of_security        (110 rows)
```

## How It Works

### Reading Nodes

```python
df = spark.read \
    .format("org.neo4j.spark.DataSource") \
    .option("labels", "Customer") \
    .load()
```

### Reading Relationships

```python
df = spark.read \
    .format("org.neo4j.spark.DataSource") \
    .option("relationship", "HAS_ACCOUNT") \
    .option("relationship.source.labels", "Customer") \
    .option("relationship.target.labels", "Account") \
    .option("relationship.nodes.map", "false") \
    .load()
```

### Writing to Unity Catalog

```python
df.write.format("delta").mode("overwrite").saveAsTable("catalog.schema.table_name")
```

## Next Steps

After exporting the data:

1. Create a Databricks Genie to query the structured data
2. Build dashboards using AI/BI
3. Set up scheduled refresh jobs to keep data in sync
