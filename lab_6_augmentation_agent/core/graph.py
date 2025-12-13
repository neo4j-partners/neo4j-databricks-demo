"""
LangGraph construction and agent class.

This module contains:
    - build_augmentation_graph: Creates the StateGraph workflow
    - GraphAugmentationAgent: Main agent class with convenience methods

Documentation References:
    - LangGraph StateGraph:
      https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph

    - LangGraph Checkpointing:
      https://langchain-ai.github.io/langgraph/concepts/persistence/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from lab_6_augmentation_agent.core.config import AnalysisType
from lab_6_augmentation_agent.core.nodes import (
    initialize_node,
    run_analysis_node,
    select_next_analysis_node,
    should_continue_analysis,
    should_select_next,
    summarize_node,
)
from lab_6_augmentation_agent.core.state import AgentState
from lab_6_augmentation_agent.schemas import (
    AugmentationResponse,
    SuggestedAttribute,
    SuggestedNode,
    SuggestedRelationship,
)


def build_augmentation_graph() -> StateGraph:
    """
    Build the LangGraph StateGraph for the augmentation workflow.

    The workflow follows this pattern:
        START -> initialize -> select_next -> run_analysis -> select_next -> ... -> summarize -> END

    Reference: https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph

    Returns:
        Configured StateGraph ready for compilation
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("initialize", initialize_node)
    workflow.add_node("select_next", select_next_analysis_node)
    workflow.add_node("run_analysis", run_analysis_node)
    workflow.add_node("summarize", summarize_node)

    # Define edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "select_next")

    # Conditional edges for workflow control
    # Reference: https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges
    workflow.add_conditional_edges(
        "select_next",
        should_continue_analysis,
        {"run_analysis": "run_analysis", "summarize": "summarize"},
    )
    workflow.add_conditional_edges(
        "run_analysis",
        should_select_next,
        {"select_next": "select_next", "summarize": "summarize"},
    )
    workflow.add_edge("summarize", END)

    return workflow


class GraphAugmentationAgent:
    """
    LangGraph-based agent with native Pydantic structured output.

    This agent uses ChatDatabricks.with_structured_output() for native
    Pydantic validation, eliminating manual JSON parsing.

    Reference:
        - https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html
        - https://langchain-ai.github.io/langgraph/concepts/persistence/

    Example:
        >>> agent = GraphAugmentationAgent()
        >>> result = agent.run_all_analyses()
        >>> response = agent.get_structured_response()
        >>> print(f"Found {response.total_suggestions} suggestions")

    Attributes:
        graph: The compiled LangGraph workflow
        checkpointer: MemorySaver for state persistence
    """

    def __init__(self, checkpointer: MemorySaver | None = None):
        """
        Initialize the agent with optional checkpointer for memory persistence.

        Args:
            checkpointer: Optional MemorySaver instance. If None, creates a new one.
        """
        self.checkpointer = checkpointer or MemorySaver()
        workflow = build_augmentation_graph()
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        self._last_thread_id: str | None = None

    def run_all_analyses(self, thread_id: str = "default") -> dict[str, Any]:
        """
        Run all analysis types and return the results.

        Args:
            thread_id: Unique identifier for conversation thread (enables memory)

        Returns:
            Final state dictionary with all results
        """
        self._last_thread_id = thread_id
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: AgentState = {
            "messages": [],
            "current_analysis": None,
            "completed_analyses": [],
            "results": {},
            "structured_response": None,
            "error": None,
            "run_all": True,
        }

        return self.graph.invoke(initial_state, config)

    def run_single_analysis(
        self,
        analysis_type: AnalysisType | str,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        """
        Run a single analysis type.

        Args:
            analysis_type: The analysis type (AnalysisType enum or string value)
            thread_id: Unique identifier for conversation thread

        Returns:
            Final state dictionary with the analysis result
        """
        if isinstance(analysis_type, str):
            analysis_type = AnalysisType(analysis_type)

        self._last_thread_id = thread_id
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: AgentState = {
            "messages": [],
            "current_analysis": analysis_type,
            "completed_analyses": [],
            "results": {},
            "structured_response": None,
            "error": None,
            "run_all": False,
        }

        return self.graph.invoke(initial_state, config)

    def get_state(self, thread_id: str | None = None) -> dict[str, Any] | None:
        """
        Get the current state for a thread.

        Args:
            thread_id: Thread identifier (uses last used if None)

        Returns:
            State values dictionary or None
        """
        thread_id = thread_id or self._last_thread_id or "default"
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        return state.values if state else None

    def get_structured_response(self, thread_id: str | None = None) -> AugmentationResponse | None:
        """
        Get the structured AugmentationResponse from the state.

        Args:
            thread_id: Thread identifier (uses last used if None)

        Returns:
            AugmentationResponse or None if not available
        """
        state = self.get_state(thread_id)
        return state.get("structured_response") if state else None

    def get_suggested_nodes(self, thread_id: str | None = None) -> list[SuggestedNode]:
        """
        Get all suggested nodes from the structured response.

        Args:
            thread_id: Thread identifier (uses last used if None)

        Returns:
            List of SuggestedNode objects
        """
        response = self.get_structured_response(thread_id)
        return response.all_suggested_nodes if response else []

    def get_suggested_relationships(self, thread_id: str | None = None) -> list[SuggestedRelationship]:
        """
        Get all suggested relationships from the structured response.

        Args:
            thread_id: Thread identifier (uses last used if None)

        Returns:
            List of SuggestedRelationship objects
        """
        response = self.get_structured_response(thread_id)
        return response.all_suggested_relationships if response else []

    def get_suggested_attributes(self, thread_id: str | None = None) -> list[SuggestedAttribute]:
        """
        Get all suggested attributes from the structured response.

        Args:
            thread_id: Thread identifier (uses last used if None)

        Returns:
            List of SuggestedAttribute objects
        """
        response = self.get_structured_response(thread_id)
        return response.all_suggested_attributes if response else []

    def export_results(self, filepath: str | Path, thread_id: str | None = None) -> None:
        """
        Export results to a JSON file.

        Args:
            filepath: Path to the output JSON file
            thread_id: Thread identifier (uses last used if None)

        Raises:
            ValueError: If no results are available to export
        """
        response = self.get_structured_response(thread_id)
        if not response:
            raise ValueError("No results to export")

        with open(filepath, "w") as f:
            json.dump(response.model_dump(), f, indent=2, default=str)
