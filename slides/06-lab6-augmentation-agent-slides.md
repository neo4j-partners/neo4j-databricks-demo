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

# Lab 6: Graph Augmentation Agent
## AI-Driven Schema Evolution

---

## Concepts Introduced

**Graph Augmentation** - Using AI to discover and suggest improvements to graph schemas based on document analysis.

**Key Concepts:**
- **Schema Evolution** - Iteratively improving graph structure based on new insights
- **Entity Extraction** - Identifying new node types from unstructured text
- **Relationship Discovery** - Finding implicit connections in documents
- **DSPy** - Framework for programming language models with signatures

**Why DSPy?**
- Declarative approach: define *what* you want, not *how* to prompt
- Native structured output via Pydantic models
- Works reliably with Databricks Multi-Agent Supervisor endpoints

---

## The Goal

Use the Multi-Agent Supervisor to **analyze documents** and **suggest graph enrichments**.

| Analysis Type | What It Finds |
|--------------|---------------|
| **Investment Themes** | Emerging trends in market research |
| **New Entities** | Node types missing from schema |
| **Missing Attributes** | Properties mentioned but not captured |
| **Implied Relationships** | Connections in documents but not in graph |

**Example:** Customer profiles mention "ESG investing interest" but no ESG relationship exists.

---

## DSPy: Signatures as Function Contracts

DSPy treats LLM calls like function definitions. You declare the **input** and **output** types, and DSPy figures out how to prompt the model.

```python
class ImpliedRelationshipsSignature(dspy.Signature):
    """Find relationships implied in documents but not captured in the graph."""

    document_context: str = dspy.InputField(
        desc="Documents containing information about entity relationships"
    )

    analysis: ImpliedRelationshipsAnalysis = dspy.OutputField(
        desc="Structured suggestions for new relationship types"
    )
```

**What DSPy handles for you:**
- Prompt generation from signature docstrings and field descriptions
- Output parsing into Pydantic models (type-safe structured output)
- Automatic prompt optimization when you run DSPy's optimizers

---

## DSPy Implementation

**Why DSPy?** Works reliably with Multi-Agent Supervisor endpoints.

```python
from lab_6_augmentation_agent.agent_dspy import run_all_analyses

results = run_all_analyses()

for result in results:
    if result.success:
        print(f"{result.analysis_type}: {result.item_count} items")
```

**Output:** Structured suggestions for graph schema improvements based on document analysis.

---

## What You've Built

```
┌─────────────────────────────────────────────────────────────────┐
│                    Complete Data Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│  CSV/HTML  →  Unity Catalog  →  Neo4j Graph  →  Delta Tables   │
│                                                                  │
│                    ↓                   ↓                         │
│              Knowledge            Genie Agent                    │
│                Agent                                             │
│                    ↓                   ↓                         │
│              Multi-Agent Supervisor                              │
│                         ↓                                        │
│              Graph Augmentation Suggestions                      │
└─────────────────────────────────────────────────────────────────┘
```

**The cycle:** Documents inform graph → Graph serves agents → Agents suggest improvements
