"""
DEPRECATED: This client does not work with MAS endpoints.

ChatDatabricks.with_structured_output() is incompatible with Multi-Agent Supervisor (MAS)
endpoints. All three methods (function_calling, json_schema, json_mode) fail because:
- function_calling: MAS doesn't support OpenAI tools format
- json_schema: MAS doesn't accept response_format parameter
- json_mode: MAS doesn't accept response_format parameter

Use the DSPy implementation instead:
    uv run python -m lab_6_augmentation_agent.agent_dspy

See WHY_NOT_LANGGRAPH.md for full technical details.

---

Multi-Agent Supervisor (MAS) client with Pydantic structured output (DEPRECATED).

This module provides the MASClient class for querying the Lab 5
Multi-Agent Supervisor endpoint using ChatDatabricks with native
Pydantic structured output support.

Key Configuration:
    - use_responses_api=True: Required for MAS endpoints (Responses API format)
    - with_structured_output(): Native Pydantic schema validation

Documentation References:
    - ChatDatabricks API:
      https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html

    - Databricks Structured Outputs:
      https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from lab_6_augmentation_agent.core.config import (
    ANALYSIS_CONFIGS,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    AnalysisType,
)


@dataclass
class MASClient:
    """
    Client for Multi-Agent Supervisor (MAS) endpoints with structured output.

    Uses ChatDatabricks with use_responses_api=True for MAS compatibility
    and with_structured_output() for native Pydantic schema validation.

    Attributes:
        endpoint: The Lab 5 Multi-Agent Supervisor endpoint name (REQUIRED)
    """

    endpoint: str = field(default_factory=lambda: os.environ.get("MAS_ENDPOINT_NAME", ""))
    _client_cache: dict[AnalysisType, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Validate that the endpoint is configured."""
        if not self.endpoint:
            raise ValueError(
                "MAS_ENDPOINT_NAME is required but not set. "
                "The Lab 6 Augmentation Agent must use the Lab 5 Multi-Agent Supervisor. "
                "Set MAS_ENDPOINT_NAME in the configuration or environment."
            )

    def _get_structured_client(self, analysis_type: AnalysisType) -> Any:
        """
        Get or create a structured output client for the given analysis type.

        Uses ChatDatabricks with:
        - use_responses_api=True: For MAS endpoint compatibility
        - with_structured_output(): For Pydantic schema validation

        Reference: https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html
        """
        if analysis_type in self._client_cache:
            return self._client_cache[analysis_type]

        try:
            from databricks_langchain import ChatDatabricks
        except ImportError as e:
            raise ImportError(
                "databricks-langchain not installed. Install with: pip install databricks-langchain>=0.11.0"
            ) from e

        config = ANALYSIS_CONFIGS[analysis_type]

        # Create ChatDatabricks with Responses API format for MAS endpoints
        # Reference: https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html
        chat = ChatDatabricks(
            endpoint=self.endpoint,
            temperature=0,
            use_responses_api=True,  # Required for MAS endpoints
        )

        # Configure structured output with Pydantic schema
        # Method options: 'function_calling' (default), 'json_mode', 'json_schema'
        # Note: MAS endpoints don't support OpenAI function calling format,
        # so we use 'json_schema' method instead.
        # Reference: https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs
        structured_client = chat.with_structured_output(
            config.schema,
            method="json_mode",
            include_raw=True,  # Include raw response for debugging
        )

        self._client_cache[analysis_type] = structured_client
        return structured_client

    def query(
        self,
        analysis_type: AnalysisType,
        query: str,
    ) -> tuple[Any | None, str | None, float]:
        """
        Query the MAS endpoint with Pydantic structured output.

        Args:
            analysis_type: The type of analysis to perform
            query: The user query

        Returns:
            Tuple of (parsed_result, error_message, duration_seconds)
            - parsed_result: Validated Pydantic model instance or None
            - error_message: Error string if failed, None otherwise
            - duration_seconds: Time taken for the query
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        config = ANALYSIS_CONFIGS[analysis_type]
        structured_client = self._get_structured_client(analysis_type)

        messages = [
            SystemMessage(content=config.system_prompt),
            HumanMessage(content=query),
        ]

        last_error = None
        start_time = time.time()

        for attempt in range(MAX_RETRIES + 1):
            try:
                result = structured_client.invoke(messages)
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
_mas_client: MASClient | None = None


def get_mas_client() -> MASClient:
    """
    Get or create the global MAS client.

    Returns:
        The singleton MASClient instance
    """
    global _mas_client
    if _mas_client is None:
        _mas_client = MASClient()
    return _mas_client
