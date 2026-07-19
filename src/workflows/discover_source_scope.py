# Databricks notebook source
# MAGIC %md
# MAGIC # Resolve authorized source scope
# MAGIC
# MAGIC This deterministic task reads Unity Catalog metadata only. It resolves
# MAGIC the approved catalog/schema policy into an exact, sorted table manifest
# MAGIC and freezes that manifest for all downstream tasks in this job run.

# COMMAND ----------

import json
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


def _add_bundle_source_to_python_path() -> None:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    notebook_path = PurePosixPath(context.notebookPath().get())
    source_root = notebook_path.parents[1]
    if not source_root.as_posix().startswith("/Workspace/"):
        source_root = PurePosixPath("/Workspace") / source_root.as_posix().lstrip("/")
    if source_root.as_posix() not in sys.path:
        sys.path.insert(0, source_root.as_posix())


_add_bundle_source_to_python_path()

from agentic_data_modeler.config.job_params import resolve_job_params
from agentic_data_modeler.control import (
    RuntimeRequest,
    SourceObjectCandidate,
    resolve_source_manifest,
)

# Load grouped parameters from metadata files
REPO_ROOT = Path("/Workspace/Users/cleancoding109@gmail.com/agentic-data-modeling-studio")
for w in ('run_id',):
    dbutils.widgets.text(w, "")

params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=('run_id',))

# Identity authorization check (§5 safety decision: keep this check)
actual_principal = spark.sql("SELECT current_user() AS principal").first().principal
if actual_principal.casefold() != params["identity"]["execution_principal"].casefold():
    raise ValueError("Execution principal differs from the authorized identity")
actual_workspace = spark.conf.get("spark.databricks.workspaceUrl")
expected_host = params["identity"]["workspace_host"]
if actual_workspace.casefold() != urlparse(expected_host).netloc.casefold():
    raise ValueError("Workspace differs from the authorized identity")
if params["identity"]["source_access_granted"].lower() != "true":
    raise ValueError("Source metadata discovery is not authorized")

# Build RuntimeRequest from grouped params
request_params = {
    "run_id": params["run_id"],
    "lob": params["scope"]["lob"],
    "domain": params["scope"]["domain"],
    "source_catalog": params["source"]["catalog"],
    "source_schema": params["source"]["schema"],
    "source_scope_mode": params["scope"]["source_scope_mode"],
    "source_table_include_patterns": json.dumps(params["scope"]["source_table_include_patterns"]),
    "source_table_exclude_patterns": json.dumps(params["scope"]["source_table_exclude_patterns"]),
    "source_object_types": json.dumps(params["scope"]["source_object_types"]),
    "source_tables": "",  # Explicit tables handled via manifest resolution
    "source_system_id": params["source"]["system_id"],
    "source_product": params["source"]["product"],
    "source_module": params["source"]["module"],
    "source_version": params["source"]["version"],
    "run_mode": params["profiling"]["run_mode"],
    "profiling_policy_id": params["profiling"]["policy_id"],
    "profiling_policy_version": params["profiling"]["policy_version"],
    "document_set_id": "",
    "requirement_set_id": "",
    "output_catalog": params["output"]["catalog"],
    "output_schema": params["output"]["schema"],
    "contract_set_version": params["contracts"]["set_version"],
}
request = RuntimeRequest.from_parameters(request_params)


def _object_type(raw_type: str) -> str:
    normalized = raw_type.upper().replace(" ", "_")
    if normalized == "MATERIALIZED_VIEW":
        return "MATERIALIZED_VIEW"
    if normalized.endswith("VIEW"):
        return "VIEW"
    return "TABLE"


information_schema = f"`{request.source_catalog}`.information_schema"
visible_rows = spark.sql(
    f"""
    SELECT table_name, table_type
    FROM {information_schema}.tables
    WHERE table_catalog = '{request.source_catalog}'
      AND table_schema = '{request.source_schema}'
    ORDER BY table_name
    """
).collect()

manifest = resolve_source_manifest(
    catalog=request.source_catalog,
    schema=request.source_schema,
    scope_mode=request.source_scope_mode,
    visible_objects=(
        SourceObjectCandidate(row.table_name, _object_type(row.table_type))
        for row in visible_rows
    ),
    explicit_tables=request.source_tables,
    include_patterns=request.source_table_include_patterns,
    exclude_patterns=request.source_table_exclude_patterns,
    object_types=request.source_object_types,
)
serialized_tables = json.dumps(list(manifest.tables), separators=(",", ":"))
if len(serialized_tables.encode("utf-8")) > 45_000:
    raise ValueError(
        "Resolved source manifest exceeds the current Databricks task-value transport limit"
    )

dbutils.jobs.taskValues.set(key="source_tables", value=list(manifest.tables))
dbutils.jobs.taskValues.set(key="source_manifest_fingerprint", value=manifest.fingerprint())
dbutils.jobs.taskValues.set(key="source_table_count", value=len(manifest.tables))

print("Source-scope discovery passed")
print(f"scope_mode={manifest.scope_mode.value}")
print(f"source_table_count={len(manifest.tables)}")
print(f"source_manifest_fingerprint={manifest.fingerprint()}")