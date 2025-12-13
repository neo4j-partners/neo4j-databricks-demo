# Lab 5: Multi-Agent Supervisor

This lab combines the Genie and Knowledge Agent into a unified system that answers complex questions requiring both structured data and unstructured document analysis.

## Prerequisites

- Completed [Lab 4](../lab_4_ai_agents/README.md) with both agents created:
  - Retail Investment Data Assistant (Genie)
  - Customer Insights Knowledge Agent

---

## Setup

### 1. Create Multi-Agent Supervisor

- Navigate to the **Multi-Agent Supervisor** interface
- Click **Build** to create a new multi-agent system

### 2. Add Agents

- **Agent 1**: Retail Investment Data Assistant (Genie) - queries structured lakehouse data
- **Agent 2**: Customer Insights Knowledge Agent - analyzes unstructured documents

### 3. Configure

- **Name**: `Retail Investment Intelligence System`

- **Description**:
  ```
  Provides comprehensive retail investment intelligence by combining structured transactional data analysis with unstructured customer insights and market research. Analyzes customer portfolios, account activity, and holdings alongside qualitative preferences, investment interests, and research recommendations to identify opportunities, gaps, and personalized financial guidance.
  ```

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

---

## Test Queries

Basic tests to verify the system works:

```
"Find customers interested in renewable energy stocks and show me their current holdings"
"Which customers have risk profiles that don't match their portfolio composition?"
"What information exists in customer profiles that isn't captured in the structured database?"
```

---

## Sample Queries

See [SAMPLE_QUERIES.md](./SAMPLE_QUERIES.md) for comprehensive examples including:

- **Use Case Categories**: Gap analysis, risk mismatch, data quality, customer intelligence, portfolio analysis, transactions, market research, banking relationships, cross-sell, compliance

- **Advanced Multi-Agent Questions**: Sophisticated queries that combine structured and unstructured data for personalized investment discovery, portfolio-profile alignment, research-driven targeting, life stage analysis, and comprehensive customer reports
