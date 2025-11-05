# Neo4j to Databricks Retail Investment Demo

A comprehensive demonstration of integrating Neo4j graph data with Databricks lakehouse architecture to build an intelligent multi-agent system for retail investment analysis.

## Overview

This project demonstrates how to extract graph data from Neo4j into Databricks Delta Lake tables and leverage that data to build a sophisticated multi-agent AI system. The system combines structured data querying with unstructured document analysis to provide comprehensive insights into customer investments, banking relationships, and portfolio holdings.

### What This Project Does

1. **Graph Data Extraction**: Extracts node and relationship data from Neo4j using the Neo4j Spark Connector
2. **Lakehouse Creation**: Creates a structured Delta Lake with 7 node tables and 7 relationship tables in Unity Catalog
3. **Multi-Agent AI System**: Demonstrates building intelligent agents that can:
   - Query structured lakehouse data using Databricks Genie
   - Analyze unstructured customer profiles and documents using a Knowledge Agent
   - Identify gaps between structured data and unstructured insights

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

## Use Case: Multi-Agent Investment Analysis System

This demo sets up a multi-agent system that combines:

### 1. **Genie Agent (Structured Data)**
Queries the lakehouse to answer questions about:
- Customer account balances and portfolios
- Investment positions and stock holdings
- Transaction history and patterns
- Banking relationships
- Portfolio performance metrics

### 2. **Knowledge Agent (Unstructured Data)**
Analyzes customer profiles and documents to extract insights about:
- Investment preferences and goals
- Risk tolerance narratives
- Life events affecting financial decisions
- Interests in emerging sectors (renewable energy, retail investment technology)
- Customer service interactions and preferences

### 3. **Combined Multi-Agent System**
Identifies gaps and enrichment opportunities by:
- Finding customer interests mentioned in profiles but not reflected in portfolios
- Discovering risk preferences that don't match current holdings
- Identifying cross-sell opportunities based on profile analysis
- Surfacing data quality issues (missing structured data that exists in documents)

## Prerequisites

Before you begin, ensure you have:

- **Databricks Workspace** with Unity Catalog enabled
- **Databricks Compute** permissions to create clusters
- **Neo4j Database** with the retail investment graph data loaded
- **Databricks Genie** access (for creating the query agent)
- **Databricks AI/BI** workspace (for knowledge agents)
- Proper **credentials** for Neo4j (username and password)
- **Databricks CLI** installed (optional, for managing secrets)

## Setup Instructions

### Step 1: Create Databricks Catalog and Schema

First, create the Unity Catalog namespace for the project:

```sql
-- Create the catalog
CREATE CATALOG IF NOT EXISTS retail_investment;

-- Create the default schema
CREATE SCHEMA IF NOT EXISTS retail_investment.default;

-- Grant appropriate permissions
GRANT USE CATALOG ON CATALOG retail_investment TO `<your-users-or-groups>`;
GRANT USE SCHEMA ON SCHEMA retail_investment.default TO `<your-users-or-groups>`;
```

### Step 2: Create a Databricks Cluster

Create a dedicated cluster with the Neo4j Spark Connector:

1. **Create a new cluster**:
   - Navigate to **Compute** in your Databricks workspace
   - Click **Create Compute**
   - Configure the cluster:
     - **Cluster name**: "Neo4j-Retail-Investment-Cluster"
     - **Cluster mode**: Standard
     - **Access mode**: **Dedicated (formerly: Single user)** ⚠️ REQUIRED for Neo4j Spark Connector
     - **Databricks Runtime**: 13.3 LTS or higher (Spark 3.x)
     - **Node type**: Choose based on your data size (e.g., Standard_DS3_v2)
     - **Workers**: 2-4 workers (adjust based on data volume)

2. **Install required libraries**:

   After creating the cluster, install the following libraries:

   **Maven Library** (Neo4j Spark Connector):
   - Click on your cluster
   - Go to **Libraries** tab
   - Click **Install New**
   - Select **Maven**
   - Enter coordinates:
     ```
     org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3
     ```
   - Click **Install**
   - Wait for installation to complete (status: Installed)

   **PyPI Library** (Neo4j Python Driver):
   - Click **Install New** again
   - Select **PyPI**
   - Enter package name:
     ```
     neo4j==6.0.2
     ```
   - Click **Install**
   - Wait for installation to complete

3. **Verify library installation**:
   - Both libraries should show status "Installed" with a green checkmark
   - Restart the cluster if needed to ensure libraries are loaded

4. **Important Notes**:
   - ⚠️ **Access mode MUST be "Dedicated (formerly: Single user)"** - the Neo4j Spark Connector does not work in Shared mode
   - The Maven library version must match your Spark version (3.x)
   - Do not upgrade the cluster runtime while libraries are installed

### Step 3: Import and Run the Extraction Notebook

1. **Import the notebook** into your Databricks workspace:
   - Navigate to your Databricks workspace
   - Go to **Workspace** → **Import**
   - Select `data_extraction.ipynb` from this repository
   - Choose the destination folder

2. **Configure Neo4j connection**:

   Set the following environment variables in your cluster configuration or notebook:
   ```bash
   NEO4J_URL=neo4j+s://<your-neo4j-instance>
   NEO4J_USERNAME=<your-username>
   NEO4J_DATABASE=<your-database>
   PYTHON_REPO_URL=/Workspace/<path-to-python-modules>
   ```

3. **Store Neo4j password** in Databricks secrets:
   ```bash
   # Using Databricks CLI
   databricks secrets create-scope neo4j
   databricks secrets put-secret neo4j password
   ```

4. **Upload Python modules**:
   - Upload `neo4j_schemas.py` to your Databricks workspace
   - Upload `databricks_constants.py` to your Databricks workspace
   - Update `PYTHON_REPO_URL` to point to the uploaded location

5. **Attach and run the notebook**:
   - Attach the notebook to the cluster created in Step 2
   - Verify both libraries are installed and cluster is running
   - Run all cells to extract data from Neo4j
   - Verify that 14 tables are created (7 nodes + 7 relationships)

Expected output:
```
Total Tables Created: 7
Total Records Extracted: <your-count>
Catalog Location: retail_investment.default
```

### Step 4: Create Unity Catalog Volume and Upload Profile Documents

Create a volume to store customer profiles and documents for the Knowledge Agent:

1. **Create a Unity Catalog Volume**:
   - Navigate to **Catalog** in your Databricks workspace
   - Select the `retail_investment` catalog
   - Click on the `default` schema
   - Click **Create** → **Volume**
   - Configure the volume:
     - **Name**: `retail_investment_volume`
     - **Volume Type**: Managed
     - **Comment** (optional): "Customer profiles and investment documents for knowledge agent"
   - Click **Create**

2. **Upload profile documents**:
   - Click on the newly created `retail_investment_volume`
   - Click **Upload to this volume**
   - Select all `.txt` files from the `data/profiles/` directory:
     ```
     bank_branch_pacific_coast_downtown.txt
     bank_profile_first_national_trust.txt
     company_analysis_techcore_solutions.txt
     company_quarterly_report_global_finance.txt
     customer_profile_james_anderson.txt
     customer_profile_maria_rodriguez.txt
     customer_profile_robert_chen.txt
     investment_strategy_guide_moderate_risk.txt
     market_analysis_technology_sector.txt
     real_estate_investment_guide.txt
     regulatory_compliance_banking_2023.txt
     renewable_energy_investment_trends.txt
     retail_investment_disruption_banking_industry.txt
     retirement_planning_strategies.txt
     ```
   - Click **Upload**
   - Wait for all files to upload successfully

3. **Verify the upload**:
   - You should see all 14 `.txt` files in the volume
   - The volume path will be: `/Volumes/retail_investment/default/retail_investment_volume/`
   - This path will be used when creating the Knowledge Agent

4. **Set permissions** (if needed):
   - Grant READ access to users who will use the Knowledge Agent
   ```sql
   GRANT READ VOLUME ON VOLUME retail_investment.default.retail_investment_volume TO `<your-users-or-groups>`;
   ```

### Step 5: Create a Databricks Genie

Once the lakehouse is created, set up a Genie to query the structured data:

1. **Navigate to Genie**:
   - In your Databricks workspace, go to **AI/BI** → **Genie**
   - Click **Create Genie Space**

2. **Configure the Genie**:
   - **Name**: "Retail Investment Data Assistant"
   - **Description**: "Query customer accounts, portfolios, and investment positions"
   - **Data Source**: Select `retail_investment.default`
   - **Tables**: Include all 14 tables (7 node + 7 relationship tables)

3. **Add business context** (optional but recommended):
   - Provide table descriptions
   - Define common metrics (total portfolio value, customer count, etc.)
   - Add sample questions:
     - "What are the top 10 customers by account balance?"
     - "Show me all technology stock positions"
     - "Which customers have high risk profiles but conservative portfolios?"

4. **Test the Genie**:
   ```
   Example query: "Show me customers with investment accounts and their total portfolio values"
   ```

### Step 6: Create a Knowledge Agent

Create a Knowledge Agent to analyze customer profiles and documents from the Unity Catalog Volume:

1. **Navigate to Knowledge Agents**:
   - Go to **AI/BI** → **Agents** → **Create Agent**
   - Select **Knowledge Agent**

2. **Connect to the Unity Catalog Volume**:
   - In the **Data Source** section, select **Unity Catalog Volume**
   - Browse to: `retail_investment.default.retail_investment_volume`
   - Or enter the path: `/Volumes/retail_investment/default/retail_investment_volume/`
   - The agent will automatically index all 14 `.txt` files in the volume:
     - Customer profiles (3 files)
     - Bank and branch profiles (2 files)
     - Company analyses (2 files)
     - Investment and market research (7 files)

3. **Configure the agent**:
   - **Name**: "Customer Insights Knowledge Agent"
   - **Description**: "Analyze customer profiles and investment documents"
   - **Instructions**: "Extract customer preferences, investment goals, risk tolerance, and interests from profile documents"

4. **Test the Knowledge Agent**:
   ```
   Example query: "What investment interests does James Anderson have that aren't reflected in his current portfolio?"
   ```

### Step 7: Create a Multi-Agent System

Combine both agents into a unified system:

1. **Create a new Agent**:
   - Go to **AI/BI** → **Agents** → **Create Agent**
   - Select **Multi-Agent**

2. **Add agents**:
   - **Agent 1**: Retail Investment Data Assistant (Genie)
     - Role: "Query structured customer, account, and portfolio data"
   - **Agent 2**: Customer Insights Knowledge Agent
     - Role: "Analyze unstructured customer profiles and documents"

3. **Configure orchestration**:
   - **Name**: "Retail Investment Intelligence System"
   - **Description**: "Comprehensive customer and portfolio analysis combining structured data and unstructured insights"
   - **Instructions**:
     ```
     You are an intelligent investment analysis system. Use the Genie agent to query
     structured data about customers, accounts, and portfolios. Use the Knowledge Agent
     to analyze customer profiles and documents. Your goal is to:

     1. Identify gaps between customer interests (from profiles) and actual investments
     2. Find data quality issues where profile information isn't captured in structured data
     3. Discover cross-sell opportunities based on customer insights
     4. Provide comprehensive customer analysis combining both data sources
     ```

4. **Test the Multi-Agent System**:
   ```
   Example queries:
   - "Find customers interested in renewable energy stocks and show me their current holdings"
   - "Which customers have risk profiles that don't match their portfolio composition?"
   - "What information exists in customer profiles that isn't captured in the structured database?"
   ```

## Project Structure

```
neo4j-databricks-demo/
├── README.md                           # This file
├── data_extraction.ipynb               # Main extraction notebook
├── neo4j_schemas.py                    # Spark schema definitions
├── databricks_constants.py             # Unity Catalog table names
├── neo4j_importer_model_financial_demo.json  # Neo4j data model
├── data/
│   ├── csv/                           # Source CSV files
│   │   ├── accounts.csv
│   │   ├── banks.csv
│   │   ├── companies.csv
│   │   ├── customers.csv
│   │   ├── portfolio_holdings.csv
│   │   ├── stocks.csv
│   │   └── transactions.csv
│   ├── profiles/                      # Customer profiles and documents (14 files)
│   │   ├── customer_profile_*.txt     # Customer profile documents
│   │   ├── bank_*.txt                 # Bank and branch profiles
│   │   ├── company_*.txt              # Company analyses
│   │   ├── market_*.txt               # Market research
│   │   ├── investment_*.txt           # Investment guides
│   │   ├── regulatory_*.txt           # Compliance documents
│   │   └── retail_investment_*.txt    # Industry insights
│   └── html/                          # HTML versions of documents
└── .gitignore                         # Git ignore file
```

### Databricks Resources Created

After completing the setup, the following resources will exist in your Databricks workspace:

**Unity Catalog**:
```
retail_investment/                                    # Catalog
├── default/                                         # Schema
│   ├── retail_investment_volume/                   # Volume (14 .txt files)
│   ├── neo4j_customer                              # Node table
│   ├── neo4j_bank                                  # Node table
│   ├── neo4j_account                               # Node table
│   ├── neo4j_company                               # Node table
│   ├── neo4j_stock                                 # Node table
│   ├── neo4j_position                              # Node table
│   ├── neo4j_transaction                           # Node table
│   ├── neo4j_has_account                           # Relationship table
│   ├── neo4j_at_bank                               # Relationship table
│   ├── neo4j_of_company                            # Relationship table
│   ├── neo4j_performs                              # Relationship table
│   ├── neo4j_benefits_to                           # Relationship table
│   ├── neo4j_has_position                          # Relationship table
│   └── neo4j_of_security                           # Relationship table
```

## Data Flow

```
┌─────────────┐                    ┌──────────────────┐
│   Neo4j    │                    │  Local Files     │
│  Graph DB  │                    │  data/profiles/  │
└──────┬──────┘                    └────────┬─────────┘
       │                                    │
       │ Neo4j Spark Connector              │ Upload
       │ (data_extraction.ipynb)            │
       │                                    │
       ▼                                    ▼
┌────────────────────────────────────────────────────────┐
│  Databricks Unity Catalog                              │
│  retail_investment.default                             │
│                                                        │
│  Volume:                     Tables (14):              │
│  ┌──────────────────────┐   ┌────────────────────┐    │
│  │ retail_investment_   │   │ Node Tables (7):   │    │
│  │ volume/              │   │ - neo4j_customer   │    │
│  │ - 14 .txt files      │   │ - neo4j_bank       │    │
│  │   (profiles, docs)   │   │ - neo4j_account    │    │
│  └──────────────────────┘   │ - neo4j_company    │    │
│                              │ - neo4j_stock      │    │
│                              │ - neo4j_position   │    │
│                              │ - neo4j_transaction│    │
│                              │                    │    │
│                              │ Relationship (7):  │    │
│                              │ - neo4j_has_account│    │
│                              │ - neo4j_at_bank    │    │
│                              │ - neo4j_of_company │    │
│                              │ - neo4j_performs   │    │
│                              │ - neo4j_benefits_to│    │
│                              │ - neo4j_has_position│   │
│                              │ - neo4j_of_security│    │
│                              └────────────────────┘    │
└────────┬───────────────────────────┬───────────────────┘
         │                           │
         │                           │
         ▼                           ▼
┌────────────────────────────────────────────────────────┐
│  Multi-Agent AI System                                 │
│                                                        │
│  ┌────────────────────┐       ┌──────────────────┐    │
│  │ Genie Agent        │       │ Knowledge Agent  │    │
│  │ (Structured Data)  │       │ (Unstructured)   │    │
│  │                    │       │                  │    │
│  │ Data Source:       │       │ Data Source:     │    │
│  │ - Delta Tables     │       │ - UC Volume      │    │
│  │                    │       │                  │    │
│  │ Queries:           │       │ Analyzes:        │    │
│  │ - Accounts         │       │ - Customer       │    │
│  │ - Portfolios       │       │   Profiles       │    │
│  │ - Transactions     │       │ - Investment     │    │
│  │ - Stock Holdings   │       │   Documents      │    │
│  └──────────┬─────────┘       └─────────┬────────┘    │
│             │                           │             │
│             └───────────┬───────────────┘             │
│                         │                             │
│              ┌──────────▼──────────┐                  │
│              │   Orchestrator      │                  │
│              │  (Multi-Agent)      │                  │
│              │                     │                  │
│              │  Combines insights  │                  │
│              │  from both sources  │                  │
│              └─────────────────────┘                  │
└────────────────────────────────────────────────────────┘
```

## Example Use Cases

### 1. Gap Analysis
**Question**: "Find customers who express interest in renewable energy in their profiles but don't have any renewable energy stocks in their portfolios"

The multi-agent system will:
1. Use Knowledge Agent to find customers mentioning renewable energy interests
2. Use Genie to check their current stock holdings
3. Identify the gap and suggest potential investment opportunities

### 2. Risk Profile Mismatch
**Question**: "Which customers have 'aggressive' risk profiles but conservative portfolio compositions?"

The system will:
1. Query structured data for risk profile and portfolio composition
2. Analyze profile documents for narrative risk tolerance
3. Flag mismatches for advisor review

### 3. Data Quality Improvement
**Question**: "What customer information exists in profiles that isn't captured in the database?"

The system will:
1. Extract structured fields from customer profiles
2. Compare with database schema and actual values
3. Report missing or inconsistent data

## Technical Details

### Neo4j Spark Connector Configuration

The notebook uses the optimized `labels` and `relationship` options for extraction:

```python
# Node extraction
df = spark.read \
    .format("org.neo4j.spark.DataSource") \
    .option("labels", node_label) \
    .load()

# Relationship extraction
df = spark.read \
    .format("org.neo4j.spark.DataSource") \
    .option("relationship", rel_type) \
    .option("relationship.source.labels", source_label) \
    .option("relationship.target.labels", dest_label) \
    .option("relationship.nodes.map", "false") \
    .load()
```

### Schema Design

All schemas are defined in `neo4j_schemas.py` with:
- Type-safe Spark schemas
- Business-meaningful column names
- Metadata tracking (neo4j_id, labels, ingestion timestamps)
- Platform-agnostic design (works with any Spark platform)

## Troubleshooting

### Cluster and Library Issues

**Problem**: Neo4j Spark Connector not working
- **Solution**: Verify cluster Access mode is set to "Dedicated (formerly: Single user)" - this is REQUIRED
- Check that the Maven library is installed: `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3`
- Ensure PyPI library is installed: `neo4j==6.0.2`
- Restart the cluster after installing libraries

**Problem**: Maven library installation fails
- **Solution**: Verify you're using the correct Spark version (3.x)
- Check that the library coordinates match your Databricks Runtime
- For Spark 3.x, use: `org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3`
- Try installing via cluster UI instead of API

**Problem**: "Access mode not supported" error
- **Solution**: Change cluster Access mode from "Shared" to "Dedicated"
- This requires recreating the cluster or changing the configuration
- Navigate to Compute → Edit Cluster → Access mode → Select "Dedicated"

### Connection Issues
- Verify Neo4j credentials in Databricks secrets
- Check network connectivity to Neo4j instance (test with `neo4j://` URL from notebook)
- Ensure Neo4j instance is running and accessible from Databricks
- Verify environment variables are set correctly (NEO4J_URL, NEO4J_USERNAME, NEO4J_DATABASE)

### Permission Issues
- Verify Unity Catalog permissions (`USE CATALOG`, `USE SCHEMA`, `CREATE TABLE`)
- Check workspace permissions for Genie and Agents (requires AI/BI workspace)
- Ensure proper IAM roles for cloud storage
- Verify secrets scope access (`neo4j` scope should be readable by your user)

### Data Extraction Failures
- Check Neo4j database availability (use Neo4j Browser to verify)
- Verify node labels and relationship types match schema definitions
- Review cluster logs for detailed error messages (Compute → Cluster → Event Log)
- Check for memory issues (increase cluster size if needed)
- Verify PYTHON_REPO_URL points to correct location of Python modules

### Volume and Knowledge Agent Issues

**Problem**: Cannot create volume
- **Solution**: Verify you have CREATE VOLUME permissions on the schema
- Check that Unity Catalog is enabled in your workspace
- Ensure the catalog and schema exist before creating the volume

**Problem**: Files not appearing in Knowledge Agent
- **Solution**: Verify files were uploaded to the correct volume path
- Check that the volume path is: `/Volumes/retail_investment/default/retail_investment_volume/`
- Ensure all 14 `.txt` files are present in the volume
- Try re-indexing the Knowledge Agent if files were added after agent creation

**Problem**: Knowledge Agent cannot access volume
- **Solution**: Grant READ VOLUME permissions:
  ```sql
  GRANT READ VOLUME ON VOLUME retail_investment.default.retail_investment_volume TO `<user-or-group>`;
  ```
- Verify the agent configuration points to the correct volume path
- Check that the volume type is "Managed" (not External)

## Next Steps

After completing the setup:

1. **Explore Genie Queries**: Test various analytical questions about customers, portfolios, and transactions
2. **Analyze Knowledge Agent**: Review profile extraction quality and document indexing
3. **Test Multi-Agent**: Try complex queries requiring both data sources (structured + unstructured)
4. **Add More Documents**: Upload additional customer profiles, market research, or compliance documents to the volume
5. **Customize Agents**: Add business-specific instructions and context to improve response quality
6. **Build Dashboards**: Create AI/BI dashboards using the lakehouse data
7. **Schedule Refreshes**: Set up periodic data extraction from Neo4j to keep lakehouse current
8. **Monitor Usage**: Track which queries are most common and refine agent configurations accordingly

## Contributing

This is a demonstration project. To adapt for your use case:

1. **Modify Graph Schema**: Update `neo4j_schemas.py` to match your Neo4j graph model
2. **Update Catalog Names**: Change `databricks_constants.py` to use your catalog/schema names
3. **Customize Agents**: Tailor agent instructions for your business domain and use cases
4. **Add Your Documents**: Upload your own customer profiles, documents, and knowledge base to the Unity Catalog volume
5. **Extend the Data Model**: Add additional node types, relationships, or document types as needed

## License

This project is provided as-is for demonstration purposes.

## Quick Reference

### Required Library Versions

**Maven (Neo4j Spark Connector)**:
```
org.neo4j:neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3
```

**PyPI (Neo4j Python Driver)**:
```
neo4j==6.0.2
```

### Cluster Configuration

- **Access Mode**: Dedicated (formerly: Single user) ⚠️ REQUIRED
- **Databricks Runtime**: 13.3 LTS or higher (Spark 3.x)
- **Cluster Mode**: Standard
- **Recommended Workers**: 2-4 (adjust based on data volume)

### Environment Variables

```bash
NEO4J_URL=neo4j+s://<your-neo4j-instance>
NEO4J_USERNAME=<your-username>
NEO4J_DATABASE=<your-database>
PYTHON_REPO_URL=/Workspace/<path-to-python-modules>
```

### Databricks Secrets

```bash
# Create secrets scope
databricks secrets create-scope neo4j

# Store Neo4j password
databricks secrets put-secret neo4j password
```

### Unity Catalog Resources

**Volume Path**:
```
/Volumes/retail_investment/default/retail_investment_volume/
```

**Catalog and Schema**:
```sql
-- Catalog
retail_investment

-- Schema
retail_investment.default

-- Volume
retail_investment.default.retail_investment_volume
```

**Files in Volume**: 14 `.txt` files from `data/profiles/`

## Support

For issues related to:
- **Neo4j Spark Connector**: See [Neo4j Spark Connector Documentation](https://neo4j.com/docs/spark/current/)
- **Databricks Genie**: See [Databricks Genie Documentation](https://docs.databricks.com/en/genie/index.html)
- **Databricks Knowledge Agents**: See [AI Agents Documentation](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)
- **Unity Catalog**: See [Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- **Unity Catalog Volumes**: See [Volumes Documentation](https://docs.databricks.com/en/connect/unity-catalog/volumes.html)
- **Databricks Clusters**: See [Cluster Configuration Documentation](https://docs.databricks.com/en/compute/configure.html)
