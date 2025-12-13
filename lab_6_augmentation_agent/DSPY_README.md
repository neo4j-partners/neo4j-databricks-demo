# DSPy Graph Augmentation Agent - Quick Start

This guide covers running the DSPy-based Graph Augmentation Agent locally and on Databricks.

## Quick Start (Local)

```bash
# Sync dependencies (includes dspy>=3.0.4 and mlflow[databricks]>=3.1)
uv sync

# Run all analyses
uv run python -m lab_6_augmentation_agent.agent_dspy

# Run a specific analysis
uv run python -m lab_6_augmentation_agent.agent_dspy --analysis investment_themes
uv run python -m lab_6_augmentation_agent.agent_dspy --analysis new_entities
uv run python -m lab_6_augmentation_agent.agent_dspy --analysis missing_attributes
uv run python -m lab_6_augmentation_agent.agent_dspy --analysis implied_relationships
```

## Environment Setup

Ensure your `.env` file contains:

```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
LLM_ENDPOINT_NAME=your-model-serving-endpoint
```

## Databricks Cluster Dependencies

Install these packages on your Databricks cluster:

| Package | Version | Purpose |
|---------|---------|---------|
| `dspy` | `>=3.0.4` | DSPy framework for programmatic AI |
| `mlflow[databricks]` | `>=3.1` | Tracing and experiment tracking |
| `pydantic` | `>=2.0.0` | Structured output schemas |
| `python-dotenv` | `>=1.0.0` | Environment configuration |

Install via cluster libraries or notebook:

```python
%pip install dspy>=3.0.4 mlflow[databricks]>=3.1 pydantic>=2.0.0 python-dotenv>=1.0.0
dbutils.library.restartPython()
```

## Project Structure

```
lab_6_augmentation_agent/
├── agent_dspy.py           # Main entry point
├── schemas.py              # Pydantic models for structured output
├── dspy_modules/
│   ├── __init__.py
│   ├── config.py           # DSPy + Databricks LM configuration
│   ├── signatures.py       # DSPy signatures for each analysis type
│   └── analyzers.py        # DSPy modules that perform analysis
├── DSPY_README.md          # This file
└── DSPYING.md              # Implementation proposal
```

## Usage Examples

### Run from Python

```python
from lab_6_augmentation_agent.agent_dspy import DSPyGraphAugmentationAgent

# Initialize agent
agent = DSPyGraphAugmentationAgent(
    temperature=0.1,
    max_tokens=4000,
)

# Run all analyses
document_context = "Your document content here..."
response = agent.run_all_analyses(document_context)

# Access results
print(f"Total suggestions: {response.total_suggestions}")
print(f"Suggested nodes: {len(response.all_suggested_nodes)}")
print(f"Suggested relationships: {len(response.all_suggested_relationships)}")
print(f"Suggested attributes: {len(response.all_suggested_attributes)}")

# Access typed data
for node in response.all_suggested_nodes:
    print(f"  - {node.label}: {node.description}")
```

### Run Single Analysis

```python
from lab_6_augmentation_agent.agent_dspy import DSPyGraphAugmentationAgent

agent = DSPyGraphAugmentationAgent()
result = agent.run_single_analysis("new_entities", document_context)

if result.success:
    analysis = result.data  # NewEntitiesAnalysis typed object
    for node in analysis.suggested_nodes:
        print(f"Node: {node.label}")
        print(f"  Key: {node.key_property}")
        print(f"  Confidence: {node.confidence}")
```

## How It Works

### DSPy Signatures

Each analysis type has a declarative signature that defines inputs and outputs:

```python
class NewEntitiesSignature(dspy.Signature):
    """Analyze documents to suggest new entity types for the graph database."""

    document_context: str = dspy.InputField(
        desc="HTML data and documents containing entity information"
    )
    analysis: NewEntitiesAnalysis = dspy.OutputField(
        desc="Structured suggestions for new node types"
    )
```

DSPy automatically:
1. Generates prompts from the signature docstring and field descriptions
2. Calls the language model
3. Parses responses into your Pydantic types

### ChainOfThought Reasoning

Each analyzer uses `dspy.ChainOfThought` which encourages step-by-step reasoning:

```python
class NewEntitiesAnalyzer(dspy.Module):
    def __init__(self):
        self.analyze = dspy.ChainOfThought(NewEntitiesSignature)

    def forward(self, document_context: str):
        result = self.analyze(document_context=document_context)
        return result.analysis  # Typed NewEntitiesAnalysis
```

### JSONAdapter for Structured Output

The agent uses `dspy.JSONAdapter()` which leverages Databricks' native `response_format` support for reliable structured output with lower latency.

## Comparison with Original Agent

| Feature | Original (`augmentation_agent.py`) | DSPy (`agent_dspy.py`) |
|---------|-----------------------------------|------------------------|
| Prompt engineering | Manual prompt strings | Declarative signatures |
| JSON parsing | Regex extraction + manual parsing | Automatic via DSPy |
| Type safety | Post-hoc validation | Native Pydantic types |
| Error handling | Try/except around parsing | Built into DSPy |
| Optimization | Not supported | DSPy compiler ready |
| Lines of code | ~1200 | ~300 |

## Troubleshooting

### Authentication Errors

```
RuntimeError: Databricks credentials not found
```

Ensure `.env` has `DATABRICKS_HOST` and `DATABRICKS_TOKEN` set correctly.

### Import Errors

```
ModuleNotFoundError: No module named 'dspy'
```

Run `uv sync` to install dependencies.

### Parsing Failures

If DSPy fails to parse structured output, it will retry automatically. For persistent issues:

1. Check that your model endpoint supports `response_format`
2. Try using `use_json_adapter=False` to fall back to ChatAdapter
3. Simplify the Pydantic schema if it has deep nesting

## References

- [DSPy on Databricks](https://docs.databricks.com/aws/en/generative-ai/dspy/)
- [DSPy Signatures](https://dspy.ai/learn/programming/signatures/)
- [DSPy Modules](https://dspy.ai/learn/programming/modules/)
- [DSPy Adapters](https://dspy.ai/learn/programming/adapters/)
- [MLflow DSPy Tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/dspy)
- [Databricks Structured Outputs](https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs)
