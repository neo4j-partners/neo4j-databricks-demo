"""
DSPy Signatures for Graph Augmentation Analysis.

This module defines DSPy signatures for each type of analysis the agent performs.
Signatures are declarative specifications of input/output behavior that DSPy
uses to generate prompts and parse responses automatically.

Each signature uses the existing Pydantic models from schemas.py as output types,
enabling type-safe structured output without manual JSON parsing.

References:
    - https://dspy.ai/learn/programming/signatures/
    - Best practice: "Don't prematurely tune the keywords of your signature by hand.
      The DSPy optimizers will likely do a better job."
"""

from __future__ import annotations

from typing import Final

import dspy

from lab_6_augmentation_agent.schemas import (
    InvestmentThemesAnalysis,
    NewEntitiesAnalysis,
    MissingAttributesAnalysis,
    ImpliedRelationshipsAnalysis,
)


class InvestmentThemesSignature(dspy.Signature):
    """
    Analyze market research documents to identify emerging investment themes.

    Extract investment themes with supporting evidence, market sizing,
    growth projections, and confidence assessments. Focus on themes
    that could inform graph database augmentation for financial analysis.
    """

    document_context: str = dspy.InputField(
        desc="Market research documents and financial analysis content to analyze"
    )

    analysis: InvestmentThemesAnalysis = dspy.OutputField(
        desc="Structured analysis of investment themes with evidence and recommendations"
    )


class NewEntitiesSignature(dspy.Signature):
    """
    Analyze documents to suggest new entity types for the graph database.

    Identify entities that should be extracted and added as new node types,
    including their properties, key identifiers, and example values.
    Focus on entities that capture customer goals, preferences, interests,
    and life stages.
    """

    document_context: str = dspy.InputField(
        desc="HTML data and documents containing entity information to extract"
    )

    analysis: NewEntitiesAnalysis = dspy.OutputField(
        desc="Structured suggestions for new node types with properties and examples"
    )


class MissingAttributesSignature(dspy.Signature):
    """
    Analyze customer profiles to identify attributes missing from graph nodes.

    Compare information mentioned in customer profiles against the current
    Customer node schema to identify missing attributes that should be added.
    Include professional details, investment preferences, financial goals,
    and behavioral attributes.
    """

    document_context: str = dspy.InputField(
        desc="Customer profile documents and data containing attribute information"
    )

    analysis: MissingAttributesAnalysis = dspy.OutputField(
        desc="Structured suggestions for missing attributes with types and examples"
    )


class ImpliedRelationshipsSignature(dspy.Signature):
    """
    Analyze documents to identify relationships implied but not captured in the graph.

    Find relationships between customers, companies, and investments that are
    mentioned or implied in documents but not explicitly modeled. Focus on
    customer-goal, customer-interest, and customer-similarity relationships.
    """

    document_context: str = dspy.InputField(
        desc="Documents containing information about entity relationships"
    )

    analysis: ImpliedRelationshipsAnalysis = dspy.OutputField(
        desc="Structured suggestions for new relationship types with properties"
    )


# Mapping of analysis type names to their corresponding signatures
ANALYSIS_SIGNATURES: Final[dict[str, type[dspy.Signature]]] = {
    "investment_themes": InvestmentThemesSignature,
    "new_entities": NewEntitiesSignature,
    "missing_attributes": MissingAttributesSignature,
    "implied_relationships": ImpliedRelationshipsSignature,
}
