# Proposal: Convert Augmentation Agent to Use DSPy for Structured Output

## Overview

This proposal outlines the conversion of the Graph Augmentation Agent from its current manual JSON parsing approach to using DSPy, a framework specifically designed for programmatic AI development with structured output capabilities.

## What is DSPy?

DSPy is a framework for programmatically defining and optimizing generative AI agents. Rather than manually crafting prompts and parsing JSON responses, DSPy allows you to declare what your AI component should do using "signatures" and automatically handles prompt generation and output parsing.

The key advantage is that DSPy shifts focus from tinkering with prompt strings to programming with structured, declarative modules. It expands your signatures into prompts and parses typed outputs automatically.

## Why Convert to DSPy?

### Current Pain Points

The existing implementation has several challenges:

1. **Manual JSON Extraction**: The `extract_json_from_text` function uses multiple regex patterns to find JSON in text responses, handling markdown code blocks and embedded JSON objects manually.

2. **Manual Parsing Functions**: Each analysis type requires a separate parsing function (`parse_investment_themes`, `parse_new_entities`, `parse_missing_attributes`, `parse_implied_relationships`) with extensive error handling.

3. **Brittle Prompts**: The structured output prompts in `STRUCTURED_OUTPUT_PROMPTS` must explicitly describe the JSON schema in natural language and hope the model follows it correctly.

4. **Error-Prone Type Conversion**: The code manually converts string values to enums and handles missing fields with defaults throughout.

### DSPy Benefits

1. **Native Structured Output**: DSPy signatures with typed fields automatically handle structured output generation and parsing.

2. **Pydantic Integration**: Your existing Pydantic models in `schemas.py` can be directly used as output types in DSPy signatures.

3. **Automatic Prompt Generation**: DSPy generates optimized prompts based on your signature definitions, field descriptions, and type annotations.

4. **Optimization Capability**: DSPy includes a compiler that can optimize prompts based on examples, potentially improving output quality over time.

5. **MLflow Integration**: DSPy integrates seamlessly with MLflow tracing, which is already set up in the current agent.

## Proposed Changes

### Step 1: Configure DSPy with Databricks

The first change involves setting up DSPy to communicate with your Databricks model serving endpoint. DSPy provides native Databricks support through the `dspy.LM` class with a `databricks/` prefix for model names.

Authentication works automatically when running on the Databricks platform. For external use, the existing environment variables `DATABRICKS_HOST` and `DATABRICKS_TOKEN` can be mapped to DSPy's expected format.

### Step 2: Convert Pydantic Models to DSPy Signatures

The existing Pydantic models in `schemas.py` can serve as output types within DSPy signatures. Each analysis type would become a DSPy signature class:

- **Investment Themes Signature**: Takes document context as input, outputs `InvestmentThemesAnalysis`
- **New Entities Signature**: Takes HTML data as input, outputs `NewEntitiesAnalysis`
- **Missing Attributes Signature**: Takes customer profiles as input, outputs `MissingAttributesAnalysis`
- **Implied Relationships Signature**: Takes document context as input, outputs `ImpliedRelationshipsAnalysis`

Each signature would use `dspy.InputField()` and `dspy.OutputField()` with the field descriptions already present in your Pydantic models.

### Step 3: Replace Manual Parsing with DSPy Predictors

Instead of calling `query_supervisor` and manually parsing responses, each analysis would use a DSPy predictor (either `dspy.Predict` or `dspy.ChainOfThought`). The predictor automatically handles:

- Generating the prompt from the signature
- Calling the language model
- Parsing the response into your Pydantic types
- Retrying on parsing failures

### Step 4: Use DSPy Adapters for JSON Output

DSPy provides two relevant adapters:

- **ChatAdapter**: The default adapter that works with all language models
- **JSONAdapter**: Optimized for models supporting native `response_format` structured output

Since Databricks Foundation Model APIs support structured outputs via `response_format`, the JSONAdapter would be the recommended choice for lower latency and more reliable parsing.

### Step 5: Simplify the LangGraph Workflow

With DSPy handling structured output natively, the LangGraph workflow nodes become simpler:

- Remove the `extract_json_from_text` function
- Remove all manual `parse_*` functions
- Simplify `run_analysis_node` to just call the DSPy predictor and store the typed result
- Remove the `parsing_error` field from `AnalysisResult` since DSPy handles this

### Step 6: Enable MLflow Tracing

DSPy provides automatic MLflow tracing via a single function call. This replaces the current OpenAI-specific autolog setup with DSPy-native tracing that captures all module invocations with nested traces.

## Databricks Documentation References

### Primary DSPy Documentation

**Build generative AI apps using DSPy on Databricks**
- URL: https://docs.databricks.com/aws/en/generative-ai/dspy/
- Content: Core documentation covering DSPy modules, signatures, compilers, and programs on Databricks

### Structured Output Documentation

**Structured outputs on Databricks**
- URL: https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs
- Content: How to use `response_format` parameter for JSON schema output; limitations on schema complexity

### MLflow Tracing Documentation

**Tracing DSPy**
- URL: https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/dspy
- Content: How to enable DSPy tracing with MLflow; installation requirements; configuration options

### Official DSPy Documentation

**DSPy Signatures**
- URL: https://dspy.ai/learn/programming/signatures/
- Content: How to define signatures with InputField and OutputField; type annotations; field descriptions

**DSPy Adapters**
- URL: https://dspy.ai/learn/programming/adapters/
- Content: ChatAdapter vs JSONAdapter; when to use each; configuration options

**DSPy Language Models**
- URL: https://dspy.ai/learn/programming/language_models/
- Content: Configuring DSPy with Databricks; authentication; model settings

## Key Considerations

### Databricks Structured Output Limitations

Per the Databricks documentation, the following JSON schema features are NOT supported:

- Regular expressions using `pattern`
- Complex composition using `anyOf`, `oneOf`, `allOf`, `prefixItems`, or `$ref`
- Maximum 64 keys in JSON schema
- No enforcement of `maxProperties`, `minProperties`, or `maxLength`

The existing Pydantic models should be reviewed to ensure they do not use unsupported features. The `ConfidenceLevel` enum and nested models like `PropertyDefinition` should work correctly.

### Simpler Schemas Yield Better Results

The Databricks documentation notes that "heavily nested JSON schemas result in lower quality generation." Consider flattening schemas where possible if output quality issues arise.

### Token Usage Considerations

Structured output on Databricks uses additional tokens due to quality-enhancement techniques. Monitor token usage after conversion and adjust if needed.

## Migration Strategy

### Phase 1: Add DSPy Dependency

Add `dspy-ai` to the project dependencies alongside the existing LangGraph setup.

### Phase 2: Create DSPy Signatures

Define DSPy signatures that use the existing Pydantic models as output types. Test each signature independently.

### Phase 3: Replace Query Function

Replace `query_supervisor` calls with DSPy predictor calls. Verify output matches expected Pydantic types.

### Phase 4: Simplify Parsing

Remove manual JSON extraction and parsing functions once DSPy predictors are working.

### Phase 5: Optimize (Optional)

Use DSPy's compilation features to optimize prompts based on example inputs/outputs if output quality needs improvement.

## Expected Outcome

After conversion, the augmentation agent will:

1. Have significantly less code for parsing and error handling
2. Produce more reliable structured output through native typing
3. Be easier to extend with new analysis types
4. Support prompt optimization through DSPy compilation
5. Maintain full MLflow tracing visibility
6. Continue working with the existing LangGraph workflow structure

## Summary

Converting to DSPy replaces approximately 150 lines of manual JSON extraction and parsing code with declarative signature definitions that leverage your existing Pydantic models. The Databricks platform provides native support for both DSPy and structured output, making this a well-supported migration path that aligns with Databricks best practices for building generative AI applications.
