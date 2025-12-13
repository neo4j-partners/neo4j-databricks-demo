# Lab 6: Graph Augmentation Agent

This lab uses LangGraph and ChatDatabricks to analyze unstructured documents and suggest graph augmentations for Neo4j with **native Pydantic structured output**.

## Key Features

- **Native Structured Output** - Uses `ChatDatabricks.with_structured_output()` for validated Pydantic models
- **LangGraph Workflow** - StateGraph orchestration with memory persistence
- **Modular Architecture** - Clean separation of concerns in `core/` module
- **Multiple Implementations** - LangGraph (primary) and DSPy (experimental)

---

## Prerequisites

1. Databricks workspace with Foundation Model APIs enabled
2. `.env` file with `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
3. Python dependencies installed via `uv sync`

---

## Quick Start

```bash
# Run the agent
uv run python -m lab_6_augmentation_agent.augmentation_agent

# Export results to JSON
uv run python -m lab_6_augmentation_agent.augmentation_agent --export results.json
```

---

## Module Structure

```
lab_6_augmentation_agent/
├── augmentation_agent.py     # Main entry point
├── schemas.py                # Pydantic schemas for structured output
├── core/                     # Modular LangGraph components
│   ├── __init__.py          # Package exports
│   ├── config.py            # Configuration, AnalysisType enum
│   ├── state.py             # LangGraph state schema
│   ├── client.py            # ChatDatabricks structured output client
│   ├── nodes.py             # LangGraph node functions
│   ├── graph.py             # Graph construction & agent class
│   └── output.py            # Demo output formatting
├── dspy_modules/            # DSPy implementation (experimental)
│   ├── config.py
│   ├── signatures.py
│   └── analyzers.py
└── agent_dspy.py            # DSPy entry point
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

## Usage Examples

### Basic Usage

```python
from lab_6_augmentation_agent import GraphAugmentationAgent, AnalysisType

# Create agent
agent = GraphAugmentationAgent()

# Run all analyses
result = agent.run_all_analyses(thread_id="my-session")

# Get structured response
response = agent.get_structured_response()
print(f"Found {response.total_suggestions} suggestions")
print(f"High confidence: {response.high_confidence_count}")
```

### Access Individual Results

```python
# Get suggested nodes
nodes = agent.get_suggested_nodes()
for node in nodes:
    print(f"{node.label}: {node.description}")

# Get suggested relationships
relationships = agent.get_suggested_relationships()
for rel in relationships:
    print(f"({rel.source_label})-[{rel.relationship_type}]->({rel.target_label})")

# Get suggested attributes
attributes = agent.get_suggested_attributes()
for attr in attributes:
    print(f"{attr.target_label}.{attr.property_name}: {attr.property_type}")
```

### Run Single Analysis

```python
# Run just one analysis type
result = agent.run_single_analysis(AnalysisType.NEW_ENTITIES)
```

### Export Results

```python
# Export to JSON
agent.export_results("augmentation_results.json")
```

---

## Example Output

```
======================================================================
 GRAPH AUGMENTATION AGENT
======================================================================

  Model:  databricks-claude-3-7-sonnet
  Method: ChatDatabricks.with_structured_output()

----------------------------------------------------------------------
 RESULTS
----------------------------------------------------------------------

  [Investment Themes] 3 items (14.1s)
    - Artificial Intelligence and Machine Learning [high]
    - Clean Energy Transition [high]
    - Digital Health [medium]

  [New Entities] 4 items (30.6s)
    - FINANCIAL_GOAL [high]
    - INVESTMENT_PREFERENCE [high]
    - LIFE_STAGE [high]
    ... and 1 more

----------------------------------------------------------------------
 SUMMARY
----------------------------------------------------------------------

  Total Suggestions: 19
  High Confidence:   10

  Suggested Nodes (4):
    - FINANCIAL_GOAL [high]
    - INVESTMENT_PREFERENCE [high]
    - LIFE_STAGE [high]
    - SERVICE_PREFERENCE [medium]

  Suggested Relationships (5):
    - (Customer)-[HAS_GOAL]->(Goal) [high]
    - (Customer)-[INTERESTED_IN]->(Sector) [medium]
    ...
```

---

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
| `LLM_MODEL` | Foundation model to use | `databricks-claude-3-7-sonnet` |

### Supported Models

- `databricks-claude-3-7-sonnet` (Anthropic Claude)
- `databricks-meta-llama-3-3-70b-instruct` (Meta Llama)
- `databricks-gpt-4o`, `databricks-gpt-4o-mini` (OpenAI)

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
