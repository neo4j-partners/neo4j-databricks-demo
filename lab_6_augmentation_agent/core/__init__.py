"""
Core modules for the Graph Augmentation Agent.

This package contains the modular components for the LangGraph-based
graph augmentation agent with native Pydantic structured output.

Modules:
    config: Configuration, analysis types, and prompts
    state: LangGraph state schema and result dataclasses
    client: ChatDatabricks structured output client
    nodes: LangGraph node functions
    graph: Graph construction and agent class
    output: Demo output formatting helpers
    utils: Reusable utilities for CLI and notebooks
"""

from lab_6_augmentation_agent.core.config import (
    AnalysisType,
    AnalysisConfig,
    ANALYSIS_CONFIGS,
    LLM_MODEL,
)
from lab_6_augmentation_agent.core.state import (
    AnalysisResult,
    AgentState,
)
from lab_6_augmentation_agent.core.client import (
    StructuredLLMClient,
    get_llm_client,
)
from lab_6_augmentation_agent.core.graph import (
    GraphAugmentationAgent,
    build_augmentation_graph,
)
from lab_6_augmentation_agent.core.output import (
    print_header,
    print_section,
    print_analysis_result,
    print_summary,
)
from lab_6_augmentation_agent.core.utils import (
    setup_environment,
    run_single_analysis,
    format_analysis_result,
    display_suggestions,
    get_high_confidence_items,
    get_model_info,
)

__all__ = [
    # Config
    "AnalysisType",
    "AnalysisConfig",
    "ANALYSIS_CONFIGS",
    "LLM_MODEL",
    # State
    "AnalysisResult",
    "AgentState",
    # Client
    "StructuredLLMClient",
    "get_llm_client",
    # Graph
    "GraphAugmentationAgent",
    "build_augmentation_graph",
    # Output
    "print_header",
    "print_section",
    "print_analysis_result",
    "print_summary",
    # Utils
    "setup_environment",
    "run_single_analysis",
    "format_analysis_result",
    "display_suggestions",
    "get_high_confidence_items",
    "get_model_info",
]
