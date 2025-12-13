# Neo4j + Databricks Demo

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Create Databricks Catalog, Schema, and Volume

In the Databricks Console:

1. **Create a Catalog**
   - Navigate to **Catalog** in the left sidebar
   - Click **Create catalog**
   - Enter a name (e.g., `neo4j_demo`)
   - Click **Create**

2. **Create a Schema**
   - Select your new catalog
   - Click **Create schema**
   - Enter a name (e.g., `raw_data`)
   - Click **Create**

3. **Create a Volume**
   - Select your new schema
   - Click **Create volume**
   - Enter a name (e.g., `source_files`)
   - Select **Managed** volume type
   - Click **Create**

Your volume path will be: `/Volumes/<catalog>/<schema>/<volume>`
(e.g., `/Volumes/neo4j_demo/raw_data/source_files`)

### 3. Configure Environment Variables

Copy the sample environment file and fill in your values:

```bash
cp .env.sample .env
```

Edit `.env` with your configuration:

```bash
# Databricks Authentication
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=your_databricks_token

# Databricks Unity Catalog (use names from step 2)
DATABRICKS_CATALOG=neo4j_demo
DATABRICKS_SCHEMA=raw_data
DATABRICKS_VOLUME=source_files

# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
```

**To get a Databricks token:**
Databricks workspace → User Settings → Developer → Access tokens → Generate new token

### 4. Setup Databricks Secrets

Run the setup script to create secrets in Databricks for the Neo4j connection:

```bash
./scripts/setup_databricks_secrets.sh
```

This creates a secret scope `neo4j-creds` with the following secrets:
- `username` - Neo4j username
- `password` - Neo4j password
- `url` - Neo4j connection URI
- `volume_path` - Databricks volume path

### 5. Upload Data Files (Lab 1)

```bash
uv run python lab_1_databricks_upload/upload_to_databricks.py
```

Files are uploaded to:
- `/Volumes/<catalog>/<schema>/<volume>/csv/*.csv`
- `/Volumes/<catalog>/<schema>/<volume>/html/*.html`

### 6. Import Data to Neo4j (Lab 2)

Import the notebook into Databricks and run it:

1. In Databricks, go to **Workspace** → **Import**
2. Upload `lab_2_neo4j_import/import_financial_data_to_neo4j.ipynb`
3. Attach to a cluster and run all cells

The notebook reads CSV files from the Databricks volume and imports them into Neo4j.

#### Query Samples

After importing data, explore the graph with sample queries using the **Neo4j Spark Connector**:

**Option A: Databricks Notebook** (Recommended)
- Upload `lab_2_neo4j_import/query_samples.ipynb` to Databricks
- Uses Neo4j Spark Connector with pushdown optimizations
- Includes portfolio analysis, transaction network, and risk profiling queries

**Option B: Local PySpark Script**
```bash
# Run all queries (requires PySpark)
uv run python lab_2_neo4j_import/query_financial_graph.py

# Run specific query
uv run python lab_2_neo4j_import/query_financial_graph.py portfolio
uv run python lab_2_neo4j_import/query_financial_graph.py sectors
uv run python lab_2_neo4j_import/query_financial_graph.py risk_profile
```

Available queries: `portfolio`, `diversified`, `sectors`, `active_senders`, `bidirectional`, `high_value`, `risk_profile`

#### Spark Connector Best Practices

All notebooks and scripts follow Neo4j Spark Connector best practices:
- **DataSource V2 API** - Uses `org.neo4j.spark.DataSource` for all operations
- **Pushdown optimizations** - Filters, columns, aggregates, and limits pushed to Neo4j
- **coalesce(1) for relationships** - Prevents deadlocks during parallel writes
- **Indexes before loading** - Constraints created before bulk writes for performance

### 7. Export Neo4j to Lakehouse (Lab 3)

Import and run the export notebook:

1. In Databricks, go to **Workspace** → **Import**
2. Upload `lab_3_neo4j_to_lakehouse/export_neo4j_to_databricks.ipynb`
3. Attach to a cluster and run all cells

The notebook queries Neo4j and exports graph data back to Databricks tables.
