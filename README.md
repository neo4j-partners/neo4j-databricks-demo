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
- **Neo4j Database** (AuraDB or Neo4j Desktop instance)
- **Databricks Genie** access (for creating the query agent)
- **Databricks AI/BI** workspace (for knowledge agents)
- Proper **credentials** for Neo4j (username and password)
- **Databricks CLI** installed (optional, for managing secrets)

## Setup Instructions

### Step 0: Setup Neo4j Database with Sample Data

Before extracting data to Databricks, you need to set up your Neo4j database with the retail investment graph data:

1. **Follow the complete setup instructions in `DATA_IMPORT.md`**
   - This guide provides detailed instructions for importing the graph schema and sample data
   - You can use either Neo4j AuraDB (cloud) or Neo4j Desktop (local)

2. **Quick summary of the import process**:
   - Create a Neo4j AuraDB instance or start Neo4j Desktop
   - Open the Neo4j Data Importer
   - Load the schema definition: `neo4j_importer_model_financial_demo.json`
   - Upload all CSV files from `data/csv/` directory
   - Run the import to create the graph database
   - Verify the import using the provided Cypher queries

3. **What gets imported**:
   - **7 Node Types**: Customer, Bank, Account, Company, Stock, Position, Transaction
   - **7 Relationship Types**: HAS_ACCOUNT, AT_BANK, OF_COMPANY, PERFORMS, BENEFITS_TO, HAS_POSITION, OF_SECURITY
   - **Sample Data**: 102 customers, 102 banks, 123 accounts, 102 companies, 102 stocks, 110 positions, 123 transactions

4. **Save your Neo4j connection details** for the next steps:
   - Neo4j URL (e.g., `neo4j+s://xxxxx.databases.neo4j.io`)
   - Username (usually `neo4j`)
   - Password
   - Database name (usually `neo4j`)

Once your Neo4j database is set up and verified, proceed to Step 1 to create the Databricks catalog.

### Step 1: Create Databricks Catalog and Schema

First, create the Unity Catalog namespace for the project:

```sql
-- Create the catalog
CREATE CATALOG IF NOT EXISTS retail_investment;

-- Create the retail_investment schema
CREATE SCHEMA IF NOT EXISTS retail_investment.retail_investment;

-- Grant appropriate permissions
GRANT USE CATALOG ON CATALOG retail_investment TO `<your-users-or-groups>`;
GRANT USE SCHEMA ON SCHEMA retail_investment.retail_investment TO `<your-users-or-groups>`;
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
   ```

3. **Store Neo4j password and url* in Databricks secrets:
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
Catalog Location: retail_investment.retail_investment
```

### Step 4: Create Unity Catalog Volume and Upload Profile Documents

Create a volume to store customer profiles and documents for the Knowledge Agent:

1. **Create a Unity Catalog Volume**:
   - Navigate to **Catalog** in your Databricks workspace
   - Select the `retail_investment` catalog
   - Click on the `retail_investment` schema
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
   - The volume path will be: `/Volumes/retail_investment/retail_investment/retail_investment_volume/`
   - This path will be used when creating the Knowledge Agent

4. **Set permissions** (if needed):
   - Grant READ access to users who will use the Knowledge Agent
   ```sql
   GRANT READ VOLUME ON VOLUME retail_investment.retail_investment.retail_investment_volume TO `<your-users-or-groups>`;
   ```

### Step 5: Create a Databricks Genie

Once the lakehouse is created, set up a Genie to query the structured data:

1. **Navigate to Genie**:
   - In your Databricks workspace, go to **AI/BI** → **Genie**
   - Click **Create Genie Space**

2. **Configure the Genie**:
   - **Name**: "Retail Investment Data Assistant"
   - **Description**: "Query customer accounts, portfolios, and investment positions"
   - **Data Source**: Select `retail_investment.retail_investment`
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
   - Browse to: `retail_investment.retail_investment.retail_investment_volume`
   - Or enter the path: `/Volumes/retail_investment/retail_investment/retail_investment_volume/`
   - The agent will automatically index all 14 `.txt` files in the volume:
     - Customer profiles (3 files)
     - Bank and branch profiles (2 files)
     - Company analyses (2 files)
     - Investment and market research (7 files)

3. **Configure the agent**:
   - **Name**: "Customer Insights Knowledge Agent"
   - **Description and Instructions**: See the detailed configuration in `KNOWLEDGE_AGENT_DESCRIPTION.md`
     - Copy the "Data Source Description" section into the agent's **Description** field
     - Copy the "Agent Instructions" section into the agent's **Instructions** field
   - These detailed descriptions help the agent understand the full scope of content and when to use this data source

4. **Test the Knowledge Agent**:
   ```
   Example queries:
   - "What investment interests does James Anderson have that aren't reflected in his current portfolio?"
   - "Describe Maria Rodriguez's risk tolerance and family circumstances that influence her investment decisions"
   - "What are Robert Chen's long-term financial goals and how aggressive is his investment approach?"
   - "What renewable energy investment opportunities are discussed in the research documents?"
   - "Compare the investment philosophies of First National Trust and Pacific Coast Bank"
   ```

### Step 7: Create a Multi-Agent Supervisor

Combine both agents into a unified system using the Multi-Agent Supervisor:

1. **Create a Multi-Agent Supervisor**:
   - In your Databricks workspace, navigate to the **Multi-Agent Supervisor** interface
   - Click **Build** to create a new multi-agent system

2. **Add agents**:
   - **Agent 1**: Retail Investment Data Assistant (Genie)
     - This agent queries structured lakehouse data
   - **Agent 2**: Customer Insights Knowledge Agent
     - This agent analyzes unstructured profiles and research documents

3. **Configure the supervisor**:
   - **Name**: "Retail Investment Intelligence System"
   - **Description**: Use the description from `KNOWLEDGE_AGENT_DESCRIPTION.md` under "Multi-Agent Supervisor Description"
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
├── retail_investment/                               # Schema
│   ├── retail_investment_volume/                   # Volume (14 .txt files)
│   ├── customer                                    # Node table
│   ├── bank                                        # Node table
│   ├── account                                     # Node table
│   ├── company                                     # Node table
│   ├── stock                                       # Node table
│   ├── position                                    # Node table
│   ├── transaction                                 # Node table
│   ├── has_account                                 # Relationship table
│   ├── at_bank                                     # Relationship table
│   ├── of_company                                  # Relationship table
│   ├── performs                                    # Relationship table
│   ├── benefits_to                                 # Relationship table
│   ├── has_position                                # Relationship table
│   └── of_security                                 # Relationship table
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
│  retail_investment.retail_investment                   │
│                                                        │
│  Volume:                     Tables (14):              │
│  ┌──────────────────────┐   ┌────────────────────┐    │
│  │ retail_investment_   │   │ Node Tables (7):   │    │
│  │ volume/              │   │ - customer         │    │
│  │ - 14 .txt files      │   │ - bank             │    │
│  │   (profiles, docs)   │   │ - account          │    │
│  └──────────────────────┘   │ - company          │    │
│                              │ - stock            │    │
│                              │ - position         │    │
│                              │ - transaction      │    │
│                              │                    │    │
│                              │ Relationship (7):  │    │
│                              │ - has_account      │    │
│                              │ - at_bank          │    │
│                              │ - of_company       │    │
│                              │ - performs         │    │
│                              │ - benefits_to      │    │
│                              │ - has_position     │    │
│                              │ - of_security      │    │
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

## Example Use Cases and Sample Queries

### 1. Gap Analysis
**Question**: "Find customers who express interest in renewable energy in their profiles but don't have any renewable energy stocks in their portfolios"

The multi-agent system will:
1. Use Knowledge Agent to find customers mentioning renewable energy interests
2. Use Genie to check their current stock holdings
3. Identify the gap and suggest potential investment opportunities

**Sample Natural Language Queries**:
- "Show me customers interested in renewable energy and tell me if they own any renewable energy stocks"
- "Which customers have expressed interest in ESG investing but don't have ESG funds in their portfolios?"
- "Find customers who mentioned real estate investing in their profiles and show me their current investment positions"
- "Are there any customers talking about technology stocks in their profiles who don't actually own any?"

### 2. Risk Profile Mismatch
**Question**: "Which customers have 'aggressive' risk profiles but conservative portfolio compositions?"

The system will:
1. Query structured data for risk profile and portfolio composition
2. Analyze profile documents for narrative risk tolerance
3. Flag mismatches for advisor review

**Sample Natural Language Queries**:
- "Show me customers with aggressive risk profiles and analyze if their portfolios match their risk tolerance"
- "Which conservative investors have portfolios that are too aggressive for their stated preferences?"
- "Find mismatches between customer risk profiles in the database and their investment behavior"
- "Are there customers whose portfolio allocation doesn't align with their stated risk tolerance from their profiles?"

### 3. Data Quality Improvement
**Question**: "What customer information exists in profiles that isn't captured in the database?"

The system will:
1. Extract structured fields from customer profiles
2. Compare with database schema and actual values
3. Report missing or inconsistent data

**Sample Natural Language Queries**:
- "What personal information appears in customer profile documents that isn't in the structured database?"
- "Find data quality gaps between customer profiles and account records"
- "Are there investment preferences mentioned in profiles that aren't reflected in account settings?"
- "Compare the structured customer data with profile narratives and identify missing fields"

### 4. Customer Intelligence and Insights

**Sample Natural Language Queries**:
- "Tell me everything about customer C0001 - their accounts, holdings, transaction patterns, and personal preferences"
- "What are the top investment interests mentioned across all customer profiles?"
- "Show me customers in their 30s with high income and tell me about their investment strategies"
- "Which banks have the most accounts and what types of customers do they serve?"
- "Find customers who are planning for retirement and show me their current portfolio allocation"

### 5. Portfolio and Holdings Analysis

**Sample Natural Language Queries**:
- "What are the most popular stocks held by customers and how are they performing?"
- "Show me the total portfolio value for each customer and rank them"
- "Which customers have the most diversified portfolios across different sectors?"
- "Find all customers holding technology stocks and show their total tech exposure"
- "What is the average portfolio size by customer risk profile?"

### 6. Transaction and Account Activity

**Sample Natural Language Queries**:
- "Show me recent large transactions over $1000 and the accounts involved"
- "Which customers have the most active trading patterns?"
- "Find customers who frequently transfer money between accounts"
- "What are the most common transaction types in the system?"
- "Show me account balances and transaction activity for customers with investment accounts"

### 7. Market Research and Investment Opportunities

**Sample Natural Language Queries**:
- "What does the market research say about renewable energy investment opportunities?"
- "Summarize the technology sector analysis and current trends"
- "What investment strategies are recommended for moderate risk investors?"
- "Tell me about real estate investment options mentioned in the research documents"
- "What are the key findings from the FinTech disruption report?"

### 8. Banking Relationship Analysis

**Sample Natural Language Queries**:
- "Which customers bank with First National Trust and what services do they use?"
- "Compare the customer base across different banks"
- "What are the capabilities of Pacific Coast Bank's downtown branch?"
- "Show me customers with accounts at multiple banks"
- "What is the total assets under management by bank?"

### 9. Cross-Sell and Personalization Opportunities

**Sample Natural Language Queries**:
- "Find customers interested in retirement planning who don't have sufficient retirement savings"
- "Which high-income customers might be good candidates for wealth management services?"
- "Show me customers with large cash balances who could benefit from investment accounts"
- "Find customers interested in specific sectors and recommend stocks they should consider"
- "Which customers have expressed interest in financial literacy workshops?"

### 10. Compliance and Regulatory Insights

**Sample Natural Language Queries**:
- "What are the key compliance requirements for banks according to the regulatory documents?"
- "Summarize the anti-money laundering regulations mentioned in the knowledge base"
- "What capital requirements do banks need to maintain?"
- "Tell me about consumer protection regulations affecting our banking operations"

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
- Check that the volume path is: `/Volumes/retail_investment/retail_investment/retail_investment_volume/`
- Ensure all 14 `.txt` files are present in the volume
- Try re-indexing the Knowledge Agent if files were added after agent creation

**Problem**: Knowledge Agent cannot access volume
- **Solution**: Grant READ VOLUME permissions:
  ```sql
  GRANT READ VOLUME ON VOLUME retail_investment.retail_investment.retail_investment_volume TO `<user-or-group>`;
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


### Databricks Secrets

```bash
# Create secrets scope
databricks secrets create-scope neo4j

# Store Neo4j password
databricks secrets put-secret neo4j password

# Store Neo4j url - neo4j+s://<your-neo4j-instance>
databricks secrets put-secret neo4j url

```

### Unity Catalog Resources

**Volume Path**:
```
/Volumes/retail_investment/retail_investment/retail_investment_volume/
```

**Catalog and Schema**:
```sql
-- Catalog
retail_investment

-- Schema
retail_investment.retail_investment

-- Volume
retail_investment.retail_investment.retail_investment_volume
```

**Files in Volume**: 14 `.txt` files from `data/profiles/`

## Advanced Multi-Agent Questions

These sophisticated questions demonstrate the full power of the multi-agent system by combining structured data analysis with unstructured document insights. These queries require coordination between the Genie agent (querying lakehouse tables) and the Knowledge Agent (analyzing customer profiles and research documents).

### Personalized Investment Opportunity Discovery

1. **"James Anderson has expressed interest in renewable energy stocks. What renewable energy companies are mentioned in our research documents, and does he currently own any of them? If not, which ones align with his moderate risk profile?"**
   - Combines: Customer profile analysis + current portfolio holdings + investment research + risk alignment

2. **"Identify customers who have mentioned interest in real estate investing in their profiles. Show me their current account balances and investment positions. Do any of them have sufficient capital to pursue real estate investments based on the investment guide recommendations?"**
   - Combines: Profile text mining + account balance data + investment position analysis + research document recommendations

3. **"Robert Chen is an aggressive investor interested in AI and autonomous vehicles. Based on the technology sector analysis, what AI and autonomous vehicle stocks are discussed in our research? Does Robert's current portfolio include these stocks, and what percentage of his portfolio do they represent?"**
   - Combines: Customer preferences + technology research analysis + current holdings + portfolio allocation calculations

4. **"Maria Rodriguez has expressed interest in ESG and socially responsible investing. Identify which companies in her current portfolio might not align with ESG principles, and suggest alternative stocks from our research documents that would better match her values while maintaining her conservative risk profile."**
   - Combines: Customer values from profile + current portfolio analysis + ESG research insights + risk profile matching

### Portfolio-Profile Alignment Analysis

5. **"Find all customers with 'aggressive' risk profiles and analyze their actual portfolio compositions. Cross-reference with their profile narratives about risk tolerance. Identify any misalignments where portfolios are too conservative for stated preferences."**
   - Combines: Structured risk profile data + portfolio holdings analysis + unstructured risk tolerance narratives

6. **"Which customers have mentioned specific investment interests (renewable energy, technology, real estate, healthcare) in their profiles that are completely absent from their current portfolio holdings? Rank by account balance to prioritize high-value opportunities."**
   - Combines: Text analysis of profiles + portfolio gap analysis + account value ranking

7. **"Analyze the three customer profiles (James, Maria, Robert) and compare their stated investment philosophies with their actual transaction patterns and portfolio compositions. Highlight inconsistencies and opportunities for advisor outreach."**
   - Combines: Deep profile analysis + transaction history + portfolio composition + behavioral analysis

### Research-Driven Customer Targeting

8. **"The renewable energy research document discusses Solar Energy Systems (SOEN) and Renewable Power Inc (RPOW). Which customers in our database have expressed interest in solar or renewable energy? Of those, who currently doesn't own these stocks and has sufficient account balance to invest?"**
   - Combines: Research document analysis + profile text search + portfolio absence detection + account balance filtering

9. **"According to the technology sector analysis, AI and cybersecurity are key growth themes. Identify customers working in technology fields (from their profiles) who might have professional insight into these trends. Do their portfolios reflect this knowledge?"**
   - Combines: Profile occupation analysis + research themes + portfolio positioning

10. **"The real estate investment guide discusses crowdfunding platforms requiring $5,000-$10,000 minimum investments. Which customers have mentioned real estate interest in their profiles and have checking or savings account balances exceeding $10,000 but no current real estate exposure?"**
    - Combines: Research document details + profile interests + account balance analysis + portfolio gap

### Life Stage and Financial Goal Analysis

11. **"Maria Rodriguez is a single mother planning for college expenses and retirement. Based on her age, income from her profile, and current investment positions, is she on track to meet the retirement planning strategies outlined in our research documents? What gaps exist?"**
    - Combines: Demographic data + income analysis + portfolio analysis + retirement planning benchmarks

12. **"Robert Chen aims to build a $5 million portfolio by age 40. Based on his current portfolio value, age, and stated aggressive investment strategy, calculate his required annual return. Is this realistic given the technology sector analysis and his current holdings?"**
    - Combines: Profile goals + current portfolio value + demographic data + sector return expectations

13. **"Identify customers in their 30s and 40s (peak earning years) who have mentioned retirement planning in their profiles. Analyze their current investment account balances and compare to the retirement planning strategy recommendations for their age group."**
    - Combines: Age filtering + profile text analysis + account balance analysis + retirement research benchmarks

### Banking Relationship and Service Opportunities

14. **"First National Trust and Pacific Coast Bank are profiled in our documents. Show me all customers banking at these institutions, their total account balances, and cross-reference their profiles for mentioned service preferences (digital vs. in-person). Are we delivering services aligned with their preferences?"**
    - Combines: Bank relationship data + account aggregation + profile service preferences + institutional capabilities

15. **"Which customers have accounts at multiple banks according to our structured data? Analyze their profiles to understand why they maintain multiple relationships. Are there consolidation opportunities or service gaps we need to address?"**
    - Combines: Multi-bank relationship detection + profile analysis for banking satisfaction + service gap identification

16. **"The bank profiles mention wealth management services. Identify high-net-worth customers (based on total account balances and investment positions) who haven't been mentioned as using wealth management services in their profiles. Calculate total assets under management potential."**
    - Combines: Net worth calculation from positions + profile service usage analysis + market opportunity sizing

### Regulatory and Compliance Intelligence

17. **"According to the regulatory compliance documents, what are the key AML (anti-money laundering) monitoring requirements? Identify customers with transaction patterns showing frequent large transfers between accounts. Cross-reference their profiles for legitimate business reasons that might explain this activity."**
    - Combines: Regulatory requirements + transaction pattern analysis + profile business context

18. **"The compliance documents discuss customer suitability requirements. For each customer, compare their stated risk profile in structured data with the risk tolerance narratives in their profile documents. Flag any customers where documentation doesn't align and might need updated suitability assessments."**
    - Combines: Structured risk data + unstructured risk narratives + compliance requirement matching

### Sector Rotation and Market Timing Opportunities

19. **"The technology sector analysis mentions valuation concerns with median P/E of 29.4 vs. historical 22.6. Identify customers heavily concentrated in technology stocks (>50% of portfolio). Do their profiles indicate they understand these risks, or should advisors reach out with rebalancing recommendations?"**
    - Combines: Sector concentration calculations + valuation context from research + profile financial sophistication assessment

20. **"Based on the market research documents, which investment themes are emerging (AI, renewable energy, cybersecurity, etc.)? For each theme, identify the top 3 customers by account balance who have expressed interest in these themes but have less than 10% portfolio allocation to them."**
    - Combines: Research theme extraction + profile interest matching + portfolio allocation analysis + customer ranking

### Data Quality and Enrichment Opportunities

21. **"Compare all structured customer data fields (age, income, risk profile, credit score) with information mentioned in the customer profile narratives. Create a data quality report showing which fields exist in profiles but are missing or inconsistent in the structured database."**
    - Combines: Structured data completeness + unstructured data extraction + data quality assessment

22. **"The customer profiles mention specific stock holdings and investment interests. Compare these with actual position records in the database. Identify any stocks mentioned in profiles that don't appear in current positions (potential closed positions or future interests)."**
    - Combines: Profile text stock extraction + position table comparison + temporal analysis

23. **"Analyze customer service notes and preferences mentioned in profiles (digital banking, in-person meetings, advisory preferences). Create a service preference matrix showing what we know from profiles vs. what's captured in structured customer service fields."**
    - Combines: Profile text mining + structured service data + preference mapping

### Cross-Sell and Product Penetration

24. **"Identify customers who have both checking and savings accounts but no investment accounts. Analyze their profiles for income levels, savings patterns, and any mentioned investment interests. Rank by cross-sell potential based on account balances and profile signals."**
    - Combines: Account type analysis + profile income/interest extraction + savings pattern + opportunity scoring

25. **"The investment strategy guides discuss different approaches for conservative, moderate, and aggressive investors. For each risk category, identify customers whose profile narratives match that category. Do they have the appropriate account types and services for their investment approach?"**
    - Combines: Research strategy recommendations + profile classification + product penetration analysis

### Competitive Intelligence and Customer Retention

26. **"James Anderson values digital banking and uses mobile apps frequently. Pacific Coast Bank is profiled as having strong digital capabilities. Does James bank with them? If not, and given his service preferences, is there a retention risk we should address?"**
    - Combines: Customer preferences + institutional capabilities + relationship mapping + retention risk

27. **"According to the bank profiles, First National Trust emphasizes personalized service while Pacific Coast Bank focuses on digital innovation. Match our customers to the bank that best fits their service preferences from their profiles. Identify any customers banking with a mismatched institution."**
    - Combines: Institutional positioning + customer service preferences + relationship alignment + satisfaction prediction

### Behavioral Finance and Advisory Opportunities

28. **"Robert Chen trades 8-10 times per month according to his profile. Analyze his actual transaction history to verify this trading frequency. Calculate trading costs and compare his returns to a buy-and-hold strategy. Should advisors discuss behavioral finance concepts with him?"**
    - Combines: Profile behavioral claims + transaction pattern analysis + performance calculation + advisory intervention identification

29. **"Maria Rodriguez maintains an emergency fund covering 6 months of expenses according to her profile. Based on her mentioned monthly expenses and current savings account balance, verify this claim. Is her emergency fund adequately sized based on financial planning best practices from our research?"**
    - Combines: Profile financial claims + account balance verification + research recommendations + planning adequacy

30. **"The investment strategy documents emphasize diversification. For each customer, calculate their portfolio diversification metrics (sector concentration, stock count, position sizing). Compare against diversification principles from the research. Identify customers who need rebalancing conversations."**
    - Combines: Portfolio diversification calculations + research best practices + risk assessment + advisory trigger

### Comprehensive Customer Intelligence Reports

31. **"Generate a complete financial intelligence report for customer C0001 (James Anderson) including: all account balances and holdings, transaction patterns, stated investment interests from his profile, gaps between interests and holdings, recommendations from research documents that match his profile, and next best actions for his advisor."**
    - Combines: Full structured data profile + complete document analysis + gap analysis + research matching + actionable recommendations

32. **"Create a market opportunity dashboard showing: total customers by risk profile, top investment interests mentioned across all profiles, current portfolio exposures by sector, gaps between interests and holdings, and total addressable assets for each investment theme from our research documents."**
    - Combines: Customer segmentation + aggregate profile analysis + portfolio analytics + gap quantification + market sizing

These questions showcase the multi-agent system's ability to deliver insights that would be impossible with either structured or unstructured data alone. They demonstrate practical use cases for financial advisors, relationship managers, and business analysts in retail investment banking.
