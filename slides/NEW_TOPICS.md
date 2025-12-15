# Suggested Slide Additions

Minor additions to enhance the existing slide decks based on concepts from `docs/GRAPH_AUGMENTATION.md`.

---

## Lab 2: Neo4j Import

**Add:** Why Graphs Beat Tables for Relationships

A simple comparison showing the same multi-hop query:

| Approach | Complexity |
|----------|------------|
| Cypher | 6 relationship hops in one pattern |
| SQL | 10 table JOINs, complex query planning |

*One slide showing the "find customers who share banks with renewable energy investors" example.*

---

## Lab 4: AI Agents

**Add:** The Structured vs Unstructured Problem

The core insight that motivates the workshop:

- **Structured data** = what customers *have* (portfolios, transactions)
- **Unstructured data** = what customers *want* (interests, goals, values)

*Example: James mentions "renewable energy" in his profile but holds zero renewable energy stocks.*

---

## Lab 6: Graph Augmentation Agent

**Add 1:** The Enrichment Loop

A simple diagram showing the continuous cycle:

```
Extract → Analyze → Propose → Validate → Enrich → Query → Repeat
```

*Emphasize that this is cyclical, not one-time ETL.*

---

**Add 2:** Gap Analysis Types

Three categories of gaps the agent finds:

| Gap Type | Example |
|----------|---------|
| Interest-holding mismatch | Wants renewable energy, holds only tech |
| Risk profile discrepancy | Database says "aggressive", profile says "careful" |
| Data quality gap | Employment change in notes, not in structured fields |

---

**Add 3:** Confidence Scoring

How agents express certainty about extractions:

| Phrase | Confidence | Action |
|--------|------------|--------|
| "expressed strong interest" | 0.95 | Auto-approve |
| "mentioned considering" | 0.70 | Approve with flag |
| "advisor suggested" | 0.40 | Queue for review |

---

**Add 4:** Graph Algorithms on Enriched Data

Once INTERESTED_IN relationships exist in Neo4j:

- **Jaccard Similarity** → Find customers with similar interests
- **Community Detection** → Discover natural customer segments

*The enrichments become first-class data for graph algorithms.*

---

## Summary

These additions are minor (1 slide each) and reinforce the "why" behind each lab:

- Lab 2: Why graphs matter for relationships
- Lab 4: The problem we're solving
- Lab 6: The mechanics of enrichment (loop, gaps, confidence, algorithms)

Total: ~5-6 new slides across 3 labs.
