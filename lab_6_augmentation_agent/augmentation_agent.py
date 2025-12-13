"""
DEPRECATED: This LangGraph implementation does not work with MAS endpoints.

ChatDatabricks.with_structured_output() is incompatible with Multi-Agent Supervisor (MAS)
endpoints. All three methods (function_calling, json_schema, json_mode) fail because:
- function_calling: MAS doesn't support OpenAI tools format
- json_schema: MAS doesn't accept response_format parameter
- json_mode: MAS doesn't accept response_format parameter

Use the DSPy implementation instead:
    uv run python -m lab_6_augmentation_agent.agent_dspy

See WHY_NOT_LANGGRAPH.md for full technical details.

---

Original docstring (for reference):

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
    # CLI application (uses .env file for local development)
    uv run python -m lab_6_augmentation_agent.augmentation_agent
    uv run python -m lab_6_augmentation_agent.augmentation_agent --export results.json

    # On Databricks (uses dbutils.secrets)
    See augmentation_agent_notebook.ipynb for interactive exploration

Module Structure:
    augmentation_agent.py           - Main CLI entry point (this file)
    augmentation_agent_notebook.ipynb - Interactive notebook
    schemas.py                      - Pydantic schemas for structured output
    core/                           - Modular components
        config.py                   - Configuration and analysis types
        state.py                    - LangGraph state schema
        client.py                   - ChatDatabricks structured output client
        nodes.py                    - LangGraph node functions
        graph.py                    - Graph construction and agent class
        output.py                   - Demo output formatting helpers
        utils.py                    - Reusable utilities for CLI and notebooks
"""

from __future__ import annotations

import os
import time
from pathlib import Path

# =============================================================================
# CONFIGURATION - Edit these values before running
# =============================================================================

# Multi-Agent Supervisor endpoint (REQUIRED - created in Lab 5)
# This must be set to the endpoint name from Lab 5's Multi-Agent Supervisor
# Example: "agents_retail-investment-intelligence-system_agent"
MAS_ENDPOINT_NAME = "mas-3ae5a347-endpoint"

# Databricks Secrets scope for credentials (used when running on Databricks)
# For local development, credentials are loaded from .env file
SECRETS_SCOPE = "neo4j-creds"

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================


def setup_databricks_environment() -> dict[str, str | None]:
    """
    Configure environment for Databricks authentication.

    Attempts to load credentials in this order:
    1. Databricks Secrets (when running on Databricks)
    2. .env file (for local development)

    Returns:
        Dict with configuration status
    """
    print("=" * 70)
    print("ENVIRONMENT SETUP")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    databricks_host = None
    databricks_token = None
    auth_method = "unknown"

    # Try Databricks Secrets first (when running on Databricks)
    print(f"[DEBUG] Checking for Databricks Secrets (scope: {SECRETS_SCOPE})...")
    try:
        # This will only work on Databricks
        import IPython
        ipython = IPython.get_ipython()
        if ipython and hasattr(ipython, 'user_ns') and 'dbutils' in ipython.user_ns:
            dbutils = ipython.user_ns['dbutils']
            try:
                databricks_host = dbutils.secrets.get(scope=SECRETS_SCOPE, key="databricks_host")
                print(f"  [OK] databricks_host: {databricks_host[:30]}...")
            except Exception:
                print("  [SKIP] databricks_host not in secrets")

            try:
                databricks_token = dbutils.secrets.get(scope=SECRETS_SCOPE, key="databricks_token")
                print(f"  [OK] databricks_token: {'*' * 10}... ({len(databricks_token)} chars)")
                auth_method = "Databricks Secrets"
            except Exception:
                print("  [SKIP] databricks_token not in secrets")
        else:
            print("  [SKIP] Not running on Databricks, skipping secrets")
    except ImportError:
        print("  [SKIP] IPython not available, skipping secrets")
    except Exception as e:
        print(f"  [SKIP] Secrets not available: {type(e).__name__}")

    # Fall back to .env file for local development
    if not databricks_token:
        print("")
        print("[DEBUG] Loading from .env file...")
        try:
            from dotenv import load_dotenv

            project_root = Path(__file__).parent.parent
            env_path = project_root / ".env"

            if env_path.exists():
                load_dotenv(env_path, override=True)
                print(f"  [OK] Loaded: {env_path}")

                databricks_host = os.environ.get("DATABRICKS_HOST")
                databricks_token = os.environ.get("DATABRICKS_TOKEN")

                if databricks_host:
                    print(f"  [OK] DATABRICKS_HOST: {databricks_host[:30]}...")
                if databricks_token:
                    print(f"  [OK] DATABRICKS_TOKEN: {'*' * 10}... ({len(databricks_token)} chars)")
                    auth_method = ".env file"
            else:
                print(f"  [WARN] .env file not found at {env_path}")
        except ImportError:
            print("  [WARN] python-dotenv not installed, skipping .env")

    # Set environment variables
    if databricks_host:
        os.environ["DATABRICKS_HOST"] = databricks_host
    if databricks_token:
        os.environ["DATABRICKS_TOKEN"] = databricks_token

    # Validate and set the Multi-Agent Supervisor endpoint (REQUIRED)
    if not MAS_ENDPOINT_NAME:
        print("")
        print("=" * 70)
        print("[FATAL] MAS_ENDPOINT_NAME is not configured!")
        print("=" * 70)
        print("  The Lab 6 Augmentation Agent requires the Lab 5 Multi-Agent")
        print("  Supervisor endpoint. Please set MAS_ENDPOINT_NAME in the")
        print("  configuration section at the top of this file.")
        print("")
        print("  Example:")
        print('    MAS_ENDPOINT_NAME = "agents_retail-investment-intelligence-system_agent"')
        print("=" * 70)
        raise SystemExit("MAS_ENDPOINT_NAME is required but not set")

    os.environ["MAS_ENDPOINT_NAME"] = MAS_ENDPOINT_NAME

    # Clear conflicting auth methods
    for var in [
        "DATABRICKS_CONFIG_PROFILE",
        "DATABRICKS_CLIENT_ID",
        "DATABRICKS_CLIENT_SECRET",
        "DATABRICKS_ACCOUNT_ID",
    ]:
        os.environ.pop(var, None)

    print("")
    print("=" * 70)
    print("CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"  Databricks Host: {databricks_host[:40] if databricks_host else 'Not set'}...")
    print(f"  Auth Method:     {auth_method}")
    print(f"  Mode:            Multi-Agent Supervisor (Lab 5)")
    print(f"  Endpoint:        {MAS_ENDPOINT_NAME}")
    print("=" * 70)

    return {
        "DATABRICKS_HOST": databricks_host,
        "DATABRICKS_TOKEN": "***" if databricks_token else None,
        "MAS_ENDPOINT_NAME": MAS_ENDPOINT_NAME,
        "auth_method": auth_method,
    }


# =============================================================================
# IMPORTS FROM CORE MODULES
# =============================================================================

from lab_6_augmentation_agent.core import (
    AnalysisType,
    GraphAugmentationAgent,
    get_endpoint_info,
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
    # Setup environment (loads secrets or .env and configures auth)
    setup_databricks_environment()

    # Get endpoint info
    endpoint_info = get_endpoint_info()

    print_header("GRAPH AUGMENTATION AGENT")
    print(f"\n  Endpoint: {endpoint_info['endpoint']}")
    print(f"  Mode:     {endpoint_info['mode']}")
    print(f"  Method:   {endpoint_info['method']}")
    print(f"  Docs:     {endpoint_info['docs']}")

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

Configuration:
  Edit the CONFIGURATION section at the top of this file to change:
  - MAS_ENDPOINT_NAME: Lab 5 Multi-Agent Supervisor endpoint (required)
  - SECRETS_SCOPE: Databricks secrets scope

Interactive:
  See augmentation_agent_notebook.ipynb for step-by-step exploration

Module Structure:
  augmentation_agent.py  - Main CLI entry point
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
