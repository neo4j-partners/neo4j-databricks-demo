"""
Pydantic schemas for structured output from the Graph Augmentation Agent.

These models define the structure for graph augmentation suggestions,
enabling machine-readable output that can be programmatically processed
and written back to Neo4j.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for a suggestion."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PropertyDefinition(BaseModel):
    """Definition of a property for a node or relationship."""
    name: str = Field(..., description="Property name")
    property_type: str = Field(..., description="Data type (string, int, float, boolean, date)")
    required: bool = Field(default=False, description="Whether the property is required")
    description: str | None = Field(default=None, description="Description of the property")


class SuggestedNode(BaseModel):
    """A suggested new node type to add to the graph."""
    label: str = Field(..., description="Node label (e.g., 'FINANCIAL_GOAL', 'STATED_INTEREST')")
    description: str = Field(..., description="Description of what this node type represents")
    key_property: str = Field(..., description="Property that uniquely identifies nodes of this type")
    properties: list[PropertyDefinition] = Field(
        default_factory=list,
        description="List of properties for this node type"
    )
    example_values: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Example node instances with property values"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level for this suggestion"
    )
    source_evidence: str = Field(..., description="Evidence from the analysis supporting this suggestion")
    rationale: str = Field(..., description="Why this node type should be added")


class SuggestedRelationship(BaseModel):
    """A suggested new relationship type to add to the graph."""
    relationship_type: str = Field(..., description="Relationship type (e.g., 'HAS_GOAL', 'INTERESTED_IN')")
    description: str = Field(..., description="Description of what this relationship represents")
    source_label: str = Field(..., description="Label of the source node")
    target_label: str = Field(..., description="Label of the target node")
    properties: list[PropertyDefinition] = Field(
        default_factory=list,
        description="List of properties for this relationship type"
    )
    example_instances: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Example relationship instances"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level for this suggestion"
    )
    source_evidence: str = Field(..., description="Evidence from the analysis supporting this suggestion")
    rationale: str = Field(..., description="Why this relationship type should be added")


class SuggestedAttribute(BaseModel):
    """A suggested new attribute to add to an existing node type."""
    target_label: str = Field(..., description="Label of the node type to add attribute to")
    property_name: str = Field(..., description="Name of the new property")
    property_type: str = Field(..., description="Data type (string, int, float, boolean, date)")
    description: str = Field(..., description="Description of what this attribute represents")
    example_values: list[Any] = Field(
        default_factory=list,
        description="Example values for this attribute"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level for this suggestion"
    )
    source_evidence: str = Field(..., description="Evidence from the analysis supporting this suggestion")
    rationale: str = Field(..., description="Why this attribute should be added")


class InvestmentTheme(BaseModel):
    """An emerging investment theme identified from analysis."""
    name: str = Field(..., description="Theme name (e.g., 'Renewable Energy', 'AI/ML')")
    description: str = Field(..., description="Description of the theme")
    market_size: str | None = Field(default=None, description="Market size or investment volume")
    growth_projection: str | None = Field(default=None, description="Growth projections")
    key_sectors: list[str] = Field(default_factory=list, description="Related sectors")
    key_companies: list[str] = Field(default_factory=list, description="Related companies")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence level for this theme"
    )
    source_evidence: str = Field(..., description="Evidence supporting this theme")


class AnalysisSection(BaseModel):
    """A section of analysis results."""
    title: str = Field(..., description="Section title")
    summary: str = Field(..., description="Brief summary of findings")
    details: str = Field(..., description="Detailed analysis text")


class InvestmentThemesAnalysis(BaseModel):
    """Structured output for investment themes analysis."""
    summary: str = Field(..., description="Overall summary of investment themes")
    themes: list[InvestmentTheme] = Field(
        default_factory=list,
        description="List of identified investment themes"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Investment recommendations based on themes"
    )


class NewEntitiesAnalysis(BaseModel):
    """Structured output for new entities analysis."""
    summary: str = Field(..., description="Overall summary of suggested entities")
    suggested_nodes: list[SuggestedNode] = Field(
        default_factory=list,
        description="List of suggested new node types"
    )
    implementation_priority: list[str] = Field(
        default_factory=list,
        description="Prioritized list of entities to implement"
    )


class MissingAttributesAnalysis(BaseModel):
    """Structured output for missing attributes analysis."""
    summary: str = Field(..., description="Overall summary of missing attributes")
    suggested_attributes: list[SuggestedAttribute] = Field(
        default_factory=list,
        description="List of suggested new attributes"
    )
    affected_node_types: list[str] = Field(
        default_factory=list,
        description="Node types that need attribute additions"
    )


class ImpliedRelationshipsAnalysis(BaseModel):
    """Structured output for implied relationships analysis."""
    summary: str = Field(..., description="Overall summary of implied relationships")
    suggested_relationships: list[SuggestedRelationship] = Field(
        default_factory=list,
        description="List of suggested new relationship types"
    )
    relationship_patterns: list[str] = Field(
        default_factory=list,
        description="Identified relationship patterns"
    )


class AugmentationAnalysis(BaseModel):
    """Combined analysis results from all analysis types."""
    investment_themes: InvestmentThemesAnalysis | None = Field(
        default=None,
        description="Investment themes analysis results"
    )
    new_entities: NewEntitiesAnalysis | None = Field(
        default=None,
        description="New entities analysis results"
    )
    missing_attributes: MissingAttributesAnalysis | None = Field(
        default=None,
        description="Missing attributes analysis results"
    )
    implied_relationships: ImpliedRelationshipsAnalysis | None = Field(
        default=None,
        description="Implied relationships analysis results"
    )


class AugmentationResponse(BaseModel):
    """Top-level response wrapper for the augmentation agent."""
    success: bool = Field(..., description="Whether the analysis completed successfully")
    analysis: AugmentationAnalysis = Field(..., description="The analysis results")
    all_suggested_nodes: list[SuggestedNode] = Field(
        default_factory=list,
        description="Consolidated list of all suggested nodes"
    )
    all_suggested_relationships: list[SuggestedRelationship] = Field(
        default_factory=list,
        description="Consolidated list of all suggested relationships"
    )
    all_suggested_attributes: list[SuggestedAttribute] = Field(
        default_factory=list,
        description="Consolidated list of all suggested attributes"
    )
    high_confidence_count: int = Field(
        default=0,
        description="Count of high-confidence suggestions"
    )
    total_suggestions: int = Field(
        default=0,
        description="Total number of suggestions"
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if analysis failed"
    )

    def compute_statistics(self) -> None:
        """Compute statistics from the suggestions."""
        all_suggestions = (
            self.all_suggested_nodes +
            self.all_suggested_relationships +
            self.all_suggested_attributes
        )
        self.total_suggestions = len(all_suggestions)
        self.high_confidence_count = sum(
            1 for s in all_suggestions
            if hasattr(s, 'confidence') and s.confidence == ConfidenceLevel.HIGH
        )
