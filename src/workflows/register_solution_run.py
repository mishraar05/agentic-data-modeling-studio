# Databricks notebook source
# MAGIC %md
# MAGIC # Register bounded solution run
# MAGIC
# MAGIC Creates the single run-rooted control record after validating source scope,
# MAGIC execution identity, workspace, and authorization.

# COMMAND ----------

import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import urlparse

from pyspark.sql import functions as F


def _add_bundle_source_to_python_path() -> None:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    root = PurePosixPath(context.notebookPath().get()).parents[1]
    if not root.as_posix().startswith("/Workspace/"):
        root = PurePosixPath("/Workspace") / root.as_posix().lstrip("/")
    if root.as_posix() not in sys.path:
        sys.path.insert(0, root.as_posix())


_add_bundle_source_to_python_path()

from agentic_data_modeler.control import RegistrationParameters, RuntimeRequest


RUNTIME_PARAMETERS = (
    "run_id", "lob", "domain", "source_catalog", "source_schema",
    "source_scope_mode", "source_table_include_patterns", "source_table_exclude_patterns",
    "source_object_types", "source_tables", "source_system_id", "source_product",
    "source_module", "source_version", "run_mode", "profiling_policy_id",
    "profiling_policy_version", "document_set_id", "requirement_set_id",
    "output_catalog", "output_schema", "contract_set_version",
)
REGISTRATION_PARAMETERS = (
    "registration_mode", "client_name", "authorization_ref", "effective_start_date",
    "workspace_host", "execution_principal", "source_access_granted",
)
for name in RUNTIME_PARAMETERS + REGISTRATION_PARAMETERS:
    dbutils.widgets.text(name, "")
parameters = {name: dbutils.widgets.get(name) for name in RUNTIME_PARAMETERS + REGISTRATION_PARAMETERS}
request = RuntimeRequest.from_parameters(parameters)
registration = RegistrationParameters.from_parameters(parameters)

actual_principal = spark.sql("SELECT current_user() AS principal").first().principal
if actual_principal.casefold() != registration.execution_principal.casefold():
    raise ValueError("Execution principal does not match the authorized principal")
actual_workspace = spark.conf.get("spark.databricks.workspaceUrl")
if actual_workspace.casefold() != urlparse(registration.workspace_host).netloc.casefold():
    raise ValueError("Workspace does not match the authorized workspace")

now = datetime.now(timezone.utc).replace(tzinfo=None)
provenance = {
    "run_id": request.run_id,
    "context_snapshot_id": None,
    "source_snapshot_id": None,
    "profile_snapshot_id": None,
    "model_version": None,
    "prompt_version": None,
    "skill_version": None,
    "tool_version": "solution-run-registration/0.2.0",
}
record = {
    "record_id": request.run_id,
    "schema_version": "0.2.0",
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "0.2.0",
    "lifecycle_state": "ACTIVE",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "workflow_state": "VALIDATED",
    "source_catalog": request.source_catalog,
    "source_schema": request.source_schema,
    "source_tables": list(request.source_tables),
    "source_product": request.source_product,
    "source_module": request.source_module,
    "source_version": request.source_version,
    "knowledge_pack_id": None,
    "knowledge_pack_version": None,
    "output_catalog": request.output_catalog,
    "output_schema": request.output_schema,
    "authorization_ref": registration.authorization_ref,
    "source_access_granted": registration.source_access_granted,
    "profiling_policy": request.profiling_mode.value,
    "run_type": "VALIDATE",
    "start_timestamp": now,
    "end_timestamp": now,
    "status": "COMPLETED",
    "error_message": None,
    "cost_usd": None,
}

target = ".".join(f"`{v}`" for v in (request.output_catalog, request.output_schema, "solution_run"))
df = spark.createDataFrame([record], schema=spark.table(target).schema)
df.createOrReplaceTempView("_solution_run_stage")
spark.sql(f"""
    MERGE INTO {target} t USING _solution_run_stage s ON t.record_id = s.record_id
    WHEN NOT MATCHED THEN INSERT *
""")
rows = spark.table(target).where(F.col("record_id") == request.run_id).limit(2).collect()
if len(rows) != 1:
    raise ValueError("Solution-run registration did not persist exactly one record")
persisted = rows[0].asDict(recursive=True)
for field in ("lob", "domain", "source_catalog", "source_schema", "source_tables", "output_catalog", "output_schema"):
    if persisted[field] != record[field]:
        raise ValueError(f"Existing solution run conflicts on {field}")

print(f"solution_run_id={request.run_id}")
print(f"workflow_state={persisted['workflow_state']}")
print(f"request_fingerprint={request.fingerprint()}")
