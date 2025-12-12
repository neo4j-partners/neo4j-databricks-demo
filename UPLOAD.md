# Proposal: Upload Data Files to Databricks Unity Catalog Volume

## Problem Statement

We have local data files that need to be accessible in Databricks for processing:

- **7 CSV files** in `data/csv/` containing structured data (accounts, banks, companies, customers, portfolio holdings, stocks, transactions)
- **14 HTML files** in `data/html/` containing unstructured content (customer profiles, company reports, investment guides, market analysis)

Currently these files only exist on the local machine. To use them in Databricks notebooks, jobs, or pipelines, they need to live in a Unity Catalog volume where Databricks can access them.

## Proposed Solution

Write a Python script that uses the Databricks SDK to:

1. **Create a catalog** (or use an existing one) to organize our data
2. **Create a schema** within that catalog for this project
3. **Create a managed volume** within that schema to store files
4. **Upload all CSV files** to a `csv/` folder in the volume
5. **Upload all HTML files** to an `html/` folder in the volume

A managed volume is the simpler option because Databricks handles the storage location automatically. No need to set up external cloud storage credentials.

After running the script, files will be accessible at paths like:
- `/Volumes/<catalog>/<schema>/<volume>/csv/accounts.csv`
- `/Volumes/<catalog>/<schema>/<volume>/html/customer_profile_james_anderson.html`

## Requirements

1. The script must connect to Databricks using the SDK's default authentication (environment variables or Databricks CLI profile)
2. The script must create a catalog named `neo4j_demo` (or skip if it already exists)
3. The script must create a schema named `raw_data` within that catalog (or skip if it already exists)
4. The script must create a managed volume named `source_files` within that schema (or skip if it already exists)
5. The script must upload all 7 CSV files from `data/csv/` to the volume under a `csv/` subfolder
6. The script must upload all 14 HTML files from `data/html/` to the volume under an `html/` subfolder
7. The script must overwrite existing files if they already exist in the volume
8. The script must print progress messages showing what is being uploaded
9. The script must handle errors gracefully and report which files failed (if any)

---

## Implementation Plan

### Phase 1: Analysis
- [x] Research Databricks SDK for Python capabilities
- [x] Confirm Unity Catalog supports programmatic catalog, schema, and volume creation
- [x] Confirm files can be uploaded via SDK without size limits
- [x] Identify all files to upload (7 CSV, 14 HTML)

### Phase 2: Implementation
- [x] Create `src/upload_to_databricks.py` script
- [x] Implement authentication using WorkspaceClient
- [x] Implement catalog creation (check if exists first)
- [x] Implement schema creation (check if exists first)
- [x] Implement managed volume creation (check if exists first)
- [x] Implement file upload function that reads local files and uploads to volume
- [x] Add progress output and error handling

### Phase 3: Verification
- [ ] Run the script against a Databricks workspace
- [ ] Verify all 21 files appear in the volume
- [ ] Verify files can be read from a Databricks notebook
- [ ] Confirm no errors or warnings during upload

---

## Technical Notes

**Databricks SDK Methods Used:**
- `WorkspaceClient()` - connect to Databricks
- `w.catalogs.create()` - create catalog
- `w.schemas.create()` - create schema
- `w.volumes.create()` with `VolumeType.MANAGED` - create managed volume
- `w.files.upload()` - upload files to volume path

**Volume Path Format:**
```
/Volumes/<catalog>/<schema>/<volume>/<subfolder>/<filename>
```

**Authentication:**
The script will use Databricks default authentication. User must have one of:
- `DATABRICKS_HOST` and `DATABRICKS_TOKEN` environment variables set
- A configured Databricks CLI profile
- Azure/AWS/GCP credentials if using cloud-native auth

**Permissions Required:**
- `CREATE_CATALOG` privilege on the metastore (or be metastore admin)
- `CREATE_SCHEMA` privilege on the catalog
- `CREATE VOLUME` privilege on the schema

---

## Files to Upload

### CSV Files (7 files)
| File | Description |
|------|-------------|
| accounts.csv | Account data |
| banks.csv | Bank data |
| companies.csv | Company data |
| customers.csv | Customer data |
| portfolio_holdings.csv | Portfolio holdings |
| stocks.csv | Stock data |
| transactions.csv | Transaction data |

### HTML Files (14 files)
| File | Description |
|------|-------------|
| bank_branch_pacific_coast_downtown.html | Bank branch info |
| bank_profile_first_national_trust.html | Bank profile |
| company_analysis_techcore_solutions.html | Company analysis |
| company_quarterly_report_global_finance.html | Quarterly report |
| customer_profile_james_anderson.html | Customer profile |
| customer_profile_maria_rodriguez.html | Customer profile |
| customer_profile_robert_chen.html | Customer profile |
| investment_strategy_guide_moderate_risk.html | Investment guide |
| market_analysis_technology_sector.html | Market analysis |
| real_estate_investment_guide.html | Investment guide |
| regulatory_compliance_banking_2023.html | Compliance docs |
| renewable_energy_investment_trends.html | Investment trends |
| retail_investment_disruption_banking_industry.html | Industry analysis |
| retirement_planning_strategies.html | Planning guide |

---

## How to Run

```bash
# 1. Install dependencies (creates .venv and uv.lock)
uv sync

# 2. Set Databricks authentication
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token-here"

# 3. Run the upload script
uv run python src/upload_to_databricks.py
```

## Next Steps

1. ~~Review and approve this proposal~~ Done
2. Ensure Databricks authentication is configured locally
3. Run the upload script with `uv run python src/upload_to_databricks.py`
4. Verify files in Databricks UI or notebook
