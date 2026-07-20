# Databricks notebook source
# MAGIC %md
# MAGIC # Snapshot authorized source metadata
# MAGIC
# MAGIC This deterministic task reads only Unity Catalog information-schema
# MAGIC metadata for the registered frozen manifest. It does not read source rows.

# COMMAND ----------

import json
import os
import sys
from collections import defaultdict
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
from agentic_data_modeler.evidence.metadata import (
    ColumnMetadata,
    ConstraintMetadata,
    MetadataInventory,
    ObjectMetadata,
    one_based_ordinal_offset,
)
from agentic_data_modeler.util import stable_record_id
from datetime import datetime, timezone
from pyspark.sql import functions as F
import hashlib

# Load grouped parameters from metadata files
# Derive REPO_ROOT as bundle root (parent of src/) with /Workspace prefix
REPO_ROOT_RAW = str(Path(sys.path[0]).parent)
if not REPO_ROOT_RAW.startswith("/Workspace/"):
    REPO_ROOT = "/Workspace" + REPO_ROOT_RAW
else:
    REPO_ROOT = REPO_ROOT_RAW
for w in ('run_id', 'source_tables'):
    dbutils.widgets.text(w, "")

params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=('run_id', 'source_tables'))

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



def _qualified(catalog: str, schema: str, table: str) -> str:
    return ".".join(f"`{identifier}`" for identifier in (catalog, schema, table))


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
if registered["workflow_state"] not in {"VALIDATED", "METADATA_READY", "PROFILE_READY"}:
    raise ValueError(f"Metadata snapshot is not allowed from state {registered['workflow_state']!r}")

table_literals = ",".join(f"'{table}'" for table in request.source_tables)
information_schema = f"`{request.source_catalog}`.information_schema"

table_rows = spark.sql(
    f"""
    SELECT table_name, table_type
    FROM {information_schema}.tables
    WHERE table_catalog = '{request.source_catalog}'
      AND table_schema = '{request.source_schema}'
      AND table_name IN ({table_literals})
    """
).collect()

column_rows = spark.sql(
    f"""
    SELECT
      table_name,
      column_name,
      ordinal_position,
      full_data_type,
      is_nullable,
      column_default,
      character_maximum_length,
      numeric_precision,
      numeric_scale
    FROM {information_schema}.columns
    WHERE table_catalog = '{request.source_catalog}'
      AND table_schema = '{request.source_schema}'
      AND table_name IN ({table_literals})
    ORDER BY table_name, ordinal_position
    """
).collect()

constraint_rows = spark.sql(
    f"""
    SELECT table_name, constraint_name, constraint_type
    FROM {information_schema}.table_constraints
    WHERE table_catalog = '{request.source_catalog}'
      AND table_schema = '{request.source_schema}'
      AND table_name IN ({table_literals})
    """
).collect()

key_column_rows = spark.sql(
    f"""
    SELECT table_name, constraint_name, column_name, ordinal_position
    FROM {information_schema}.key_column_usage
    WHERE table_catalog = '{request.source_catalog}'
      AND table_schema = '{request.source_schema}'
      AND table_name IN ({table_literals})
    ORDER BY table_name, constraint_name, ordinal_position
    """
).collect()

constraint_columns = defaultdict(list)
for row in key_column_rows:
    constraint_columns[(row.table_name, row.constraint_name)].append(row.column_name)

constraints_by_table = defaultdict(list)
constraint_types_by_column = defaultdict(list)
for row in constraint_rows:
    columns = tuple(constraint_columns[(row.table_name, row.constraint_name)])
    constraint = ConstraintMetadata(
        name=row.constraint_name,
        constraint_type=row.constraint_type,
        columns=columns,
    )
    constraints_by_table[row.table_name].append(constraint)
    for column_name in columns:
        constraint_types_by_column[(row.table_name, column_name)].append(row.constraint_type)

columns_by_table = defaultdict(list)
raw_ordinals_by_table = defaultdict(list)
for row in column_rows:
    raw_ordinals_by_table[row.table_name].append(int(row.ordinal_position))
ordinal_offsets = {
    table_name: one_based_ordinal_offset(positions)
    for table_name, positions in raw_ordinals_by_table.items()
}
for row in column_rows:
    columns_by_table[row.table_name].append(
        ColumnMetadata(
            name=row.column_name,
            ordinal_position=int(row.ordinal_position) + ordinal_offsets[row.table_name],
            data_type=row.full_data_type,
            nullable=row.is_nullable.upper() == "YES",
            default_value=row.column_default,
            length=int(row.character_maximum_length) if row.character_maximum_length is not None else None,
            precision=int(row.numeric_precision) if row.numeric_precision is not None else None,
            scale=int(row.numeric_scale) if row.numeric_scale is not None else None,
            constraint_types=tuple(constraint_types_by_column[(row.table_name, row.column_name)]),
        )
    )


def _object_type(raw_type: str) -> str:
    normalized = raw_type.upper().replace(" ", "_")
    if normalized == "MATERIALIZED_VIEW":
        return "MATERIALIZED_VIEW"
    if normalized.endswith("VIEW"):
        return "VIEW"
    return "TABLE"


inventory = MetadataInventory.from_iterables(
    catalog=request.source_catalog,
    schema=request.source_schema,
    expected_tables=request.source_tables,
    objects=(
        ObjectMetadata(
            name=row.table_name,
            object_type=_object_type(row.table_type),
            columns=tuple(columns_by_table[row.table_name]),
            constraints=tuple(constraints_by_table[row.table_name]),
        )
        for row in table_rows
    ),
)
inventory.validate()
snapshot_fingerprint = inventory.fingerprint()
snapshot_id = inventory.snapshot_id(request.run_id)
now = datetime.now(timezone.utc).replace(tzinfo=None)
provenance = {
    "run_id": request.run_id,
    "context_snapshot_id": None,
    "source_snapshot_id": snapshot_id,
    "profile_snapshot_id": None,
    "model_version": None,
    "prompt_version": None,
    "skill_version": None,
    "tool_version": inventory.query_template_version,
}


def _insert_records_idempotently(table_name: str, records: list[dict]) -> None:
    if not records:
        return
    target_name = _qualified(request.output_catalog, request.output_schema, table_name)
    target_schema = spark.table(target_name).schema
    source = spark.createDataFrame(records, schema=target_schema)
    view_name = f"_metadata_{table_name}"
    source.createOrReplaceTempView(view_name)
    spark.sql(
        f"""
        MERGE INTO {target_name} AS target
        USING {view_name} AS source
        ON target.record_id = source.record_id
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    record_ids = [record["record_id"] for record in records]
    persisted_count = (
        spark.table(target_name)
        .where(F.col("record_id").isin(record_ids))
        .select("record_id")
        .distinct()
        .count()
    )
    if persisted_count != len(set(record_ids)):
        raise ValueError(
            f"Persistence count mismatch for {table_name}: expected {len(set(record_ids))}, "
            f"received {persisted_count}"
        )


snapshot_record = {
    "record_id": snapshot_id,
    "schema_version": "0.1.0",
    "lob": request.lob,
    "domain": request.domain,
    "artifact_version": "synthetic-dev/0.1.0",
    "lifecycle_state": "COMMITTED",
    "provenance": provenance,
    "created_at": now,
    "updated_at": now,
    "solution_run_ref": request.run_id,
    "snapshot_timestamp": now,
    "source_catalog": request.source_catalog,
    "source_schema": request.source_schema,
    "captured_table_count": inventory.table_count,
    "captured_column_count": inventory.column_count,
    "metadata_query_ref": inventory.query_template_version,
    "fingerprint": snapshot_fingerprint,
    "notes": "" ,
}
_insert_records_idempotently("source_snapshot", [snapshot_record])

evidence_records = []
object_records = []
attribute_records = []
for source_object in inventory.objects:
    content = inventory.object_evidence_content(source_object.name)
    evidence_fingerprint = hashlib.sha256(content.encode("utf-8")).hexdigest()
    evidence_id = stable_record_id("evidence_metadata", snapshot_id, source_object.name)
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
            "evidence_type": "METADATA",
            "content": content,
            "source_snapshot_ref": snapshot_id,
            "profile_snapshot_ref": None,
            "document_set_ref": None,
            "document_locator": f"uc://{request.source_catalog}/{request.source_schema}/{source_object.name}",
            "source_object_name": source_object.name,
            "source_attribute_name": None,
            "governed_pack_id": None,
            "governed_pack_version": None,
            "fingerprint": evidence_fingerprint,
            "notes": "" ,
        }
    )
    object_records.append(
        {
            "record_id": stable_record_id("source_object", snapshot_id, source_object.name),
            "schema_version": "0.1.0",
            "lob": request.lob,
            "domain": request.domain,
            "artifact_version": "synthetic-dev/0.1.0",
            "lifecycle_state": "COMMITTED",
            "provenance": provenance,
            "created_at": now,
            "updated_at": now,
            "source_snapshot_ref": snapshot_id,
            "evidence_item_ref": evidence_id,
            "catalog_name": request.source_catalog,
            "schema_name": request.source_schema,
            "object_name": source_object.name,
            "object_type": source_object.object_type,
            "attribute_count": len(source_object.columns),
            "constraint_observations": [
                {
                    "constraint_type": constraint.constraint_type,
                    "constraint_details": json.dumps(
                        {"name": constraint.name, "columns": sorted(constraint.columns)},
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
                for constraint in source_object.constraints
            ],
        }
    )
    for column in source_object.columns:
        attribute_records.append(
            {
                "record_id": stable_record_id(
                    "source_attribute", snapshot_id, source_object.name, column.name
                ),
                "schema_version": "0.1.0",
                "lob": request.lob,
                "domain": request.domain,
                "artifact_version": "synthetic-dev/0.1.0",
                "lifecycle_state": "COMMITTED",
                "provenance": provenance,
                "created_at": now,
                "updated_at": now,
                "source_snapshot_ref": snapshot_id,
                "evidence_item_ref": evidence_id,
                "object_name": source_object.name,
                "attribute_name": column.name,
                "ordinal_position": column.ordinal_position,
                "data_type": column.data_type,
                "nullable": column.nullable,
                "default_value": column.default_value,
                "length": column.length,
                "precision": column.precision,
                "scale": column.scale,
                "constraint_role": column.constraint_role(),
            }
        )

_insert_records_idempotently("evidence_item", evidence_records)
_insert_records_idempotently("source_object_observation", object_records)
_insert_records_idempotently("source_attribute_observation", attribute_records)

persisted_object_count = (
    spark.table(_qualified(request.output_catalog, request.output_schema, "source_object_observation"))
    .where(F.col("source_snapshot_ref") == snapshot_id)
    .count()
)
persisted_attribute_count = (
    spark.table(_qualified(request.output_catalog, request.output_schema, "source_attribute_observation"))
    .where(F.col("source_snapshot_ref") == snapshot_id)
    .count()
)
if persisted_object_count != inventory.table_count:
    raise ValueError("Persisted source-object coverage is not 100%")
if persisted_attribute_count != inventory.column_count:
    raise ValueError("Persisted source-attribute coverage is not 100%")

spark.sql(
    f"""
    UPDATE {solution_run_table}
    SET workflow_state = 'METADATA_READY', updated_at = current_timestamp()
    WHERE record_id = '{request.run_id}'
      AND workflow_state = 'VALIDATED'
    """
)
final_state = (
    spark.table(solution_run_table)
    .where(F.col("record_id") == request.run_id)
    .select("workflow_state")
    .first()
    .workflow_state
)
if final_state not in {"METADATA_READY", "PROFILE_READY"}:
    raise ValueError(f"Solution run did not preserve metadata readiness; received {final_state!r}")

print("Metadata snapshot passed")
print(f"snapshot_id={snapshot_id}")
print(f"table_count={inventory.table_count}")
print(f"column_count={inventory.column_count}")
print(f"fingerprint={snapshot_fingerprint}")
print(f"solution_run_state={final_state}")