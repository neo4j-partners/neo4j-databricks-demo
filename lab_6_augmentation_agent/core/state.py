"""
LangGraph state schema for the Graph Augmentation Agent.

This module defines:
    - AnalysisResult: Dataclass for individual analysis results
    - AgentState: TypedDict for LangGraph state management

Documentation References:
    - LangGraph State:
      https://langchain-ai.github.io/langgraph/concepts/low_level/#state

    - LangGraph Message Handling:
      https://langchain-ai.github.io/langgraph/concepts/low_level/#messages
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from lab_6_augmentation_agent.core.config import AnalysisType
from lab_6_augmentation_agent.schemas import AugmentationResponse


@dataclass
class AnalysisResult:
    """
    Result from a single analysis step with timing information.

    Attributes:
        analysis_type: The type of analysis performed
        query: The query sent to the LLM
        structured_data: Parsed Pydantic model as dict (if successful)
        success: Whether the analysis completed successfully
        error: Error message if analysis failed
        duration_seconds: Time taken for the analysis
    """

    analysis_type: str
    query: str
    structured_data: dict[str, Any] | None = None
    success: bool = False
    error: str | None = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization in LangGraph state."""
        return {
            "analysis_type": self.analysis_type,
            "query": self.query,
            "structured_data": self.structured_data,
            "success": self.success,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 2),
        }


class AgentState(TypedDict):
    """
    State schema for the Graph Augmentation Agent.

    This TypedDict defines the structure of data passed between nodes
    in the LangGraph workflow. The state is persisted via checkpointing
    to enable memory across sessions.

    Reference: https://langchain-ai.github.io/langgraph/concepts/low_level/#state

    Attributes:
        messages: Conversation history with add_messages reducer
        current_analysis: The analysis type currently being processed
        completed_analyses: List of completed analysis type values
        results: Dictionary mapping analysis types to serialized AnalysisResult
        structured_response: Final consolidated AugmentationResponse
        error: Any error message from the workflow
        run_all: Whether to run all analyses or just the current one
    """

    messages: Annotated[list[AnyMessage], add_messages]
    current_analysis: AnalysisType | None
    completed_analyses: list[str]
    results: dict[str, dict[str, Any]]  # Serialized AnalysisResult
    structured_response: AugmentationResponse | None
    error: str | None
    run_all: bool
