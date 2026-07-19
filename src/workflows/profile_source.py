# Databricks notebook source
# MAGIC %md
# MAGIC # Profile authorized source tables
# MAGIC
# MAGIC This deterministic task executes only the approved aggregate-count
# MAGIC template. It never selects or persists source values or generated SQL.

# COMMAND ----------

import hashlib
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from pyspark.sql import functions as F
from databricks.labs.dqx.profiler.profiler import DQProfiler
from databricks.sdk import WorkspaceClient


def _bundle_paths() -> tuple[PurePosixPath, PurePosixPath]:
    context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    notebook_path = PurePosixPath(context.notebookPath().get())
    source_root = notebook_path.parents[1]
    if not source_root.as_posix().startswith("/Workspace/"):
        source_root = PurePosixPath("/Workspace") / source_root.as_posix().lstrip("/")
    bundle_root = source_root.parent
    if source_root.as_posix() not in sys.path:
        sys.path.insert(0, source_root.as_posix())
    return source_root, bundle_root


_, BUNDLE_ROOT = _bundle_paths()

from agentic_data_modeler.control import RegistrationParameters, RuntimeRequest
from agentic_data_modeler.evidence import (
    AttributeProfile,
    ProfileInventory,
    stable_record_id,
)
from agentic_data_modeler.source_adapters import (
    ProfilingPolicy,
    dqx_profile_ref,
    project_dqx_summary,
)


RUNTIME_PARAMETERS = (
    "run_id",
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


def _qualified(catalog: str, schema: str, table: str) -> str:
    return ".".join(f"`{identifier}`" for identifier in (catalog, schema, table))


policy_path = Path(
    BUNDLE_ROOT.as_posix(),
    "config",
    "profiling_policies",
    "source_discovery.json",
)
if not policy_path.is_file():
    raise ValueError("No approved profiling policy projection exists for this solution run")
policy_payload = json.loads(policy_path.read_text(encoding="utf-8"))
policy = ProfilingPolicy.from_mapping(
    policy_payload
)
if request.profiling_mode.value != policy.profiling_mode:
    raise ValueError("Runtime profiling mode differs from the approved policy")
if request.profiling_policy_id != policy.policy_id:
    raise ValueError("Runtime profiling policy ID differs from the approved policy")
if request.profiling_policy_version != policy.policy_version:
    raise ValueError("Runtime profiling policy version differs from the approved policy")

solution_run_table = _qualified(request.output_catalog, request.output_schema, "solution_run")
solution_runs = (
    spark.table(solution_run_table)
    .where(F.col("record_id") == request.run_id)
    .limit(2)
    .collect()
)
if len(solution_runs) != 1:
    raise ValueError(f"Expected one registered solution run; found {len(solution_runs)}")
registered = solution_runs[0].asDict(recursive=True)
expected_boundary = {
    "lob": request.lob,
    "domain": request.domain,
    "source_catalog": request.source_catalog,
    "source_schema": request.source_schema,
    "source_tables": list(request.source_tables),
    "output_catalog": request.output_catalog,
    "output_schema": request.output_schema,
}
conflicts = [key for key, value in expected_boundary.items() if registered.get(key) != value]
if conflicts:
    raise ValueError(f"Registered solution-run boundary conflicts on: {sorted(conflicts)}")
if registered["workflow_state"] not in {"METADATA_READY", "PROFILE_READY"}:
    raise ValueError(f"Profiling is not allowed from state {registered['workflow_state']!r}")

if (
    registered.get("authorization_ref") != registration.authorization_ref
    or not registered.get("source_access_granted")
    or registered.get("profiling_policy") != policy.profiling_mode
):
    raise ValueError("Solution run does not authorize the requested profiling policy")

source_snapshots = (
    spark.table(_qualified(request.output_catalog, request.output_schema, "source_snapshot"))
    .where(F.col("solution_run_ref") == request.run_id)
    .where(F.col("lifecycle_state") == "COMMITTED")
    .limit(2)
    .collect()
)
if len(source_snapshots) != 1:
    raise ValueError(f"Expected one committed source snapshot; found {len(source_snapshots)}")
source_snapshot_id = source_snapshots[0].record_id

attribute_rows = (
    spark.table(
        _qualified(request.output_catalog, request.output_schema, "source_attribute_observation")
    )
    .where(F.col("source_snapshot_ref") == source_snapshot_id)
    .select("object_name", "attribute_name", "ordinal_position")
    .orderBy("object_name", "ordinal_position")
    .collect()
)
attributes_by_table = defaultdict(list)
for row in attribute_rows:
    attributes_by_table[row.object_name].append(row.attribute_name)

if set(attributes_by_table) != set(request.source_tables):
    raise ValueError("Profile table coverage differs from the registered allow-list")
if len(attribute_rows) > policy.max_attributes:
    raise ValueError(
        f"Profile attribute coverage exceeds the approved budget: {len(attribute_rows)}"
    )

profiles = []
template_version = f"dqx/{policy.profiler_engine_version}/restricted-projection/0.1.0"
profiler = DQProfiler(WorkspaceClient(), spark=spark)
task_started = time.monotonic()
for table_name in request.source_tables:
    table_attributes = tuple(attributes_by_table[table_name])
    query_ref = dqx_profile_ref(
        catalog=request.source_catalog,
        schema=request.source_schema,
        table=table_name,
        attributes=table_attributes,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        engine_version=policy.profiler_engine_version,
    )
    query_started = time.monotonic()
    try:
        summary_stats, generated_profiles = profiler.profile(
            spark.table(_qualified(request.source_catalog, request.source_schema, table_name)),
            columns=list(table_attributes),
            options={
                "sample_fraction": None,
                "limit": None,
                "trim_strings": False,
                "remove_outliers": False,
                "llm_primary_key_detection": False,
                "max_in_count": 0,
            },
        )
        del generated_profiles
        projection = project_dqx_summary(
            object_name=table_name,
            attributes=table_attributes,
            summary_stats=summary_stats,
            query_ref=query_ref,
            engine_version=policy.profiler_engine_version,
        )
        del summary_stats
    except Exception:
        raise RuntimeError(
            f"DQX profiling failed for authorized object {table_name!r}"
        ) from None
    query_duration = time.monotonic() - query_started
    if query_duration > policy.per_query_timeout_seconds:
        raise TimeoutError(f"Aggregate profiling exceeded the per-query limit for {table_name!r}")
    if time.monotonic() - task_started > policy.total_timeout_seconds:
        raise TimeoutError("Aggregate profiling exceeded the total task limit")

    for metric in projection.metrics:
        profiles.append(
            AttributeProfile(
                object_name=table_name,
                attribute_name=metric.attribute_name,
                row_count=metric.row_count,
                null_count=metric.null_count,
                distinct_count=metric.distinct_count,
                query_ref=projection.query_ref,
            )
        )

policy_ref = (
    f"{policy.policy_id}@{policy.policy_version}:"
    + ",".join(policy.accepted_decision_refs)
)
inventory = ProfileInventory.from_iterable(
    run_id=request.run_id,
    source_snapshot_id=source_snapshot_id,
    policy_ref=policy_ref,
    template_version=template_version,
    profiles=profiles,
)
if inventory.table_count != len(request.source_tables):
    raise ValueError("Profiled table coverage is not 100%")
if inventory.attribute_count != len(attribute_rows):
    raise ValueError("Profiled attribute coverage is not 100%")

profile_snapshot_id = inventory.snapshot_id()
profile_fingerprint = inventory.fingerprint()
now = datetime.now(timezone.utc).replace(tzinfo=None)
retention_until = (now.date() + timedelta(days=policy.evidence_retention_days)).isoformat()
provenance = {
    "run_id": request.run_id,
    "context_snapshot_id": None,
    "source_snapshot_id": source_snapshot_id,
    "profile_snapshot_id": profile_snapshot_id,
    "model_version": None,
    "prompt_version": None,
    "skill_version": None,
    "tool_version": f"{template_version};{policy.policy_id}@{policy.policy_version}",
}


def _insert_records_idempotently(table_name: str, records: list[dict]) -> None:
    if not records:
        return
    target_name = _qualified(request.output_catalog, request.output_schema, table_name)
    source = spark.createDataFrame(records, schema=spark.table(target_name).schema)
    view_name = f"_profile_{table_name}"
    source.createOrReplaceTempView(view_name)
    spark.sql(
        f"""
        MERGE INTO {target_name} AS target
        USING {view_name} AS source
        ON target.record_id = source.record_id
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    expected_ids = {record["record_id"] for record in records}
    persisted_count = (
        spark.table(target_name)
        .where(F.col("record_id").isin(sorted(expected_ids)))
        .select("record_id")
        .distinct()
        .count()
    )
    if persisted_count != len(expected_ids):
        raise ValueError(f"Persistence count mismatch for {table_name}")


notes = f"{registration.note}; policy_ref={policy_ref}; retention_until={retention_until}"
profile_snapshot_record = {
    "record_id": profile_snapshot_id,
    "schema_version": "0.1.0",
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "COMMITTED",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "source_snapshot_ref": source_snapshot_id,
    "profiling_mode": policy.profiling_mode,
    "profile_timestamp": now,
    "profiled_table_count": inventory.table_count,
    "profiled_attribute_count": inventory.attribute_count,
    "profile_query_ref": inventory.query_set_ref(),
    "fingerprint": profile_fingerprint,
}
_insert_records_idempotently("profile_snapshot", [profile_snapshot_record])

evidence_records = []
profile_records = []
for profile in inventory.profiles:
    content = profile.content(policy_ref, retention_until)
    evidence_id = stable_record_id(
        "evidence_profile",
        profile_snapshot_id,
        profile.object_name,
        profile.attribute_name,
    )
    evidence_records.append(
        {
            "record_id": evidence_id,
            "schema_version": "0.1.0",
            "lob": request.lob,
            "domain": request.domain,
            "artifact_version": "synthetic-dev/0.1.0",
            "lifecycle_state": "COMMITTED",
            "provenance": provenance,
            "created_at": now,
            "updated_at": now,
            "solution_run_ref": request.run_id,
            "provenance_class": "SOURCE_FACT",
            "evidence_type": "PROFILE",
            "content": content,
            "source_snapshot_ref": source_snapshot_id,
            "profile_snapshot_ref": profile_snapshot_id,
            "document_set_ref": None,
            "document_locator": None,
            "source_object_name": profile.object_name,
            "source_attribute_name": profile.attribute_name,
            "governed_pack_id": None,
            "governed_pack_version": None,
            "fingerprint": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "notes": notes,
        }
    )
    profile_records.append(
        {
            "record_id": stable_record_id(
                "profile_evidence",
                profile_snapshot_id,
                profile.object_name,
                profile.attribute_name,
            ),
            "schema_version": "0.1.0",
            "lob": request.lob,
            "domain": request.domain,
            "artifact_version": "synthetic-dev/0.1.0",
            "lifecycle_state": "COMMITTED",
            "provenance": provenance,
            "created_at": now,
            "updated_at": now,
            "profile_snapshot_ref": profile_snapshot_id,
            "evidence_item_ref": evidence_id,
            "object_name": profile.object_name,
            "attribute_name": profile.attribute_name,
            "row_count": profile.row_count,
            "null_count": profile.null_count,
            "distinct_count": profile.distinct_count,
            "min_value": None,
            "max_value": None,
            "top_values": None,
            "pattern_sample": None,
        }
    )

_insert_records_idempotently("evidence_item", evidence_records)
_insert_records_idempotently("profile_evidence", profile_records)

persisted_count = (
    spark.table(_qualified(request.output_catalog, request.output_schema, "profile_evidence"))
    .where(F.col("profile_snapshot_ref") == profile_snapshot_id)
    .count()
)
if persisted_count != inventory.attribute_count:
    raise ValueError("Persisted profile evidence coverage is not 100%")

spark.sql(
    f"""
    UPDATE {solution_run_table}
    SET workflow_state = 'PROFILE_READY', updated_at = current_timestamp()
    WHERE record_id = '{request.run_id}'
      AND workflow_state IN ('METADATA_READY', 'PROFILE_READY')
    """
)
final_state = (
    spark.table(solution_run_table)
    .where(F.col("record_id") == request.run_id)
    .select("workflow_state")
    .first()
    .workflow_state
)
if final_state != "PROFILE_READY":
    raise ValueError(f"Solution run did not reach PROFILE_READY; received {final_state!r}")

print("Restricted DQX profiling passed")
print(f"profiler_engine=DQX@{policy.profiler_engine_version}")
print(f"profile_snapshot_id={profile_snapshot_id}")
print(f"table_count={inventory.table_count}")
print(f"attribute_count={inventory.attribute_count}")
print(f"fingerprint={profile_fingerprint}")
print(f"retention_until={retention_until}")
print(f"solution_run_state={final_state}")
