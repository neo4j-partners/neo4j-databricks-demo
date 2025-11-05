# Neo4j Data Import Instructions

## Overview

This directory contains a complete Neo4j graph schema definition and sample data for a **retail banking and investment portfolio** demonstration. The schema models customers, banks, accounts, companies, stocks, portfolio holdings, and financial transactions.

---

## Files Included

### Schema Definition
- **`neo4j_importer_model_financial_demo.json`**: Complete Neo4j Data Importer schema configuration

### Documentation
- **`SCHEMA_MODEL.md`**: Comprehensive schema design proposal with rationale and query patterns

### Sample Data (CSV)
Located in `demo_data/csv/`:
- `customers.csv` (102 records) - Customer profiles
- `banks.csv` (102 records) - Financial institutions
- `accounts.csv` (123 records) - Customer accounts
- `companies.csv` (102 records) - Publicly traded companies
- `stocks.csv` (102 records) - Stock market data
- `portfolio_holdings.csv` (110 records) - Investment positions
- `transactions.csv` (123 records) - Inter-account transfers

---

## Graph Schema Summary

### Node Types (7)

1. **Customer** - Individual banking customers
   - Key Property: `customerId`
   - Properties: demographics, financial profile, risk classification

2. **Bank** - Financial institutions
   - Key Property: `bankId`
   - Properties: name, type, assets, routing info

3. **Account** - Customer accounts (hub node)
   - Key Property: `accountId`
   - Properties: account type, balance, status, interest rate

4. **Company** - Publicly traded corporations
   - Key Property: `companyId`
   - Properties: corporate data, financials, industry/sector

5. **Stock** - Tradeable securities
   - Key Property: `stockId`
   - Properties: market data, pricing, performance metrics

6. **Transaction** - Financial transactions (as per Neo4j best practices)
   - Key Property: `transactionId`
   - Properties: amount, currency, date, time, type, status, description
   - Pattern: Account -[:PERFORMS]-> Transaction -[:BENEFITS_TO]-> Account

7. **Position** - Portfolio holdings
   - Key Property: `positionId`
   - Properties: shares, purchase price/date, current value, portfolio percentage
   - Pattern: Account -[:HAS_POSITION]-> Position -[:OF_SECURITY]-> Stock

### Relationship Types (7)

1. **HAS_ACCOUNT** - Customer → Account (ownership)
2. **AT_BANK** - Account → Bank (custody)
3. **OF_COMPANY** - Stock → Company (security issuer linkage)
4. **PERFORMS** - Account → Transaction (account initiates transaction)
5. **BENEFITS_TO** - Transaction → Account (account receives funds)
6. **HAS_POSITION** - Account → Position (account holds investment position)
7. **OF_SECURITY** - Position → Stock (position is of specific security)

---

## Import Using Neo4j Data Importer

### Prerequisites

1. **Neo4j AuraDB** or **Neo4j Desktop** instance running
2. **Neo4j Data Importer** access (available in Aura Console or via https://data-importer.graphapp.io/)
3. CSV files available locally or accessible via URL

### Step-by-Step Import Process

#### Option 1: Neo4j Aura Console (Recommended)

1. **Access Neo4j Aura Console**
   - Log in to https://console.neo4j.io/
   - Navigate to your AuraDB instance

2. **Open Data Importer**
   - Click on "Import" in the left sidebar
   - Select "Graph models" tab
   - Click "New graph model"

3. **Load Schema Definition**
   - Click the three dots next to "Run import"
   - Select "Open model"
   - Upload `neo4j_importer_model_financial_demo.json`

4. **Review Schema**
   - Verify the graph model displays correctly
   - Check node types: Customer, Bank, Account, Company, Stock
   - Check relationships: HAS_ACCOUNT, AT_BANK, HOLDS, OF_COMPANY, TRANSFERRED_TO

5. **Add Data Sources**
   - For each CSV file listed in the schema:
     - Click "Browse" next to the file name
     - Upload the corresponding CSV file from `demo_data/csv/`

   Upload order (doesn't matter, but recommended):
   ```
   1. customers.csv
   2. banks.csv
   3. companies.csv
   4. stocks.csv
   5. accounts.csv
   6. portfolio_holdings.csv
   7. transactions.csv
   ```

6. **Run Import**
   - Click "Run import" button
   - Wait for completion (should take 1-2 minutes for this dataset)
   - Review import summary for any errors

7. **Verify Import**
   - Open Neo4j Browser or Bloom
   - Run verification queries (see below)

---

#### Option 2: Neo4j Desktop with Data Importer Plugin

1. **Install Data Importer Plugin**
   - Open Neo4j Desktop
   - Go to your project
   - Click "Add Application"
   - Install "Neo4j Data Importer"

2. **Follow Same Steps as Option 1**
   - The interface is identical to the Aura version

---

## Verification Queries

After import, run these Cypher queries to verify the data loaded correctly:

### Check Node Counts

```cypher
// Count all nodes by label
MATCH (n)
RETURN labels(n)[0] AS label, COUNT(n) AS count
ORDER BY label;

// Expected results:
// Account: 123
// Bank: 102
// Company: 102
// Customer: 102
// Position: 110
// Stock: 102
// Transaction: 123
```

### Check Relationship Counts

```cypher
// Count all relationships by type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, COUNT(r) AS count
ORDER BY relationship_type;

// Expected results:
// AT_BANK: 123
// BENEFITS_TO: 123
// HAS_ACCOUNT: 123
// HAS_POSITION: 110
// OF_COMPANY: 102
// OF_SECURITY: 110
// PERFORMS: 123
```

### Sample Data Query

```cypher
// Show a customer's complete financial profile
MATCH (c:Customer {customerId: 'C0001'})-[:HAS_ACCOUNT]->(a:Account)
OPTIONAL MATCH (a)-[:AT_BANK]->(b:Bank)
OPTIONAL MATCH (a)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)-[:OF_COMPANY]->(co:Company)
RETURN
    c.firstName + ' ' + c.lastName AS customer_name,
    a.accountId AS account,
    a.accountType AS accountType,
    a.balance AS balance,
    b.name AS bank_name,
    co.name AS holding_company,
    s.ticker AS ticker,
    p.shares AS shares,
    p.currentValue AS holding_value
ORDER BY holding_value DESC;
```

### Graph Visualization

```cypher
// Visualize customer C0001's financial network
MATCH path = (c:Customer {customerId: 'C0001'})-[*1..3]-(connected)
RETURN path
LIMIT 50;
```

### Validate Transaction Relationships (PERFORMS and BENEFITS_TO)

```cypher
// Verify Transaction nodes are properly linked
MATCH (from:Account)-[:PERFORMS]->(t:Transaction)-[:BENEFITS_TO]->(to:Account)
RETURN
    from.accountId AS from_account,
    t.transactionId AS transaction_id,
    t.amount AS amount,
    t.transactionDate AS date,
    to.accountId AS to_account
ORDER BY t.transactionDate DESC
LIMIT 10;

// Count transactions by status
MATCH (t:Transaction)
RETURN t.status AS status, COUNT(t) AS count
ORDER BY count DESC;

// Find high-value transactions
MATCH (from:Account)-[:PERFORMS]->(t:Transaction)-[:BENEFITS_TO]->(to:Account)
WHERE t.amount > 1000
RETURN
    from.accountId AS sender,
    to.accountId AS recipient,
    t.amount AS amount,
    t.transactionDate AS date,
    t.description AS description
ORDER BY t.amount DESC
LIMIT 10;
```

### Validate Position Relationships (HAS_POSITION and OF_SECURITY)

```cypher
// Verify Position nodes are properly linked
MATCH (a:Account)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)
RETURN
    a.accountId AS account,
    p.positionId AS position_id,
    s.ticker AS ticker,
    p.shares AS shares,
    p.currentValue AS value,
    p.percentageOfPortfolio AS pct_portfolio
ORDER BY p.currentValue DESC
LIMIT 10;

// Find accounts with multiple positions
MATCH (a:Account)-[:HAS_POSITION]->(p:Position)
WITH a, COUNT(p) AS position_count
WHERE position_count > 1
RETURN
    a.accountId AS account,
    a.accountType AS type,
    position_count AS num_positions
ORDER BY position_count DESC
LIMIT 10;

// Stock diversification analysis
MATCH (a:Account)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)-[:OF_COMPANY]->(c:Company)
RETURN
    a.accountId AS account,
    COUNT(DISTINCT c.sector) AS num_sectors,
    COLLECT(DISTINCT c.sector) AS sectors,
    SUM(p.currentValue) AS total_portfolio_value
ORDER BY total_portfolio_value DESC
LIMIT 10;
```

### Validate Transaction Flow Patterns

```cypher
// Find accounts that both send and receive transactions
MATCH (a:Account)-[:PERFORMS]->(:Transaction)
WITH a
MATCH (a)<-[:BENEFITS_TO]-(:Transaction)
RETURN
    a.accountId AS account,
    a.accountType AS type,
    a.balance AS balance
LIMIT 10;

// Transaction network visualization (show money flow)
MATCH path = (from:Account)-[:PERFORMS]->(t:Transaction)-[:BENEFITS_TO]->(to:Account)
RETURN path
LIMIT 25;
```

---

## Common Use Cases and Queries

### 1. Portfolio Analysis

```cypher
// Calculate total portfolio value by customer
MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)-[:HAS_POSITION]->(p:Position)
RETURN
    c.customerId,
    c.firstName + ' ' + c.lastName AS customer_name,
    SUM(p.currentValue) AS total_portfolio_value
ORDER BY total_portfolio_value DESC
LIMIT 10;
```

### 2. Bank Exposure

```cypher
// Total assets under management by bank
MATCH (b:Bank)<-[:AT_BANK]-(a:Account)
RETURN
    b.name AS bank_name,
    b.bankType AS bankType,
    COUNT(DISTINCT a) AS num_accounts,
    SUM(a.balance) AS total_deposits
ORDER BY total_deposits DESC;
```

### 3. Stock Popularity

```cypher
// Most widely held stocks
MATCH (a:Account)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)-[:OF_COMPANY]->(c:Company)
RETURN
    c.name AS company_name,
    s.ticker AS ticker,
    COUNT(DISTINCT a) AS num_holders,
    SUM(p.shares) AS total_shares_held,
    SUM(p.currentValue) AS total_market_value
ORDER BY num_holders DESC
LIMIT 10;
```

### 4. Transaction Network Analysis

```cypher
// Find accounts with most outbound transactions
MATCH (a:Account)-[:PERFORMS]->(t:Transaction)
WITH a, COUNT(t) AS tx_count
ORDER BY tx_count DESC
LIMIT 10
MATCH (c:Customer)-[:HAS_ACCOUNT]->(a)
RETURN
    c.firstName + ' ' + c.lastName AS customer_name,
    a.accountId AS account,
    a.accountType AS accountType,
    tx_count AS num_transactions;
```

### 5. Risk Profile Segmentation

```cypher
// Portfolio characteristics by risk profile
MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)
OPTIONAL MATCH (a)-[:HAS_POSITION]->(p:Position)
RETURN
    c.riskProfile AS riskProfile,
    COUNT(DISTINCT c) AS num_customers,
    AVG(c.annualIncome) AS avg_income,
    AVG(c.creditScore) AS avg_credit_score,
    AVG(a.balance) AS avg_account_balance,
    SUM(p.currentValue) AS total_investment_value
ORDER BY riskProfile;
```

### 6. Sector Allocation

```cypher
// Investment allocation by sector
MATCH (a:Account)-[:HAS_POSITION]->(p:Position)-[:OF_SECURITY]->(s:Stock)-[:OF_COMPANY]->(c:Company)
WITH c.sector AS sector, SUM(p.currentValue) AS sector_value
RETURN
    sector,
    sector_value,
    ROUND(sector_value / SUM(sector_value) * 100, 2) AS pct_of_total
ORDER BY sector_value DESC;
```

---

## Troubleshooting

### Import Fails with "Node not found" Error

**Problem**: Relationship mapping references a node that doesn't exist

**Solution**:
- Ensure all node CSV files are uploaded before relationship CSVs
- Check that foreign key fields match (e.g., `customerId` in accounts.csv matches `customerId` in customers.csv)

### Import Shows 0 Relationships Created

**Problem**: Relationship mappings are incorrect or CSV data has mismatches

**Solution**:
- Verify CSV column names match exactly (case-sensitive)
- Check that foreign key values exist in both source and target CSVs
- Look for empty/null values in key fields

### Missing Properties on Nodes

**Problem**: Property mappings not applied

**Solution**:
- Verify CSV headers match field names in schema
- Check for BOM (Byte Order Mark) in CSV files - remove if present
- Ensure CSV is UTF-8 encoded

### Performance Issues with Large Datasets

**Problem**: Import is very slow

**Solution**:
- For production data (millions of records), use `neo4j-admin import` instead
- Increase heap memory in Neo4j configuration
- Consider batching large CSV files

---

## Schema Modifications

If you need to modify the schema:

1. **Add a New Property**:
   - Edit the JSON file
   - Add property to the `properties` array of the relevant node/relationship label
   - Add corresponding `propertyMapping` in `nodeMappings` or `relationshipMappings`

2. **Add a New Relationship**:
   - Add relationship type to `relationshipTypes`
   - Create relationship object type in `relationshipObjectTypes`
   - Add relationship mapping in `relationshipMappings`
   - Create or modify CSV file with appropriate from/to keys

3. **Add a New Node Type**:
   - Add node label to `nodeLabels`
   - Create node object type in `nodeObjectTypes`
   - Add node mapping in `nodeMappings`
   - Create corresponding CSV file

---

## Data Provenance

This dataset is **synthetic demonstration data** created for educational purposes. It does not represent real customers, banks, or transactions.

Data characteristics:
- 102 customers across all 50 US states
- 102 banks (commercial, regional, community, savings, credit unions)
- 102 companies across 12+ sectors
- Account balances: $12K - $456K
- Portfolio holdings: $1K - $49K per position
- Transactions: $185 - $5,600 transfers

---

## Next Steps

After successful import:

1. **Explore with Neo4j Bloom**
   - Visual graph exploration
   - Search for customers, companies, or stocks
   - Follow relationship paths

2. **Run Graph Algorithms**
   - PageRank: Identify influential accounts
   - Community Detection: Find customer clusters
   - Shortest Path: Transaction routing analysis

3. **Build Applications**
   - Portfolio dashboard
   - Risk analysis tools
   - Transaction monitoring
   - Recommendation engine

4. **Extend the Schema**
   - Add Advisor nodes
   - Add Branch locations
   - Add Product nodes (loans, CDs, mortgages)
   - Implement temporal snapshots for historical analysis

---

## Additional Resources

- **Neo4j Documentation**: https://neo4j.com/docs/
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/current/
- **Graph Data Science Library**: https://neo4j.com/docs/graph-data-science/current/
- **Neo4j Bloom**: https://neo4j.com/docs/bloom-user-guide/current/

---

## Support

For questions or issues:

1. Review `SCHEMA_MODEL.md` for detailed schema documentation
2. Check Neo4j Community Forum: https://community.neo4j.com/
3. Consult Neo4j documentation for specific features

---

**Schema Version**: 1.0
**Last Updated**: 2025-11-04
**Compatible with**: Neo4j 5.x, AuraDB Professional/Enterprise
