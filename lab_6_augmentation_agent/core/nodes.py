"""
LangGraph node functions for the Graph Augmentation Agent.

This module contains the node functions that execute at each step
of the LangGraph workflow.

Documentation References:
    - LangGraph Nodes:
      https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes

    - LangGraph Conditional Edges:
      https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import ValidationError

from lab_6_augmentation_agent.core.client import get_mas_client
from lab_6_augmentation_agent.core.config import ANALYSIS_CONFIGS, AnalysisType
from lab_6_augmentation_agent.core.state import AgentState, AnalysisResult
from lab_6_augmentation_agent.schemas import (
    AugmentationAnalysis,
    AugmentationResponse,
    ImpliedRelationshipsAnalysis,
    InvestmentThemesAnalysis,
    MissingAttributesAnalysis,
    NewEntitiesAnalysis,
    SuggestedAttribute,
    SuggestedNode,
    SuggestedRelationship,
)


def initialize_node(state: AgentState) -> dict[str, Any]:
    """
    Initialize the workflow state.

    Sets up default values and adds an initial system message.
    """
    return {
        "messages": [SystemMessage(content="Graph Augmentation Agent initialized.")],
        "completed_analyses": state.get("completed_analyses", []),
        "results": state.get("results", {}),
        "error": None,
    }


def select_next_analysis_node(state: AgentState) -> dict[str, Any]:
    """
    Select the next analysis to perform.

    Iterates through AnalysisType enum to find the next uncompleted analysis.
    """
    completed = set(state.get("completed_analyses", []))
    run_all = state.get("run_all", True)

    if not run_all:
        current = state.get("current_analysis")
        if current and current in completed:
            return {"current_analysis": None}
        return {}

    # Find next uncompleted analysis
    for analysis_type in AnalysisType:
        if analysis_type.value not in completed:
            config = ANALYSIS_CONFIGS[analysis_type]
            return {
                "current_analysis": analysis_type,
                "messages": [HumanMessage(content=f"Starting: {config.display_name}")],
            }

    return {"current_analysis": None}


def run_analysis_node(state: AgentState) -> dict[str, Any]:
    """
    Execute the current analysis using MAS endpoint with structured output.

    Queries the MAS endpoint and stores the structured result in state.

    Reference: https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html
    """
    current = state.get("current_analysis")
    if not current:
        return {"error": "No analysis type selected"}

    config = ANALYSIS_CONFIGS[current]
    client = get_mas_client()

    # Execute query with structured output
    parsed_result, error, duration = client.query(current, config.query)

    # Build result
    result = AnalysisResult(
        analysis_type=current.value,
        query=config.query,
        structured_data=parsed_result.model_dump() if parsed_result else None,
        success=parsed_result is not None,
        error=error,
        duration_seconds=duration,
    )

    # Update state
    results = dict(state.get("results", {}))
    results[current.value] = result.to_dict()

    completed = list(state.get("completed_analyses", []))
    if current.value not in completed:
        completed.append(current.value)

    # Build summary message
    if parsed_result:
        count = _get_result_count(parsed_result)
        summary = f"{config.display_name}: {count} items ({duration:.1f}s)"
    else:
        summary = f"{config.display_name}: FAILED - {error}"

    return {
        "messages": [AIMessage(content=summary)],
        "results": results,
        "completed_analyses": completed,
        "error": None if parsed_result else error,
    }


def _get_result_count(result: Any) -> int:
    """Get the count of items in a structured result."""
    if hasattr(result, "themes"):
        return len(result.themes)
    if hasattr(result, "suggested_nodes"):
        return len(result.suggested_nodes)
    if hasattr(result, "suggested_attributes"):
        return len(result.suggested_attributes)
    if hasattr(result, "suggested_relationships"):
        return len(result.suggested_relationships)
    return 0


def summarize_node(state: AgentState) -> dict[str, Any]:
    """
    Generate final summary and build consolidated AugmentationResponse.

    Combines all analysis results into a single structured response.
    """
    results = state.get("results", {})
    completed = state.get("completed_analyses", [])

    # Build consolidated response
    analysis = AugmentationAnalysis()
    all_nodes: list[SuggestedNode] = []
    all_relationships: list[SuggestedRelationship] = []
    all_attributes: list[SuggestedAttribute] = []

    for analysis_type_str, result_dict in results.items():
        if not result_dict.get("success") or not result_dict.get("structured_data"):
            continue

        data = result_dict["structured_data"]

        try:
            if analysis_type_str == AnalysisType.INVESTMENT_THEMES.value:
                parsed = InvestmentThemesAnalysis.model_validate(data)
                analysis.investment_themes = parsed

            elif analysis_type_str == AnalysisType.NEW_ENTITIES.value:
                parsed = NewEntitiesAnalysis.model_validate(data)
                analysis.new_entities = parsed
                all_nodes.extend(parsed.suggested_nodes)

            elif analysis_type_str == AnalysisType.MISSING_ATTRIBUTES.value:
                parsed = MissingAttributesAnalysis.model_validate(data)
                analysis.missing_attributes = parsed
                all_attributes.extend(parsed.suggested_attributes)

            elif analysis_type_str == AnalysisType.IMPLIED_RELATIONSHIPS.value:
                parsed = ImpliedRelationshipsAnalysis.model_validate(data)
                analysis.implied_relationships = parsed
                all_relationships.extend(parsed.suggested_relationships)

        except ValidationError as e:
            print(f"  [!] Validation warning for {analysis_type_str}: {e}")

    # Build final response
    response = AugmentationResponse(
        success=True,
        analysis=analysis,
        all_suggested_nodes=all_nodes,
        all_suggested_relationships=all_relationships,
        all_suggested_attributes=all_attributes,
    )
    response.compute_statistics()

    # Calculate total duration
    total_duration = sum(r.get("duration_seconds", 0) for r in results.values())

    summary = (
        f"Analysis complete: {len(completed)} analyses, "
        f"{response.total_suggestions} suggestions, "
        f"{response.high_confidence_count} high confidence ({total_duration:.1f}s total)"
    )

    return {
        "messages": [AIMessage(content=summary)],
        "structured_response": response,
    }


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================


def should_continue_analysis(state: AgentState) -> Literal["run_analysis", "summarize"]:
    """
    Determine whether to continue with more analyses or summarize.

    Reference: https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges
    """
    return "run_analysis" if state.get("current_analysis") else "summarize"


def should_select_next(state: AgentState) -> Literal["select_next", "summarize"]:
    """
    Determine whether to select the next analysis or finish.

    Reference: https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges
    """
    if not state.get("run_all", True):
        return "summarize"
    completed = state.get("completed_analyses", [])
    return "select_next" if len(completed) < len(AnalysisType) else "summarize"
