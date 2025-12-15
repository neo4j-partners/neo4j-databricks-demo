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

# Agent-Augmented Knowledge Graphs
## Bridging Structured and Unstructured Data

---

## The Problem: Facts vs Intent

**Structured data captures what customers *have*, not what they *want*.**

A retail investment graph knows:
- Customer C0001 holds 50 shares of TCOR at $142.50
- The position sits in an account at First National Trust
- TCOR is TechCore Solutions in the technology sector

What the graph *cannot* answer:

> Which customers want renewable energy exposure but don't have it?

---

## The Gap: James Anderson

James's **portfolio** (structured data):
- TCOR, SMTC, MOBD — all technology stocks
- Zero renewable energy holdings

James's **profile document** (unstructured data):

> "James is particularly interested in emerging technologies and has expressed interest in expanding his portfolio to include **renewable energy stocks**."

**The insight exists. It's just not connected to the graph.**

---

![](images/graph_augmentation.png)

---

## The Solution: Agent-Augmented Enrichment

![](images/architecture-diagram.jpeg)

**The loop:** Extract graph → Analyze with agents → Enrich graph → Repeat

---

![h:500](images/use_cases.jpeg)

---

## What Agents Discover

| Gap Type | Example |
|----------|---------|
| **Interest-holding mismatch** | Wants renewable energy, holds only tech |
| **Risk profile discrepancy** | Database says "aggressive", profile says "careful" |
| **Data quality gap** | Job change in notes, not in structured fields |

**Result:** New relationships like `(:Customer)-[:INTERESTED_IN]->(:Sector)`

These become first-class graph data for queries and algorithms.

---

## Workshop Flow

```
┌────────────────────────────────────────────────────────────────────┐
│  Lab 1: Upload Data       →  CSV + HTML to Unity Catalog           │
│  Lab 2: Import to Neo4j   →  Build the knowledge graph             │
│  Lab 4: Export to Delta   →  Enable SQL-based agents               │
│  Lab 5: Create Agents     →  Genie (structured) + Knowledge (docs) │
│  Lab 6: Multi-Agent       →  Combine agents into unified system    │
│  Lab 7: Augmentation      →  AI suggests graph enrichments         │
└────────────────────────────────────────────────────────────────────┘
```

**Goal:** Close the loop between documents and graph structure.

---

## What is a Graph Database?

A **graph database** stores data as entities and their connections, rather than rows and columns.

**Why graphs?**
- Relationships are first-class citizens, not foreign key lookups
- Traversing connections is fast regardless of data size
- Schema flexibility — add new node types and relationships without migrations
- Natural fit for connected data: networks, hierarchies, recommendations

**Neo4j** is the leading native graph database, optimized for traversing relationships.

---

## Nodes

**Nodes** represent entities — the things in your data.

**Labels** categorize nodes (like table names in SQL):
```
(:Customer)    (:Account)    (:Stock)    (:Sector)
```

A node can have multiple labels: `(:Person:Employee:Manager)`

**Properties** store data as key-value pairs:
```
(:Customer {
    customer_id: "C0001",
    name: "James Anderson",
    risk_tolerance: "moderate"
})
```

Properties can be strings, numbers, booleans, dates, or arrays.

---

## Relationships

**Relationships** connect nodes — they always have a direction and a type.

**Type** describes how nodes are connected:
```
(:Customer)-[:HAS_ACCOUNT]->(:Account)
(:Account)-[:HAS_POSITION]->(:Stock)
(:Stock)-[:IN_SECTOR]->(:Sector)
```

**Properties** can also be stored on relationships:
```
[:HAS_POSITION {
    shares: 50,
    cost_basis: 142.50,
    purchase_date: date("2024-03-15")
}]
```

Relationships are always stored with direction, but can be queried in either direction.

---

## Graph Data Model: ASCII Art Notation

Graphs are represented using ASCII art in documentation and Cypher:

```
(james:Customer {name: "James Anderson"})
    │
    ├──[:HAS_ACCOUNT]──► (acc:Account {account_id: "A001"})
    │                         │
    │                         └──[:HAS_POSITION {shares: 50}]──► (tcor:Stock)
    │                                                                │
    │                                                                └──[:IN_SECTOR]──► (tech:Sector)
    │
    └──[:INTERESTED_IN]──► (renewable:Sector {name: "Renewable Energy"})
```

**Pattern:** `(node)-[relationship]->(node)`

---

## Cypher: The Graph Query Language

**Cypher** is Neo4j's declarative query language — like SQL for graphs.

```cypher
MATCH (c:Customer)
RETURN c
```

**Core clauses:**
- `MATCH` — find patterns in the graph
- `WHERE` — filter results
- `RETURN` — specify what to return
- `CREATE` — create nodes and relationships
- `SET` — update properties
- `DELETE` — remove nodes and relationships

**Pattern matching** is the core concept — you draw the shape of data you want.

---

## Cypher: Label Matching

Find all nodes with a specific **label**:

```cypher
MATCH (c:Customer)
RETURN c
```

Find all stocks:
```cypher
MATCH (s:Stock)
RETURN s.ticker, s.company_name
```

Count nodes by label:
```cypher
MATCH (a:Account)
RETURN count(a) AS total_accounts
```

Labels act like table names — they define what type of entity you're looking for.

---

## Cypher: Property Filtering

Filter nodes using the `WHERE` clause:

```cypher
MATCH (c:Customer)
WHERE c.risk_tolerance = "aggressive"
RETURN c.name
```

Inline property matching (shorthand):
```cypher
MATCH (c:Customer {risk_tolerance: "aggressive"})
RETURN c.name
```

Multiple conditions:
```cypher
MATCH (s:Stock)
WHERE s.sector = "Technology" AND s.price > 100
RETURN s.ticker, s.price
```

Common operators: `=`, `<>`, `<`, `>`, `CONTAINS`, `STARTS WITH`, `IN`

---

## Cypher: Single Relationship

Traverse one relationship using the arrow pattern:

```cypher
MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)
RETURN c.name, a.account_id
```

**What it matches:**
```
(Customer)--[:HAS_ACCOUNT]-->(Account)
```

**What it returns:** Every customer-account pair where the customer has that account.

| c.name | a.account_id |
|--------|--------------|
| James Anderson | A001 |
| Sarah Chen | A002 |

---

## Cypher: Chaining Relationships

Chain multiple relationships to traverse deeper:

```cypher
MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)-[:HAS_POSITION]->(s:Stock)
WHERE c.name = "James Anderson"
RETURN s.ticker, s.company_name
```

**What it matches:**
```
(Customer)--[:HAS_ACCOUNT]-->(Account)--[:HAS_POSITION]-->(Stock)
```

**What it returns:** All stocks held by James Anderson across all his accounts.

| s.ticker | s.company_name |
|----------|----------------|
| TCOR | TechCore Solutions |
| SMTC | SmartTech Corp |

---

## Cypher: Variable-Length Paths

Match paths of varying length with `*min..max`:

```cypher
MATCH (c:Customer)-[*1..3]->(s:Sector)
WHERE c.name = "James Anderson"
RETURN c.name, s.name
```

**What it matches:** Any path from Customer to Sector that is 1, 2, or 3 hops.
```
(Customer)--[*1..3]-->(Sector)
```

**Possible paths found:**
- `(Customer)-[:INTERESTED_IN]->(Sector)` — 1 hop
- `(Customer)-[:HAS_ACCOUNT]->()-[:HAS_POSITION]->()-[:IN_SECTOR]->(Sector)` — 3 hops

Variable-length paths are powerful for discovering indirect connections.

---

## Common Cypher Operations

| Operation | Cypher |
|-----------|--------|
| **Create node** | `CREATE (c:Customer {name: "Jane"})` |
| **Create relationship** | `MATCH (c:Customer), (s:Sector) CREATE (c)-[:INTERESTED_IN]->(s)` |
| **Find patterns** | `MATCH (c)-[:HAS_ACCOUNT]->(a) RETURN c, a` |
| **Filter results** | `WHERE c.name CONTAINS "James"` |
| **Aggregate** | `RETURN count(c), sum(p.shares)` |
| **Update** | `SET c.status = "active"` |
| **Delete** | `DELETE c` or `DETACH DELETE c` |

**Key insight:** You query by describing the pattern, not by joining tables.
