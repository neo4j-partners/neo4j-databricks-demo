# Neo4j + Databricks Integration Demo

A comprehensive demonstration of integrating Neo4j graph data with Databricks lakehouse architecture for retail investment analysis.

## Overview

This project demonstrates bidirectional data flow between Neo4j and Databricks:

1. **Upload to Databricks** - Load source CSV files to Unity Catalog volumes
2. **Import to Neo4j** - Build a graph database from the uploaded data
3. **Export to Lakehouse** - Extract graph data back to Delta Lake tables

### Data Model

The project models a retail investment platform with the following entities:

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

## Setup

### Step 1: Install Dependencies

```bash
uv sync
```

### Step 2: Create Databricks Catalog, Schema, and Volume

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

### Step 3: Configure Environment Variables

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

### Step 4: Setup Databricks Secrets

Run the setup script to create secrets in Databricks for the Neo4j connection:

```bash
./scripts/setup_databricks_secrets.sh
```

This creates a secret scope `neo4j-creds` with the following secrets:
- `username` - Neo4j username
- `password` - Neo4j password
- `url` - Neo4j connection URI
- `volume_path` - Databricks volume path

## Labs

After completing the setup steps above, proceed through the labs in order:

| Lab | Description | Link |
|-----|-------------|------|
| **Lab 1** | Upload CSV and HTML files to Databricks Unity Catalog | [lab_1_databricks_upload](./lab_1_databricks_upload/README.md) |
| **Lab 2** | Import data from Databricks into Neo4j graph database | [lab_2_neo4j_import](./lab_2_neo4j_import/README.md) |
| **Lab 3** | Export Neo4j graph data to Databricks Delta Lake tables | [lab_3_neo4j_to_lakehouse](./lab_3_neo4j_to_lakehouse/README.md) |
| **Lab 4** | Create Databricks AI agents (Genie and Knowledge Agent) | [lab_4_ai_agents](./lab_4_ai_agents/README.md) |
| **Lab 5** | Build Multi-Agent Supervisor with sample queries | [lab_5_multi_agent](./lab_5_multi_agent/README.md) |
| **Lab 6** | Graph augmentation agent for entity extraction | [lab_6_augmentation_agent](./lab_6_augmentation_agent/README.md) |

## Project Structure

```
neo4j-databricks-demo/
├── README.md                              # This file
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
├── lab_3_neo4j_to_lakehouse/              # Lab 3: Export to Lakehouse
│   ├── README.md
│   ├── export_neo4j_to_databricks.ipynb
│   └── export_neo4j_to_databricks.py
├── lab_4_ai_agents/                       # Lab 4: AI Agents
│   └── README.md
├── lab_5_multi_agent/                     # Lab 5: Multi-Agent Supervisor
│   ├── README.md
│   └── SAMPLE_QUERIES.md
├── lab_6_augmentation_agent/              # Lab 6: Graph Augmentation
│   ├── README.md
│   ├── augmentation_agent.py
│   └── augmentation_agent.ipynb
├── scripts/
│   └── setup_databricks_secrets.sh
└── src/
    └── ...
```

## Quick Reference

### Required Library Versions

**Maven (Neo4j Spark Connector)**:
```
org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3
```

### Cluster Configuration

- **Access Mode**: Dedicated (required for Neo4j Spark Connector)
- **Databricks Runtime**: 13.3 LTS or higher (Spark 3.x)
- **Cluster Mode**: Standard

### Databricks Secrets

```bash
# Create secrets scope
databricks secrets create-scope neo4j-creds

# Store Neo4j credentials
databricks secrets put-secret neo4j-creds password
databricks secrets put-secret neo4j-creds url
databricks secrets put-secret neo4j-creds username
```
