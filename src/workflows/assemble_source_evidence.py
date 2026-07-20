# Databricks notebook source
# MAGIC %md
# MAGIC # Assemble immutable source evidence
# MAGIC
# MAGIC This deterministic task freezes the metadata and restricted-profile
# MAGIC evidence already created for the authorized solution run. It does not
# MAGIC infer business meaning or manufacture absent documents/requirements.

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

from agentic_data_modeler.config.job_params import resolve_job_params
from agentic_data_modeler.control import RuntimeRequest

# Load grouped parameters from metadata files
# Derive REPO_ROOT as bundle root (parent of src/) with /Workspace prefix
REPO_ROOT_RAW = str(Path(sys.path[0]).parent)
if not REPO_ROOT_RAW.startswith("/Workspace/"):
    REPO_ROOT = "/Workspace" + REPO_ROOT_RAW
else:
    REPO_ROOT = REPO_ROOT_RAW
for w in ('run_id', 'source_tables', 'source_snapshot_id'):
    dbutils.widgets.text(w, "")

params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=('run_id', 'source_tables', 'source_snapshot_id'))

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


solution_run_table = _qualified("solution_run")
solution_run = _exactly_one(
    spark.table(solution_run_table).where(F.col("record_id") == request.run_id),
    "solution run",
).asDict(recursive=True)
if solution_run["workflow_state"] not in {"PROFILE_READY", "EVIDENCE_READY"}:
    raise ValueError(
        "Evidence assembly requires PROFILE_READY or EVIDENCE_READY; received "
        f"{solution_run['workflow_state']!r}"
    )
if tuple(solution_run["source_tables"]) != tuple(request.source_tables):
    raise ValueError("Frozen source manifest differs from the registered solution run")

source_snapshot = _exactly_one(
    spark.table(_qualified("source_snapshot")).where(
        (F.col("provenance.run_id") == request.run_id)
        & (F.col("source_catalog") == request.source_catalog)
        & (F.col("source_schema") == request.source_schema)
    ),
    "source snapshot",
).asDict(recursive=True)
source_snapshot_id = source_snapshot["record_id"]

profile_snapshot = _exactly_one(
    spark.table(_qualified("profile_snapshot")).where(
        (F.col("provenance.run_id") == request.run_id)
        & (F.col("source_snapshot_ref") == source_snapshot_id)
        & F.col("provenance.tool_version").startswith("dqx/0.15.0/")
    ),
    "approved DQX profile snapshot",
).asDict(recursive=True)
profile_snapshot_id = profile_snapshot["record_id"]

evidence_rows = (
    spark.table(_qualified("evidence_item"))
    .where(
        (F.col("solution_run_ref") == request.run_id)
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
    run_id=request.run_id,
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
provenance = {
    "run_id": request.run_id,
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


evidence_set_record = {
    "record_id": evidence_set_id,
    "schema_version": "0.1.0",
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "COMMITTED",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "solution_run_ref": request.run_id,
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
    UPDATE {solution_run_table}
    SET workflow_state = 'EVIDENCE_READY', updated_at = current_timestamp()
    WHERE record_id = '{request.run_id}'
      AND workflow_state IN ('PROFILE_READY', 'EVIDENCE_READY')
    """
)
final_state = _exactly_one(
    spark.table(solution_run_table)
    .where(F.col("record_id") == request.run_id)
    .select("workflow_state"),
    "final solution-run state",
).workflow_state
if final_state != "EVIDENCE_READY":
    raise ValueError(f"Solution run did not reach EVIDENCE_READY; received {final_state!r}")

dbutils.jobs.taskValues.set(key="evidence_set_id", value=evidence_set_id)
dbutils.jobs.taskValues.set(key="source_snapshot_id", value=source_snapshot_id)
print("Source evidence assembly passed")
print(f"evidence_set_id={evidence_set_id}")
print(f"evidence_item_count={len(manifest.items)}")
print(f"metadata_evidence_count={metadata_count}")
print(f"profile_evidence_count={profile_count}")
print(f"fingerprint={manifest.fingerprint()}")
print(f"solution_run_state={final_state}")