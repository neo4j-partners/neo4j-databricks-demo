"""
Graph Augmentation Agent - Native Structured Output with ChatDatabricks

This agent analyzes unstructured documents and suggests graph augmentations
for Neo4j using LangGraph workflows and native Pydantic structured output.

Key Features:
    - Native Pydantic structured output via ChatDatabricks.with_structured_output()
    - LangGraph StateGraph for workflow orchestration
    - Memory persistence via MemorySaver checkpointing
    - Modular architecture for easy extension

Documentation References:
    - ChatDatabricks with_structured_output():
      https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html

    - Databricks Structured Outputs:
      https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs

    - LangGraph StateGraph:
      https://langchain-ai.github.io/langgraph/concepts/low_level/

    - LangGraph Checkpointing:
      https://langchain-ai.github.io/langgraph/concepts/persistence/

Usage:
    uv run python -m lab_6_augmentation_agent.augmentation_agent
    uv run python -m lab_6_augmentation_agent.augmentation_agent --export results.json

Module Structure:
    augmentation_agent.py  - Main entry point (this file)
    schemas.py             - Pydantic schemas for structured output
    core/                  - Modular components
        config.py          - Configuration and analysis types
        state.py           - LangGraph state schema
        client.py          - ChatDatabricks structured output client
        nodes.py           - LangGraph node functions
        graph.py           - Graph construction and agent class
        output.py          - Demo output formatting helpers
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Load .env from project root
# Reference: https://docs.databricks.com/aws/en/dev-tools/auth/
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods - use only HOST + TOKEN from .env
for var in [
    "DATABRICKS_CONFIG_PROFILE",
    "DATABRICKS_CLIENT_ID",
    "DATABRICKS_CLIENT_SECRET",
    "DATABRICKS_ACCOUNT_ID",
]:
    os.environ.pop(var, None)

# =============================================================================
# IMPORTS FROM CORE MODULES
# =============================================================================

from lab_6_augmentation_agent.core import (
    AnalysisType,
    GraphAugmentationAgent,
    LLM_MODEL,
    print_analysis_result,
    print_header,
    print_section,
    print_summary,
)

# Re-export for convenience
__all__ = [
    "GraphAugmentationAgent",
    "AnalysisType",
    "main",
]


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main(export_path: str | None = None) -> tuple[GraphAugmentationAgent, dict]:
    """
    Main entry point for the Graph Augmentation Agent.

    Runs all analyses and prints formatted results.

    Args:
        export_path: Optional path to export results as JSON

    Returns:
        Tuple of (agent, final_state)
    """
    print_header("GRAPH AUGMENTATION AGENT")
    print(f"\n  Model:  {LLM_MODEL}")
    print("  Method: ChatDatabricks.with_structured_output()")
    print("  Docs:   https://api-docs.databricks.com/python/databricks-ai-bridge/latest/")

    # Initialize agent
    agent = GraphAugmentationAgent()
    print("\n  [OK] Agent initialized with LangGraph workflow")
    print("  [OK] Memory persistence enabled via MemorySaver")

    # Run analyses
    print_section("RUNNING ANALYSES")
    start_time = time.time()

    thread_id = "demo-session"
    result = agent.run_all_analyses(thread_id=thread_id)
    total_time = time.time() - start_time

    # Print results
    print_section("RESULTS")
    for analysis_type in AnalysisType:
        if analysis_type.value in result.get("results", {}):
            print_analysis_result(analysis_type.value, result["results"][analysis_type.value])

    # Print summary
    response = agent.get_structured_response(thread_id)
    if response:
        print_summary(response)

        # Export if requested
        if export_path:
            agent.export_results(export_path, thread_id)
            print(f"\n  [OK] Results exported to: {export_path}")

    # Final stats
    print_header("COMPLETE")
    print(f"\n  Total time: {total_time:.1f}s")
    print(f"  Thread ID:  {thread_id}")
    print("\n  Available methods:")
    print(f"    agent.get_structured_response('{thread_id}')")
    print(f"    agent.get_suggested_nodes('{thread_id}')")
    print(f"    agent.export_results('results.json', '{thread_id}')")

    return agent, result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Graph Augmentation Agent - Native Structured Output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m lab_6_augmentation_agent.augmentation_agent
  uv run python -m lab_6_augmentation_agent.augmentation_agent --export results.json

Module Structure:
  augmentation_agent.py  - Main entry point
  schemas.py             - Pydantic schemas
  core/                  - Modular components
        """,
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export results to JSON file",
    )
    args = parser.parse_args()

    agent, result = main(export_path=args.export)
