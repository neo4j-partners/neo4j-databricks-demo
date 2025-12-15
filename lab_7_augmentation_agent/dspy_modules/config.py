"""
DSPy Language Model Configuration for Databricks Multi-Agent Supervisor.

This module handles the configuration of DSPy to work with Databricks
Multi-Agent Supervisor (MAS) endpoints created in Lab 6. It supports both
automatic authentication when running on Databricks and manual authentication
via environment variables.

The MAS endpoint routes queries to the Genie + Knowledge Agent for combined
structured and unstructured data analysis.

References:
    - https://docs.databricks.com/aws/en/generative-ai/dspy/
    - https://dspy.ai/learn/programming/language_models/
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final

import dspy
from dspy.clients.lm import LM
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods - use only HOST + TOKEN from .env
_CONFLICTING_AUTH_VARS: Final[tuple[str, ...]] = (
    "DATABRICKS_CONFIG_PROFILE",
    "DATABRICKS_CLIENT_ID",
    "DATABRICKS_CLIENT_SECRET",
    "DATABRICKS_ACCOUNT_ID",
)
for var in _CONFLICTING_AUTH_VARS:
    os.environ.pop(var, None)


# Default MAS endpoint name (from Lab 6)
# Override via MAS_ENDPOINT_NAME environment variable if needed
DEFAULT_ENDPOINT: Final[str] = os.environ.get("MAS_ENDPOINT_NAME", "mas-3ae5a347-endpoint")


class DatabricksResponsesLM(LM):
    """
    Custom DSPy Language Model for Databricks Responses API endpoints.

    This LM adapter works with Databricks Multi-Agent Supervisor endpoints
    that use the Responses API format (input array) instead of the standard
    OpenAI Chat Completions format (messages array).

    The Responses API expects:
        {
            "input": [{"role": "user", "content": "..."}]
        }

    Instead of OpenAI's:
        {
            "messages": [{"role": "user", "content": "..."}]
        }

    Authentication is handled automatically by WorkspaceClient:
    - On Databricks: Uses runtime's built-in authentication
    - Locally: Uses DATABRICKS_HOST and DATABRICKS_TOKEN from environment
    """

    def __init__(
        self,
        model: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Databricks Responses API LM.

        Args:
            model: The Databricks MAS endpoint name from Lab 6.
            **kwargs: Additional arguments (temperature, max_tokens, etc.)
        """
        self._model_name = model
        self._client: Any = None

        # Initialize parent with model name
        super().__init__(model=model, **kwargs)

    def _get_client(self) -> Any:
        """Get or create the Databricks OpenAI-compatible client."""
        if self._client is not None:
            return self._client

        try:
            from databricks.sdk import WorkspaceClient

            workspace_client = WorkspaceClient()
            self._client = workspace_client.serving_endpoints.get_open_ai_client()
            return self._client
        except Exception as e:
            raise RuntimeError(f"Failed to create Databricks client: {e}")

    def __call__(
        self,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Call the Databricks Responses API endpoint.

        Args:
            prompt: Optional prompt string (converted to user message).
            messages: List of message dicts with role and content.
            **kwargs: Additional arguments (ignored for Responses API).

        Returns:
            List containing response dict with 'text' key.
        """
        client = self._get_client()

        # Build input from messages or prompt
        if messages:
            # Convert messages to single user input for Responses API
            # Combine all messages into a single prompt
            combined_content = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    combined_content += f"{content}\n\n"
                elif role == "user":
                    combined_content += f"{content}\n"
                elif role == "assistant":
                    combined_content += f"Assistant: {content}\n"
            input_messages = [{"role": "user", "content": combined_content.strip()}]
        elif prompt:
            input_messages = [{"role": "user", "content": prompt}]
        else:
            raise ValueError("Either prompt or messages must be provided")

        try:
            response = client.responses.create(
                model=self._model_name,
                input=input_messages,
            )
            # Extract text from response
            text = response.output[0].content[0].text
            return [{"text": text}]
        except Exception as e:
            raise RuntimeError(f"Databricks API call failed: {e}")


def get_lm(
    model_name: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 4000,
) -> LM:
    """
    Create a DSPy Language Model configured for Databricks MAS endpoint.

    This function ONLY supports Multi-Agent Supervisor endpoints from Lab 6.
    The MAS endpoint uses the Databricks Responses API format, which requires
    a custom LM adapter (DatabricksResponsesLM).

    Authentication is handled automatically by WorkspaceClient:
    - On Databricks: Uses runtime's built-in authentication
    - Locally: Uses DATABRICKS_HOST and DATABRICKS_TOKEN from .env

    Args:
        model_name: The MAS endpoint name from Lab 6. If None, uses DEFAULT_ENDPOINT.
        temperature: Sampling temperature (0.0-1.0). Lower = more deterministic.
        max_tokens: Maximum tokens in the response.

    Returns:
        Configured dspy.LM instance for MAS endpoint.

    Raises:
        RuntimeError: If Databricks authentication fails.
    """
    endpoint = model_name or DEFAULT_ENDPOINT

    # DatabricksResponsesLM is specifically designed for MAS endpoints
    # which use the Responses API format (not OpenAI Chat Completions)
    lm = DatabricksResponsesLM(
        model=endpoint,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return lm


def configure_dspy(
    model_name: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 4000,
    track_usage: bool = True,
) -> LM:
    """
    Configure DSPy globally with the Databricks MAS endpoint.

    This sets up the default LM and adapter for all DSPy operations.
    Call this once at application startup.

    This function ONLY supports Multi-Agent Supervisor endpoints from Lab 6:
    - Uses DatabricksResponsesLM (Responses API format, not OpenAI format)
    - Uses ChatAdapter (required for MAS, JSONAdapter not supported)

    Args:
        model_name: The MAS endpoint name from Lab 6. If None, uses DEFAULT_ENDPOINT.
        temperature: Sampling temperature (0.0-1.0).
        max_tokens: Maximum tokens in the response.
        track_usage: If True, enable token usage tracking.

    Returns:
        The configured LM instance.

    Example:
        >>> from lab_7_augmentation_agent.dspy_modules import configure_dspy
        >>> lm = configure_dspy()
        >>> print(f"Configured with endpoint: {lm.model}")
    """
    lm = get_lm(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # MAS endpoints require ChatAdapter (JSONAdapter is not supported)
    adapter = dspy.ChatAdapter()

    dspy.configure(
        lm=lm,
        adapter=adapter,
        track_usage=track_usage,
    )

    print(f"[OK] DSPy configured")
    print(f"    Endpoint: {model_name or DEFAULT_ENDPOINT}")
    print(f"    Adapter: ChatAdapter")
    print(f"    Temperature: {temperature}")
    print(f"    Max tokens: {max_tokens}")

    return lm


def setup_mlflow_tracing() -> bool:
    """
    Enable MLflow tracing for DSPy operations.

    MLflow provides automatic tracing for DSPy modules, capturing
    inputs, outputs, and intermediate reasoning steps.

    Returns:
        True if tracing was enabled, False otherwise.

    References:
        - https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/dspy
    """
    try:
        import mlflow

        mlflow.dspy.autolog()
        print("[OK] MLflow DSPy tracing enabled")
        return True
    except ImportError:
        print("[WARN] MLflow not installed, tracing disabled")
        print("       Install with: pip install 'mlflow[databricks]>=3.1'")
        return False
    except AttributeError:
        # Older MLflow versions may not have dspy.autolog
        try:
            mlflow.openai.autolog()
            print("[OK] MLflow OpenAI tracing enabled (DSPy tracing requires MLflow 3.1+)")
            return True
        except Exception:
            print("[WARN] MLflow tracing setup failed")
            return False
    except Exception as e:
        print(f"[WARN] MLflow tracing setup failed: {e}")
        return False
