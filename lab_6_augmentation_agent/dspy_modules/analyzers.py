"""
DSPy Analyzer Modules for Graph Augmentation.

This module contains DSPy modules that perform the actual analysis work.
Each analyzer wraps a DSPy predictor (ChainOfThought) with a signature
and provides a clean interface for the main agent.

DSPy modules handle:
- Prompt generation from signatures
- Language model invocation
- Response parsing into typed Pydantic models
- Automatic retries on parsing failures

References:
    - https://dspy.ai/learn/programming/modules/
    - ChainOfThought: "Teaches the LM to think step-by-step before
      committing to the signature's response."
"""

from __future__ import annotations

from dataclasses import dataclass

import dspy

from lab_6_augmentation_agent.schemas import (
    InvestmentThemesAnalysis,
    NewEntitiesAnalysis,
    MissingAttributesAnalysis,
    ImpliedRelationshipsAnalysis,
    AugmentationAnalysis,
    AugmentationResponse,
    SuggestedNode,
    SuggestedRelationship,
    SuggestedAttribute,
)
from lab_6_augmentation_agent.dspy_modules.signatures import (
    InvestmentThemesSignature,
    NewEntitiesSignature,
    MissingAttributesSignature,
    ImpliedRelationshipsSignature,
)


# Specific result types for each analyzer - no generics needed
@dataclass(slots=True)
class InvestmentThemesResult:
    """Result from investment themes analysis."""
    success: bool
    data: InvestmentThemesAnalysis | None = None
    error: str | None = None
    reasoning: str | None = None


@dataclass(slots=True)
class NewEntitiesResult:
    """Result from new entities analysis."""
    success: bool
    data: NewEntitiesAnalysis | None = None
    error: str | None = None
    reasoning: str | None = None


@dataclass(slots=True)
class MissingAttributesResult:
    """Result from missing attributes analysis."""
    success: bool
    data: MissingAttributesAnalysis | None = None
    error: str | None = None
    reasoning: str | None = None


@dataclass(slots=True)
class ImpliedRelationshipsResult:
    """Result from implied relationships analysis."""
    success: bool
    data: ImpliedRelationshipsAnalysis | None = None
    error: str | None = None
    reasoning: str | None = None


class InvestmentThemesAnalyzer(dspy.Module):
    """
    Analyzer for identifying investment themes from market research documents.

    Uses ChainOfThought to encourage step-by-step reasoning before
    producing the structured output.
    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(InvestmentThemesSignature)

    def forward(self, document_context: str) -> InvestmentThemesResult:
        """
        Analyze documents for investment themes.

        Args:
            document_context: The market research content to analyze.

        Returns:
            InvestmentThemesResult with typed data.
        """
        try:
            result = self.analyze(document_context=document_context)
            return InvestmentThemesResult(
                success=True,
                data=result.analysis,
                reasoning=getattr(result, "reasoning", None),
            )
        except Exception as e:
            return InvestmentThemesResult(
                success=False,
                error=str(e),
            )


class NewEntitiesAnalyzer(dspy.Module):
    """
    Analyzer for suggesting new entity types from document analysis.

    Identifies new node types that should be added to the graph
    based on document content.
    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(NewEntitiesSignature)

    def forward(self, document_context: str) -> NewEntitiesResult:
        """
        Analyze documents for new entity suggestions.

        Args:
            document_context: The HTML/document content to analyze.

        Returns:
            NewEntitiesResult with typed data.
        """
        try:
            result = self.analyze(document_context=document_context)
            return NewEntitiesResult(
                success=True,
                data=result.analysis,
                reasoning=getattr(result, "reasoning", None),
            )
        except Exception as e:
            return NewEntitiesResult(
                success=False,
                error=str(e),
            )


class MissingAttributesAnalyzer(dspy.Module):
    """
    Analyzer for identifying missing attributes on existing nodes.

    Compares document content against current schema to find
    attributes that should be added to existing node types.
    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(MissingAttributesSignature)

    def forward(self, document_context: str) -> MissingAttributesResult:
        """
        Analyze documents for missing attribute suggestions.

        Args:
            document_context: Customer profile content to analyze.

        Returns:
            MissingAttributesResult with typed data.
        """
        try:
            result = self.analyze(document_context=document_context)
            return MissingAttributesResult(
                success=True,
                data=result.analysis,
                reasoning=getattr(result, "reasoning", None),
            )
        except Exception as e:
            return MissingAttributesResult(
                success=False,
                error=str(e),
            )


class ImpliedRelationshipsAnalyzer(dspy.Module):
    """
    Analyzer for discovering implied relationships between entities.

    Identifies relationships that exist in documents but are not
    currently captured in the graph schema.
    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(ImpliedRelationshipsSignature)

    def forward(self, document_context: str) -> ImpliedRelationshipsResult:
        """
        Analyze documents for implied relationship suggestions.

        Args:
            document_context: Document content to analyze.

        Returns:
            ImpliedRelationshipsResult with typed data.
        """
        try:
            result = self.analyze(document_context=document_context)
            return ImpliedRelationshipsResult(
                success=True,
                data=result.analysis,
                reasoning=getattr(result, "reasoning", None),
            )
        except Exception as e:
            return ImpliedRelationshipsResult(
                success=False,
                error=str(e),
            )


class GraphAugmentationAnalyzer(dspy.Module):
    """
    Composite analyzer that runs all analysis types and consolidates results.

    This module orchestrates the individual analyzers and builds
    a unified AugmentationResponse from their outputs.
    """

    def __init__(self):
        super().__init__()
        self.investment_themes = InvestmentThemesAnalyzer()
        self.new_entities = NewEntitiesAnalyzer()
        self.missing_attributes = MissingAttributesAnalyzer()
        self.implied_relationships = ImpliedRelationshipsAnalyzer()

    def forward(
        self,
        document_context: str,
        analyses_to_run: list[str] | None = None,
    ) -> AugmentationResponse:
        """
        Run specified analyses and return consolidated results.

        Args:
            document_context: The document content to analyze.
            analyses_to_run: List of analysis types to run. If None, runs all.
                Valid values: "investment_themes", "new_entities",
                "missing_attributes", "implied_relationships"

        Returns:
            AugmentationResponse with all analysis results consolidated.
        """
        all_analyses = (
            "investment_themes",
            "new_entities",
            "missing_attributes",
            "implied_relationships",
        )
        to_run = analyses_to_run or list(all_analyses)

        analysis = AugmentationAnalysis()

        # Collect all suggestions for consolidation
        all_nodes: list[SuggestedNode] = []
        all_relationships: list[SuggestedRelationship] = []
        all_attributes: list[SuggestedAttribute] = []

        # Track success for final response
        any_success = False

        # Run each requested analysis - each returns a specific typed result
        for analysis_type in to_run:
            if analysis_type not in all_analyses:
                continue

            print(f"  Running {analysis_type} analysis...")

            if analysis_type == "investment_themes":
                result = self.investment_themes(document_context)
                if result.success and result.data:
                    analysis.investment_themes = result.data
                    any_success = True
                status = "OK" if result.success else f"FAILED: {result.error}"

            elif analysis_type == "new_entities":
                result = self.new_entities(document_context)
                if result.success and result.data:
                    analysis.new_entities = result.data
                    all_nodes.extend(result.data.suggested_nodes)
                    any_success = True
                status = "OK" if result.success else f"FAILED: {result.error}"

            elif analysis_type == "missing_attributes":
                result = self.missing_attributes(document_context)
                if result.success and result.data:
                    analysis.missing_attributes = result.data
                    all_attributes.extend(result.data.suggested_attributes)
                    any_success = True
                status = "OK" if result.success else f"FAILED: {result.error}"

            elif analysis_type == "implied_relationships":
                result = self.implied_relationships(document_context)
                if result.success and result.data:
                    analysis.implied_relationships = result.data
                    all_relationships.extend(result.data.suggested_relationships)
                    any_success = True
                status = "OK" if result.success else f"FAILED: {result.error}"

            else:
                status = "SKIPPED"

            print(f"    [{status}]")

        # Build the consolidated response
        response = AugmentationResponse(
            success=any_success,
            analysis=analysis,
            all_suggested_nodes=all_nodes,
            all_suggested_relationships=all_relationships,
            all_suggested_attributes=all_attributes,
        )
        response.compute_statistics()

        return response

    def run_single(
        self,
        analysis_type: str,
        document_context: str,
    ) -> InvestmentThemesResult | NewEntitiesResult | MissingAttributesResult | ImpliedRelationshipsResult:
        """
        Run a single analysis type.

        Args:
            analysis_type: The type of analysis to run.
            document_context: The document content to analyze.

        Returns:
            The typed result for the specified analysis.

        Raises:
            ValueError: If analysis_type is not recognized.
        """
        if analysis_type == "investment_themes":
            return self.investment_themes(document_context)
        elif analysis_type == "new_entities":
            return self.new_entities(document_context)
        elif analysis_type == "missing_attributes":
            return self.missing_attributes(document_context)
        elif analysis_type == "implied_relationships":
            return self.implied_relationships(document_context)
        else:
            raise ValueError(
                f"Unknown analysis type: {analysis_type}. "
                f"Must be one of: investment_themes, new_entities, missing_attributes, implied_relationships"
            )
