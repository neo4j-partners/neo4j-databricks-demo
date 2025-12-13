# Lab 6: Graph Augmentation Agent

> **Important:** The LangGraph/LangChain implementation does not work with Multi-Agent Supervisor (MAS) endpoints.
>
> `ChatDatabricks.with_structured_output()` is incompatible with MAS endpoints because:
> - `function_calling` method: MAS doesn't support OpenAI tools format
> - `json_schema` method: MAS doesn't accept `response_format` parameter
> - `json_mode` method: MAS doesn't accept `response_format` parameter
>
> Custom JSON parsing is problematic and error-prone. **Use the DSPy implementation instead.**
>
> See [WHY_NOT_LANGGRAPH.md](./WHY_NOT_LANGGRAPH.md) for full technical details on the incompatibility.

---

## Recommended: DSPy Implementation

The DSPy implementation works reliably with MAS endpoints using a custom `DatabricksResponsesLM` adapter.

### Quick Start

```bash
# Sync dependencies (includes dspy>=3.0.4)
uv sync

# Run all analyses
uv run python -m lab_6_augmentation_agent.agent_dspy
```

On Databricks, use the `augmentation_dspy_agent.ipynb` notebook.

### Why DSPy?

| Feature | LangGraph (Broken) | DSPy (Working) |
|---------|-------------------|----------------|
| MAS endpoint support | No | Yes |
| Structured output | Fails | Native via signatures |
| Pydantic validation | Fails | Built-in |
| Custom JSON parsing | Required (fragile) | Not needed |

See [DSPY_README.md](./DSPY_README.md) for full DSPy documentation and best practices.

---

## Environment Setup

Ensure your `.env` file contains:

```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
MAS_ENDPOINT_NAME=your-mas-endpoint
```

### Databricks Cluster Libraries

Install these libraries on your Databricks cluster:

| Library | Version | Purpose |
|---------|---------|---------|
| `dspy` | `>=3.0.4` | DSPy framework |
| `mlflow[databricks]` | `>=3.1` | Tracing |
| `pydantic` | `>=2.0.0` | Structured output schemas |
| `python-dotenv` | `>=1.0.0` | Environment configuration |

Install via cluster UI or `%pip`:
```python
%pip install dspy>=3.0.4 mlflow[databricks]>=3.1 pydantic>=2.0.0 python-dotenv>=1.0.0
dbutils.library.restartPython()
```

---

## Project Structure

```
lab_6_augmentation_agent/
├── agent_dspy.py                # DSPy entry point (RECOMMENDED)
├── augmentation_dspy_agent.ipynb # DSPy notebook for Databricks
├── schemas.py                   # Pydantic schemas for structured output
├── dspy_modules/                # DSPy implementation
│   ├── config.py               # DSPy + Databricks LM configuration
│   ├── signatures.py           # DSPy signatures for each analysis
│   └── analyzers.py            # DSPy modules that perform analysis
├── DSPY_README.md              # DSPy documentation
├── WHY_NOT_LANGGRAPH.md                # LangGraph incompatibility docs
│
├── [DEPRECATED] augmentation_agent.py      # LangGraph CLI (does not work)
├── [DEPRECATED] augmentation_agent*.ipynb  # LangGraph notebooks (do not work)
└── [DEPRECATED] core/                      # LangGraph components (do not work)
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

## Usage Example (DSPy)

```python
from lab_6_augmentation_agent.agent_dspy import run_all_analyses

# Run all four analyses
results = run_all_analyses()

# Access results
for result in results:
    if result.success:
        print(f"{result.analysis_type}: {result.item_count} items")
```

---

## Documentation References

- [DSPy on Databricks](https://docs.databricks.com/aws/en/generative-ai/dspy/)
- [DSPy Signatures](https://dspy.ai/learn/programming/signatures/)
- [Databricks Multi-Agent Supervisor](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor)

---

## Deprecated: LangGraph Implementation

The `core/` directory and `augmentation_agent.py` contain a LangGraph implementation that **does not work** with MAS endpoints. These files are preserved for reference but should not be used.

See [WHY_NOT_LANGGRAPH.md](./WHY_NOT_LANGGRAPH.md) for technical details on why the LangGraph approach failed.
