# Databricks notebook source
# MAGIC %md
# MAGIC # LLM source relationship analyst
# MAGIC
# MAGIC Uses a bounded context snapshot, approved semantic memory, a producer
# MAGIC model, and an independent critic. Model output is DRAFT and contract gated.

# COMMAND ----------

import json
import os
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

from agentic_data_modeler.analyst.model import DatabricksFoundationModel
from agentic_data_modeler.config.job_params import resolve_job_params
from agentic_data_modeler.control import RuntimeRequest

# Load grouped parameters from metadata files
# Derive REPO_ROOT as bundle root (parent of src/) with /Workspace prefix
REPO_ROOT_RAW = str(Path(sys.path[0]).parent)
if not REPO_ROOT_RAW.startswith("/Workspace/"):
    REPO_ROOT = "/Workspace" + REPO_ROOT_RAW
else:
    REPO_ROOT = REPO_ROOT_RAW
for w in ('run_id', 'context_snapshot_id', 'source_snapshot_id', 'evidence_set_id'):
    dbutils.widgets.text(w, "")

params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=('run_id', 'context_snapshot_id', 'source_snapshot_id', 'evidence_set_id'))

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

# Extract endpoints from metadata and enforce independence (PROTECTED guard)
producer_endpoint = params["models"]["producer_endpoint"]
critic_endpoint   = params["models"]["critic_endpoint"]
if producer_endpoint == critic_endpoint:
    raise ValueError("Critic endpoint must differ from the producer endpoint (independence).")

# Initialize models
producer = DatabricksFoundationModel(producer_endpoint)
critic   = DatabricksFoundationModel(critic_endpoint) if critic_endpoint else None

print(f"✅ Models initialized: Producer={producer_endpoint}, Critic={critic_endpoint}")

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
    "source_tables": params.get("source_tables", ""),  # Dynamic task value
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

# TODO: Wire relationship analysis logic here using producer & critic models
print("⚠️  Relationship analysis logic not yet implemented")