"""
DSPy Modules for Graph Augmentation Agent.

This package contains the DSPy-based components for structured output generation:
- config: Language model configuration for Databricks
- signatures: DSPy signatures for each analysis type
- analyzers: DSPy modules that perform the actual analysis
"""

from lab_6_augmentation_agent.dspy_modules.config import (
    configure_dspy,
    get_lm,
    setup_mlflow_tracing,
)
from lab_6_augmentation_agent.dspy_modules.signatures import (
    InvestmentThemesSignature,
    NewEntitiesSignature,
    MissingAttributesSignature,
    ImpliedRelationshipsSignature,
    ANALYSIS_SIGNATURES,
)
from lab_6_augmentation_agent.dspy_modules.analyzers import (
    AnalysisResult,
    AnalysisData,
    InvestmentThemesAnalyzer,
    NewEntitiesAnalyzer,
    MissingAttributesAnalyzer,
    ImpliedRelationshipsAnalyzer,
    GraphAugmentationAnalyzer,
)

__all__ = [
    # Config
    "configure_dspy",
    "get_lm",
    "setup_mlflow_tracing",
    # Signatures
    "InvestmentThemesSignature",
    "NewEntitiesSignature",
    "MissingAttributesSignature",
    "ImpliedRelationshipsSignature",
    "ANALYSIS_SIGNATURES",
    # Analyzers
    "AnalysisResult",
    "AnalysisData",
    "InvestmentThemesAnalyzer",
    "NewEntitiesAnalyzer",
    "MissingAttributesAnalyzer",
    "ImpliedRelationshipsAnalyzer",
    "GraphAugmentationAnalyzer",
]
