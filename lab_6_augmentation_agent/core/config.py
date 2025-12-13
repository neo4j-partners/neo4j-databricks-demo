"""
DEPRECATED: This LangGraph implementation does not work with MAS endpoints.

ChatDatabricks.with_structured_output() is incompatible with Multi-Agent Supervisor (MAS)
endpoints. All three methods (function_calling, json_schema, json_mode) fail.

Use the DSPy implementation instead:
    uv run python -m lab_6_augmentation_agent.agent_dspy

See WHY_NOT_LANGGRAPH.md for full technical details.

---

Configuration for the Graph Augmentation Agent (DEPRECATED).

This module contains:
    - AnalysisType enum for type-safe analysis types
    - AnalysisConfig dataclass for analysis metadata
    - ANALYSIS_CONFIGS dictionary with all analysis configurations
    - Retry configuration settings

Documentation References:
    - Databricks Multi-Agent Supervisor:
      https://docs.databricks.com/aws/en/generative-ai/agent-framework/

    - Databricks Structured Outputs:
      https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from lab_6_augmentation_agent.schemas import (
    ImpliedRelationshipsAnalysis,
    InvestmentThemesAnalysis,
    MissingAttributesAnalysis,
    NewEntitiesAnalysis,
)


class AnalysisType(StrEnum):
    """
    Analysis types supported by the agent.

    Using StrEnum for type safety and better IDE support.
    Reference: https://docs.python.org/3/library/enum.html#enum.StrEnum
    """

    INVESTMENT_THEMES = "investment_themes"
    NEW_ENTITIES = "new_entities"
    MISSING_ATTRIBUTES = "missing_attributes"
    IMPLIED_RELATIONSHIPS = "implied_relationships"


# Retry configuration for transient failures
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 1.0


@dataclass(frozen=True)
class AnalysisConfig:
    """Configuration for a single analysis type."""

    analysis_type: AnalysisType
    schema: type
    system_prompt: str
    query: str
    display_name: str


# Analysis configurations with rich metadata
ANALYSIS_CONFIGS: dict[AnalysisType, AnalysisConfig] = {
    AnalysisType.INVESTMENT_THEMES: AnalysisConfig(
        analysis_type=AnalysisType.INVESTMENT_THEMES,
        schema=InvestmentThemesAnalysis,
        display_name="Investment Themes",
        system_prompt="""You are a financial analyst expert. Analyze market research documents
and identify emerging investment themes. Be thorough and extract all relevant themes with
supporting evidence including market sizes, growth projections, key sectors, and companies.
Provide confidence levels (high, medium, low) based on the strength of evidence.""",
        query="What are the emerging investment themes mentioned in the market research documents?",
    ),
    AnalysisType.NEW_ENTITIES: AnalysisConfig(
        analysis_type=AnalysisType.NEW_ENTITIES,
        schema=NewEntitiesAnalysis,
        display_name="New Entities",
        system_prompt="""You are a knowledge graph architect. Analyze documents and suggest new
entity types that should be added to a Neo4j graph database. Focus on entities that capture:
- Customer goals and financial objectives
- Investment preferences and interests
- Life stages and family circumstances
- Service preferences and behaviors
Provide detailed property definitions and example values for each suggested node type.""",
        query="What new entities should be extracted from the HTML data for inclusion in the graph?",
    ),
    AnalysisType.MISSING_ATTRIBUTES: AnalysisConfig(
        analysis_type=AnalysisType.MISSING_ATTRIBUTES,
        schema=MissingAttributesAnalysis,
        display_name="Missing Attributes",
        system_prompt="""You are a data modeling expert. Compare customer profile documents
against the existing database schema and identify attributes mentioned in profiles but missing
from Customer nodes. Focus on:
- Professional and career details
- Investment preferences and behavior patterns
- Financial goals and interests
- Family circumstances and life stage information
Provide property types and example values for each suggested attribute.""",
        query="What customer attributes are mentioned in profiles but missing from the Customer nodes in the database?",
    ),
    AnalysisType.IMPLIED_RELATIONSHIPS: AnalysisConfig(
        analysis_type=AnalysisType.IMPLIED_RELATIONSHIPS,
        schema=ImpliedRelationshipsAnalysis,
        display_name="Implied Relationships",
        system_prompt="""You are a graph relationship analyst. Analyze documents and identify
relationships between entities that are implied but not explicitly captured in the current
graph structure. Focus on:
- Customer-to-goal relationships
- Customer-to-interest relationships
- Customer similarity relationships
- Investment correlation relationships
Provide relationship types, source/target labels, and example instances.""",
        query="What relationships between customers, companies, and investments are implied in the documents but not captured in the graph?",
    ),
}
