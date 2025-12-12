#!/bin/bash
#
# Setup Databricks Secrets from .env file
#
# This script reads Neo4j and Databricks configuration from .env
# and creates the required secrets in Databricks for the import notebook.
#
# Usage:
#   ./scripts/setup_databricks_secrets.sh
#
# Prerequisites:
#   - Databricks CLI installed and configured
#   - .env file with required variables
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
SCOPE_NAME="neo4j-creds"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Databricks Secrets Setup"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    echo "Please create a .env file with the required variables."
    echo "See .env.sample for reference."
    exit 1
fi

echo -e "${GREEN}Found .env file: $ENV_FILE${NC}"
echo ""

# Parse .env file manually to avoid conflicts with Databricks CLI auth
get_env_value() {
    local key=$1
    grep "^${key}=" "$ENV_FILE" | head -1 | cut -d'=' -f2-
}

NEO4J_URI=$(get_env_value "NEO4J_URI")
NEO4J_USERNAME=$(get_env_value "NEO4J_USERNAME")
NEO4J_PASSWORD=$(get_env_value "NEO4J_PASSWORD")
DATABRICKS_CATALOG=$(get_env_value "DATABRICKS_CATALOG")
DATABRICKS_SCHEMA=$(get_env_value "DATABRICKS_SCHEMA")
DATABRICKS_VOLUME=$(get_env_value "DATABRICKS_VOLUME")

# Validate required variables
REQUIRED_VARS=(
    "NEO4J_URI"
    "NEO4J_USERNAME"
    "NEO4J_PASSWORD"
    "DATABRICKS_CATALOG"
    "DATABRICKS_SCHEMA"
    "DATABRICKS_VOLUME"
)

echo "Validating required variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo -e "${GREEN}All required variables present.${NC}"
echo ""

# Construct volume path
VOLUME_PATH="/Volumes/${DATABRICKS_CATALOG}/${DATABRICKS_SCHEMA}/${DATABRICKS_VOLUME}"

# Display configuration (mask sensitive values)
echo "Configuration:"
echo "  NEO4J_URI: $NEO4J_URI"
echo "  NEO4J_USERNAME: $NEO4J_USERNAME"
echo "  NEO4J_PASSWORD: ********"
echo "  VOLUME_PATH: $VOLUME_PATH"
echo ""

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}Error: Databricks CLI not found.${NC}"
    echo "Install with: pip install databricks-cli"
    exit 1
fi

echo -e "${GREEN}Databricks CLI found.${NC}"

# Detect CLI version
CLI_VERSION=$(databricks --version 2>/dev/null | head -1 || echo "unknown")
echo "CLI Version: $CLI_VERSION"
echo ""

# Create secret scope (ignore error if already exists)
echo "Creating secret scope '$SCOPE_NAME'..."
OUTPUT=$(databricks secrets create-scope "$SCOPE_NAME" 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Secret scope '$SCOPE_NAME' created.${NC}"
else
    echo -e "${YELLOW}Secret scope '$SCOPE_NAME' already exists (continuing...).${NC}"
fi
echo ""

# Create secrets
echo "Creating secrets in scope '$SCOPE_NAME'..."
FAILED=0

echo -n "  Setting secret: username ... "
databricks secrets put-secret "$SCOPE_NAME" "username" --string-value "$NEO4J_USERNAME" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=$((FAILED + 1))
fi

echo -n "  Setting secret: password ... "
databricks secrets put-secret "$SCOPE_NAME" "password" --string-value "$NEO4J_PASSWORD" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=$((FAILED + 1))
fi

echo -n "  Setting secret: url ... "
databricks secrets put-secret "$SCOPE_NAME" "url" --string-value "$NEO4J_URI" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=$((FAILED + 1))
fi

echo -n "  Setting secret: volume_path ... "
databricks secrets put-secret "$SCOPE_NAME" "volume_path" --string-value "$VOLUME_PATH" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}$FAILED secret(s) failed to create.${NC}"
    exit 1
fi

# Verify secrets
echo "Verifying secrets..."
echo ""
databricks secrets list-secrets "$SCOPE_NAME"
echo ""

echo "========================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "========================================"
echo ""
echo "Secrets created in scope: $SCOPE_NAME"
echo ""
echo "Next steps:"
echo "  1. Upload CSV files to: $VOLUME_PATH"
echo "  2. Import notebook: src/import_financial_data_to_neo4j.ipynb"
echo "  3. Run the notebook to import data to Neo4j"
echo ""
