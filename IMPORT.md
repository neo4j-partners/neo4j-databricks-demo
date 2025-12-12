# Data Import: Databricks Unity Catalog to Neo4j

This document describes how to import the retail banking and investment portfolio demonstration data from Databricks Unity Catalog into Neo4j.

---

## Overview

The data flow routes all CSV files through Databricks Unity Catalog and Volumes before importing to Neo4j using the Neo4j Spark Connector. This approach provides:

- Centralized data storage with enterprise governance
- Programmatic, repeatable imports through Databricks notebooks
- Leverage of Databricks compute for data transformation
- Secure credential management via Databricks Secrets

---

## Prerequisites

### Neo4j Database

You need a running Neo4j instance (Aura or self-hosted). Save these credentials:

- **Connection URI**: `neo4j+s://<instance>.databases.neo4j.io:7687` (Aura) or `bolt://<host>:7687` (self-hosted)
- **Username**: `neo4j` (default)
- **Password**: Your database password

### Databricks Cluster

Create a cluster with the Neo4j Spark Connector:

1. **Runtime Version**: 17.3 LTS (Spark 4.0.0, Scala 2.13) or compatible
2. **Access Mode**: Dedicated (Single user) - required for Neo4j Connector
3. **Library**: Install from Maven: `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.x_for_spark_3`

**Reference**: See `/Users/ryanknight/projects/aircraft_analyst/data_setup/README.md` Section 4 for detailed cluster setup instructions.

---

## Setup Instructions

### Step 1: Configure Databricks Secrets

**Option A: Use the setup script (Recommended)**

Run the provided script to automatically create secrets from your `.env` file:

```bash
./scripts/setup_databricks_secrets.sh
```

The script reads from `.env` and creates:
- `username` from `NEO4J_USERNAME`
- `password` from `NEO4J_PASSWORD`
- `url` from `NEO4J_URI`
- `volume_path` constructed from `DATABRICKS_CATALOG/DATABRICKS_SCHEMA/DATABRICKS_VOLUME`

**Option B: Manual setup**

Create a secret scope and add secrets manually:

```bash
# Create secret scope
databricks secrets create-scope neo4j-creds

# Store credentials
databricks secrets put-secret neo4j-creds username
databricks secrets put-secret neo4j-creds password
databricks secrets put-secret neo4j-creds url
databricks secrets put-secret neo4j-creds volume_path

# Verify
databricks secrets list-secrets neo4j-creds
```

**Secret Values:**
- `username`: Your Neo4j username (e.g., `neo4j`)
- `password`: Your Neo4j password
- `url`: Your Neo4j connection URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io:7687`)
- `volume_path`: Unity Catalog Volume path (e.g., `/Volumes/your_catalog/your_schema/financial_demo`)

**Reference**: See `/Users/ryanknight/projects/aircraft_analyst/data_setup/README.md` Section 3 for detailed secrets configuration.

### Step 2: Create Unity Catalog Volume

If the Volume does not already exist:

1. Navigate to **Catalogs** in your Databricks workspace
2. Select or create your catalog and schema
3. Click **Create** → **Volume**
4. Name: `financial_demo` (or your preferred name)
5. Volume Type: **Managed**
6. Click **Create**

The Volume path will be: `/Volumes/<catalog>/<schema>/financial_demo`

**Reference**: See `/Users/ryanknight/projects/aircraft_analyst/data_setup/README.md` Section 5 for detailed Volume creation.

### Step 3: Upload CSV Files

Upload all 7 CSV files from `data/csv/` to the Unity Catalog Volume:

**Files to upload:**
- `customers.csv` (102 records)
- `banks.csv` (102 records)
- `accounts.csv` (123 records)
- `companies.csv` (102 records)
- `stocks.csv` (102 records)
- `portfolio_holdings.csv` (110 records)
- `transactions.csv` (123 records)

**Option A: Use the upload script (Recommended)**

```bash
./scripts/upload_csv_to_volume.sh
```

The script reads Volume path from `.env` and uploads all CSV files.

**Option B: Using Databricks UI**
1. Navigate to your Volume in the Catalog Explorer
2. Click **Upload to Volume**
3. Select all CSV files
4. Click **Upload**

**Option C: Using Databricks CLI**
```bash
databricks fs cp ./data/csv/*.csv dbfs:/Volumes/<catalog>/<schema>/financial_demo/ --recursive
```

**Reference**: See `/Users/ryanknight/projects/aircraft_analyst/data_setup/README.md` Section 5 for upload methods.

### Step 4: Run the Import Notebook

1. Import `src/import_financial_data_to_neo4j.ipynb` into your Databricks workspace
2. Attach the notebook to your cluster with the Neo4j Connector
3. Run all cells sequentially

The notebook will:
1. Verify prerequisites (CSV files and Neo4j connectivity)
2. Load and transform CSV data with proper data types
3. Create uniqueness constraints and indexes
4. Write all nodes to Neo4j
5. Write all relationships to Neo4j
6. Validate the import with count checks and sample queries

---

## Graph Schema

### Node Types (7)

| Node Label | Key Property | Record Count | Description |
|------------|--------------|--------------|-------------|
| Customer | customer_id | 102 | Individual banking customers |
| Bank | bank_id | 102 | Financial institutions |
| Account | account_id | 123 | Customer accounts (checking, savings, investment) |
| Company | company_id | 102 | Publicly traded corporations |
| Stock | stock_id | 102 | Tradeable securities |
| Position | position_id | 110 | Portfolio holdings |
| Transaction | transaction_id | 123 | Financial transactions |

### Relationship Types (7)

| Relationship | Pattern | Count | Description |
|--------------|---------|-------|-------------|
| HAS_ACCOUNT | Customer → Account | 123 | Customer owns account |
| AT_BANK | Account → Bank | 123 | Account held at bank |
| OF_COMPANY | Stock → Company | 102 | Stock issued by company |
| PERFORMS | Account → Transaction | 123 | Account initiates transfer |
| BENEFITS_TO | Transaction → Account | 123 | Account receives funds |
| HAS_POSITION | Account → Position | 110 | Account holds investment position |
| OF_SECURITY | Position → Stock | 110 | Position is in specific stock |

### Graph Model Diagram

```
                    ┌──────────┐
                    │ Customer │
                    └────┬─────┘
                         │ HAS_ACCOUNT
                         ▼
┌──────┐  AT_BANK   ┌─────────┐  HAS_POSITION   ┌──────────┐
│ Bank │◄───────────│ Account │────────────────►│ Position │
└──────┘            └────┬────┘                 └────┬─────┘
                         │                           │
                         │ PERFORMS                  │ OF_SECURITY
                         ▼                           ▼
                 ┌─────────────┐              ┌───────┐  OF_COMPANY   ┌─────────┐
                 │ Transaction │              │ Stock │──────────────►│ Company │
                 └──────┬──────┘              └───────┘               └─────────┘
                        │
                        │ BENEFITS_TO
                        ▼
                    ┌─────────┐
                    │ Account │
                    └─────────┘
```

---

## Data Type Mappings

The notebook applies these type conversions before writing to Neo4j:

### Customer
- `annual_income`: INTEGER
- `credit_score`: INTEGER
- `registration_date`: DATE
- `date_of_birth`: DATE

### Bank
- `total_assets_billions`: DOUBLE
- `established_year`: INTEGER

### Account
- `balance`: DOUBLE
- `interest_rate`: DOUBLE
- `opened_date`: DATE

### Company
- `market_cap_billions`: DOUBLE
- `annual_revenue_billions`: DOUBLE
- `founded_year`: INTEGER
- `employee_count`: INTEGER

### Stock
- `current_price`, `previous_close`, `opening_price`, `day_high`, `day_low`: DOUBLE
- `volume`: INTEGER
- `market_cap_billions`, `pe_ratio`, `dividend_yield`: DOUBLE
- `fifty_two_week_high`, `fifty_two_week_low`: DOUBLE

### Position
- `shares`: INTEGER
- `purchase_price`, `current_value`, `percentage_of_portfolio`: DOUBLE
- `purchase_date`: DATE

### Transaction
- `amount`: DOUBLE
- `transaction_date`: DATE

---

## Validation Queries

After import, verify the data with these queries:

### Count Nodes by Label

```cypher
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
ORDER BY label
```

**Expected Results:**
- Account: 123
- Bank: 102
- Company: 102
- Customer: 102
- Position: 110
- Stock: 102
- Transaction: 123

### Count Relationships by Type

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY relationship_type
```

**Expected Results:**
- AT_BANK: 123
- BENEFITS_TO: 123
- HAS_ACCOUNT: 123
- HAS_POSITION: 110
- OF_COMPANY: 102
- OF_SECURITY: 110
- PERFORMS: 123

### Sample Customer Profile

```cypher
MATCH (c:Customer {customer_id: 'C0001'})-[:HAS_ACCOUNT]->(a:Account)
OPTIONAL MATCH (a)-[:AT_BANK]->(b:Bank)
OPTIONAL MATCH (a)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)
RETURN
    c.first_name + ' ' + c.last_name AS customer_name,
    a.account_id AS account,
    a.account_type AS account_type,
    a.balance AS balance,
    b.name AS bank_name,
    s.ticker AS ticker,
    p.shares AS shares,
    p.current_value AS holding_value
ORDER BY holding_value DESC
```

---

## Troubleshooting

### "Secret not found" Error

Verify secrets exist:
```bash
databricks secrets list-secrets neo4j-creds
```

Ensure all four secrets are configured: `username`, `password`, `url`, `volume_path`

### "Connection failed" Error

1. Verify Neo4j is running
2. Check the URL format:
   - Aura: `neo4j+s://<instance>.databases.neo4j.io:7687`
   - Self-hosted with TLS: `neo4j+s://<host>:7687`
   - Self-hosted without TLS: `bolt://<host>:7687`
3. Verify network connectivity from Databricks to Neo4j

### "CSV file not found" Error

1. Verify files were uploaded to the correct Volume path
2. Check the `volume_path` secret matches the actual path
3. Use `dbutils.fs.ls(VOLUME_PATH)` to list files

### Cluster Library Error

Ensure the Neo4j Connector is installed:
1. Go to cluster → Libraries tab
2. Verify `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.x_for_spark_3` is installed
3. Cluster must use **Dedicated (Single user)** access mode

---

## References

### Aircraft Analyst Implementation

The Aircraft Analyst project demonstrates the same pattern with a more complex schema:

- **Location**: `/Users/ryanknight/projects/aircraft_analyst/data_setup`
- **README.md**: Complete setup guide
- **2_upload_test_data_to_neo4j.ipynb**: Example notebook for Neo4j import

Key patterns borrowed:
- Databricks Secrets for credential management
- Unity Catalog Volumes for data storage
- Neo4j Spark Connector for write operations
- Helper functions for node and relationship writes

### Additional Resources

- **DATA_IMPORT.md**: Original schema documentation and query examples
- **Neo4j Spark Connector**: https://neo4j.com/docs/spark/current/
- **Databricks Secrets**: https://docs.databricks.com/en/security/secrets/
- **Unity Catalog Volumes**: https://docs.databricks.com/en/connect/unity-catalog/volumes.html

---

**Last Updated**: 2025-12-12
**Notebook**: `src/import_financial_data_to_neo4j.ipynb`
