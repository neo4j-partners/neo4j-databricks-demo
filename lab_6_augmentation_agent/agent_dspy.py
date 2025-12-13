"""
Graph Augmentation Agent - DSPy Implementation

This script implements a DSPy-based agent for analyzing unstructured documents
and suggesting graph augmentations for Neo4j. It uses DSPy signatures for
declarative structured output instead of manual JSON parsing.

Key advantages over the original implementation:
- Automatic prompt generation from signatures
- Type-safe structured output via Pydantic models
- Built-in support for optimization via DSPy compiler
- Native MLflow tracing integration
- Simpler, more maintainable code

Prerequisites:
    1. Multi-Agent Supervisor deployed as a Databricks serving endpoint
    2. DSPy and MLflow installed (see pyproject.toml)
    3. .env file with DATABRICKS_HOST and DATABRICKS_TOKEN

Usage:
    uv run python -m lab_6_augmentation_agent.agent_dspy

References:
    - https://docs.databricks.com/aws/en/generative-ai/dspy/
    - https://dspy.ai/learn/programming/signatures/
    - https://dspy.ai/learn/programming/modules/
"""

from __future__ import annotations

import argparse

from lab_6_augmentation_agent.schemas import AugmentationResponse
from lab_6_augmentation_agent.dspy_modules.config import (
    configure_dspy,
    setup_mlflow_tracing,
)
from lab_6_augmentation_agent.dspy_modules.analyzers import (
    GraphAugmentationAnalyzer,
    InvestmentThemesResult,
    NewEntitiesResult,
    MissingAttributesResult,
    ImpliedRelationshipsResult,
)
from lab_6_augmentation_agent.utils import (
    ANALYSIS_TYPES,
    SAMPLE_DOCUMENT_CONTEXT,
    print_response_summary,
)

# Union of all result types for type hints
AnalysisResult = InvestmentThemesResult | NewEntitiesResult | MissingAttributesResult | ImpliedRelationshipsResult


class DSPyGraphAugmentationAgent:
    """
    DSPy-based agent for graph augmentation analysis.

    This agent uses DSPy modules with typed signatures to analyze documents
    and produce structured suggestions for graph schema improvements.

    Attributes:
        analyzer: The GraphAugmentationAnalyzer DSPy module
    """

    def __init__(
        self,
        model_name: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        use_json_adapter: bool = False,
        use_responses_api: bool = True,
        enable_tracing: bool = True,
    ):
        """
        Initialize the DSPy agent.

        Args:
            model_name: Databricks model endpoint name. Uses default if None.
            temperature: Sampling temperature for the LM.
            max_tokens: Maximum tokens in LM responses.
            use_json_adapter: Use JSONAdapter for structured output.
                             Note: JSONAdapter requires OpenAI-compatible endpoints.
            use_responses_api: Use DatabricksResponsesLM for MAS endpoints.
            enable_tracing: Enable MLflow tracing for observability.
        """
        # Configure DSPy globally
        configure_dspy(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            use_json_adapter=use_json_adapter,
            use_responses_api=use_responses_api,
        )

        # Enable MLflow tracing if requested
        if enable_tracing:
            setup_mlflow_tracing()

        # Create the analyzer module
        self.analyzer = GraphAugmentationAnalyzer()

        print("[OK] DSPy Graph Augmentation Agent initialized")

    def run_all_analyses(
        self,
        document_context: str,
    ) -> AugmentationResponse:
        """
        Run all analysis types on the provided document context.

        Args:
            document_context: The document content to analyze.

        Returns:
            AugmentationResponse with all suggestions consolidated.
        """
        print("\nRunning all analyses...")
        return self.analyzer(document_context=document_context)

    def run_single_analysis(
        self,
        analysis_type: str,
        document_context: str,
    ) -> AnalysisResult:
        """
        Run a single analysis type.

        Args:
            analysis_type: One of the ANALYSIS_TYPES.
            document_context: The document content to analyze.

        Returns:
            AnalysisResult for the specified analysis.
        """
        if analysis_type not in ANALYSIS_TYPES:
            raise ValueError(
                f"Unknown analysis type: {analysis_type}. "
                f"Must be one of: {ANALYSIS_TYPES}"
            )

        print(f"\nRunning {analysis_type} analysis...")
        return self.analyzer.run_single(analysis_type, document_context)


def main(
    analysis_type: str | None = None,
    use_sample_data: bool = True,
) -> tuple[DSPyGraphAugmentationAgent, AugmentationResponse | AnalysisResult]:
    """
    Main entry point for the DSPy Graph Augmentation Agent.

    Args:
        analysis_type: Specific analysis to run, or None for all analyses.
        use_sample_data: If True, use built-in sample data for testing.

    Returns:
        Tuple of (agent, response) for further interaction.
    """
    print("\n" + "=" * 70)
    print("GRAPH AUGMENTATION AGENT - DSPY IMPLEMENTATION")
    print("=" * 70)

    # Initialize the agent
    agent = DSPyGraphAugmentationAgent(
        temperature=0.1,
        max_tokens=4000,
        use_json_adapter=False,  # ChatAdapter for MAS endpoints
        use_responses_api=True,   # Use Responses API for MAS
        enable_tracing=True,
    )

    # Get document context
    if use_sample_data:
        document_context = SAMPLE_DOCUMENT_CONTEXT
        print("\n[INFO] Using sample document context for testing")
    else:
        # In production, you would fetch this from your data sources
        # or the Multi-Agent Supervisor
        document_context = SAMPLE_DOCUMENT_CONTEXT
        print("\n[INFO] Document context would be fetched from data sources")

    # Run analysis
    if analysis_type:
        result = agent.run_single_analysis(analysis_type, document_context)
        print(f"\nAnalysis result: {'SUCCESS' if result.success else 'FAILED'}")
        if result.success:
            print(f"Data type: {type(result.data).__name__}")
        if result.error:
            print(f"Error: {result.error}")
        if result.reasoning:
            print(f"\nReasoning:\n{result.reasoning[:500]}...")
        return agent, result
    else:
        response = agent.run_all_analyses(document_context)
        print_response_summary(response)
        return agent, response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DSPy Graph Augmentation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all analyses
    uv run python -m lab_6_augmentation_agent.agent_dspy

    # Run a specific analysis
    uv run python -m lab_6_augmentation_agent.agent_dspy --analysis investment_themes
    uv run python -m lab_6_augmentation_agent.agent_dspy --analysis new_entities
        """,
    )
    parser.add_argument(
        "--analysis",
        choices=ANALYSIS_TYPES,
        help="Run a specific analysis type instead of all",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        default=True,
        help="Use sample document data (default: True)",
    )

    args = parser.parse_args()

    agent, result = main(
        analysis_type=args.analysis,
        use_sample_data=args.sample,
    )
