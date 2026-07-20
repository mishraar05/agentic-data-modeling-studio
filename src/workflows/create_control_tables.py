# Databricks notebook source
# MAGIC %md
# MAGIC # Create Control Tables
# MAGIC
# MAGIC This task creates all control tables from generated DDL if they don't exist.
# MAGIC It applies the CREATE TABLE IF NOT EXISTS statements from generated/ddl/control/*.sql
# MAGIC to the output catalog/schema specified in job parameters.

# COMMAND ----------

# DBTITLE 1,Load parameters and initialize
import json
import os
import sys
from pathlib import Path, PurePosixPath


def _add_bundle_source_to_python_path() -> None:
    """Make the synced ``src`` root importable in a Databricks notebook task."""

    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    notebook_path = PurePosixPath(context.notebookPath().get())
    source_root = notebook_path.parents[1]
    if not source_root.as_posix().startswith("/Workspace/"):
        source_root = PurePosixPath("/Workspace") / source_root.as_posix().lstrip("/")
    source_root_text = source_root.as_posix()
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)


_add_bundle_source_to_python_path()

from agentic_data_modeler.config.job_params import resolve_job_params

# Load grouped parameters from metadata files
# Derive REPO_ROOT as bundle root (parent of src/) with /Workspace prefix
# sys.path[0] points to src/ after _add_bundle_source_to_python_path()
REPO_ROOT_RAW = str(Path(sys.path[0]).parent)
if not REPO_ROOT_RAW.startswith("/Workspace/"):
    REPO_ROOT = "/Workspace" + REPO_ROOT_RAW
else:
    REPO_ROOT = REPO_ROOT_RAW

params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=())

# Get target catalog and schema from output params
target_catalog = params["output"]["catalog"]
target_schema = params["output"]["schema"]

print(f"🎯 Target: {target_catalog}.{target_schema}")
print(f"📁 DDL directory: {REPO_ROOT}/generated/ddl/control")

# COMMAND ----------

# DBTITLE 1,Load and execute DDL files
ddl_dir = Path(REPO_ROOT) / "generated" / "ddl" / "control"

if not ddl_dir.exists():
    raise FileNotFoundError(f"DDL directory not found: {ddl_dir}")

# Find all SQL files
ddl_files = sorted(ddl_dir.glob("*.sql"))

if not ddl_files:
    raise FileNotFoundError(f"No DDL files found in {ddl_dir}")

print(f"📄 Found {len(ddl_files)} DDL files\n")

created = 0
already_existed = 0
errors = 0

for ddl_file in ddl_files:
    table_name = ddl_file.stem
    
    try:
        with open(ddl_file, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
        
        # Replace hardcoded catalog.schema with target catalog.schema
        # The generated DDL has "insurance_source_discovery.control" hardcoded
        ddl_content = ddl_content.replace(
            "insurance_source_discovery.control",
            f"{target_catalog}.{target_schema}"
        )
        
        # Split by semicolon to handle CREATE TABLE + ALTER TABLE statements
        statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
        
        for stmt in statements:
            if not stmt:
                continue
            
            # Strip leading comment lines from statement
            stmt_lines = stmt.split('\n')
            non_comment_lines = []
            for line in stmt_lines:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('--'):
                    non_comment_lines.append(line)
            
            if not non_comment_lines:
                continue  # Statement was all comments
            
            clean_stmt = '\n'.join(non_comment_lines)
            
            try:
                spark.sql(clean_stmt)
            except Exception as alter_error:
                # ALTER TABLE constraint failures are expected if constraint already exists
                error_msg = str(alter_error).lower()
                if "already exists" in error_msg or "constraint" in error_msg:
                    pass  # Ignore constraint already exists errors
                else:
                    raise
        
        print(f"✅ {table_name}")
        created += 1
        
    except Exception as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg:
            print(f"ℹ️  {table_name} (already exists)")
            already_existed += 1
        else:
            print(f"❌ {table_name}: {str(e)}")
            errors += 1

print()
print(f"✅ Created: {created}")
print(f"ℹ️  Already existed: {already_existed}")
if errors:
    print(f"❌ Errors: {errors}")
    raise RuntimeError(f"Failed to create {errors} control table(s)")

print()
print(f"✅ All control tables are ready in {target_catalog}.{target_schema}")

# COMMAND ----------

# DBTITLE 1,Verify control tables
# List all tables in the control schema to verify
tables = spark.sql(f"SHOW TABLES IN {target_catalog}.{target_schema}").collect()
print(f"📊 Control tables in {target_catalog}.{target_schema}:")
for table in sorted(tables, key=lambda t: t.tableName):
    print(f"   - {table.tableName}")

print(f"\n✅ Total: {len(tables)} tables")
