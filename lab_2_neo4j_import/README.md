# Lab 2: Import Data to Neo4j

This lab reads CSV files from the Databricks volume and imports them into your Neo4j graph database.

## Running the Import

### Option A: Databricks Notebook

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

### Option A: Databricks Notebook

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
