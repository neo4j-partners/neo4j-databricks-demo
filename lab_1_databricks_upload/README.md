# Lab 1: Upload Data to Databricks

This lab uploads CSV and HTML source files from the `data/` directory to your Databricks Unity Catalog volume.

There are two ways to upload the data:
1. **Manual upload** (Option A) - Drag and drop files directly in the Databricks UI
2. **Programmatic upload** (Option B) - Using the Python script with Databricks SDK

## Option A: Manual Upload via Databricks UI

Upload files directly through the Databricks web interface.

### Prerequisites

- Access to your Databricks workspace
- `WRITE VOLUME` privilege on the target volume
- `USE CATALOG` privilege on the parent catalog

### Steps to Upload

1. **Access the upload interface** using one of these methods:
   - **From the sidebar**: Click **New** → **Add data** → **Upload files to volume**
   - **From Catalog Explorer**: Navigate to your volume, then click **Add** → **Upload to volume**
   - **From a notebook**: Go to **File** → **Upload files to volume**

2. **Select destination**: Navigate to or paste the volume path:
   ```
   /Volumes/<catalog>/<schema>/<volume>/
   ```

3. **Create subdirectories**: Create `csv/` and `html/` directories in your volume if they don't exist

4. **Upload CSV files**:
   - Navigate to the `csv/` directory in your volume
   - Drag and drop all files from `data/csv/` in this repository, or click **Browse** to select them
   - Files to upload:
     - `accounts.csv`
     - `banks.csv`
     - `companies.csv`
     - `customers.csv`
     - `portfolio_holdings.csv`
     - `stocks.csv`
     - `transactions.csv`

5. **Upload HTML files**:
   - Navigate to the `html/` directory in your volume
   - Drag and drop all files from `data/html/` in this repository

For more details, see the official Databricks documentation: [Upload files to a Unity Catalog volume](https://docs.databricks.com/aws/en/ingestion/file-upload/upload-to-volume)

---

## Option B: Programmatic Upload

If you prefer to automate the upload process using Python and the Databricks SDK.

### Prerequisites

Before running the upload script, ensure you have:

1. **Python environment configured** - Installed dependencies with `uv sync`
2. **Databricks authentication set up** - You need one of the following:
   - Databricks personal access token configured in your environment
   - OAuth configured via Databricks CLI (`databricks auth login`)
   - Service principal credentials
3. Created your Databricks catalog, schema, and volume
4. Configured environment variables in `.env`
5. Set up Databricks secrets (see main [README.md](../README.md))

### What Gets Uploaded

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

### Running the Upload

From the project root directory:

```bash
uv run python lab_1_databricks_upload/upload_to_databricks.py
```

### Destination Paths

Files are uploaded to your Databricks volume at:
- `/Volumes/<catalog>/<schema>/<volume>/csv/*.csv`
- `/Volumes/<catalog>/<schema>/<volume>/html/*.html`

For example, with the default configuration:
- `/Volumes/neo4j_demo/raw_data/source_files/csv/customers.csv`
- `/Volumes/neo4j_demo/raw_data/source_files/html/customer_profile.html`

---

## Verification

After uploading (via either method), verify the files in Databricks:

1. Navigate to **Catalog** in your Databricks workspace
2. Browse to your volume: `<catalog>` → `<schema>` → `<volume>`
3. Confirm all CSV and HTML files are present

## Next Steps

Continue to [Lab 2: Import Data to Neo4j](../lab_2_neo4j_import/README.md) to load the data into your Neo4j graph database.
