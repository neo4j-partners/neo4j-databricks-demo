"""
DSPy Language Model Configuration for Databricks.

This module handles the configuration of DSPy to work with Databricks
model serving endpoints. It supports both automatic authentication when
running on Databricks and manual authentication via environment variables.

Includes a custom LM adapter for Databricks Multi-Agent Supervisor endpoints
that use the Responses API format.

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


# Default model endpoint name
DEFAULT_ENDPOINT: Final[str] = os.environ.get("LLM_ENDPOINT_NAME", "mas-3ae5a347-endpoint")


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
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Databricks Responses API LM.

        Args:
            model: The Databricks model endpoint name.
            api_key: Databricks API token.
            api_base: Databricks workspace URL.
            **kwargs: Additional arguments (temperature, max_tokens, etc.)
        """
        # Store config before calling super().__init__
        self._model_name = model
        self._api_key = api_key or os.environ.get("DATABRICKS_TOKEN")
        self._api_base = api_base or os.environ.get("DATABRICKS_HOST")
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
    use_responses_api: bool = True,
) -> LM:
    """
    Create a DSPy Language Model configured for Databricks.

    Args:
        model_name: The Databricks model endpoint name. If None, uses DEFAULT_ENDPOINT.
        temperature: Sampling temperature (0.0-1.0). Lower = more deterministic.
        max_tokens: Maximum tokens in the response.
        use_responses_api: If True, use DatabricksResponsesLM for MAS endpoints.
                          If False, use standard OpenAI-compatible LM.

    Returns:
        Configured dspy.LM instance.

    Raises:
        RuntimeError: If Databricks authentication fails.
    """
    endpoint = model_name or DEFAULT_ENDPOINT

    # Get Databricks configuration from environment
    databricks_host = os.environ.get("DATABRICKS_HOST")
    databricks_token = os.environ.get("DATABRICKS_TOKEN")

    if not databricks_host or not databricks_token:
        raise RuntimeError(
            "Databricks credentials not found. Set DATABRICKS_HOST and DATABRICKS_TOKEN "
            "in your .env file or environment."
        )

    if use_responses_api:
        # Use custom LM for Multi-Agent Supervisor endpoints
        lm = DatabricksResponsesLM(
            model=endpoint,
            api_key=databricks_token,
            api_base=databricks_host,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        # Use standard OpenAI-compatible LM for Foundation Model APIs
        host = databricks_host.rstrip("/")
        api_base = f"{host}/serving-endpoints"
        lm = dspy.LM(
            model=f"openai/{endpoint}",
            api_key=databricks_token,
            api_base=api_base,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return lm


def configure_dspy(
    model_name: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 4000,
    use_json_adapter: bool = False,
    use_responses_api: bool = True,
    track_usage: bool = True,
) -> LM:
    """
    Configure DSPy globally with a Databricks language model.

    This sets up the default LM and adapter for all DSPy operations.
    Call this once at application startup.

    Args:
        model_name: The Databricks model endpoint name. If None, uses DEFAULT_ENDPOINT.
        temperature: Sampling temperature (0.0-1.0).
        max_tokens: Maximum tokens in the response.
        use_json_adapter: If True, use JSONAdapter for structured output.
                         Note: JSONAdapter requires OpenAI-compatible endpoints.
                         For MAS endpoints, use ChatAdapter (default).
        use_responses_api: If True, use DatabricksResponsesLM for MAS endpoints.
                          If False, use standard OpenAI-compatible LM.
        track_usage: If True, enable token usage tracking.

    Returns:
        The configured LM instance.

    Example:
        >>> from lab_6_augmentation_agent.dspy_modules import configure_dspy
        >>> lm = configure_dspy()
        >>> print(f"Configured with endpoint: {lm.model}")
    """
    lm = get_lm(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        use_responses_api=use_responses_api,
    )

    # Configure adapter based on preference
    # JSONAdapter is more efficient for models supporting response_format
    # ChatAdapter is the fallback for universal compatibility
    adapter = dspy.JSONAdapter() if use_json_adapter else dspy.ChatAdapter()

    dspy.configure(
        lm=lm,
        adapter=adapter,
        track_usage=track_usage,
    )

    print(f"[OK] DSPy configured")
    print(f"    Endpoint: {model_name or DEFAULT_ENDPOINT}")
    print(f"    Adapter: {'JSONAdapter' if use_json_adapter else 'ChatAdapter'}")
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
