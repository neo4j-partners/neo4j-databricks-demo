---
marp: true
theme: default
paginate: true
---

<style>
section {
  font-size: 22px;
}
h1 { font-size: 36px; }
h2 { font-size: 28px; }
code { font-size: 18px; }
table { font-size: 20px; }
</style>

# Lab 3: Export Neo4j to Lakehouse
## Bidirectional Data Flow

---

## Concepts Introduced

**Delta Lake** - Open-source storage layer that brings ACID transactions to data lakes.

**Key Concepts:**
- **Delta Tables** - Versioned, transactional tables stored as Parquet
- **Time Travel** - Query previous versions of your data
- **ACID Transactions** - Reliable writes, no partial failures
- **Unity Catalog Tables** - Governed Delta tables with access control

**Why Export Graph → Tables?**
- Enable SQL-based tools (BI, Genie) to query graph data
- Leverage Databricks compute for large-scale analytics
- Create governed, shareable datasets from graph insights

---

## Why Export Back?

The Spark Connector works **both directions:**

```
┌─────────────────┐                      ┌─────────────────┐
│   Delta Lake    │   Neo4j Spark        │     Neo4j       │
│                 │   Connector          │                 │
│  • Delta Tables │◄────────────────────►│  • Graph Nodes  │
│  • SQL Queries  │                      │  • Cypher       │
│  • AI/BI Genie  │   Bidirectional      │  • Graph Algos  │
└─────────────────┘                      └─────────────────┘
```

**Key Use Case:** Enable SQL-based AI agents (Genie) to query graph-derived data.

---

## What We're Creating

**14 Delta Tables** in Unity Catalog:

| Type | Tables | Purpose |
|------|--------|---------|
| **Node Tables** | customer, bank, account, company, stock, position, transaction | Entity data |
| **Relationship Tables** | has_account, at_bank, of_company, performs, benefits_to, has_position, of_security | Connection data |

```python
# Read from Neo4j
df = spark.read.format("org.neo4j.spark.DataSource")
    .option("labels", "Customer").load()

# Write to Delta
df.write.format("delta").saveAsTable("catalog.schema.customer")
```

**Next:** Create AI agents that query these tables
