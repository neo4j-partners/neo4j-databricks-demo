# Quick Start

## 1. Install Dependencies

```bash
uv sync
```

## 2. Configure Databricks Authentication

Create a `.env` file in the project root:

```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
```

To get a token: Databricks workspace → User Settings → Developer → Access tokens → Generate new token

## 3. Upload Data Files

```bash
uv run python src/upload_to_databricks.py
```

This creates:
- Catalog: `neo4j_demo`
- Schema: `neo4j_demo.raw_data`
- Volume: `neo4j_demo.raw_data.source_files`

Files are uploaded to:
- `/Volumes/neo4j_demo/raw_data/source_files/csv/*.csv`
- `/Volumes/neo4j_demo/raw_data/source_files/html/*.html`
