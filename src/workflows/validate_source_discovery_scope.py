# Databricks notebook source
# MAGIC %md
# MAGIC # Validate source-discovery run scope
# MAGIC
# MAGIC This entry point parses per-run job parameters and fails before any
# MAGIC source read when scope, policy, contract version, or output separation
# MAGIC is incomplete or unsafe.

# COMMAND ----------

# DBTITLE 1,Load and validate parameters
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
from agentic_data_modeler.control import RuntimeRequest

# Load grouped parameters from metadata files
REPO_ROOT = Path(
    os.environ.get("BUNDLE_ROOT")
    or dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        .notebookPath().get().rsplit("/src/", 1)[0]
)
for w in ("run_id",):
    dbutils.widgets.text(w, "")

params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=("run_id",))

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

# Observability output
print("Source-discovery scope validation passed")
print(f"run_id={request.run_id}")
print(f"lob={request.lob}")
print(f"domain={request.domain}")
print(f"source_scope_mode={request.source_scope_mode.value}")
print(f"requested_explicit_table_count={len(request.source_tables)}")
print(f"run_mode={request.profiling_mode.value}")
print(f"request_fingerprint={request.fingerprint()}")
