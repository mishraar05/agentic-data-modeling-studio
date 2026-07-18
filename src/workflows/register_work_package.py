# Databricks notebook source
# MAGIC %md
# MAGIC # Register authorized source-discovery work package
# MAGIC
# MAGIC This task writes dev-only synthetic control records after validating
# MAGIC the runtime boundary, execution identity, workspace, and authorization.

# COMMAND ----------

import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import urlparse

from pyspark.sql import functions as F


def _add_bundle_source_to_python_path() -> None:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    notebook_path = PurePosixPath(context.notebookPath().get())
    source_root = notebook_path.parents[1]
    if not source_root.as_posix().startswith("/Workspace/"):
        source_root = PurePosixPath("/Workspace") / source_root.as_posix().lstrip("/")
    source_root_text = source_root.as_posix()
    if source_root_text not in sys.path:
        sys.path.insert(0, source_root_text)


_add_bundle_source_to_python_path()

from agentic_data_modeler.control import RegistrationParameters, RuntimeRequest


RUNTIME_PARAMETERS = (
    "run_id",
    "engagement_id",
    "work_package_id",
    "lob",
    "domain",
    "source_catalog",
    "source_schema",
    "source_tables",
    "source_system_id",
    "source_product",
    "source_module",
    "source_version",
    "run_mode",
    "profiling_policy_id",
    "profiling_policy_version",
    "document_set_id",
    "requirement_set_id",
    "output_catalog",
    "output_schema",
    "contract_set_version",
)
REGISTRATION_PARAMETERS = (
    "registration_mode",
    "client_name",
    "authorization_ref",
    "effective_start_date",
    "workspace_host",
    "execution_principal",
    "source_access_granted",
)

for parameter in RUNTIME_PARAMETERS + REGISTRATION_PARAMETERS:
    dbutils.widgets.text(parameter, "")

parameters = {
    parameter: dbutils.widgets.get(parameter)
    for parameter in RUNTIME_PARAMETERS + REGISTRATION_PARAMETERS
}
request = RuntimeRequest.from_parameters(parameters)
registration = RegistrationParameters.from_parameters(parameters)

actual_principal = spark.sql("SELECT current_user() AS principal").first().principal
if actual_principal.casefold() != registration.execution_principal.casefold():
    raise ValueError(
        f"Execution principal mismatch: expected {registration.execution_principal!r}, "
        f"received {actual_principal!r}"
    )

actual_workspace = spark.conf.get("spark.databricks.workspaceUrl")
expected_workspace = urlparse(registration.workspace_host).netloc
if actual_workspace.casefold() != expected_workspace.casefold():
    raise ValueError(
        f"Workspace mismatch: expected {expected_workspace!r}, received {actual_workspace!r}"
    )

now = datetime.now(timezone.utc).replace(tzinfo=None)
provenance = {
    "work_package_id": request.work_package_id,
    "run_id": request.run_id,
    "context_snapshot_id": None,
    "source_snapshot_id": None,
    "profile_snapshot_id": None,
    "model_version": None,
    "prompt_version": None,
    "skill_version": None,
    "tool_version": "source-discovery-registration/0.1.0",
}


def _qualified(table_name: str) -> str:
    return ".".join(
        f"`{identifier}`"
        for identifier in (request.output_catalog, request.output_schema, table_name)
    )


def _insert_idempotently(
    table_name: str,
    record: dict,
    comparison_fields: tuple[str, ...],
) -> str:
    target_name = _qualified(table_name)
    target_schema = spark.table(target_name).schema
    source = spark.createDataFrame([record], schema=target_schema)
    view_name = f"_register_{table_name}"
    source.createOrReplaceTempView(view_name)
    spark.sql(
        f"""
        MERGE INTO {target_name} AS target
        USING {view_name} AS source
        ON target.record_id = source.record_id
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    rows = (
        spark.table(target_name)
        .where(F.col("record_id") == record["record_id"])
        .limit(2)
        .collect()
    )
    if len(rows) != 1:
        raise ValueError(
            f"Expected exactly one {table_name} record for {record['record_id']!r}; "
            f"found {len(rows)}"
        )
    persisted = rows[0].asDict(recursive=True)
    conflicts = [
        field
        for field in comparison_fields
        if persisted.get(field) != record.get(field)
    ]
    if conflicts:
        raise ValueError(
            f"Existing {table_name} record conflicts on fields: {sorted(conflicts)}"
        )
    return "existing" if persisted["created_at"] != now else "inserted"


engagement_record = {
    "record_id": request.engagement_id,
    "schema_version": "0.1.0",
    "engagement_id": request.engagement_id,
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "ACTIVE",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "client_name": registration.client_name,
    "authorization_ref": registration.authorization_ref,
    "effective_start_date": registration.effective_start_date,
    "effective_end_date": None,
    "workspace_host": registration.workspace_host,
    "source_access_granted": registration.source_access_granted,
    "profiling_policy": request.profiling_mode.value,
    "output_catalog": request.output_catalog,
    "output_schema": request.output_schema,
    "notes": registration.note,
}
engagement_status = _insert_idempotently(
    "engagement",
    engagement_record,
    (
        "engagement_id",
        "lob",
        "domain",
        "client_name",
        "authorization_ref",
        "effective_start_date",
        "workspace_host",
        "source_access_granted",
        "profiling_policy",
        "output_catalog",
        "output_schema",
    ),
)

work_package_record = {
    "record_id": request.work_package_id,
    "schema_version": "0.1.0",
    "engagement_id": request.engagement_id,
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "ACTIVE",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "engagement_ref": request.engagement_id,
    "workflow_state": "VALIDATED",
    "source_catalog": request.source_catalog,
    "source_schema": request.source_schema,
    "source_tables_allow_list": list(request.source_tables),
    "source_product": request.source_product,
    "source_module": request.source_module,
    "source_version": request.source_version,
    "knowledge_pack_id": None,
    "knowledge_pack_version": None,
    "output_catalog": request.output_catalog,
    "output_schema": request.output_schema,
    "authorization_validated_at": now,
    "notes": registration.note,
}
work_package_status = _insert_idempotently(
    "work_package",
    work_package_record,
    (
        "engagement_id",
        "lob",
        "domain",
        "engagement_ref",
        "workflow_state",
        "source_catalog",
        "source_schema",
        "source_tables_allow_list",
        "source_product",
        "source_module",
        "source_version",
        "output_catalog",
        "output_schema",
    ),
)

solution_run_record = {
    "record_id": request.run_id,
    "schema_version": "0.1.0",
    "engagement_id": request.engagement_id,
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "ACTIVE",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "work_package_ref": request.work_package_id,
    "run_type": "VALIDATE",
    "start_timestamp": now,
    "end_timestamp": now,
    "status": "COMPLETED",
    "error_message": None,
    "cost_usd": None,
}
solution_run_status = _insert_idempotently(
    "solution_run",
    solution_run_record,
    ("engagement_id", "lob", "domain", "work_package_ref", "run_type", "status"),
)

print("Synthetic dev work-package registration passed")
print(f"engagement_id={request.engagement_id}; status={engagement_status}")
print(f"work_package_id={request.work_package_id}; status={work_package_status}")
print(f"solution_run_id={request.run_id}; status={solution_run_status}")
print(f"request_fingerprint={request.fingerprint()}")
