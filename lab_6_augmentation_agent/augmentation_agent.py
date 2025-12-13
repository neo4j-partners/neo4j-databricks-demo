"""
Graph Augmentation Agent

This script queries the Multi-Agent Supervisor to analyze unstructured documents
and suggest new entities and relationships for graph augmentation.

Prerequisites:
    1. Multi-Agent Supervisor deployed as a Databricks serving endpoint
    2. MLflow installed for tracing (optional but recommended)
    3. Databricks notebook context for authentication

Usage:
    Run this script in a Databricks notebook or as a job.
    Set LLM_ENDPOINT_NAME to your Multi-Agent Supervisor endpoint.
"""

import os

# =============================================================================
# CONFIGURATION
# =============================================================================

# Multi-Agent Supervisor endpoint name
# Override with environment variable or set directly
LLM_ENDPOINT_NAME = os.environ.get("LLM_ENDPOINT_NAME", "mas-3ae5a347-endpoint")

# Sample queries for graph augmentation analysis
AUGMENTATION_QUERIES = [
    "What are the emerging investment themes mentioned in the market research documents?",
    "What new entities should be extracted from the HTML data for inclusion in the graph?",
    "What customer attributes are mentioned in profiles but missing from structured data?",
    "What relationships between customers and companies are implied but not captured?",
    "What new node types would enable richer investment analysis queries?",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def setup_mlflow():
    """Enable MLflow tracing for debugging and monitoring."""
    print("=" * 70)
    print("MLFLOW SETUP")
    print("=" * 70)

    try:
        import mlflow
        mlflow.openai.autolog()
        print("[OK] MLflow tracing enabled")
        return True
    except ImportError:
        print("[WARN] MLflow not installed, tracing disabled")
        print("       Install with: %pip install -U mlflow")
        return False
    except Exception as e:
        print(f"[WARN] MLflow setup failed: {e}")
        return False


def get_client():
    """Get OpenAI-compatible client for Databricks serving endpoints."""
    print("\n" + "=" * 70)
    print("CLIENT SETUP")
    print("=" * 70)

    try:
        from databricks.sdk import WorkspaceClient

        # Initialize using notebook's default authentication
        workspace_client = WorkspaceClient()
        client = workspace_client.serving_endpoints.get_open_ai_client()

        print("[OK] Databricks workspace client initialized")
        print(f"[OK] Target endpoint: {LLM_ENDPOINT_NAME}")

        return client
    except ImportError:
        print("[ERROR] databricks-sdk not installed")
        print("        Install with: %pip install databricks-sdk")
        raise
    except Exception as e:
        print(f"[ERROR] Failed to initialize client: {e}")
        raise


def query_agent(client, query: str) -> str:
    """Send a query to the Multi-Agent Supervisor and return the response."""
    try:
        response = client.responses.create(
            model=LLM_ENDPOINT_NAME,
            input=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        return response.output[0].content[0].text
    except Exception as e:
        return f"[ERROR] Query failed: {e}"


def print_response(query: str, response: str):
    """Format and print a query-response pair."""
    print("\n" + "-" * 70)
    print(f"QUERY: {query}")
    print("-" * 70)
    print(response)
    print("-" * 70)


# =============================================================================
# AUGMENTATION ANALYSIS
# =============================================================================

def analyze_investment_themes(client) -> str:
    """Analyze emerging investment themes from market research."""
    query = "What are the emerging investment themes mentioned in the market research documents?"
    return query_agent(client, query)


def suggest_new_entities(client) -> str:
    """Suggest new entities that could be extracted from documents."""
    query = "What new entities should be extracted from the HTML data for inclusion in the graph?"
    return query_agent(client, query)


def find_missing_attributes(client) -> str:
    """Find customer attributes mentioned in profiles but missing from structured data."""
    query = "What customer attributes are mentioned in profiles but missing from the Customer nodes in the database?"
    return query_agent(client, query)


def discover_implied_relationships(client) -> str:
    """Discover relationships implied in documents but not captured in the graph."""
    query = "What relationships between customers, companies, and investments are implied in the documents but not captured in the graph?"
    return query_agent(client, query)


def run_all_analyses(client) -> dict:
    """Run all augmentation analyses and return results."""
    print("\n" + "=" * 70)
    print("GRAPH AUGMENTATION ANALYSIS")
    print("=" * 70)

    results = {}

    analyses = [
        ("Investment Themes", analyze_investment_themes),
        ("New Entities", suggest_new_entities),
        ("Missing Attributes", find_missing_attributes),
        ("Implied Relationships", discover_implied_relationships),
    ]

    for i, (name, func) in enumerate(analyses, 1):
        print(f"\n[{i}/{len(analyses)}] Analyzing: {name}")
        response = func(client)
        results[name] = response
        print_response(name, response)

    return results


# =============================================================================
# INTERACTIVE MODE
# =============================================================================

def interactive_query(client, query: str) -> str:
    """Run a custom query against the Multi-Agent Supervisor."""
    print("\n" + "=" * 70)
    print("CUSTOM QUERY")
    print("=" * 70)

    response = query_agent(client, query)
    print_response(query, response)

    return response


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("GRAPH AUGMENTATION AGENT")
    print("=" * 70)
    print(f"Endpoint: {LLM_ENDPOINT_NAME}")
    print("=" * 70)

    # Setup
    setup_mlflow()
    client = get_client()

    # Run analyses
    results = run_all_analyses(client)

    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Analyses run: {len(results)}")
    print("\nResults available in 'results' dictionary.")
    print("Use interactive_query(client, 'your question') for custom queries.")
    print("=" * 70)

    return client, results


if __name__ == "__main__":
    client, results = main()
