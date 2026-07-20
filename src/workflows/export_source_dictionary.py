# Databricks notebook source
# DBTITLE 1,Export source dictionary to Excel
# MAGIC %md
# MAGIC # Export source dictionary to Excel
# MAGIC
# MAGIC Final phase: reads the complete semantic Source Data Dictionary from Delta
# MAGIC tables (objects, attributes, dictionary attributes, code values, open questions,
# MAGIC relationships) and renders them into a full-semantic .xlsx workbook for review
# MAGIC and consumption.
# MAGIC
# MAGIC Deterministic and LLM-free — it only renders the records already produced by
# MAGIC the analysis phases. No new approvals, no re-derivation of meaning.

# COMMAND ----------

# DBTITLE 1,Load configuration and export
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from pyspark.sql import functions as F


def _add_bundle_source_to_python_path() -> None:
    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    root = PurePosixPath(ctx.notebookPath().get()).parents[1]
    if not root.as_posix().startswith("/Workspace/"):
        root = PurePosixPath("/Workspace") / root.as_posix().lstrip("/")
    if root.as_posix() not in sys.path:
        sys.path.insert(0, root.as_posix())


_add_bundle_source_to_python_path()

from agentic_data_modeler.config.job_params import resolve_job_params
from agentic_data_modeler.export.data_dictionary_excel import build_full_source_dictionary_workbook

# Create widget for dynamic parameter
dbutils.widgets.text("run_id", "")

# Derive REPO_ROOT as bundle root (parent of src/) with /Workspace prefix
REPO_ROOT_RAW = str(Path(sys.path[0]).parent)
if not REPO_ROOT_RAW.startswith("/Workspace/"):
    REPO_ROOT = "/Workspace" + REPO_ROOT_RAW
else:
    REPO_ROOT = REPO_ROOT_RAW
params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=("run_id",))

run_id = params["run_id"]
output_catalog = params["output"]["catalog"]
output_schema = params["output"]["schema"]

print(f"✅ Config loaded: exporting run {run_id} from {output_catalog}.{output_schema}")


def _q(*idents: str) -> str:
    return ".".join(f"`{i}`" for i in idents)


def _rows(table: str, filter_col: str = "provenance.run_id") -> list[dict]:
    """Read all rows for this run_id from a table."""
    t = _q(output_catalog, output_schema, table)
    df = spark.table(t)
    # Check if the filter column exists (some tables might use run_id at top level)
    if filter_col in df.columns or "." in filter_col:
        if "." in filter_col:
            # Nested field like "provenance.run_id"
            parent, child = filter_col.rsplit(".", 1)
            df = df.where(F.col(filter_col) == run_id)
        else:
            df = df.where(F.col(filter_col) == run_id)
    return [r.asDict(recursive=True) for r in df.collect()]


# Read all SDD tables for this run_id
objects = _rows("source_object_observation", "source_snapshot_ref")
attributes = _rows("source_attribute_observation", "source_snapshot_ref")
dictionary_attributes = _rows("source_dictionary_attribute")
code_values = _rows("source_dictionary_code_value")
open_questions = _rows("open_question")
relationships = _rows("source_dictionary_relationship") if spark.catalog.tableExists(_q(output_catalog, output_schema, "source_dictionary_relationship")) else None

print(f"📊 Records loaded:")
print(f"   Objects: {len(objects)}")
print(f"   Attributes: {len(attributes)}")
print(f"   Dictionary attributes: {len(dictionary_attributes)}")
print(f"   Code values: {len(code_values)}")
print(f"   Open questions: {len(open_questions)}")
print(f"   Relationships: {len(relationships) if relationships else 0}")

# Determine output path (UC Volume or workspace files)
# Try UC Volume first if configured, otherwise use workspace files
try:
    volumes_path = f"/Volumes/{output_catalog}/{output_schema}/artifacts"
    dbutils.fs.mkdirs(volumes_path)
    out_path = f"{volumes_path}/source_dictionary_{run_id}.xlsx"
    print(f"📁 Using UC Volume: {out_path}")
except Exception as e:
    # Fall back to workspace files
    workspace_path = Path(REPO_ROOT) / "outputs" / "dictionaries"
    workspace_path.mkdir(parents=True, exist_ok=True)
    out_path = str(workspace_path / f"source_dictionary_{run_id}.xlsx")
    print(f"📁 Using workspace files: {out_path}")

# Get source snapshot info for metadata
source_snapshot_rows = spark.table(_q(output_catalog, output_schema, "source_snapshot")).where(
    F.col("source_snapshot_id") == dictionary_attributes[0]["provenance"]["source_snapshot_ref"] if dictionary_attributes else ""  
).collect()

context_snapshot_rows = spark.table(_q(output_catalog, output_schema, "context_snapshot")).where(
    F.col("provenance.run_id") == run_id
).collect()

meta = {
    "run_id": run_id,
    "catalog": params["source"]["catalog"],
    "schema": params["source"]["schema"],
    "scope_mode": "schema",  # TODO: derive from actual scope
    "source_snapshot_id": source_snapshot_rows[0]["source_snapshot_id"] if source_snapshot_rows else "",
    "context_snapshot_id": context_snapshot_rows[0]["context_snapshot_id"] if context_snapshot_rows else "",
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
}

# Build the workbook
final_path = build_full_source_dictionary_workbook(
    objects=objects,
    attributes=attributes,
    dictionary_attributes=dictionary_attributes,
    code_values=code_values,
    open_questions=open_questions,
    relationships=relationships,
    meta=meta,
    out_path=out_path,
)

print(f"✅ Excel workbook written: {final_path}")

# Emit task value for downstream tasks
dbutils.jobs.taskValues.set(key="export_path", value=str(final_path))

# COMMAND ----------

