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

# Lab 2: Import Data to Neo4j
## Building Your Knowledge Graph

---

## Concepts Introduced

**Neo4j Spark Connector** - A library that enables bidirectional data transfer between Spark DataFrames and Neo4j graphs.

**Key Concepts:**
- **Nodes** - Entities in the graph (Customer, Account, Stock)
- **Relationships** - Connections between nodes (HAS_ACCOUNT, AT_BANK)
- **Properties** - Key-value attributes on nodes and relationships
- **Labels** - Categories that classify nodes (like table names)

**Graph vs Relational:**
- Relationships are first-class citizens, not foreign keys
- Traversing connections is O(1), not O(n) JOINs
- Schema-flexible: add properties without migrations

---

## The Neo4j Spark Connector

**Bridges two data models:**

| Databricks (Tables) | Neo4j (Graph) |
|---------------------|---------------|
| Rows become | Nodes |
| Foreign keys become | Relationships |
| Columns become | Properties |

**Why use both?**
- Tables excel at aggregations and analytics
- Graphs excel at relationship traversals and pattern matching

---

## What We're Creating

```
Financial Knowledge Graph

(Customer)-[:HAS_ACCOUNT]->(Account)-[:AT_BANK]->(Bank)
                              |
                     [:HAS_POSITION]
                              |
                              v
                         (Position)-[:OF_SECURITY]->(Stock)-[:OF_COMPANY]->(Company)
```

**764 nodes** across 7 types | **814 relationships** across 7 types

---

## Key Steps

1. **Configure** - Connect Spark to Neo4j via secrets
2. **Create constraints** - Indexes before data load
3. **Write nodes** - DataFrames become graph nodes
4. **Write relationships** - Foreign keys become edges
5. **Validate** - Verify counts match expectations

**Best Practice:** Use `coalesce(1)` for relationship writes to prevent deadlocks.

**Next:** Export graph data back to Delta Lake for AI agents
