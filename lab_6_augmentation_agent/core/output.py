"""
DEPRECATED: This LangGraph implementation does not work with MAS endpoints.

ChatDatabricks.with_structured_output() is incompatible with Multi-Agent Supervisor (MAS)
endpoints. All three methods (function_calling, json_schema, json_mode) fail.

Use the DSPy implementation instead:
    uv run python -m lab_6_augmentation_agent.agent_dspy

See WHY_NOT_LANGGRAPH.md for full technical details.

---

Demo output formatting helpers (DEPRECATED).

This module provides clean, formatted output for demos and CLI usage.
"""

from __future__ import annotations

from typing import Any

from lab_6_augmentation_agent.core.config import ANALYSIS_CONFIGS, AnalysisType
from lab_6_augmentation_agent.schemas import AugmentationResponse


def print_header(title: str, width: int = 70) -> None:
    """Print a formatted header with double-line border."""
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)


def print_section(title: str, width: int = 70) -> None:
    """Print a section divider with single-line border."""
    print("\n" + "-" * width)
    print(f" {title}")
    print("-" * width)


def print_analysis_result(analysis_type: str, result: dict[str, Any]) -> None:
    """
    Print a single analysis result with sample items.

    Args:
        analysis_type: The analysis type value
        result: The serialized AnalysisResult dictionary
    """
    config = ANALYSIS_CONFIGS.get(AnalysisType(analysis_type))
    display_name = config.display_name if config else analysis_type
    duration = result.get("duration_seconds", 0)

    if result.get("success"):
        data = result.get("structured_data", {})
        count = len(
            data.get("themes", [])
            or data.get("suggested_nodes", [])
            or data.get("suggested_attributes", [])
            or data.get("suggested_relationships", [])
        )
        print(f"\n  [{display_name}] {count} items ({duration:.1f}s)")

        # Show sample items (up to 3)
        items = (
            data.get("themes", [])[:3]
            or data.get("suggested_nodes", [])[:3]
            or data.get("suggested_attributes", [])[:3]
            or data.get("suggested_relationships", [])[:3]
        )
        for item in items:
            name = (
                item.get("name")
                or item.get("label")
                or item.get("property_name")
                or item.get("relationship_type", "Unknown")
            )
            confidence = item.get("confidence", "medium")
            # Handle both string and enum confidence values
            if hasattr(confidence, "value"):
                confidence = confidence.value
            print(f"    - {name} [{confidence}]")
        if count > 3:
            print(f"    ... and {count - 3} more")
    else:
        print(f"\n  [{display_name}] FAILED ({duration:.1f}s)")
        print(f"    Error: {result.get('error', 'Unknown error')}")


def print_summary(response: AugmentationResponse) -> None:
    """
    Print the final summary with all suggestions.

    Args:
        response: The AugmentationResponse with consolidated results
    """
    print_section("SUMMARY")

    print(f"\n  Total Suggestions: {response.total_suggestions}")
    print(f"  High Confidence:   {response.high_confidence_count}")

    if response.all_suggested_nodes:
        print(f"\n  Suggested Nodes ({len(response.all_suggested_nodes)}):")
        for node in response.all_suggested_nodes:
            conf = node.confidence.value if hasattr(node.confidence, "value") else node.confidence
            print(f"    - {node.label} [{conf}]")

    if response.all_suggested_relationships:
        print(f"\n  Suggested Relationships ({len(response.all_suggested_relationships)}):")
        for rel in response.all_suggested_relationships:
            conf = rel.confidence.value if hasattr(rel.confidence, "value") else rel.confidence
            print(f"    - ({rel.source_label})-[{rel.relationship_type}]->({rel.target_label}) [{conf}]")

    if response.all_suggested_attributes:
        print(f"\n  Suggested Attributes ({len(response.all_suggested_attributes)}):")
        for attr in response.all_suggested_attributes:
            conf = attr.confidence.value if hasattr(attr.confidence, "value") else attr.confidence
            print(f"    - {attr.target_label}.{attr.property_name}: {attr.property_type} [{conf}]")
