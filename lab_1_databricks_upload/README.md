# Lab 1: Upload Data to Databricks

This lab uploads CSV and HTML source files from the `data/` directory to your Databricks Unity Catalog volume.

## Prerequisites

Before running this lab, ensure you have completed the setup steps in the main [README.md](../README.md):

1. Installed dependencies with `uv sync`
2. Created your Databricks catalog, schema, and volume
3. Configured environment variables in `.env`
4. Set up Databricks secrets

## What Gets Uploaded

The script uploads the following files to your Databricks volume:

**CSV Files** (`data/csv/`):
- `accounts.csv` - Customer account information
- `banks.csv` - Financial institution data
- `companies.csv` - Corporate entity information
- `customers.csv` - Customer profile data
- `portfolio_holdings.csv` - Investment portfolio positions
- `stocks.csv` - Stock and security data
- `transactions.csv` - Financial transaction records

**HTML Files** (`data/html/`):
- Customer profiles and investment documents for knowledge agent analysis

## Running the Upload

From the project root directory:

```bash
uv run python lab_1_databricks_upload/upload_to_databricks.py
```

## Destination Paths

Files are uploaded to your Databricks volume at:
- `/Volumes/<catalog>/<schema>/<volume>/csv/*.csv`
- `/Volumes/<catalog>/<schema>/<volume>/html/*.html`

For example, with the default configuration:
- `/Volumes/neo4j_demo/raw_data/source_files/csv/customers.csv`
- `/Volumes/neo4j_demo/raw_data/source_files/html/customer_profile.html`

## Verification

After uploading, verify the files in Databricks:

1. Navigate to **Catalog** in your Databricks workspace
2. Browse to your volume: `<catalog>` → `<schema>` → `<volume>`
3. Confirm all CSV and HTML files are present

## Next Steps

Continue to [Lab 2: Import Data to Neo4j](../lab_2_neo4j_import/README.md) to load the data into your Neo4j graph database.
