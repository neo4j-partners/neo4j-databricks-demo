"""
Shared utilities for the Graph Augmentation Agent.

This module contains reusable components for both the CLI agent and
Jupyter notebook implementations:
- Sample data for testing
- Display functions for analysis results
- Constants and type definitions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from lab_6_augmentation_agent.schemas import (
        AugmentationResponse,
        InvestmentThemesAnalysis,
        NewEntitiesAnalysis,
        MissingAttributesAnalysis,
        ImpliedRelationshipsAnalysis,
    )
    from lab_6_augmentation_agent.dspy_modules.analyzers import (
        InvestmentThemesResult,
        NewEntitiesResult,
        MissingAttributesResult,
        ImpliedRelationshipsResult,
    )

from lab_6_augmentation_agent.schemas import ConfidenceLevel


# Analysis types available (immutable tuple for type safety)
ANALYSIS_TYPES: Final[tuple[str, ...]] = (
    "investment_themes",
    "new_entities",
    "missing_attributes",
    "implied_relationships",
)

# Sample document context for testing
# In production, this would come from your Multi-Agent Supervisor
SAMPLE_DOCUMENT_CONTEXT: Final[str] = """
Market Research Analysis - Q4 2024

Investment Themes:
1. Renewable Energy Transition
   - Market size: $495 billion globally
   - Growth projection: 15% CAGR through 2030
   - Key sectors: Solar, Wind, Battery Storage
   - Key companies: Tesla, NextEra Energy, Vestas

2. AI/ML Infrastructure
   - Explosive growth in compute demand
   - Data center investments surging
   - Key players: NVIDIA, AMD, Microsoft Azure

Customer Profile Data:
- Customer ID: C-12345
- Name: John Smith
- Occupation: Software Engineer at TechCorp
- Annual Income: $185,000
- Investment Goals: Retirement planning, children's education fund
- Risk Tolerance: Moderate
- Interests: Technology stocks, ESG investing, Real estate
- Life Stage: Mid-career with young family
- Preferred Communication: Email, Mobile app

Entity Relationships Observed:
- John Smith WORKS_AT TechCorp
- John Smith HAS_GOAL "Retirement by 60"
- John Smith HAS_GOAL "College fund for kids"
- John Smith INTERESTED_IN "ESG Investing"
- John Smith SIMILAR_TO customers with tech backgrounds and moderate risk

Missing from current graph:
- Customer occupation details
- Investment goals as separate nodes
- Interest categories
- Life stage classification
- Risk tolerance scoring
"""


def _get_confidence_str(confidence: ConfidenceLevel | str) -> str:
    """Extract confidence string from ConfidenceLevel enum or string."""
    return confidence.value if isinstance(confidence, ConfidenceLevel) else confidence


def print_investment_themes(themes: InvestmentThemesAnalysis) -> None:
    """Print formatted investment themes analysis results."""
    print(f"\n{'='*60}")
    print("INVESTMENT THEMES ANALYSIS")
    print(f"{'='*60}")
    print(f"\nSummary: {themes.summary[:300]}..." if len(themes.summary) > 300 else f"\nSummary: {themes.summary}")
    print(f"\nThemes Found: {len(themes.themes)}")

    for i, theme in enumerate(themes.themes, 1):
        confidence = _get_confidence_str(theme.confidence)
        print(f"\n  {i}. {theme.name} [{confidence}]")
        print(f"     {theme.description[:100]}...")
        if theme.market_size:
            print(f"     Market Size: {theme.market_size}")
        if theme.growth_projection:
            print(f"     Growth: {theme.growth_projection}")
        if theme.key_sectors:
            print(f"     Sectors: {', '.join(theme.key_sectors[:5])}")
        if theme.key_companies:
            print(f"     Companies: {', '.join(theme.key_companies[:5])}")

    if themes.recommendations:
        print(f"\nRecommendations:")
        for rec in themes.recommendations[:3]:
            print(f"  - {rec}")


def print_new_entities(entities: NewEntitiesAnalysis) -> None:
    """Print formatted new entities analysis results."""
    print(f"\n{'='*60}")
    print("NEW ENTITIES ANALYSIS")
    print(f"{'='*60}")
    print(f"\nSummary: {entities.summary[:300]}..." if len(entities.summary) > 300 else f"\nSummary: {entities.summary}")
    print(f"\nSuggested Nodes: {len(entities.suggested_nodes)}")

    for i, node in enumerate(entities.suggested_nodes, 1):
        confidence = _get_confidence_str(node.confidence)
        print(f"\n  {i}. {node.label} [{confidence}]")
        print(f"     Key Property: {node.key_property}")
        print(f"     {node.description[:100]}...")
        if node.properties:
            props = [f"{p.name}:{p.property_type}" for p in node.properties[:3]]
            print(f"     Properties: {', '.join(props)}")
        print(f"     Rationale: {node.rationale[:80]}...")

    if entities.implementation_priority:
        print(f"\nImplementation Priority:")
        for i, item in enumerate(entities.implementation_priority[:5], 1):
            print(f"  {i}. {item}")


def print_missing_attributes(attributes: MissingAttributesAnalysis) -> None:
    """Print formatted missing attributes analysis results."""
    print(f"\n{'='*60}")
    print("MISSING ATTRIBUTES ANALYSIS")
    print(f"{'='*60}")
    print(f"\nSummary: {attributes.summary[:300]}..." if len(attributes.summary) > 300 else f"\nSummary: {attributes.summary}")
    print(f"\nSuggested Attributes: {len(attributes.suggested_attributes)}")

    for i, attr in enumerate(attributes.suggested_attributes, 1):
        confidence = _get_confidence_str(attr.confidence)
        print(f"\n  {i}. {attr.target_label}.{attr.property_name}: {attr.property_type} [{confidence}]")
        print(f"     {attr.description[:100]}...")
        if attr.example_values:
            examples = [str(v) for v in attr.example_values[:3]]
            print(f"     Examples: {', '.join(examples)}")
        print(f"     Rationale: {attr.rationale[:80]}...")

    if attributes.affected_node_types:
        print(f"\nAffected Node Types: {', '.join(attributes.affected_node_types)}")


def print_implied_relationships(relationships: ImpliedRelationshipsAnalysis) -> None:
    """Print formatted implied relationships analysis results."""
    print(f"\n{'='*60}")
    print("IMPLIED RELATIONSHIPS ANALYSIS")
    print(f"{'='*60}")
    print(f"\nSummary: {relationships.summary[:300]}..." if len(relationships.summary) > 300 else f"\nSummary: {relationships.summary}")
    print(f"\nSuggested Relationships: {len(relationships.suggested_relationships)}")

    for i, rel in enumerate(relationships.suggested_relationships, 1):
        confidence = _get_confidence_str(rel.confidence)
        print(f"\n  {i}. ({rel.source_label})-[{rel.relationship_type}]->({rel.target_label}) [{confidence}]")
        print(f"     {rel.description[:100]}...")
        if rel.properties:
            props = [f"{p.name}:{p.property_type}" for p in rel.properties[:3]]
            print(f"     Properties: {', '.join(props)}")
        print(f"     Rationale: {rel.rationale[:80]}...")

    if relationships.relationship_patterns:
        print(f"\nRelationship Patterns:")
        for pattern in relationships.relationship_patterns[:3]:
            print(f"  - {pattern}")


def print_analysis_result(
    result: InvestmentThemesResult | NewEntitiesResult | MissingAttributesResult | ImpliedRelationshipsResult,
    analysis_type: str,
) -> None:
    """Print a single analysis result with appropriate formatting."""
    if not result.success:
        print(f"\n[FAILED] {analysis_type} analysis")
        print(f"Error: {result.error}")
        return

    if result.reasoning:
        print(f"\n[Reasoning] {result.reasoning[:200]}...")

    if result.data is None:
        print(f"\n[WARNING] {analysis_type} returned no data")
        return

    # Import here to avoid circular imports
    from lab_6_augmentation_agent.schemas import (
        InvestmentThemesAnalysis,
        NewEntitiesAnalysis,
        MissingAttributesAnalysis,
        ImpliedRelationshipsAnalysis,
    )

    if isinstance(result.data, InvestmentThemesAnalysis):
        print_investment_themes(result.data)
    elif isinstance(result.data, NewEntitiesAnalysis):
        print_new_entities(result.data)
    elif isinstance(result.data, MissingAttributesAnalysis):
        print_missing_attributes(result.data)
    elif isinstance(result.data, ImpliedRelationshipsAnalysis):
        print_implied_relationships(result.data)


def print_response_summary(response: AugmentationResponse) -> None:
    """Print a formatted summary of the augmentation response."""
    print("\n" + "=" * 70)
    print("AUGMENTATION ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\nSuccess: {response.success}")
    print(f"Total suggestions: {response.total_suggestions}")
    print(f"High confidence: {response.high_confidence_count}")

    # Investment Themes
    if response.analysis.investment_themes:
        themes = response.analysis.investment_themes
        print(f"\n--- Investment Themes ({len(themes.themes)} found) ---")
        summary = themes.summary[:200] + "..." if len(themes.summary) > 200 else themes.summary
        print(f"Summary: {summary}")
        for theme in themes.themes[:3]:
            confidence = _get_confidence_str(theme.confidence)
            print(f"  - {theme.name} [{confidence}]")
            if theme.market_size:
                print(f"    Market: {theme.market_size}")

    # Suggested Nodes
    if response.all_suggested_nodes:
        print(f"\n--- Suggested Nodes ({len(response.all_suggested_nodes)}) ---")
        for node in response.all_suggested_nodes[:5]:
            confidence = _get_confidence_str(node.confidence)
            print(f"  - {node.label} [{confidence}]")
            print(f"    Key property: {node.key_property}")
            print(f"    {node.description[:60]}...")

    # Suggested Relationships
    if response.all_suggested_relationships:
        print(f"\n--- Suggested Relationships ({len(response.all_suggested_relationships)}) ---")
        for rel in response.all_suggested_relationships[:5]:
            confidence = _get_confidence_str(rel.confidence)
            print(f"  - ({rel.source_label})-[{rel.relationship_type}]->({rel.target_label}) [{confidence}]")
            print(f"    {rel.description[:60]}...")

    # Suggested Attributes
    if response.all_suggested_attributes:
        print(f"\n--- Suggested Attributes ({len(response.all_suggested_attributes)}) ---")
        for attr in response.all_suggested_attributes[:5]:
            confidence = _get_confidence_str(attr.confidence)
            print(f"  - {attr.target_label}.{attr.property_name}: {attr.property_type} [{confidence}]")
            print(f"    {attr.description[:60]}...")

    print("\n" + "=" * 70)
