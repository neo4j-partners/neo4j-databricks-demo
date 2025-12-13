# Lab 6: Graph Augmentation Agent

This lab uses LangGraph and ChatDatabricks to analyze unstructured documents and suggest graph augmentations for Neo4j with **native Pydantic structured output**.

## Key Features

- **Native Structured Output** - Uses `ChatDatabricks.with_structured_output()` for validated Pydantic models
- **LangGraph Workflow** - StateGraph orchestration with memory persistence
- **Modular Architecture** - Clean separation of concerns in `core/` module
- **Interactive Notebook** - Step-by-step exploration with separate cells per analysis
- **Multiple Implementations** - LangGraph (primary) and DSPy (experimental)

---

## Prerequisites

1. Databricks workspace with Foundation Model APIs enabled
2. `.env` file with `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
3. Python dependencies installed via `uv sync`

### Databricks Cluster Libraries

Install these libraries on your Databricks cluster:

| Library | Version | PyPI |
|---------|---------|------|
| `databricks-langchain` | >= 0.11.0 | [pypi.org/project/databricks-langchain](https://pypi.org/project/databricks-langchain/) |
| `langgraph` | >= 1.0.5 | [pypi.org/project/langgraph](https://pypi.org/project/langgraph/) |
| `langchain-core` | >= 1.2.0 | [pypi.org/project/langchain-core](https://pypi.org/project/langchain-core/) |
| `pydantic` | >= 2.12.5 | [pypi.org/project/pydantic](https://pypi.org/project/pydantic/) |

Install via cluster UI or `%pip`:
```python
%pip install databricks-langchain>=0.11.0 langgraph>=1.0.5 langchain-core>=1.2.0 pydantic>=2.12.5
```

---

## Quick Start

```bash
# Run the CLI agent (all analyses at once)
uv run python -m lab_6_augmentation_agent.augmentation_agent

# Export results to JSON
uv run python -m lab_6_augmentation_agent.augmentation_agent --export results.json

# Interactive exploration (Jupyter notebook)
jupyter notebook lab_6_augmentation_agent/augmentation_agent_notebook.ipynb
```

---

## Module Structure

```
lab_6_augmentation_agent/
├── augmentation_agent.py           # CLI entry point
├── augmentation_agent_notebook.ipynb # Interactive notebook
├── schemas.py                      # Pydantic schemas for structured output
├── core/                           # Modular LangGraph components
│   ├── __init__.py                # Package exports
│   ├── config.py                  # Configuration, AnalysisType enum
│   ├── state.py                   # LangGraph state schema
│   ├── client.py                  # ChatDatabricks structured output client
│   ├── nodes.py                   # LangGraph node functions
│   ├── graph.py                   # Graph construction & agent class
│   ├── output.py                  # Demo output formatting
│   └── utils.py                   # Reusable utilities for CLI/notebooks
├── dspy_modules/                  # DSPy implementation (experimental)
│   ├── config.py
│   ├── signatures.py
│   └── analyzers.py
└── agent_dspy.py                  # DSPy entry point
```

---

## Analysis Types

The agent performs four types of analysis:

| Analysis | Description | Output |
|----------|-------------|--------|
| **Investment Themes** | Identifies emerging investment trends | Themes with market data |
| **New Entities** | Suggests new node types for the graph | Node definitions with properties |
| **Missing Attributes** | Finds attributes not captured in schema | Property suggestions |
| **Implied Relationships** | Discovers hidden connections | Relationship types |

---

## Notebook Usage

The `augmentation_agent_notebook.ipynb` provides interactive exploration with:

- **Separate cells for each analysis** - See what happens at each step
- **Detailed result display** - Examine suggestions with evidence and examples
- **Easy re-runs** - Re-run individual analyses without starting over


## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Graph Augmentation Agent                      │
│                      (LangGraph Workflow)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ChatDatabricks                                │
│              with_structured_output()                            │
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│   │  Pydantic   │  │  Function   │  │   Foundation Model      │ │
│   │   Schema    │──│  Calling    │──│   (Claude/GPT/Llama)    │ │
│   └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Structured Output (Pydantic)                     │
│                                                                  │
│   • SuggestedNode        - New node types for graph             │
│   • SuggestedRelationship - New relationship types              │
│   • SuggestedAttribute   - New properties for existing nodes    │
│   • InvestmentTheme      - Market trends and themes             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Databricks workspace URL | Required |
| `DATABRICKS_TOKEN` | Databricks access token | Required |
| `LLM_MODEL` | Foundation model to use | `databricks-claude-sonnet-4` |

### Supported Models

**Claude (Anthropic)** - Recommended for structured output:
- `databricks-claude-sonnet-4-5` (Latest - Claude Sonnet 4.5)
- `databricks-claude-opus-4-5` (Claude Opus 4.5)
- `databricks-claude-sonnet-4` (Claude Sonnet 4)
- `databricks-claude-opus-4-1` (Claude Opus 4.1)
- `databricks-claude-3-7-sonnet` (Claude 3.7 Sonnet)

**Llama (Meta)**:
- `databricks-meta-llama-3-3-70b-instruct`

**GPT (OpenAI)**:
- `databricks-gpt-4o`, `databricks-gpt-4o-mini`

---

## Documentation References

- [ChatDatabricks API](https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html)
- [Databricks Structured Outputs](https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs)
- [LangGraph StateGraph](https://langchain-ai.github.io/langgraph/concepts/low_level/)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/concepts/persistence/)

---

## Next Steps

After identifying augmentation opportunities:

1. **Update Neo4j schema** - Add new node labels and relationship types
2. **Extract new entities** - Parse documents to create new nodes
3. **Write back to Neo4j** - Use the structured output for graph updates (Phase 4-6 in proposal)
