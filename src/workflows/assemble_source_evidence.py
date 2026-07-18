# Databricks notebook source
# MAGIC %md
# MAGIC # Assemble immutable source evidence
# MAGIC
# MAGIC This deterministic task freezes the metadata and restricted-profile
# MAGIC evidence already created for the authorized work package. It does not
# MAGIC infer business meaning or manufacture absent documents/requirements.

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
    if source_root.as_posix() not in sys.path:
        sys.path.insert(0, source_root.as_posix())


_add_bundle_source_to_python_path()

from agentic_data_modeler.control import RegistrationParameters, RuntimeRequest
from agentic_data_modeler.evidence import EvidenceItemReference, EvidenceSetManifest


RUNTIME_PARAMETERS = (
    "run_id",
    "engagement_id",
    "work_package_id",
    "lob",
    "domain",
    "source_catalog",
    "source_schema",
    "source_scope_mode",
    "source_table_include_patterns",
    "source_table_exclude_patterns",
    "source_object_types",
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
    raise ValueError("Execution principal differs from the registered authorization boundary")
actual_workspace = spark.conf.get("spark.databricks.workspaceUrl")
if actual_workspace.casefold() != urlparse(registration.workspace_host).netloc.casefold():
    raise ValueError("Workspace differs from the registered authorization boundary")
if not registration.source_access_granted:
    raise ValueError("Source evidence assembly is not authorized")
if request.document_set_id or request.requirement_set_id:
    raise ValueError(
        "Supplied document/requirement IDs require the governed normalization task "
        "before evidence-set assembly"
    )


def _qualified(table_name: str) -> str:
    return ".".join(
        f"`{identifier}`"
        for identifier in (request.output_catalog, request.output_schema, table_name)
    )


def _exactly_one(dataframe, description: str):
    rows = dataframe.limit(2).collect()
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one {description}; found {len(rows)}")
    return rows[0]


work_package_table = _qualified("work_package")
work_package = _exactly_one(
    spark.table(work_package_table).where(F.col("record_id") == request.work_package_id),
    "work package",
).asDict(recursive=True)
if work_package["workflow_state"] not in {"PROFILE_READY", "EVIDENCE_READY"}:
    raise ValueError(
        "Evidence assembly requires PROFILE_READY or EVIDENCE_READY; received "
        f"{work_package['workflow_state']!r}"
    )
if tuple(work_package["source_tables_allow_list"]) != tuple(request.source_tables):
    raise ValueError("Frozen source manifest differs from the registered work package")

source_snapshot = _exactly_one(
    spark.table(_qualified("source_snapshot")).where(
        (F.col("provenance.work_package_id") == request.work_package_id)
        & (F.col("source_catalog") == request.source_catalog)
        & (F.col("source_schema") == request.source_schema)
    ),
    "source snapshot",
).asDict(recursive=True)
source_snapshot_id = source_snapshot["record_id"]

profile_snapshot = _exactly_one(
    spark.table(_qualified("profile_snapshot")).where(
        (F.col("provenance.work_package_id") == request.work_package_id)
        & (F.col("source_snapshot_ref") == source_snapshot_id)
        & F.col("provenance.tool_version").startswith("dqx/0.15.0/")
    ),
    "approved DQX profile snapshot",
).asDict(recursive=True)
profile_snapshot_id = profile_snapshot["record_id"]

evidence_rows = (
    spark.table(_qualified("evidence_item"))
    .where(
        (F.col("work_package_ref") == request.work_package_id)
        & (F.col("source_snapshot_ref") == source_snapshot_id)
        & (
            F.col("profile_snapshot_ref").isNull()
            | (F.col("profile_snapshot_ref") == profile_snapshot_id)
        )
    )
    .select("record_id", "fingerprint", "evidence_type")
    .collect()
)
manifest = EvidenceSetManifest.from_iterable(
    work_package_id=request.work_package_id,
    source_snapshot_id=source_snapshot_id,
    profile_snapshot_id=profile_snapshot_id,
    document_set_id=None,
    requirement_set_id=None,
    items=(
        EvidenceItemReference(row.record_id, row.fingerprint, row.evidence_type)
        for row in evidence_rows
    ),
)

metadata_count = sum(item.evidence_type == "METADATA" for item in manifest.items)
profile_count = sum(item.evidence_type == "PROFILE" for item in manifest.items)
expected_metadata_count = int(source_snapshot["captured_table_count"])
if metadata_count != expected_metadata_count:
    raise ValueError(
        f"Metadata evidence coverage mismatch: expected {expected_metadata_count}, "
        f"received {metadata_count}"
    )
if profile_count != int(profile_snapshot["profiled_attribute_count"]):
    raise ValueError(
        "Profile evidence coverage differs from the approved profile snapshot"
    )

now = datetime.now(timezone.utc).replace(tzinfo=None)
evidence_set_id = manifest.evidence_set_id()
assembly_run_id = manifest.solution_run_id()
provenance = {
    "work_package_id": request.work_package_id,
    "run_id": assembly_run_id,
    "context_snapshot_id": None,
    "source_snapshot_id": source_snapshot_id,
    "profile_snapshot_id": profile_snapshot_id,
    "model_version": None,
    "prompt_version": None,
    "skill_version": None,
    "tool_version": manifest.assembler_version,
}


def _insert_record_idempotently(
    table_name: str, record: dict, comparison_fields: tuple[str, ...]
) -> None:
    target_name = _qualified(table_name)
    target_schema = spark.table(target_name).schema
    source = spark.createDataFrame([record], schema=target_schema)
    view_name = f"_assemble_{table_name}"
    source.createOrReplaceTempView(view_name)
    spark.sql(
        f"""
        MERGE INTO {target_name} AS target
        USING {view_name} AS source
        ON target.record_id = source.record_id
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    persisted = _exactly_one(
        spark.table(target_name).where(F.col("record_id") == record["record_id"]),
        f"{table_name} record",
    ).asDict(recursive=True)
    conflicts = [
        field
        for field in comparison_fields
        if persisted.get(field) != record.get(field)
    ]
    if conflicts:
        raise ValueError(
            f"Existing {table_name} record conflicts on fields: {sorted(conflicts)}"
        )


solution_run_record = {
    "record_id": assembly_run_id,
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
    "run_type": "EVIDENCE",
    "start_timestamp": now,
    "end_timestamp": now,
    "status": "COMPLETED",
    "error_message": None,
    "cost_usd": None,
}
_insert_record_idempotently(
    "solution_run",
    solution_run_record,
    ("work_package_ref", "run_type", "status"),
)

evidence_set_record = {
    "record_id": evidence_set_id,
    "schema_version": "0.1.0",
    "engagement_id": request.engagement_id,
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "COMMITTED",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "work_package_ref": request.work_package_id,
    "solution_run_ref": assembly_run_id,
    "source_snapshot_ref": source_snapshot_id,
    "profile_snapshot_ref": profile_snapshot_id,
    "document_set_ref": None,
    "requirement_set_ref": None,
    "evidence_item_count": len(manifest.items),
    "assembly_timestamp": now,
    "fingerprint": manifest.fingerprint(),
}
_insert_record_idempotently(
    "evidence_set",
    evidence_set_record,
    (
        "work_package_ref",
        "solution_run_ref",
        "source_snapshot_ref",
        "profile_snapshot_ref",
        "document_set_ref",
        "requirement_set_ref",
        "evidence_item_count",
        "fingerprint",
    ),
)

spark.sql(
    f"""
    UPDATE {work_package_table}
    SET workflow_state = 'EVIDENCE_READY', updated_at = current_timestamp()
    WHERE record_id = '{request.work_package_id}'
      AND workflow_state IN ('PROFILE_READY', 'EVIDENCE_READY')
    """
)
final_state = _exactly_one(
    spark.table(work_package_table)
    .where(F.col("record_id") == request.work_package_id)
    .select("workflow_state"),
    "final work-package state",
).workflow_state
if final_state != "EVIDENCE_READY":
    raise ValueError(f"Work package did not reach EVIDENCE_READY; received {final_state!r}")

dbutils.jobs.taskValues.set(key="evidence_set_id", value=evidence_set_id)
print("Source evidence assembly passed")
print(f"evidence_set_id={evidence_set_id}")
print(f"evidence_item_count={len(manifest.items)}")
print(f"metadata_evidence_count={metadata_count}")
print(f"profile_evidence_count={profile_count}")
print(f"fingerprint={manifest.fingerprint()}")
print(f"work_package_state={final_state}")
