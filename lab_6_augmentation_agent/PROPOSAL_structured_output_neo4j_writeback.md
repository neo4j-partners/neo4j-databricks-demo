# Proposal: LangGraph Conversion, Structured Output, and Neo4j Writeback for Graph Augmentation Agent

## Problem Statement

The augmentation agent currently has several limitations that prevent it from being a production-ready system:

1. **Simple script architecture** - The current agent is a basic Python script that makes direct API calls to the Multi-Agent Supervisor. It lacks the sophisticated state management, memory, and workflow orchestration needed for complex multi-step analysis.

2. **No machine-readable output** - The agent identifies new entities, attributes, and relationships, but the output is human-readable prose that cannot be programmatically processed.

3. **Manual intervention required** - A human must read the analysis, interpret the suggestions, and manually create Cypher queries to update Neo4j.

4. **No feedback loop** - The suggested graph augmentations are never written back to Neo4j, so the graph remains static despite the agent identifying gaps.

5. **No conversation memory** - Each query is independent with no ability to maintain context across multiple analysis steps or remember previous findings.

The impact is significant: the Multi-Agent Supervisor correctly identifies missing entities like `STATED_INTEREST`, `FINANCIAL_GOAL`, and `VALUES_PREFERENCE`, but none of these suggestions ever become actual graph data.

---

## Proposed Solution

The solution has two major components:

### Part 1: Convert to LangGraph

Rewrite the augmentation agent using LangGraph, a framework for building stateful, multi-step agent workflows. LangGraph provides the orchestration layer needed for complex analysis pipelines with built-in state management, memory persistence, and structured control flow.

Key benefits of LangGraph for this use case:
- **State management** - LangGraph uses a StateGraph pattern where agent state is explicitly defined and tracked across workflow steps
- **Built-in memory** - Checkpointers enable persistent memory so the agent can maintain context across multiple analysis sessions
- **Structured responses** - LangGraph agents support a response_format parameter for requesting structured output directly from the model
- **Multi-agent coordination** - LangGraph provides supervisor patterns for orchestrating multiple specialized agents, which aligns with the existing Multi-Agent Supervisor architecture

### Part 2: Structured Output and Neo4j Writeback

Update the LangGraph agent to return structured Pydantic models instead of free-form text. Then use the Neo4j Spark Connector (the same pattern used in `lab_2_neo4j_import`) to write the suggested entities and relationships directly to Neo4j.

The agent will output three types of structured suggestions:
- **New Node Types** - Entities that should be added to the graph
- **New Node Attributes** - Properties that should be added to existing nodes
- **New Relationships** - Connections between nodes that are implied but not captured

Each suggestion will include the source evidence from the original analysis, allowing for human review before committing changes.

Expected outcomes:
- Agent uses LangGraph for sophisticated workflow orchestration and state management
- Agent maintains memory across analysis sessions via checkpointing
- Agent output is machine-parseable JSON matching Pydantic schemas
- Suggested augmentations can be automatically written to Neo4j via Spark
- The graph grows and improves based on agent analysis
- Full audit trail of what was added and why

---

## Requirements

### LangGraph Architecture Requirements

1. The agent must be built using LangGraph StateGraph for explicit state management and workflow orchestration.

2. The agent state must include message history, analysis results, and any intermediate findings using a TypedDict schema.

3. The agent must use a checkpointer for memory persistence, enabling the agent to resume analysis across sessions and maintain conversation context.

4. The agent must use the create_react_agent pattern from langgraph.prebuilt for tool-calling capabilities.

5. The workflow must define explicit nodes for each analysis step (investment themes, new entities, missing attributes, implied relationships) connected via conditional edges.

### Structured Output Requirements

6. The agent must return responses conforming to a Pydantic schema for each analysis type.

7. Each suggested node must include: label name, required properties with types, a unique key property, and source evidence (which document or query produced this suggestion).

8. Each suggested relationship must include: relationship type name, source node label, target node label, any relationship properties, and source evidence.

9. Each suggested attribute must include: target node label, property name, property type, and source evidence.

10. The agent must distinguish between high-confidence suggestions (clear evidence) and speculative suggestions (inferred).

### Neo4j Writeback Requirements

11. New node types must have constraints created before data is written (matching the lab_2 pattern).

12. Node writes must use the Spark Neo4j Connector with the same write_nodes pattern from lab_2.

13. Relationship writes must use the Spark Neo4j Connector with the same write_relationship pattern from lab_2.

14. All writes must be validated by querying Neo4j to confirm the expected count of new nodes and relationships.

15. The writeback process must be idempotent - running it twice should not create duplicates.

### Testing Requirements

16. Each phase must have at least one integration test that validates the phase works end-to-end.

17. Schema validation tests must confirm agent output matches Pydantic models.

18. Neo4j writeback tests must confirm data appears in the graph with correct labels and properties.

19. LangGraph workflow tests must confirm state transitions and memory persistence work correctly.

---

## Implementation Plan

### Phase 1: Convert Agent to LangGraph Architecture

**Objective**: Rewrite the augmentation agent using LangGraph StateGraph to provide proper workflow orchestration, state management, and memory persistence.

**Tasks**:
- [ ] Create AgentState TypedDict defining the state schema with fields for messages, analysis results, and intermediate findings
- [ ] Set up LangGraph StateGraph with the AgentState schema
- [ ] Implement analysis node functions for each analysis type (investment themes, new entities, missing attributes, implied relationships)
- [ ] Define conditional edges to route between analysis steps based on current state
- [ ] Add a checkpointer (MemorySaver) to enable conversation memory and session persistence
- [ ] Connect to the Multi-Agent Supervisor endpoint using the existing Databricks authentication pattern
- [ ] Update main entry point to compile and invoke the LangGraph workflow

**Test**:
- [ ] Unit test that verifies the graph compiles without errors
- [ ] Integration test that runs a simple query through the workflow and confirms state updates correctly
- [ ] Test that memory persists across multiple invocations using the same thread_id

**Status**: Pending

---

### Phase 2: Define Pydantic Schemas for Structured Output

**Objective**: Create Pydantic models that represent the structured output the agent should return.

**Tasks**:
- [ ] Create SuggestedNode model with fields for label, properties, key property, confidence level, and source evidence
- [ ] Create SuggestedRelationship model with fields for type, source label, target label, properties, confidence level, and source evidence
- [ ] Create SuggestedAttribute model with fields for target label, property name, property type, confidence level, and source evidence
- [ ] Create AugmentationAnalysis model that contains lists of the above three types
- [ ] Create AugmentationResponse model as the top-level response wrapper

**Test**:
- [ ] Unit test that validates sample JSON data against each Pydantic model
- [ ] Test that invalid data raises validation errors with clear messages

**Status**: Pending

---

### Phase 3: Update LangGraph Agent to Request Structured Output

**Objective**: Modify the LangGraph agent to use the response_format parameter for structured output that matches the Pydantic schemas.

**Tasks**:
- [ ] Configure the LangGraph agent with response_format parameter pointing to the AugmentationResponse schema
- [ ] Update node functions to extract structured data from the agent response
- [ ] Add error handling for responses that do not match the expected schema
- [ ] Update the AgentState to store parsed structured results alongside raw messages
- [ ] Implement a post-processing step that validates all structured output before returning

**Test**:
- [ ] Integration test that calls the agent and validates the response parses into valid Pydantic models
- [ ] Test that the agent returns at least one suggestion for each analysis type
- [ ] Test that malformed responses are handled gracefully with clear error messages

**Status**: Pending

---

### Phase 4: Create Neo4j Writer Module

**Objective**: Build the Neo4j writeback functionality using the Spark Connector pattern from lab_2.

**Tasks**:
- [ ] Create augmentation_writer.py module
- [ ] Implement create_augmentation_constraints function to create uniqueness constraints for new node types
- [ ] Implement write_suggested_nodes function that converts Pydantic models to Spark DataFrames and writes to Neo4j
- [ ] Implement write_suggested_relationships function that converts Pydantic models to Spark DataFrames and writes to Neo4j
- [ ] Implement validate_augmentation_import function that queries Neo4j to confirm writes succeeded
- [ ] Add configuration for Neo4j credentials using the same Databricks Secrets pattern as lab_2

**Test**:
- [ ] Integration test that writes a known set of test nodes and validates they appear in Neo4j
- [ ] Integration test that writes test relationships and validates they connect the correct nodes
- [ ] Test that running the same write twice does not create duplicate nodes (idempotency check)

**Status**: Pending

---

### Phase 5: Integrate LangGraph Agent with Writer

**Objective**: Connect the LangGraph agent structured output to the Neo4j writer, creating the complete pipeline.

**Tasks**:
- [ ] Add a writeback node to the LangGraph workflow that takes structured suggestions and writes to Neo4j
- [ ] Implement conditional edge logic to skip writeback in dry-run mode
- [ ] Add configuration for confidence threshold filtering (only write high-confidence suggestions)
- [ ] Update AgentState to track what was written to Neo4j for audit purposes
- [ ] Add summary output showing what was written to Neo4j

**Test**:
- [ ] End-to-end integration test: run agent workflow, verify structured output, verify Neo4j contains new data
- [ ] Test dry-run mode produces valid output but does not modify Neo4j
- [ ] Test confidence filtering excludes low-confidence suggestions

**Status**: Pending

---

### Phase 6: Validation and Documentation

**Objective**: Ensure the complete system works reliably and is documented for users.

**Tasks**:
- [ ] Run full LangGraph pipeline against production Neo4j instance
- [ ] Validate augmented graph with sample Cypher queries demonstrating new data
- [ ] Update README with usage instructions for the LangGraph agent
- [ ] Add example output showing before and after graph state
- [ ] Document the LangGraph workflow structure with a diagram

**Test**:
- [ ] Manual validation: query Neo4j for new node types and confirm they exist
- [ ] Manual validation: run a graph traversal query that uses the new relationships
- [ ] Review test coverage report and ensure all critical paths are tested
- [ ] Verify memory persistence works across multiple sessions

**Status**: Pending

---

## Success Criteria

The project is complete when:

1. The augmentation agent is rewritten using LangGraph StateGraph with proper state management
2. The agent maintains conversation memory across multiple invocations using a checkpointer
3. Running the agent produces JSON output matching the Pydantic schema
4. The JSON output contains at least one suggestion for nodes, relationships, and attributes
5. Running the pipeline writes new data to Neo4j visible in the browser
6. All integration tests pass
7. Running the pipeline twice does not create duplicate data

---

## Files Affected

- `lab_6_augmentation_agent/augmentation_agent.py` - Complete rewrite using LangGraph StateGraph
- `lab_6_augmentation_agent/schemas.py` - New file for Pydantic models
- `lab_6_augmentation_agent/augmentation_writer.py` - New file for Neo4j writeback
- `lab_6_augmentation_agent/test_langgraph_agent.py` - New file for LangGraph workflow tests
- `lab_6_augmentation_agent/test_structured_output.py` - New file for schema validation tests

---

## Dependencies

- Existing: `databricks-sdk`, `mlflow`, `openai`
- Existing: `pyspark` with Neo4j Spark Connector (already configured in lab_2)
- New: `langgraph` - Core framework for building stateful agent workflows
- New: `langchain-core` - Foundation for message handling and tool integration
- New: `pydantic` (likely already available in Databricks runtime)

---

## References

The following documentation sources were used to inform the LangGraph architecture decisions in this proposal:

**LangGraph Core Concepts**
- LangGraph StateGraph and state management: The agent uses a TypedDict schema to define explicit state that is tracked across workflow steps. This pattern comes from the LangGraph low-level concepts documentation.
- Persistence and checkpointing: LangGraph checkpointers save graph state at every super-step, enabling memory across sessions, human-in-the-loop workflows, and fault tolerance. The MemorySaver checkpointer provides in-memory persistence for development.
- Structured output with response_format: When response_format is provided to a LangGraph agent, a separate step is added at the end of the agent loop where message history is passed to an LLM with structured output to generate a response matching the schema.

**LangGraph Multi-Agent Patterns**
- Supervisor architecture: Individual agents are coordinated by a central supervisor agent that controls communication flow and task delegation. This aligns with the existing Multi-Agent Supervisor deployment on Databricks.
- The langgraph-supervisor library provides prebuilt implementations for creating supervisor multi-agent systems.

**LangGraph Agent Creation**
- The create_react_agent function from langgraph.prebuilt provides a high-level way to create ReAct-style agents with tool calling support, automatic tool execution via ToolNode, and configurable system prompts.
- Agents can be created with pre_model_hook and post_model_hook functions for customizing behavior before and after model calls.

**Source Documentation**
- LangGraph GitHub repository: github.com/langchain-ai/langgraph
- LangGraph concepts documentation: langchain-ai.github.io/langgraph/concepts
- LangGraph tutorials: langchain-ai.github.io/langgraph/tutorials
- LangGraph how-to guides: langchain-ai.github.io/langgraph/how-tos
