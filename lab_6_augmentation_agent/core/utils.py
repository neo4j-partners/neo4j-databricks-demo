"""
Reusable utilities for the Graph Augmentation Agent.

This module provides utilities that can be shared between the
CLI application and Jupyter notebooks.

Functions:
    setup_environment: Configure Databricks authentication
    run_single_analysis: Execute one analysis type and return results
    format_analysis_result: Format analysis result for display
    display_suggestions: Display suggestions in a readable format
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from lab_6_augmentation_agent.core.client import get_llm_client
from lab_6_augmentation_agent.core.config import (
    ANALYSIS_CONFIGS,
    LLM_MODEL,
    AnalysisType,
)
from lab_6_augmentation_agent.core.state import AnalysisResult
from lab_6_augmentation_agent.schemas import ConfidenceLevel


def setup_environment(env_path: str | Path | None = None) -> dict[str, str | None]:
    """
    Configure environment for Databricks authentication.

    Loads .env file and clears conflicting auth methods to ensure
    only HOST + TOKEN authentication is used.

    Args:
        env_path: Path to .env file. If None, uses project root.

    Returns:
        Dict with DATABRICKS_HOST and DATABRICKS_TOKEN values

    Reference:
        https://docs.databricks.com/aws/en/dev-tools/auth/
    """
    from dotenv import load_dotenv

    # Determine .env path
    if env_path is None:
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"

    load_dotenv(env_path, override=True)

    # Clear conflicting auth methods - use only HOST + TOKEN
    for var in [
        "DATABRICKS_CONFIG_PROFILE",
        "DATABRICKS_CLIENT_ID",
        "DATABRICKS_CLIENT_SECRET",
        "DATABRICKS_ACCOUNT_ID",
    ]:
        os.environ.pop(var, None)

    return {
        "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST"),
        "DATABRICKS_TOKEN": os.environ.get("DATABRICKS_TOKEN"),
    }


def run_single_analysis(
    analysis_type: AnalysisType | str,
    verbose: bool = True,
) -> AnalysisResult:
    """
    Execute a single analysis type and return the result.

    This is a simplified interface for running one analysis at a time,
    useful for notebooks and interactive exploration.

    Args:
        analysis_type: The analysis type to run
        verbose: Whether to print progress messages

    Returns:
        AnalysisResult with structured data and metadata

    Example:
        >>> result = run_single_analysis(AnalysisType.NEW_ENTITIES)
        >>> if result.success:
        ...     print(f"Found {len(result.structured_data['suggested_nodes'])} nodes")
    """
    if isinstance(analysis_type, str):
        analysis_type = AnalysisType(analysis_type)

    config = ANALYSIS_CONFIGS[analysis_type]

    if verbose:
        print(f"Running: {config.display_name}")
        print(f"  Query: {config.query[:60]}...")

    client = get_llm_client()
    start_time = time.time()

    parsed_result, error, duration = client.query(analysis_type, config.query)

    result = AnalysisResult(
        analysis_type=analysis_type.value,
        query=config.query,
        structured_data=parsed_result.model_dump() if parsed_result else None,
        success=parsed_result is not None,
        error=error,
        duration_seconds=duration,
    )

    if verbose:
        if result.success:
            count = _count_items(result.structured_data)
            print(f"  Result: {count} items in {duration:.1f}s")
        else:
            print(f"  Error: {error}")

    return result


def _count_items(data: dict[str, Any] | None) -> int:
    """Count items in structured result data."""
    if not data:
        return 0
    return len(
        data.get("themes", [])
        or data.get("suggested_nodes", [])
        or data.get("suggested_attributes", [])
        or data.get("suggested_relationships", [])
    )


def format_analysis_result(result: AnalysisResult, max_items: int = 5) -> str:
    """
    Format an analysis result as a readable string.

    Args:
        result: The AnalysisResult to format
        max_items: Maximum number of items to show

    Returns:
        Formatted string representation
    """
    config = ANALYSIS_CONFIGS.get(AnalysisType(result.analysis_type))
    display_name = config.display_name if config else result.analysis_type

    lines = [f"=== {display_name} ==="]
    lines.append(f"Duration: {result.duration_seconds:.1f}s")

    if not result.success:
        lines.append(f"Status: FAILED")
        lines.append(f"Error: {result.error}")
        return "\n".join(lines)

    lines.append(f"Status: SUCCESS")

    data = result.structured_data or {}

    # Show summary if available
    if "summary" in data:
        lines.append(f"\nSummary: {data['summary'][:200]}...")

    # Show items based on type
    items = (
        data.get("themes", [])
        or data.get("suggested_nodes", [])
        or data.get("suggested_attributes", [])
        or data.get("suggested_relationships", [])
    )

    if items:
        lines.append(f"\nItems ({len(items)} total):")
        for item in items[:max_items]:
            name = (
                item.get("name")
                or item.get("label")
                or item.get("property_name")
                or item.get("relationship_type", "Unknown")
            )
            confidence = item.get("confidence", "medium")
            if hasattr(confidence, "value"):
                confidence = confidence.value
            lines.append(f"  - {name} [{confidence}]")

        if len(items) > max_items:
            lines.append(f"  ... and {len(items) - max_items} more")

    return "\n".join(lines)


def display_suggestions(
    result: AnalysisResult,
    show_evidence: bool = False,
    show_examples: bool = False,
) -> None:
    """
    Display suggestions from an analysis result in detail.

    Args:
        result: The AnalysisResult to display
        show_evidence: Whether to show source evidence
        show_examples: Whether to show example values
    """
    if not result.success or not result.structured_data:
        print(f"No data to display (success={result.success})")
        return

    data = result.structured_data
    analysis_type = AnalysisType(result.analysis_type)

    if analysis_type == AnalysisType.INVESTMENT_THEMES:
        _display_themes(data, show_evidence)
    elif analysis_type == AnalysisType.NEW_ENTITIES:
        _display_nodes(data, show_evidence, show_examples)
    elif analysis_type == AnalysisType.MISSING_ATTRIBUTES:
        _display_attributes(data, show_evidence, show_examples)
    elif analysis_type == AnalysisType.IMPLIED_RELATIONSHIPS:
        _display_relationships(data, show_evidence, show_examples)


def _display_themes(data: dict, show_evidence: bool) -> None:
    """Display investment themes."""
    themes = data.get("themes", [])
    print(f"\nInvestment Themes ({len(themes)}):")
    print("-" * 40)

    for theme in themes:
        conf = theme.get("confidence", "medium")
        print(f"\n{theme['name']} [{conf}]")
        print(f"  {theme.get('description', 'No description')}")

        if theme.get("market_size"):
            print(f"  Market Size: {theme['market_size']}")
        if theme.get("growth_projection"):
            print(f"  Growth: {theme['growth_projection']}")
        if theme.get("key_sectors"):
            print(f"  Sectors: {', '.join(theme['key_sectors'][:3])}")
        if show_evidence and theme.get("source_evidence"):
            print(f"  Evidence: {theme['source_evidence'][:100]}...")


def _display_nodes(data: dict, show_evidence: bool, show_examples: bool) -> None:
    """Display suggested nodes."""
    nodes = data.get("suggested_nodes", [])
    print(f"\nSuggested Nodes ({len(nodes)}):")
    print("-" * 40)

    for node in nodes:
        conf = node.get("confidence", "medium")
        print(f"\n:{node['label']} [{conf}]")
        print(f"  {node.get('description', 'No description')}")
        print(f"  Key Property: {node.get('key_property', 'N/A')}")

        props = node.get("properties", [])
        if props:
            print(f"  Properties: {', '.join(p['name'] for p in props[:4])}")

        if show_examples and node.get("example_values"):
            print(f"  Examples: {node['example_values'][:2]}")

        if show_evidence and node.get("source_evidence"):
            print(f"  Evidence: {node['source_evidence'][:100]}...")


def _display_attributes(data: dict, show_evidence: bool, show_examples: bool) -> None:
    """Display suggested attributes."""
    attrs = data.get("suggested_attributes", [])
    print(f"\nSuggested Attributes ({len(attrs)}):")
    print("-" * 40)

    for attr in attrs:
        conf = attr.get("confidence", "medium")
        print(f"\n{attr['target_label']}.{attr['property_name']}: {attr['property_type']} [{conf}]")
        print(f"  {attr.get('description', 'No description')}")

        if show_examples and attr.get("example_values"):
            print(f"  Examples: {attr['example_values'][:3]}")

        if show_evidence and attr.get("source_evidence"):
            print(f"  Evidence: {attr['source_evidence'][:100]}...")


def _display_relationships(data: dict, show_evidence: bool, show_examples: bool) -> None:
    """Display suggested relationships."""
    rels = data.get("suggested_relationships", [])
    print(f"\nSuggested Relationships ({len(rels)}):")
    print("-" * 40)

    for rel in rels:
        conf = rel.get("confidence", "medium")
        print(f"\n(:{rel['source_label']})-[:{rel['relationship_type']}]->(:{rel['target_label']}) [{conf}]")
        print(f"  {rel.get('description', 'No description')}")

        if show_examples and rel.get("example_instances"):
            print(f"  Examples: {rel['example_instances'][:2]}")

        if show_evidence and rel.get("source_evidence"):
            print(f"  Evidence: {rel['source_evidence'][:100]}...")


def get_high_confidence_items(result: AnalysisResult) -> list[dict[str, Any]]:
    """
    Extract high-confidence items from an analysis result.

    Args:
        result: The AnalysisResult to filter

    Returns:
        List of items with high confidence
    """
    if not result.success or not result.structured_data:
        return []

    data = result.structured_data
    items = (
        data.get("themes", [])
        + data.get("suggested_nodes", [])
        + data.get("suggested_attributes", [])
        + data.get("suggested_relationships", [])
    )

    return [
        item for item in items
        if item.get("confidence") in ("high", ConfidenceLevel.HIGH)
    ]


def get_model_info() -> dict[str, str]:
    """
    Get information about the configured LLM model.

    Returns:
        Dict with model name and method
    """
    return {
        "model": LLM_MODEL,
        "method": "ChatDatabricks.with_structured_output()",
        "docs": "https://api-docs.databricks.com/python/databricks-ai-bridge/latest/",
    }
