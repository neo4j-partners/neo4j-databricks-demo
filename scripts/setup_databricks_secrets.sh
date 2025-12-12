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

set -e

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

# Load .env file
set -a
source "$ENV_FILE"
set +a

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
echo ""

# Check if CLI is configured
if ! databricks auth describe &> /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Databricks CLI may not be configured.${NC}"
    echo "Configure with: databricks configure --token"
    echo ""
fi

# Create secret scope (ignore error if already exists)
echo "Creating secret scope '$SCOPE_NAME'..."
if databricks secrets create-scope "$SCOPE_NAME" 2>/dev/null; then
    echo -e "${GREEN}Secret scope '$SCOPE_NAME' created.${NC}"
else
    echo -e "${YELLOW}Secret scope '$SCOPE_NAME' already exists (or error occurred).${NC}"
fi
echo ""

# Function to create a secret
create_secret() {
    local key=$1
    local value=$2

    echo "  Setting secret: $key"
    if echo -n "$value" | databricks secrets put-secret "$SCOPE_NAME" "$key" --value-stdin 2>/dev/null; then
        echo -e "    ${GREEN}OK${NC}"
    else
        # Try alternative method
        if databricks secrets put-secret "$SCOPE_NAME" "$key" --string-value "$value" 2>/dev/null; then
            echo -e "    ${GREEN}OK${NC}"
        else
            echo -e "    ${RED}FAILED${NC}"
            return 1
        fi
    fi
}

# Create secrets
echo "Creating secrets in scope '$SCOPE_NAME'..."
create_secret "username" "$NEO4J_USERNAME"
create_secret "password" "$NEO4J_PASSWORD"
create_secret "url" "$NEO4J_URI"
create_secret "volume_path" "$VOLUME_PATH"
echo ""

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
