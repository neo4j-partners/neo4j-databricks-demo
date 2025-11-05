#!/bin/bash

# Neo4j Databricks Demo Archive Creation Script
# This script creates a compressed archive of the project excluding virtual environments and data files

# Get the project directory name
PROJECT_DIR=$(basename "$PWD")

# Create archive name with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="neo4j-databricks-demo_${TIMESTAMP}.tar.gz"

echo "Creating archive: ${ARCHIVE_NAME}"
echo "Excluding: venv/, .venv/, data/, .claude/"

# Create tar.gz archive, excluding venv and data directories
tar -czf "../${ARCHIVE_NAME}" \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='data' \
    --exclude='.claude' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.DS_Store' \
    -C .. \
    "${PROJECT_DIR}"

# Check if archive was created successfully
if [ $? -eq 0 ]; then
    echo "✓ Archive created successfully: ../${ARCHIVE_NAME}"
    echo "Archive size: $(du -h "../${ARCHIVE_NAME}" | cut -f1)"
else
    echo "✗ Error creating archive"
    exit 1
fi
