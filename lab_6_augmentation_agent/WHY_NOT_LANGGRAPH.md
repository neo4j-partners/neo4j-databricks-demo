# LangGraph + Databricks MAS + Pydantic Structured Output

## Core Goals

Lab 6 Graph Augmentation Agent must:
1. **Use the Lab 5 Multi-Agent Supervisor (MAS) endpoint** - This is non-negotiable
2. **Return Pydantic-validated structured output** - For type-safe graph augmentation suggestions
3. **Use LangGraph workflow** - For orchestration with memory persistence

## The Challenge

**MAS endpoints use a different API format than standard Foundation Model endpoints.**

| Feature | Foundation Model API | Multi-Agent Supervisor |
|---------|---------------------|----------------------|
| Message format | `messages` array (OpenAI Chat) | `input` array (Responses API) |
| Function calling | Supported | **NOT supported** |
| Structured output | `response_format` with `json_schema` | Limited - see below |
| Tools format | `{type: "function", function: {...}}` | `{type: string}` only |

The error we encountered:
```
Error: Invalid properties not defined in the schema found: {'function'}
```

This occurs because `ChatDatabricks.with_structured_output(method="function_calling")` sends OpenAI-style tools, but MAS expects a simpler format.

---

## Research Findings

### 1. ChatDatabricks `use_responses_api` Parameter

**Source:** [Databricks AI Bridge API Docs](https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html)

> `use_responses_api` (bool, default: False): "Whether to use the Responses API to format inputs and outputs."
>
> For Responses API endpoints like a ResponsesAgent, set `use_responses_api=True`.

**Result:** Setting `use_responses_api=True` correctly converts `messages` to `input` array format. ✅

### 2. Structured Output Methods

**Source:** [Databricks Structured Outputs](https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs)

Three methods available in `with_structured_output()`:

| Method | Description | MAS Compatible? |
|--------|-------------|-----------------|
| `function_calling` | OpenAI-style function calling | ❌ No - MAS doesn't support `function` type |
| `json_mode` | Returns unstructured JSON | ⚠️ Unknown |
| `json_schema` | Returns JSON conforming to schema | ⚠️ Unknown |

**Limitation from docs:**
> Anthropic Claude models can only accept `json_schema` structured outputs.

### 3. MAS Endpoint Schema

The MAS endpoint expects this request schema:
```
'input': Array(Any) (required)
'tools': Array({type: string (required)}) (optional)
'tool_choice': Any (optional)
'temperature': double (optional)
...
```

Key issue: `tools` expects `Array({type: string})` not OpenAI's `Array({type: "function", function: {...}})`.

### 4. ResponsesAgent Architecture

**Source:** [Author AI Agents in Code](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent)

> Databricks recommends using the `ResponsesAgent` interface from MLflow, which "lets you build agents with any third-party framework, then integrate it with Databricks AI features."

The ResponsesAgent schema is compatible with OpenAI Responses schema, but this is for **creating** agents, not **calling** them.

### 5. LangChain Integration Compatibility

**Source:** [LangChain on Databricks](https://docs.databricks.com/aws/en/large-language-models/langchain)

> The serving endpoint `ChatDatabricks` wraps must have **OpenAI-compatible chat input/output format**.

This suggests ChatDatabricks was designed for Foundation Model endpoints, not MAS endpoints.

---

## Attempted Solutions

### Attempt 1: `use_responses_api=True` + `method="function_calling"`

```python
chat = ChatDatabricks(
    endpoint=self.endpoint,
    temperature=0,
    use_responses_api=True,
)
structured_client = chat.with_structured_output(
    config.schema,
    method="function_calling",
)
```

**Result:** ❌ Failed
```
Error: Invalid properties not defined in the schema found: {'function'}
```

The `input` format is correct, but `tools` format is incompatible with MAS.

### Attempt 2: `use_responses_api=True` + `method="json_schema"`

```python
structured_client = chat.with_structured_output(
    config.schema,
    method="json_schema",
)
```

**Result:** ❌ Failed
```
Error: Responses.create() got an unexpected keyword argument 'response_format'
```

The Responses API doesn't accept `response_format` parameter.

### Attempt 3: `use_responses_api=True` + `method="json_mode"`

```python
structured_client = chat.with_structured_output(
    config.schema,
    method="json_mode",
)
```

**Result:** ❌ Failed
```
Error: Responses.create() got an unexpected keyword argument 'response_format'
```

Same issue - all methods rely on `response_format` which MAS doesn't support.

---

## Alternative Approaches

### Option A: Direct Responses API + Manual JSON Parsing

Bypass `ChatDatabricks` entirely and use the Databricks SDK directly:

```python
from databricks.sdk import WorkspaceClient

client = WorkspaceClient().serving_endpoints.get_open_ai_client()
response = client.responses.create(
    model=endpoint,
    input=[{"role": "user", "content": prompt_with_schema}],
)
# Parse JSON from response.output[0].content[0].text
```

**Pros:** Full control over request format
**Cons:** Manual JSON parsing, no native Pydantic validation

### Option B: DSPy Implementation

The existing `agent_dspy.py` already handles MAS endpoints correctly using a custom `DatabricksResponsesLM` adapter.

**Pros:** Already working
**Cons:** Different framework than LangGraph

### Option C: Wrap MAS in a Custom LangChain LLM

Create a custom `BaseChatModel` that:
1. Sends requests in Responses API format
2. Handles structured output via prompt engineering + JSON parsing
3. Validates with Pydantic

---

## Key Documentation References

1. **ChatDatabricks API:** https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html

2. **Databricks Structured Outputs:** https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs

3. **Multi-Agent Supervisor:** https://docs.databricks.com/aws/en/generative-ai/agent-bricks/multi-agent-supervisor

4. **Author AI Agents:** https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent

5. **LangChain on Databricks:** https://docs.databricks.com/aws/en/large-language-models/langchain

6. **LangChain ChatDatabricks:** https://docs.langchain.com/oss/python/integrations/chat/databricks

7. **databricks-langchain Package:** https://pypi.org/project/databricks-langchain/ (v0.11.0)

---

## Current Status

| Component | Status |
|-----------|--------|
| `use_responses_api=True` | ✅ Working - converts to `input` format |
| `method="function_calling"` | ❌ Failed - MAS doesn't support OpenAI tools format |
| `method="json_schema"` | ❌ Failed - MAS doesn't support `response_format` |
| `method="json_mode"` | ❌ Failed - MAS doesn't support `response_format` |
| Direct Responses API | ✅ Works (see DSPy implementation) |

---

## Conclusion

**`ChatDatabricks.with_structured_output()` is NOT compatible with MAS endpoints.**

All three methods (`function_calling`, `json_schema`, `json_mode`) fail because:
1. `function_calling` requires OpenAI tools format which MAS doesn't support
2. `json_schema` and `json_mode` require `response_format` which MAS doesn't accept

**Recommended Solution: Direct Responses API + Prompt Engineering + Pydantic Validation**

```python
from databricks.sdk import WorkspaceClient
from pydantic import BaseModel

# 1. Get client
client = WorkspaceClient().serving_endpoints.get_open_ai_client()

# 2. Include JSON schema in prompt
prompt = f"""
{system_prompt}

{user_query}

Respond with valid JSON matching this schema:
{schema.model_json_schema()}
"""

# 3. Call MAS endpoint
response = client.responses.create(
    model=endpoint,
    input=[{"role": "user", "content": prompt}],
)

# 4. Parse and validate with Pydantic
text = response.output[0].content[0].text
data = json.loads(text)
result = MySchema.model_validate(data)
```

This approach:
- ✅ Works with MAS endpoints
- ✅ Uses Pydantic for type safety
- ✅ Leverages the model's JSON generation capability
- ⚠️ Requires robust JSON extraction from potentially markdown-wrapped responses

## Next Steps

1. Implement Option A in `client.py` (Direct Responses API + manual parsing)
2. Add robust JSON extraction (handle ```json blocks, etc.)
3. Update all LLM references to MAS
4. Test with all four analysis types
