# Neo4j + Databricks Integration Demo

A comprehensive demonstration of integrating Neo4j graph data with Databricks lakehouse architecture for retail investment analysis.

## Overview

This project demonstrates bidirectional data flow between Neo4j and Databricks:

1. **Upload to Databricks** - Load source CSV files to Unity Catalog volumes
2. **Import to Neo4j** - Build a graph database from the uploaded data
3. **Export to Lakehouse** - Extract graph data back to Delta Lake tables

### Data Model

The graph models a retail investment platform where **customers** own **accounts** at various **banks**. Accounts can hold investment **positions** in **stocks** issued by **companies**, and accounts perform financial **transactions** that transfer money to other accounts.

```
Customer ──owns──> Account ──held at──> Bank
                      │
                      ├──performs──> Transaction ──benefits──> Account
                      │
                      └──holds──> Position ──of──> Stock ──issued by──> Company
```

For detailed schema documentation including properties, constraints, indexes, and sample queries, see [docs/SCHEMA_MODEL_OVERVIEW.md](./docs/SCHEMA_MODEL_OVERVIEW.md).

## Setup

You can run this demo entirely in Databricks or with local development tools. Both options start with the same Databricks setup.

### 1. Create Databricks Catalog, Schema, and Volume

In the Databricks Console:

1. **Create a Catalog**: Catalog → Create catalog → Enter name (e.g., `neo4j_demo`)
2. **Create a Schema**: Select catalog → Create schema → Enter name (e.g., `raw_data`)
3. **Create a Volume**: Select schema → Create volume → Enter name (e.g., `source_files`) → Select **Managed**

Your volume path will be: `/Volumes/<catalog>/<schema>/<volume>`

### 2. Create a Databricks Cluster

Create a cluster with the Neo4j Spark Connector for running the import/export notebooks.

1. **Create a new cluster**:
   - Navigate to **Compute** → **Create Compute**
   - **Cluster name**: `Neo4j-Demo-Cluster`
   - **Access mode**: **Dedicated** (required for Neo4j Spark Connector)
   - **Databricks Runtime**: 13.3 LTS or higher
   - **Workers**: 2-4 (adjust based on data volume)

2. **Install the Neo4j Spark Connector**:
   - Click on your cluster → **Libraries** tab
   - Click **Install New** → Select **Maven**
   - Enter coordinates: `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3`
   - Click **Install**

3. **Verify installation**:
   - Library should show status "Installed"
   - Restart the cluster if needed

**Important**: Access mode MUST be "Dedicated" - the Neo4j Spark Connector does not work in Shared mode.

### 3. Choose Your Setup Option

---

### Option A: Databricks Only

Run everything directly in Databricks. No local Python setup required. Good for workshops and demos.

#### Upload Data Files

1. Download or clone this repository
2. In Databricks, navigate to your volume
3. Click **Upload** and upload all files from:
   - `data/csv/*.csv`
   - `data/html/*.html`

#### Upload Notebooks

1. In Databricks, go to **Workspace**
2. Create a folder for this project
3. Click **Import** and upload the `.ipynb` files from each lab folder

#### Create Secrets

Using the [Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/install.html):

```bash
databricks secrets create-scope neo4j-creds

databricks secrets put-secret neo4j-creds username --string-value "neo4j"
databricks secrets put-secret neo4j-creds password --string-value "your_neo4j_password"
databricks secrets put-secret neo4j-creds url --string-value "neo4j+s://your-instance.databases.neo4j.io"
databricks secrets put-secret neo4j-creds volume_path --string-value "/Volumes/neo4j_demo/raw_data/source_files"
```

**Alternative - Using Databricks UI:**
1. Click on your username → **User Settings** → **Developer**
2. Under Secret Scopes, click **Manage**
3. Create scope `neo4j-creds` and add secrets: `username`, `password`, `url`, `volume_path`

---

### Option B: Local Development

Run Python scripts locally and use VS Code with the [Databricks extension](https://marketplace.visualstudio.com/items?itemName=databricks.databricks) for notebooks. Good for development and testing.

#### Install Dependencies

```bash
uv sync
```

#### Configure Environment Variables

```bash
cp .env.sample .env
```

Edit `.env`:

```bash
# Databricks Authentication
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=your_databricks_token

# Databricks Unity Catalog
DATABRICKS_CATALOG=neo4j_demo
DATABRICKS_SCHEMA=raw_data
DATABRICKS_VOLUME=source_files

# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
```

**To get a Databricks token:** Workspace → User Settings → Developer → Access tokens → Generate new token

#### Setup Databricks Secrets

Run the setup script to create secrets from your `.env` file:

```bash
./scripts/setup_databricks_secrets.sh
```

This creates a `neo4j-creds` secret scope with: `username`, `password`, `url`, `volume_path`

## Labs

After completing the setup steps above, proceed through the labs in order:

| Lab | Description | Link |
|-----|-------------|------|
| **Lab 1** | Upload CSV and HTML files to Databricks Unity Catalog | [lab_1_databricks_upload](./lab_1_databricks_upload/README.md) |
| **Lab 2** | Import data from Databricks into Neo4j graph database | [lab_2_neo4j_import](./lab_2_neo4j_import/README.md) |
| **Lab 3** | *(Reserved for future lab)* | — |
| **Lab 4** | Export Neo4j graph data to Databricks Delta Lake tables | [lab_4_neo4j_to_lakehouse](./lab_4_neo4j_to_lakehouse/README.md) |
| **Lab 5** | Create Databricks AI agents (Genie and Knowledge Agent) | [lab_5_ai_agents](./lab_5_ai_agents/README.md) |
| **Lab 6** | Build Multi-Agent Supervisor with sample queries | [lab_6_multi_agent](./lab_6_multi_agent/README.md) |
| **Lab 7** | Graph augmentation agent for entity extraction | [lab_7_augmentation_agent](./lab_7_augmentation_agent/README.md) |

## Project Structure

```
neo4j-databricks-demo/
├── README.md                              # This file
├── docs/
│   ├── SCHEMA_MODEL_OVERVIEW.md           # Detailed graph schema documentation
│   ├── BACKGROUND_CONCEPTS.md             # Neo4j and graph database concepts
│   └── GRAPH_AUGMENTATION.md              # Graph augmentation strategies
├── data/
│   ├── csv/                               # Source CSV files
│   │   ├── accounts.csv
│   │   ├── banks.csv
│   │   ├── companies.csv
│   │   ├── customers.csv
│   │   ├── portfolio_holdings.csv
│   │   ├── stocks.csv
│   │   └── transactions.csv
│   └── html/                              # Customer profiles and documents
├── lab_1_databricks_upload/               # Lab 1: Upload to Databricks
│   ├── README.md
│   └── upload_to_databricks.py
├── lab_2_neo4j_import/                    # Lab 2: Import to Neo4j
│   ├── README.md
│   ├── import_financial_data_to_neo4j.ipynb
│   ├── import_financial_data.py
│   ├── query_samples.ipynb
│   └── query_financial_graph.py
├── lab_4_neo4j_to_lakehouse/              # Lab 4: Export to Lakehouse
│   ├── README.md
│   ├── export_neo4j_to_databricks.ipynb
│   └── export_neo4j_to_databricks.py
├── lab_5_ai_agents/                       # Lab 5: AI Agents
│   └── README.md
├── lab_6_multi_agent/                     # Lab 6: Multi-Agent Supervisor
│   ├── README.md
│   └── SAMPLE_QUERIES.md
├── lab_7_augmentation_agent/              # Lab 7: Graph Augmentation
│   ├── README.md
│   ├── augmentation_agent.py
│   └── augmentation_agent.ipynb
├── scripts/
│   └── setup_databricks_secrets.sh
└── src/
    └── ...
```

## Quick Reference

### Databricks Cluster Requirements

For notebooks using the Neo4j Spark Connector:

- **Access Mode**: Dedicated (required for Neo4j Spark Connector)
- **Databricks Runtime**: 13.3 LTS or higher (Spark 3.x)
- **Maven Library**: `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3`

### Secrets Reference

The notebooks expect a `neo4j-creds` secret scope with:

| Secret | Description | Example |
|--------|-------------|---------|
| `username` | Neo4j username | `neo4j` |
| `password` | Neo4j password | `your_password` |
| `url` | Neo4j connection URI | `neo4j+s://xxx.databases.neo4j.io` |
| `volume_path` | Databricks volume path | `/Volumes/neo4j_demo/raw_data/source_files` |
