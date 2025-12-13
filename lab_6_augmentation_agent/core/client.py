"""
ChatDatabricks structured output client.

This module provides the StructuredLLMClient class for querying
Databricks Foundation Models with native Pydantic structured output.

Documentation References:
    - ChatDatabricks with_structured_output():
      https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html

    - Databricks Structured Outputs:
      https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from lab_6_augmentation_agent.core.config import (
    ANALYSIS_CONFIGS,
    LLM_MODEL,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    AnalysisType,
)


@dataclass
class StructuredLLMClient:
    """
    Client for ChatDatabricks with structured output support.

    Encapsulates LLM configuration and provides retry logic for robustness.
    Uses lazy initialization to avoid startup overhead.

    Reference: https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html

    Attributes:
        model: The Databricks model name to use
    """

    model: str = field(default_factory=lambda: LLM_MODEL)
    _llm_cache: dict[AnalysisType, Any] = field(default_factory=dict, repr=False)

    def _get_llm(self, analysis_type: AnalysisType) -> Any:
        """
        Get or create a structured LLM for the given analysis type.

        Uses caching to avoid recreating LLM instances.
        """
        if analysis_type in self._llm_cache:
            return self._llm_cache[analysis_type]

        # Lazy import to avoid startup overhead
        # Reference: https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html
        try:
            from databricks_langchain import ChatDatabricks
        except ImportError as e:
            raise ImportError(
                "databricks-langchain not installed. Install with: pip install databricks-langchain"
            ) from e

        config = ANALYSIS_CONFIGS[analysis_type]

        # Create ChatDatabricks instance
        # Reference: https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html#databricks_langchain.ChatDatabricks
        llm = ChatDatabricks(
            model=self.model,
            temperature=0,  # Deterministic output for structured data
        )

        # Configure for structured output with Pydantic schema
        # Method options:
        #   - 'function_calling': Uses OpenAI-style function calling (default, most compatible)
        #   - 'json_mode': Returns unstructured JSON
        #   - 'json_schema': Returns JSON conforming to schema
        #
        # Reference: https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs
        structured_llm = llm.with_structured_output(
            config.schema,
            method="function_calling",
            include_raw=True,  # Include raw response for debugging
        )

        self._llm_cache[analysis_type] = structured_llm
        return structured_llm

    def query(
        self,
        analysis_type: AnalysisType,
        query: str,
    ) -> tuple[Any | None, str | None, float]:
        """
        Query the LLM with structured output.

        Includes retry logic for transient failures.

        Args:
            analysis_type: The type of analysis to perform
            query: The user query

        Returns:
            Tuple of (parsed_result, error_message, duration_seconds)
            - parsed_result: Validated Pydantic model instance or None
            - error_message: Error string if failed, None otherwise
            - duration_seconds: Time taken for the query
        """
        config = ANALYSIS_CONFIGS[analysis_type]
        structured_llm = self._get_llm(analysis_type)

        messages = [
            SystemMessage(content=config.system_prompt),
            HumanMessage(content=query),
        ]

        last_error = None
        start_time = time.time()

        for attempt in range(MAX_RETRIES + 1):
            try:
                result = structured_llm.invoke(messages)
                duration = time.time() - start_time

                # Extract parsed result (include_raw=True returns dict)
                if isinstance(result, dict):
                    if result.get("parsing_error"):
                        return None, str(result["parsing_error"]), duration
                    return result.get("parsed"), None, duration
                return result, None, duration

            except ValidationError as e:
                return None, f"Validation error: {e}", time.time() - start_time

            except Exception as e:
                last_error = str(e)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue

        return None, f"Query failed after {MAX_RETRIES + 1} attempts: {last_error}", time.time() - start_time


# Global client instance (lazy initialization)
_llm_client: StructuredLLMClient | None = None


def get_llm_client() -> StructuredLLMClient:
    """
    Get or create the global LLM client.

    Returns:
        The singleton StructuredLLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = StructuredLLMClient()
    return _llm_client
