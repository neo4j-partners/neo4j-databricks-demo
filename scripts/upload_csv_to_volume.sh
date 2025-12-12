#!/bin/bash
#
# Upload CSV files to Databricks Unity Catalog Volume
#
# This script uploads all CSV files from data/csv/ to the configured
# Databricks Unity Catalog Volume.
#
# Usage:
#   ./scripts/upload_csv_to_volume.sh
#
# Prerequisites:
#   - Databricks CLI installed and configured
#   - .env file with DATABRICKS_CATALOG, DATABRICKS_SCHEMA, DATABRICKS_VOLUME
#   - Unity Catalog Volume already created
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
CSV_DIR="$PROJECT_ROOT/data/csv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Upload CSV Files to Databricks Volume"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    exit 1
fi

# Check if CSV directory exists
if [ ! -d "$CSV_DIR" ]; then
    echo -e "${RED}Error: CSV directory not found at $CSV_DIR${NC}"
    exit 1
fi

# Load .env file
set -a
source "$ENV_FILE"
set +a

# Validate required variables
if [ -z "$DATABRICKS_CATALOG" ] || [ -z "$DATABRICKS_SCHEMA" ] || [ -z "$DATABRICKS_VOLUME" ]; then
    echo -e "${RED}Error: Missing required variables in .env${NC}"
    echo "Required: DATABRICKS_CATALOG, DATABRICKS_SCHEMA, DATABRICKS_VOLUME"
    exit 1
fi

# Construct volume path
VOLUME_PATH="/Volumes/${DATABRICKS_CATALOG}/${DATABRICKS_SCHEMA}/${DATABRICKS_VOLUME}"

echo "Source directory: $CSV_DIR"
echo "Target volume: $VOLUME_PATH"
echo ""

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}Error: Databricks CLI not found.${NC}"
    echo "Install with: pip install databricks-cli"
    exit 1
fi

# List CSV files to upload
CSV_FILES=(
    "customers.csv"
    "banks.csv"
    "accounts.csv"
    "companies.csv"
    "stocks.csv"
    "portfolio_holdings.csv"
    "transactions.csv"
)

echo "Files to upload:"
for file in "${CSV_FILES[@]}"; do
    if [ -f "$CSV_DIR/$file" ]; then
        size=$(wc -c < "$CSV_DIR/$file" | tr -d ' ')
        echo "  - $file ($(numfmt --to=iec-i --suffix=B $size 2>/dev/null || echo "${size} bytes"))"
    else
        echo -e "  - $file ${RED}(NOT FOUND)${NC}"
    fi
done
echo ""

# Confirm upload
read -p "Proceed with upload? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Upload cancelled."
    exit 0
fi
echo ""

# Upload each file
echo "Uploading files..."
SUCCESS_COUNT=0
FAIL_COUNT=0

for file in "${CSV_FILES[@]}"; do
    local_path="$CSV_DIR/$file"
    remote_path="$VOLUME_PATH/$file"

    if [ ! -f "$local_path" ]; then
        echo -e "  $file: ${RED}SKIPPED (not found)${NC}"
        ((FAIL_COUNT++))
        continue
    fi

    echo -n "  $file: "
    if databricks fs cp "$local_path" "dbfs:$remote_path" --overwrite 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}FAILED${NC}"
        ((FAIL_COUNT++))
    fi
done

echo ""
echo "========================================"
echo "Upload Summary"
echo "========================================"
echo -e "  Successful: ${GREEN}$SUCCESS_COUNT${NC}"
echo -e "  Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}All files uploaded successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Import notebook: src/import_financial_data_to_neo4j.ipynb"
    echo "  2. Run the notebook to import data to Neo4j"
else
    echo -e "${YELLOW}Some files failed to upload. Check errors above.${NC}"
    exit 1
fi
