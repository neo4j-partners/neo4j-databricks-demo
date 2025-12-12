"""
Upload local data files to Databricks Unity Catalog Volume.

Usage:
    uv run python src/upload_to_databricks.py           # Upload files
    uv run python src/upload_to_databricks.py --delete  # Delete all schemas/volumes in catalog

Authentication: Set DATABRICKS_HOST and DATABRICKS_TOKEN in .env file.
"""

import argparse
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

# Load .env from project root (override any existing env vars)
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Clear conflicting auth methods - use only HOST + TOKEN from .env
for var in ["DATABRICKS_CONFIG_PROFILE", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET", "DATABRICKS_ACCOUNT_ID"]:
    os.environ.pop(var, None)
from databricks.sdk.service.catalog import VolumeType
from databricks.sdk.errors import NotFound

# Configuration (can be overridden via .env)
CATALOG_NAME = os.environ.get("DATABRICKS_CATALOG", "neo4j_augmentation_demo")
SCHEMA_NAME = os.environ.get("DATABRICKS_SCHEMA", "raw_data")
VOLUME_NAME = os.environ.get("DATABRICKS_VOLUME", "source_files")

# Paths relative to project root
CSV_DIR = PROJECT_ROOT / "data" / "csv"
HTML_DIR = PROJECT_ROOT / "data" / "html"


def get_or_create_catalog(client: WorkspaceClient, catalog_name: str) -> str:
    """Create catalog if it doesn't exist, return catalog name."""
    try:
        client.catalogs.get(catalog_name)
        print(f"  Catalog '{catalog_name}' already exists")
    except NotFound:
        client.catalogs.create(name=catalog_name)
        print(f"  Created catalog '{catalog_name}'")
    return catalog_name


def get_or_create_schema(client: WorkspaceClient, catalog_name: str, schema_name: str) -> str:
    """Create schema if it doesn't exist, return full schema name."""
    full_name = f"{catalog_name}.{schema_name}"
    try:
        client.schemas.get(full_name)
        print(f"  Schema '{full_name}' already exists")
    except NotFound:
        client.schemas.create(name=schema_name, catalog_name=catalog_name)
        print(f"  Created schema '{full_name}'")
    return full_name


def get_or_create_volume(
    client: WorkspaceClient, catalog_name: str, schema_name: str, volume_name: str
) -> str:
    """Create managed volume if it doesn't exist, return full volume name."""
    full_name = f"{catalog_name}.{schema_name}.{volume_name}"
    try:
        client.volumes.read(full_name)
        print(f"  Volume '{full_name}' already exists")
    except NotFound:
        client.volumes.create(
            catalog_name=catalog_name,
            schema_name=schema_name,
            name=volume_name,
            volume_type=VolumeType.MANAGED,
        )
        print(f"  Created managed volume '{full_name}'")
    return full_name


def upload_file(client: WorkspaceClient, local_path: Path, volume_path: str) -> bool:
    """Upload a single file to the volume. Returns True on success."""
    try:
        with open(local_path, "rb") as f:
            file_bytes = f.read()
        binary_data = io.BytesIO(file_bytes)
        client.files.upload(volume_path, binary_data, overwrite=True)
        return True
    except Exception as e:
        print(f"    ERROR uploading {local_path.name}: {e}")
        return False


def upload_directory(
    client: WorkspaceClient,
    local_dir: Path,
    volume_base_path: str,
    subfolder: str,
    file_pattern: str,
) -> tuple[int, int]:
    """
    Upload all files matching pattern from local_dir to volume subfolder.
    Returns (success_count, failure_count).
    """
    success_count = 0
    failure_count = 0

    files = sorted(local_dir.glob(file_pattern))
    if not files:
        print(f"  No {file_pattern} files found in {local_dir}")
        return 0, 0

    print(f"  Uploading {len(files)} files to {subfolder}/")

    for file_path in files:
        volume_path = f"{volume_base_path}/{subfolder}/{file_path.name}"
        if upload_file(client, file_path, volume_path):
            print(f"    Uploaded: {file_path.name}")
            success_count += 1
        else:
            failure_count += 1

    return success_count, failure_count


def delete_catalog_contents(client: WorkspaceClient, catalog_name: str) -> None:
    """Delete all schemas, volumes, and tables in a catalog."""
    print(f"\n[1/2] Discovering contents of catalog '{catalog_name}'...")

    # Get all schemas (excluding information_schema)
    schemas = [s for s in client.schemas.list(catalog_name=catalog_name)
               if s.name != "information_schema"]

    if not schemas:
        print(f"  No schemas found in catalog '{catalog_name}'")
        return

    print(f"  Found {len(schemas)} schema(s)")

    print(f"\n[2/2] Deleting contents...")
    for schema in schemas:
        schema_full = f"{catalog_name}.{schema.name}"
        print(f"\n  Schema: {schema_full}")

        # Delete volumes first
        try:
            for volume in client.volumes.list(catalog_name=catalog_name, schema_name=schema.name):
                volume_full = f"{schema_full}.{volume.name}"
                print(f"    Deleting volume: {volume_full}")
                try:
                    client.volumes.delete(volume_full)
                except Exception as e:
                    print(f"      Error: {e}")
        except Exception as e:
            print(f"    Error listing volumes: {e}")

        # Delete tables
        try:
            for table in client.tables.list(catalog_name=catalog_name, schema_name=schema.name):
                table_full = f"{schema_full}.{table.name}"
                print(f"    Deleting table: {table_full}")
                try:
                    client.tables.delete(table_full)
                except Exception as e:
                    print(f"      Error: {e}")
        except Exception as e:
            print(f"    Error listing tables: {e}")

        # Delete functions
        try:
            for func in client.functions.list(catalog_name=catalog_name, schema_name=schema.name):
                func_full = f"{schema_full}.{func.name}"
                print(f"    Deleting function: {func_full}")
                try:
                    client.functions.delete(func_full)
                except Exception as e:
                    print(f"      Error: {e}")
        except Exception as e:
            print(f"    Error listing functions: {e}")

        # Delete schema
        print(f"    Deleting schema: {schema.name}")
        try:
            client.schemas.delete(schema_full)
        except Exception as e:
            print(f"      Error: {e}")


def get_client() -> WorkspaceClient:
    """Create and return authenticated WorkspaceClient."""
    try:
        client = WorkspaceClient()
        return client
    except Exception as e:
        print(f"  ERROR: Failed to connect to Databricks: {e}")
        print("\n  Make sure .env file exists with:")
        print("    DATABRICKS_HOST=https://your-workspace.cloud.databricks.com")
        print("    DATABRICKS_TOKEN=your-token")
        sys.exit(1)


def do_upload(client: WorkspaceClient) -> None:
    """Upload files to Databricks volume."""
    # Create catalog, schema, volume
    print(f"\n[2/4] Setting up Unity Catalog structure...")
    try:
        get_or_create_catalog(client, CATALOG_NAME)
        get_or_create_schema(client, CATALOG_NAME, SCHEMA_NAME)
        get_or_create_volume(client, CATALOG_NAME, SCHEMA_NAME, VOLUME_NAME)
    except Exception as e:
        print(f"  ERROR: Failed to create Unity Catalog objects: {e}")
        sys.exit(1)

    volume_base_path = f"/Volumes/{CATALOG_NAME}/{SCHEMA_NAME}/{VOLUME_NAME}"
    print(f"  Volume path: {volume_base_path}")

    # Upload CSV files
    print(f"\n[3/4] Uploading CSV files from {CSV_DIR}...")
    csv_success, csv_failure = upload_directory(
        client, CSV_DIR, volume_base_path, "csv", "*.csv"
    )

    # Upload HTML files
    print(f"\n[4/4] Uploading HTML files from {HTML_DIR}...")
    html_success, html_failure = upload_directory(
        client, HTML_DIR, volume_base_path, "html", "*.html"
    )

    # Summary
    total_success = csv_success + html_success
    total_failure = csv_failure + html_failure

    print("\n" + "=" * 60)
    print("Upload Complete!")
    print("=" * 60)
    print(f"  CSV files:  {csv_success} uploaded, {csv_failure} failed")
    print(f"  HTML files: {html_success} uploaded, {html_failure} failed")
    print(f"  Total:      {total_success} uploaded, {total_failure} failed")
    print(f"\n  Files available at: {volume_base_path}/")

    if total_failure > 0:
        print("\n  WARNING: Some files failed to upload. Check errors above.")
        sys.exit(1)


def do_delete(client: WorkspaceClient) -> None:
    """Delete all contents from the catalog."""
    delete_catalog_contents(client, CATALOG_NAME)
    print("\n" + "=" * 60)
    print("Delete Complete!")
    print("=" * 60)
    print(f"  All schemas and volumes removed from catalog '{CATALOG_NAME}'")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Upload data files to Databricks Unity Catalog")
    parser.add_argument("--delete", action="store_true", help="Delete all schemas/volumes in catalog")
    args = parser.parse_args()

    if args.delete:
        print("=" * 60)
        print(f"Databricks Unity Catalog - Delete '{CATALOG_NAME}'")
        print("=" * 60)
    else:
        print("=" * 60)
        print("Databricks Unity Catalog Volume Upload")
        print("=" * 60)

    print("\n[1/4] Connecting to Databricks..." if not args.delete else "\n[1/2] Connecting to Databricks...")
    client = get_client()
    print(f"  Connected to: {client.config.host}")

    if args.delete:
        do_delete(client)
    else:
        do_upload(client)


if __name__ == "__main__":
    main()
