"""
Graph Augmentation Agent - LangGraph Implementation

This script implements a LangGraph-based workflow for analyzing unstructured documents
and suggesting graph augmentations for Neo4j. The agent uses a StateGraph pattern
for explicit state management and includes checkpointing for memory persistence.

The agent returns structured Pydantic models that can be programmatically processed
and written back to Neo4j.

Prerequisites:
    1. Multi-Agent Supervisor deployed as a Databricks serving endpoint
    2. MLflow installed for tracing (optional but recommended)
    3. .env file with DATABRICKS_HOST and DATABRICKS_TOKEN

Usage:
    uv run python -m lab_6_augmentation_agent.augmentation_agent
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Annotated, Any, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv

# Load .env from project root (same pattern as lab_1)
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods - use only HOST + TOKEN from .env
for var in ["DATABRICKS_CONFIG_PROFILE", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET", "DATABRICKS_ACCOUNT_ID"]:
    os.environ.pop(var, None)

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from pydantic import ValidationError

from lab_6_augmentation_agent.schemas import (
    AugmentationResponse,
    AugmentationAnalysis,
    InvestmentThemesAnalysis,
    NewEntitiesAnalysis,
    MissingAttributesAnalysis,
    ImpliedRelationshipsAnalysis,
    InvestmentTheme,
    SuggestedNode,
    SuggestedRelationship,
    SuggestedAttribute,
    ConfidenceLevel,
    PropertyDefinition,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Multi-Agent Supervisor endpoint name
LLM_ENDPOINT_NAME = os.environ.get("LLM_ENDPOINT_NAME", "mas-3ae5a347-endpoint")

# Analysis types that the agent can perform
ANALYSIS_TYPES = [
    "investment_themes",
    "new_entities",
    "missing_attributes",
    "implied_relationships",
]

# Base queries for each analysis type
ANALYSIS_QUERIES = {
    "investment_themes": "What are the emerging investment themes mentioned in the market research documents?",
    "new_entities": "What new entities should be extracted from the HTML data for inclusion in the graph?",
    "missing_attributes": "What customer attributes are mentioned in profiles but missing from the Customer nodes in the database?",
    "implied_relationships": "What relationships between customers, companies, and investments are implied in the documents but not captured in the graph?",
}

# Structured output prompt templates for each analysis type
STRUCTURED_OUTPUT_PROMPTS = {
    "investment_themes": """Analyze the market research documents and identify emerging investment themes.

Return your response as a JSON object with this structure:
{
    "summary": "Brief overall summary of investment themes found",
    "themes": [
        {
            "name": "Theme name",
            "description": "Description of the theme",
            "market_size": "Market size if mentioned (e.g., '$495 billion')",
            "growth_projection": "Growth projections if mentioned",
            "key_sectors": ["sector1", "sector2"],
            "key_companies": ["company1", "company2"],
            "confidence": "high|medium|low",
            "source_evidence": "Quote or reference from the documents"
        }
    ],
    "recommendations": ["recommendation1", "recommendation2"]
}

Be thorough and extract all relevant themes with supporting evidence.""",

    "new_entities": """Analyze the HTML data and suggest new entity types for the graph database.

Return your response as a JSON object with this structure:
{
    "summary": "Brief summary of suggested entities",
    "suggested_nodes": [
        {
            "label": "NODE_LABEL (e.g., FINANCIAL_GOAL, STATED_INTEREST)",
            "description": "What this node type represents",
            "key_property": "The property that uniquely identifies nodes (e.g., goal_id)",
            "properties": [
                {"name": "property_name", "property_type": "string|int|float|boolean|date", "required": true, "description": "Description"}
            ],
            "example_values": [{"property_name": "example_value"}],
            "confidence": "high|medium|low",
            "source_evidence": "Quote or reference from the documents",
            "rationale": "Why this entity should be added"
        }
    ],
    "implementation_priority": ["highest priority entity", "second priority"]
}

Focus on entities that capture customer goals, preferences, interests, and life stages.""",

    "missing_attributes": """Analyze customer profiles and identify attributes mentioned but missing from Customer nodes.

Return your response as a JSON object with this structure:
{
    "summary": "Brief summary of missing attributes",
    "suggested_attributes": [
        {
            "target_label": "Customer",
            "property_name": "attribute_name",
            "property_type": "string|int|float|boolean|date",
            "description": "What this attribute represents",
            "example_values": ["value1", "value2"],
            "confidence": "high|medium|low",
            "source_evidence": "Quote or reference from profiles",
            "rationale": "Why this attribute should be added"
        }
    ],
    "affected_node_types": ["Customer", "other affected types"]
}

Include professional details, investment preferences, financial goals, and behavioral attributes.""",

    "implied_relationships": """Analyze the documents and identify relationships that are implied but not captured in the graph.

Return your response as a JSON object with this structure:
{
    "summary": "Brief summary of implied relationships",
    "suggested_relationships": [
        {
            "relationship_type": "RELATIONSHIP_TYPE (e.g., HAS_GOAL, INTERESTED_IN)",
            "description": "What this relationship represents",
            "source_label": "Source node label",
            "target_label": "Target node label",
            "properties": [
                {"name": "property_name", "property_type": "string|int|float", "required": false, "description": "Description"}
            ],
            "example_instances": [{"source": "example", "target": "example"}],
            "confidence": "high|medium|low",
            "source_evidence": "Quote or reference from documents",
            "rationale": "Why this relationship should be added"
        }
    ],
    "relationship_patterns": ["pattern1", "pattern2"]
}

Focus on customer-goal, customer-interest, and customer-similarity relationships.""",
}


# =============================================================================
# STATE SCHEMA
# =============================================================================

class AnalysisResult(TypedDict):
    """Result from a single analysis step."""
    analysis_type: str
    query: str
    response: str
    structured_data: dict[str, Any] | None
    parsing_error: str | None
    success: bool
    error: str | None


class AgentState(TypedDict):
    """
    State schema for the Graph Augmentation Agent.

    This TypedDict defines the structure of data passed between nodes
    in the LangGraph workflow. The state is persisted via checkpointing
    to enable memory across sessions.

    Attributes:
        messages: Conversation history with add_messages reducer for append-only updates
        current_analysis: The analysis type currently being processed
        completed_analyses: List of analysis types that have been completed
        results: Dictionary mapping analysis types to their results
        structured_response: The final structured AugmentationResponse
        error: Any error message from the workflow
        run_all: Whether to run all analyses or just the current one
        use_structured_output: Whether to request and parse structured output
    """
    messages: Annotated[list[AnyMessage], add_messages]
    current_analysis: str | None
    completed_analyses: list[str]
    results: dict[str, AnalysisResult]
    structured_response: dict[str, Any] | None
    error: str | None
    run_all: bool
    use_structured_output: bool


# =============================================================================
# DATABRICKS CLIENT
# =============================================================================

_client = None

def get_client():
    """
    Get OpenAI-compatible client for Databricks serving endpoints.

    Uses lazy initialization to avoid creating the client until needed.
    The client is cached for reuse across invocations.

    Authentication: Reads DATABRICKS_HOST and DATABRICKS_TOKEN from .env file.
    """
    global _client
    if _client is not None:
        return _client

    try:
        from databricks.sdk import WorkspaceClient

        workspace_client = WorkspaceClient()
        _client = workspace_client.serving_endpoints.get_open_ai_client()
        print(f"[OK] Databricks client initialized")
        print(f"    Host: {workspace_client.config.host}")
        print(f"    Endpoint: {LLM_ENDPOINT_NAME}")
        return _client
    except ImportError:
        raise ImportError(
            "databricks-sdk not installed. Install with: pip install databricks-sdk"
        )
    except Exception as e:
        print(f"\n  ERROR: Failed to connect to Databricks: {e}")
        print("\n  Make sure .env file exists with:")
        print("    DATABRICKS_HOST=https://your-workspace.cloud.databricks.com")
        print("    DATABRICKS_TOKEN=your-token")
        raise RuntimeError(f"Failed to initialize Databricks client: {e}")


def query_supervisor(query: str) -> str:
    """
    Send a query to the Multi-Agent Supervisor and return the response.

    Args:
        query: The question to send to the supervisor

    Returns:
        The text response from the supervisor

    Raises:
        RuntimeError: If the query fails
    """
    client = get_client()
    try:
        response = client.responses.create(
            model=LLM_ENDPOINT_NAME,
            input=[{"role": "user", "content": query}]
        )
        return response.output[0].content[0].text
    except Exception as e:
        raise RuntimeError(f"Query failed: {e}")


# =============================================================================
# JSON PARSING
# =============================================================================

def extract_json_from_text(text: str) -> dict[str, Any] | None:
    """
    Extract JSON from a text response that may contain markdown or other content.

    Handles:
    - Pure JSON responses
    - JSON wrapped in ```json ... ``` code blocks
    - JSON embedded in other text

    Args:
        text: The text containing JSON

    Returns:
        Parsed JSON as a dictionary, or None if parsing fails
    """
    # Try to parse the entire text as JSON first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(code_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Try to find JSON object in the text (starts with { and ends with })
    brace_pattern = r'\{[\s\S]*\}'
    matches = re.findall(brace_pattern, text)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    return None


def parse_investment_themes(data: dict[str, Any]) -> InvestmentThemesAnalysis | None:
    """Parse investment themes analysis from JSON data."""
    try:
        themes = []
        for theme_data in data.get("themes", []):
            confidence = theme_data.get("confidence", "medium")
            if isinstance(confidence, str):
                confidence = ConfidenceLevel(confidence.lower())
            themes.append(InvestmentTheme(
                name=theme_data.get("name", "Unknown"),
                description=theme_data.get("description", ""),
                market_size=theme_data.get("market_size"),
                growth_projection=theme_data.get("growth_projection"),
                key_sectors=theme_data.get("key_sectors", []),
                key_companies=theme_data.get("key_companies", []),
                confidence=confidence,
                source_evidence=theme_data.get("source_evidence", ""),
            ))
        return InvestmentThemesAnalysis(
            summary=data.get("summary", ""),
            themes=themes,
            recommendations=data.get("recommendations", []),
        )
    except (ValidationError, KeyError, ValueError) as e:
        print(f"[WARN] Failed to parse investment themes: {e}")
        return None


def parse_new_entities(data: dict[str, Any]) -> NewEntitiesAnalysis | None:
    """Parse new entities analysis from JSON data."""
    try:
        nodes = []
        for node_data in data.get("suggested_nodes", []):
            confidence = node_data.get("confidence", "medium")
            if isinstance(confidence, str):
                confidence = ConfidenceLevel(confidence.lower())

            properties = []
            for prop in node_data.get("properties", []):
                properties.append(PropertyDefinition(
                    name=prop.get("name", ""),
                    property_type=prop.get("property_type", "string"),
                    required=prop.get("required", False),
                    description=prop.get("description"),
                ))

            nodes.append(SuggestedNode(
                label=node_data.get("label", "UNKNOWN"),
                description=node_data.get("description", ""),
                key_property=node_data.get("key_property", "id"),
                properties=properties,
                example_values=node_data.get("example_values", []),
                confidence=confidence,
                source_evidence=node_data.get("source_evidence", ""),
                rationale=node_data.get("rationale", ""),
            ))
        return NewEntitiesAnalysis(
            summary=data.get("summary", ""),
            suggested_nodes=nodes,
            implementation_priority=data.get("implementation_priority", []),
        )
    except (ValidationError, KeyError, ValueError) as e:
        print(f"[WARN] Failed to parse new entities: {e}")
        return None


def parse_missing_attributes(data: dict[str, Any]) -> MissingAttributesAnalysis | None:
    """Parse missing attributes analysis from JSON data."""
    try:
        attributes = []
        for attr_data in data.get("suggested_attributes", []):
            confidence = attr_data.get("confidence", "medium")
            if isinstance(confidence, str):
                confidence = ConfidenceLevel(confidence.lower())

            attributes.append(SuggestedAttribute(
                target_label=attr_data.get("target_label", "Customer"),
                property_name=attr_data.get("property_name", ""),
                property_type=attr_data.get("property_type", "string"),
                description=attr_data.get("description", ""),
                example_values=attr_data.get("example_values", []),
                confidence=confidence,
                source_evidence=attr_data.get("source_evidence", ""),
                rationale=attr_data.get("rationale", ""),
            ))
        return MissingAttributesAnalysis(
            summary=data.get("summary", ""),
            suggested_attributes=attributes,
            affected_node_types=data.get("affected_node_types", []),
        )
    except (ValidationError, KeyError, ValueError) as e:
        print(f"[WARN] Failed to parse missing attributes: {e}")
        return None


def parse_implied_relationships(data: dict[str, Any]) -> ImpliedRelationshipsAnalysis | None:
    """Parse implied relationships analysis from JSON data."""
    try:
        relationships = []
        for rel_data in data.get("suggested_relationships", []):
            confidence = rel_data.get("confidence", "medium")
            if isinstance(confidence, str):
                confidence = ConfidenceLevel(confidence.lower())

            properties = []
            for prop in rel_data.get("properties", []):
                properties.append(PropertyDefinition(
                    name=prop.get("name", ""),
                    property_type=prop.get("property_type", "string"),
                    required=prop.get("required", False),
                    description=prop.get("description"),
                ))

            relationships.append(SuggestedRelationship(
                relationship_type=rel_data.get("relationship_type", "UNKNOWN"),
                description=rel_data.get("description", ""),
                source_label=rel_data.get("source_label", ""),
                target_label=rel_data.get("target_label", ""),
                properties=properties,
                example_instances=rel_data.get("example_instances", []),
                confidence=confidence,
                source_evidence=rel_data.get("source_evidence", ""),
                rationale=rel_data.get("rationale", ""),
            ))
        return ImpliedRelationshipsAnalysis(
            summary=data.get("summary", ""),
            suggested_relationships=relationships,
            relationship_patterns=data.get("relationship_patterns", []),
        )
    except (ValidationError, KeyError, ValueError) as e:
        print(f"[WARN] Failed to parse implied relationships: {e}")
        return None


def parse_analysis_response(
    analysis_type: str,
    response_text: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Parse an analysis response into structured data.

    Args:
        analysis_type: The type of analysis
        response_text: The raw text response from the supervisor

    Returns:
        Tuple of (parsed_data, error_message)
    """
    json_data = extract_json_from_text(response_text)
    if json_data is None:
        return None, "Could not extract JSON from response"

    # Return the raw JSON data - validation will happen when building the final response
    return json_data, None


def build_augmentation_response(results: dict[str, AnalysisResult]) -> AugmentationResponse:
    """
    Build a consolidated AugmentationResponse from all analysis results.

    Args:
        results: Dictionary mapping analysis types to their results

    Returns:
        AugmentationResponse with all suggestions consolidated
    """
    analysis = AugmentationAnalysis()
    all_nodes: list[SuggestedNode] = []
    all_relationships: list[SuggestedRelationship] = []
    all_attributes: list[SuggestedAttribute] = []

    # Parse each analysis type
    for analysis_type, result in results.items():
        if not result.get("success") or not result.get("structured_data"):
            continue

        data = result["structured_data"]

        if analysis_type == "investment_themes":
            parsed = parse_investment_themes(data)
            if parsed:
                analysis.investment_themes = parsed

        elif analysis_type == "new_entities":
            parsed = parse_new_entities(data)
            if parsed:
                analysis.new_entities = parsed
                all_nodes.extend(parsed.suggested_nodes)

        elif analysis_type == "missing_attributes":
            parsed = parse_missing_attributes(data)
            if parsed:
                analysis.missing_attributes = parsed
                all_attributes.extend(parsed.suggested_attributes)

        elif analysis_type == "implied_relationships":
            parsed = parse_implied_relationships(data)
            if parsed:
                analysis.implied_relationships = parsed
                all_relationships.extend(parsed.suggested_relationships)

    # Build the response
    response = AugmentationResponse(
        success=True,
        analysis=analysis,
        all_suggested_nodes=all_nodes,
        all_suggested_relationships=all_relationships,
        all_suggested_attributes=all_attributes,
    )
    response.compute_statistics()

    return response


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

def initialize_node(state: AgentState) -> AgentState:
    """
    Initialize the workflow state.

    Sets up default values for the workflow and adds an initial system message.
    """
    return {
        "messages": [
            SystemMessage(content="Graph Augmentation Agent initialized. Ready to analyze documents and suggest graph improvements.")
        ],
        "completed_analyses": state.get("completed_analyses", []),
        "results": state.get("results", {}),
        "error": None,
    }


def select_next_analysis_node(state: AgentState) -> AgentState:
    """
    Select the next analysis to perform.

    Checks which analyses have been completed and selects the next one
    from the ANALYSIS_TYPES list. If all are done, sets current_analysis to None.
    """
    completed = state.get("completed_analyses", [])
    run_all = state.get("run_all", True)

    if not run_all:
        # Single analysis mode - check if current is done
        current = state.get("current_analysis")
        if current and current in completed:
            return {"current_analysis": None}
        return {}

    # Find next uncompleted analysis
    for analysis_type in ANALYSIS_TYPES:
        if analysis_type not in completed:
            return {
                "current_analysis": analysis_type,
                "messages": [
                    HumanMessage(content=f"Starting analysis: {analysis_type}")
                ],
            }

    # All analyses complete
    return {"current_analysis": None}


def run_analysis_node(state: AgentState) -> AgentState:
    """
    Execute the current analysis by querying the Multi-Agent Supervisor.

    Sends the appropriate query for the current analysis type and stores
    the result in the state. If use_structured_output is enabled, uses
    structured output prompts and parses the response into structured data.
    """
    current = state.get("current_analysis")
    if not current:
        return {"error": "No analysis type selected"}

    use_structured = state.get("use_structured_output", False)

    # Choose the appropriate query based on structured output mode
    if use_structured and current in STRUCTURED_OUTPUT_PROMPTS:
        query = STRUCTURED_OUTPUT_PROMPTS[current]
    else:
        query = ANALYSIS_QUERIES.get(current)

    if not query:
        return {"error": f"Unknown analysis type: {current}"}

    try:
        response = query_supervisor(query)

        # Parse structured data if enabled
        structured_data = None
        parsing_error = None
        if use_structured:
            structured_data, parsing_error = parse_analysis_response(current, response)
            if parsing_error:
                print(f"[WARN] Structured parsing failed for {current}: {parsing_error}")

        result: AnalysisResult = {
            "analysis_type": current,
            "query": query,
            "response": response,
            "structured_data": structured_data,
            "parsing_error": parsing_error,
            "success": True,
            "error": None,
        }

        # Update results dictionary
        results = dict(state.get("results", {}))
        results[current] = result

        # Mark as completed
        completed = list(state.get("completed_analyses", []))
        if current not in completed:
            completed.append(current)

        # Prepare summary message
        if use_structured and structured_data:
            summary = f"Completed {current} analysis with structured output"
            if current == "new_entities" and "suggested_nodes" in structured_data:
                summary += f" ({len(structured_data['suggested_nodes'])} nodes suggested)"
            elif current == "missing_attributes" and "suggested_attributes" in structured_data:
                summary += f" ({len(structured_data['suggested_attributes'])} attributes suggested)"
            elif current == "implied_relationships" and "suggested_relationships" in structured_data:
                summary += f" ({len(structured_data['suggested_relationships'])} relationships suggested)"
            elif current == "investment_themes" and "themes" in structured_data:
                summary += f" ({len(structured_data['themes'])} themes identified)"
        else:
            summary = f"Completed {current} analysis:\n\n{response[:500]}..."

        return {
            "messages": [AIMessage(content=summary)],
            "results": results,
            "completed_analyses": completed,
            "error": None,
        }

    except Exception as e:
        result: AnalysisResult = {
            "analysis_type": current,
            "query": query,
            "response": "",
            "structured_data": None,
            "parsing_error": None,
            "success": False,
            "error": str(e),
        }

        results = dict(state.get("results", {}))
        results[current] = result

        # Mark as completed even on failure to prevent infinite retry loop
        completed = list(state.get("completed_analyses", []))
        if current not in completed:
            completed.append(current)

        return {
            "messages": [
                AIMessage(content=f"Analysis {current} failed: {e}")
            ],
            "results": results,
            "completed_analyses": completed,
            "error": str(e),
        }


def summarize_node(state: AgentState) -> AgentState:
    """
    Generate a summary of all completed analyses.

    Creates a final summary message listing all analysis results.
    If structured output is enabled, builds the consolidated AugmentationResponse.
    """
    results = state.get("results", {})
    completed = state.get("completed_analyses", [])
    use_structured = state.get("use_structured_output", False)

    summary_parts = [
        "=" * 70,
        "GRAPH AUGMENTATION ANALYSIS COMPLETE",
        "=" * 70,
        f"Analyses completed: {len(completed)}",
        "",
    ]

    for analysis_type in completed:
        result = results.get(analysis_type, {})
        success = result.get("success", False)
        status = "SUCCESS" if success else "FAILED"

        # Add structured data info if available
        if use_structured and result.get("structured_data"):
            status += " (structured)"
        elif use_structured and result.get("parsing_error"):
            status += " (parsing failed)"

        summary_parts.append(f"- {analysis_type}: {status}")

    # Build structured response if enabled
    structured_response = None
    if use_structured:
        try:
            augmentation_response = build_augmentation_response(results)
            structured_response = augmentation_response.model_dump()

            summary_parts.extend([
                "",
                "STRUCTURED OUTPUT SUMMARY:",
                f"  - Suggested nodes: {len(augmentation_response.all_suggested_nodes)}",
                f"  - Suggested relationships: {len(augmentation_response.all_suggested_relationships)}",
                f"  - Suggested attributes: {len(augmentation_response.all_suggested_attributes)}",
                f"  - High confidence: {augmentation_response.high_confidence_count}",
                f"  - Total suggestions: {augmentation_response.total_suggestions}",
            ])
        except Exception as e:
            summary_parts.append(f"\n[WARN] Failed to build structured response: {e}")

    summary_parts.extend([
        "",
        "Results are available in the 'results' field of the agent state.",
        "=" * 70,
    ])

    summary = "\n".join(summary_parts)

    return {
        "messages": [AIMessage(content=summary)],
        "structured_response": structured_response,
    }


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def should_continue_analysis(state: AgentState) -> Literal["run_analysis", "summarize"]:
    """
    Determine whether to continue with more analyses or summarize.

    Returns:
        "run_analysis" if there's a current analysis to run
        "summarize" if all analyses are complete
    """
    current = state.get("current_analysis")
    if current is not None:
        return "run_analysis"
    return "summarize"


def should_select_next(state: AgentState) -> Literal["select_next", "summarize"]:
    """
    Determine whether to select the next analysis or finish.

    Returns:
        "select_next" if running all analyses and more remain
        "summarize" if done
    """
    run_all = state.get("run_all", True)
    completed = state.get("completed_analyses", [])

    if run_all and len(completed) < len(ANALYSIS_TYPES):
        return "select_next"
    return "summarize"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================

def build_augmentation_graph() -> StateGraph:
    """
    Build the LangGraph StateGraph for the augmentation workflow.

    The workflow follows this pattern:
    1. Initialize state
    2. Select next analysis to run
    3. Run the analysis (query Multi-Agent Supervisor)
    4. Check if more analyses needed
    5. Summarize results

    Returns:
        Compiled StateGraph ready for invocation
    """
    # Create the graph with our state schema
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("initialize", initialize_node)
    workflow.add_node("select_next", select_next_analysis_node)
    workflow.add_node("run_analysis", run_analysis_node)
    workflow.add_node("summarize", summarize_node)

    # Set entry point
    workflow.add_edge(START, "initialize")

    # Initialize leads to selecting the first analysis
    workflow.add_edge("initialize", "select_next")

    # After selecting, decide whether to run or summarize
    workflow.add_conditional_edges(
        "select_next",
        should_continue_analysis,
        {
            "run_analysis": "run_analysis",
            "summarize": "summarize",
        }
    )

    # After running analysis, decide whether to continue or summarize
    workflow.add_conditional_edges(
        "run_analysis",
        should_select_next,
        {
            "select_next": "select_next",
            "summarize": "summarize",
        }
    )

    # Summarize leads to end
    workflow.add_edge("summarize", END)

    return workflow


# =============================================================================
# AGENT CLASS
# =============================================================================

class GraphAugmentationAgent:
    """
    LangGraph-based agent for analyzing documents and suggesting graph augmentations.

    This agent uses a StateGraph workflow with checkpointing for memory persistence.
    It can run all analyses in sequence or individual analyses on demand.
    Supports both free-form text output and structured Pydantic model output.

    Attributes:
        graph: The compiled LangGraph workflow
        checkpointer: MemorySaver for state persistence
    """

    def __init__(self, checkpointer: MemorySaver | None = None):
        """
        Initialize the agent with optional checkpointer.

        Args:
            checkpointer: Optional MemorySaver for state persistence.
                         If None, a new MemorySaver is created.
        """
        self.checkpointer = checkpointer or MemorySaver()
        workflow = build_augmentation_graph()
        self.graph = workflow.compile(checkpointer=self.checkpointer)

    def run_all_analyses(
        self,
        thread_id: str = "default",
        use_structured_output: bool = False,
    ) -> dict:
        """
        Run all analysis types and return the results.

        Args:
            thread_id: Unique identifier for this conversation thread.
                      Using the same thread_id enables memory persistence.
            use_structured_output: If True, request and parse structured JSON output.

        Returns:
            Dictionary containing all analysis results
        """
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "messages": [],
            "current_analysis": None,
            "completed_analyses": [],
            "results": {},
            "structured_response": None,
            "error": None,
            "run_all": True,
            "use_structured_output": use_structured_output,
        }

        result = self.graph.invoke(initial_state, config)
        return result

    def run_single_analysis(
        self,
        analysis_type: str,
        thread_id: str = "default",
        use_structured_output: bool = False,
    ) -> dict:
        """
        Run a single analysis type.

        Args:
            analysis_type: One of "investment_themes", "new_entities",
                          "missing_attributes", "implied_relationships"
            thread_id: Unique identifier for this conversation thread
            use_structured_output: If True, request and parse structured JSON output.

        Returns:
            Dictionary containing the analysis result

        Raises:
            ValueError: If analysis_type is not recognized
        """
        if analysis_type not in ANALYSIS_TYPES:
            raise ValueError(
                f"Unknown analysis type: {analysis_type}. "
                f"Must be one of: {ANALYSIS_TYPES}"
            )

        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "messages": [],
            "current_analysis": analysis_type,
            "completed_analyses": [],
            "results": {},
            "structured_response": None,
            "error": None,
            "run_all": False,
            "use_structured_output": use_structured_output,
        }

        result = self.graph.invoke(initial_state, config)
        return result

    def get_state(self, thread_id: str = "default") -> dict:
        """
        Get the current state for a thread.

        Args:
            thread_id: The thread identifier

        Returns:
            The current state snapshot
        """
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.get_state(config)

    def get_results(self, thread_id: str = "default") -> dict[str, AnalysisResult]:
        """
        Get analysis results from the state.

        Args:
            thread_id: The thread identifier

        Returns:
            Dictionary mapping analysis types to their results
        """
        state = self.get_state(thread_id)
        if state and state.values:
            return state.values.get("results", {})
        return {}

    def get_structured_response(self, thread_id: str = "default") -> AugmentationResponse | None:
        """
        Get the structured AugmentationResponse from the state.

        Args:
            thread_id: The thread identifier

        Returns:
            AugmentationResponse if available, None otherwise
        """
        state = self.get_state(thread_id)
        if state and state.values:
            response_data = state.values.get("structured_response")
            if response_data:
                try:
                    return AugmentationResponse.model_validate(response_data)
                except ValidationError:
                    return None
        return None

    def get_suggested_nodes(self, thread_id: str = "default") -> list[SuggestedNode]:
        """
        Get all suggested nodes from the structured response.

        Args:
            thread_id: The thread identifier

        Returns:
            List of SuggestedNode objects
        """
        response = self.get_structured_response(thread_id)
        if response:
            return response.all_suggested_nodes
        return []

    def get_suggested_relationships(self, thread_id: str = "default") -> list[SuggestedRelationship]:
        """
        Get all suggested relationships from the structured response.

        Args:
            thread_id: The thread identifier

        Returns:
            List of SuggestedRelationship objects
        """
        response = self.get_structured_response(thread_id)
        if response:
            return response.all_suggested_relationships
        return []

    def get_suggested_attributes(self, thread_id: str = "default") -> list[SuggestedAttribute]:
        """
        Get all suggested attributes from the structured response.

        Args:
            thread_id: The thread identifier

        Returns:
            List of SuggestedAttribute objects
        """
        response = self.get_structured_response(thread_id)
        if response:
            return response.all_suggested_attributes
        return []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def setup_mlflow():
    """Enable MLflow tracing for debugging and monitoring."""
    try:
        import mlflow
        mlflow.openai.autolog()
        print("[OK] MLflow tracing enabled")
        return True
    except ImportError:
        print("[WARN] MLflow not installed, tracing disabled")
        return False
    except Exception as e:
        print(f"[WARN] MLflow setup failed: {e}")
        return False


def print_results(results: dict[str, AnalysisResult], verbose: bool = True):
    """Print analysis results in a formatted way."""
    for analysis_type, result in results.items():
        print("\n" + "=" * 70)
        print(f"ANALYSIS: {analysis_type.upper()}")
        print("=" * 70)

        if result.get("success"):
            # Check for structured data
            if result.get("structured_data"):
                print("[STRUCTURED OUTPUT]")
                data = result["structured_data"]

                # Print summary based on analysis type
                if "summary" in data:
                    print(f"Summary: {data['summary'][:200]}...")

                if analysis_type == "investment_themes" and "themes" in data:
                    print(f"Themes found: {len(data['themes'])}")
                    for theme in data["themes"][:3]:  # Show first 3
                        print(f"  - {theme.get('name', 'Unknown')}: {theme.get('description', '')[:80]}...")

                elif analysis_type == "new_entities" and "suggested_nodes" in data:
                    print(f"Nodes suggested: {len(data['suggested_nodes'])}")
                    for node in data["suggested_nodes"][:3]:
                        print(f"  - {node.get('label', 'UNKNOWN')}: {node.get('description', '')[:60]}...")

                elif analysis_type == "missing_attributes" and "suggested_attributes" in data:
                    print(f"Attributes suggested: {len(data['suggested_attributes'])}")
                    for attr in data["suggested_attributes"][:3]:
                        print(f"  - {attr.get('property_name', 'unknown')}: {attr.get('description', '')[:60]}...")

                elif analysis_type == "implied_relationships" and "suggested_relationships" in data:
                    print(f"Relationships suggested: {len(data['suggested_relationships'])}")
                    for rel in data["suggested_relationships"][:3]:
                        print(f"  - {rel.get('relationship_type', 'UNKNOWN')}: {rel.get('description', '')[:60]}...")

            elif verbose:
                # Print raw response for non-structured output
                print(f"Query: {result.get('query', 'N/A')[:100]}...")
                print("-" * 70)
                response = result.get("response", "No response")
                # Truncate long responses
                if len(response) > 1000:
                    print(response[:1000] + "\n... [truncated]")
                else:
                    print(response)
            else:
                print("[SUCCESS] Response received (use verbose=True to see full response)")

            if result.get("parsing_error"):
                print(f"\n[WARN] Parsing error: {result['parsing_error']}")
        else:
            print(f"FAILED: {result.get('error', 'Unknown error')}")

        print("=" * 70)


def print_structured_summary(response: AugmentationResponse):
    """Print a summary of the structured response."""
    print("\n" + "=" * 70)
    print("STRUCTURED OUTPUT SUMMARY")
    print("=" * 70)

    print(f"\nTotal suggestions: {response.total_suggestions}")
    print(f"High confidence: {response.high_confidence_count}")

    if response.all_suggested_nodes:
        print(f"\nSuggested Nodes ({len(response.all_suggested_nodes)}):")
        for node in response.all_suggested_nodes:
            confidence = node.confidence.value if hasattr(node.confidence, 'value') else node.confidence
            print(f"  - {node.label} [{confidence}]: {node.description[:50]}...")

    if response.all_suggested_relationships:
        print(f"\nSuggested Relationships ({len(response.all_suggested_relationships)}):")
        for rel in response.all_suggested_relationships:
            confidence = rel.confidence.value if hasattr(rel.confidence, 'value') else rel.confidence
            print(f"  - {rel.relationship_type} [{confidence}]: ({rel.source_label})-[{rel.relationship_type}]->({rel.target_label})")

    if response.all_suggested_attributes:
        print(f"\nSuggested Attributes ({len(response.all_suggested_attributes)}):")
        for attr in response.all_suggested_attributes:
            confidence = attr.confidence.value if hasattr(attr.confidence, 'value') else attr.confidence
            print(f"  - {attr.target_label}.{attr.property_name} [{confidence}]: {attr.property_type}")

    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================

def main(use_structured_output: bool = True):
    """
    Main entry point for the Graph Augmentation Agent.

    Args:
        use_structured_output: If True, request and parse structured JSON output.
    """
    print("\n" + "=" * 70)
    print("GRAPH AUGMENTATION AGENT - LANGGRAPH IMPLEMENTATION")
    print("=" * 70)
    print(f"Endpoint: {LLM_ENDPOINT_NAME}")
    print(f"Structured Output: {'Enabled' if use_structured_output else 'Disabled'}")
    print("=" * 70)

    # Setup
    setup_mlflow()

    # Create agent with checkpointer for memory
    checkpointer = MemorySaver()
    agent = GraphAugmentationAgent(checkpointer=checkpointer)

    print("\n[OK] Agent initialized with LangGraph workflow")
    print("[OK] Memory persistence enabled via MemorySaver")

    # Run all analyses
    print("\n" + "-" * 70)
    print("Running all analyses...")
    print("-" * 70)

    thread_id = "augmentation-session-structured" if use_structured_output else "augmentation-session-1"
    result = agent.run_all_analyses(
        thread_id=thread_id,
        use_structured_output=use_structured_output,
    )

    # Print results
    results = result.get("results", {})
    print_results(results, verbose=not use_structured_output)

    # Print structured summary if available
    if use_structured_output:
        structured_response = agent.get_structured_response(thread_id)
        if structured_response:
            print_structured_summary(structured_response)
        else:
            print("\n[WARN] No structured response available")

    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Analyses completed: {len(results)}")
    print(f"\nThe agent state is persisted (thread_id='{thread_id}'). You can:")
    print(f"  - agent.get_results('{thread_id}') - Get raw results")
    print(f"  - agent.get_structured_response('{thread_id}') - Get structured response")
    print(f"  - agent.get_suggested_nodes('{thread_id}') - Get suggested nodes")
    print(f"  - agent.get_suggested_relationships('{thread_id}') - Get suggested relationships")
    print(f"  - agent.get_suggested_attributes('{thread_id}') - Get suggested attributes")
    print("=" * 70)

    return agent, result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Graph Augmentation Agent")
    parser.add_argument(
        "--no-structured",
        action="store_true",
        help="Disable structured output (use free-form text)",
    )
    args = parser.parse_args()

    agent, result = main(use_structured_output=not args.no_structured)
