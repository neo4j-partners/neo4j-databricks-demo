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

## The Solution: Agent-Augmented Enrichment

```
┌─────────────────┐                      ┌─────────────────────────────┐
│                 │      Extract         │      DATABRICKS LAKEHOUSE   │
│   Neo4j Graph   │─────────────────────▶│                             │
│                 │                      │  Delta Tables + Documents   │
│  Nodes & Rels   │                      │         │                   │
│  (facts)        │      Enrich          │         ▼                   │
│                 │◀─────────────────────│  Multi-Agent Supervisor     │
└─────────────────┘                      │  (Genie + Knowledge Agent)  │
                                         └─────────────────────────────┘
```

**The loop:** Extract graph → Analyze with agents → Enrich graph → Repeat

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
│  Lab 3: Export to Delta   →  Enable SQL-based agents               │
│  Lab 4: Create Agents     →  Genie (structured) + Knowledge (docs) │
│  Lab 5: Multi-Agent       →  Combine agents into unified system    │
│  Lab 6: Augmentation      →  AI suggests graph enrichments         │
└────────────────────────────────────────────────────────────────────┘
```

**Goal:** Close the loop between documents and graph structure.
