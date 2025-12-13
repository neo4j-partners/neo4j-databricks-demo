# Lab 6: Graph Augmentation Agent

This lab uses the Multi-Agent Supervisor to analyze unstructured documents and suggest new entities and relationships for graph augmentation.

## Prerequisites

- Completed [Lab 5](../lab_5_multi_agent/README.md) with Multi-Agent Supervisor deployed
- Databricks serving endpoint for your Multi-Agent Supervisor
- MLflow installed for tracing (optional but recommended)

---

## Overview

The augmentation agent queries the Multi-Agent Supervisor to:

1. **Analyze unstructured documents** - Extract insights from HTML profiles and research documents
2. **Identify missing entities** - Find entities mentioned in documents but not in the graph
3. **Suggest new relationships** - Discover connections that could enrich the graph model
4. **Generate extraction recommendations** - Provide actionable suggestions for graph augmentation

---

## Setup

### 1. Get Your Endpoint Name

Find your Multi-Agent Supervisor endpoint:
- Go to **Serving** in Databricks
- Locate your deployed Multi-Agent Supervisor
- Copy the endpoint name (e.g., `mas-01875d0e-endpoint`)

### 2. Enable MLflow Tracing

MLflow tracing helps debug latency, cost, and quality issues:

```python
%pip install -U mlflow
dbutils.library.restartPython()

import mlflow
mlflow.openai.autolog()
```

---

## Running the Agent

### Option A: Databricks Notebook

1. Upload `augmentation_agent.ipynb` to Databricks
2. Update `LLM_ENDPOINT_NAME` with your endpoint
3. Run all cells

### Option B: Python Script

```bash
# Set your endpoint name
export LLM_ENDPOINT_NAME="mas-01875d0e-endpoint"

# Run in Databricks
python augmentation_agent.py
```

---

## Sample Queries

The agent can answer questions like:

```
"What are the emerging investment themes mentioned in the market research documents?"
"What new entities should be extracted from the HTML data for inclusion in the graph?"
"What customer attributes are mentioned in profiles but missing from the Customer nodes?"
"What relationships between customers and companies are implied but not captured?"
```

---

## Example Output

```
Query: "What new entities should be extracted from the HTML data for inclusion in the graph?"

Response: Based on the analysis of HTML documents, the following entities could be added:

1. **Investment Theme** nodes - Renewable energy, ESG, AI, Cybersecurity
2. **Financial Goal** nodes - Retirement, College savings, Wealth building
3. **Service Preference** nodes - Digital banking, In-person advisory
4. **Industry Sector** nodes - Technology, Healthcare, Real Estate

These would enable richer queries about customer interests and portfolio alignment.
```

---

## Architecture

```
┌─────────────────────────┐
│  Augmentation Agent     │
│  (This Lab)             │
└───────────┬─────────────┘
            │ OpenAI-compatible API
            ▼
┌─────────────────────────┐
│  Multi-Agent Supervisor │
│  (Databricks Endpoint)  │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌─────────┐  ┌─────────────┐
│  Genie  │  │  Knowledge  │
│  Agent  │  │  Agent      │
└────┬────┘  └──────┬──────┘
     │              │
     ▼              ▼
┌─────────┐  ┌─────────────┐
│  Delta  │  │  UC Volume  │
│  Tables │  │  (HTML/TXT) │
└─────────┘  └─────────────┘
```

---

## Next Steps

After identifying augmentation opportunities:

1. **Update Neo4j schema** - Add new node labels and relationship types
2. **Extract new entities** - Parse documents to create new nodes
3. **Re-export to lakehouse** - Run Lab 3 again with updated graph
4. **Update agents** - Refresh Genie and Knowledge Agent configurations
